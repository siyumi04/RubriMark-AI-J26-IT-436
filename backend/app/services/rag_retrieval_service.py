"""
RAG Knowledge Retrieval Service for RubriMark AI (Research Component IT23376472).

Phase 1: Retrieval-Augmented Generation — Knowledge Base Loader & Retriever.

Responsibilities:
- Loads lecturer rubric knowledge from the CSV file
  (data/RubriMark_RAG_Lecturer_Rubrics_Draft_v1_1.csv).
- Parses structured criterion details (JSON), marking guides, model answers,
  Bloom's levels, learning outcomes, and lecturer guidelines into knowledge documents.
- Embeds documents using the locally installed Ollama nomic-embed-text model.
- Retrieves the top-k most relevant documents for a new query using cosine similarity.
- Operates without ChromaDB (pure Python vector cosine similarity).
- Preserves metadata: Question ID, RAG Topic, Rubric Version, Lecturer Approval,
  RAG Trust Level, Source File, Review Required.
- Clearly marks all Pending records as [UNVERIFIED DRAFT REFERENCE] — never as approved ground truth.
- Falls back gracefully to TF-IDF keyword-based cosine similarity if Ollama is unavailable or times out.
- Formats retrieved context with question, model answer, criteria, marking guidelines,
  Bloom's level, and learning outcome ready for LLM consumption.

NOTE: This service implements RETRIEVAL ONLY (Phase 1).
LLM-augmented rubric generation and lecturer rejection/regeneration are NOT included here.
"""

import csv
import json
import math
import os
import re
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import httpx

try:
    from app.core.config import settings
except ImportError:
    settings = None

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration & Path Discovery
# ---------------------------------------------------------------------------

def _get_setting(attr: str, default: Any) -> Any:
    if settings is not None and hasattr(settings, attr):
        val = getattr(settings, attr)
        if val is not None:
            return val
    return os.environ.get(attr, default)


OLLAMA_BASE_URL: str = str(_get_setting("OLLAMA_BASE_URL", "http://localhost:11434"))
OLLAMA_EMBED_MODEL: str = str(_get_setting("OLLAMA_EMBED_MODEL", "nomic-embed-text"))
OLLAMA_TIMEOUT_SECONDS: float = float(_get_setting("OLLAMA_TIMEOUT_SECONDS", 60.0))


def resolve_csv_path(custom_path: Optional[str] = None) -> str:
    """
    Locates the lecturer rubrics CSV file across multiple candidate directory layouts.
    Ensures tests and FastAPI runtime reliably find the file whether run from root or backend.
    """
    if custom_path and os.path.isfile(custom_path):
        return os.path.abspath(custom_path)

    # 1. Environment variable
    env_path = os.environ.get("RAG_KNOWLEDGE_CSV_PATH")
    if env_path and os.path.isfile(env_path):
        return os.path.abspath(env_path)

    candidate_filenames = [
        "IT23376472_Complete_Lecturer_Rubric_Template (1).csv",
        "IT23376472_Complete_Lecturer_Rubric_Template.csv",
        "lecturer_rubric.csv",
        "RubriMark_RAG_Lecturer_Rubrics_Draft_v1_1.csv",
    ]
    current_file = Path(__file__).resolve()

    candidate_dirs = [
        current_file.parents[3] / "data",  # workspace_root/data
        current_file.parents[2] / "data",  # backend/data
        Path.cwd() / "data",               # cwd/data
        Path.cwd().parent / "data",        # cwd/../data
        Path("data"),                      # relative data
        Path("../data"),                   # relative ../data
    ]

    for fname in candidate_filenames:
        for cdir in candidate_dirs:
            candidate_file = cdir / fname
            if candidate_file.is_file():
                return str(candidate_file.resolve())

    # 2. Config setting
    if settings is not None and hasattr(settings, "RAG_KNOWLEDGE_CSV_PATH"):
        cfg_path = getattr(settings, "RAG_KNOWLEDGE_CSV_PATH")
        if cfg_path and os.path.isfile(cfg_path):
            return os.path.abspath(cfg_path)

    # Fallback default
    return str((current_file.parents[3] / "data" / candidate_filenames[0]).resolve())


DEFAULT_CSV_PATH = resolve_csv_path()


# ---------------------------------------------------------------------------
# Knowledge Document Model
# ---------------------------------------------------------------------------

class KnowledgeDocument:
    """
    A single RAG knowledge document constructed from one row of the lecturer rubrics CSV.
    Contains the composite text content for embedding and all preserved metadata.
    """

    def __init__(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None,
    ):
        self.doc_id = doc_id
        self.content = content
        self.metadata = metadata
        self.embedding = embedding

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "has_embedding": self.embedding is not None,
        }


# ---------------------------------------------------------------------------
# CSV Loader — builds knowledge documents
# ---------------------------------------------------------------------------

class RAGKnowledgeLoader:
    """
    Reads the verified lecturer rubrics CSV and constructs KnowledgeDocument objects
    with composite text content and preserved metadata.
    """

    @staticmethod
    def _parse_criterion_json(raw: str) -> List[Dict[str, Any]]:
        """
        Safely parses the 'Criterion Details (JSON)' column.
        Handles standard JSON, double-escaped CSV quotes, and empty values.
        """
        if not raw or not str(raw).strip():
            return []
        cleaned = str(raw).strip()
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

        # Handle double-quotes commonly found in CSV exports
        try:
            if '""' in cleaned:
                unescaped = cleaned.replace('""', '"')
                parsed = json.loads(unescaped)
                if isinstance(parsed, list):
                    return parsed
        except json.JSONDecodeError:
            pass

        # Handle wrapped quotes
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
            try:
                inner = cleaned[1:-1].replace('""', '"')
                parsed = json.loads(inner)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass

        logger.warning("Failed to parse criterion JSON: %s", raw[:120])
        return []

    @staticmethod
    def _parse_marking_guide_fallback(marking_guide: str, marks_allocation: str = "", max_marks_val: str = "10") -> List[Dict[str, Any]]:
        """
        Parses criteria from a text marking guide if 'Criterion Details (JSON)' is absent.
        Handles semicolons and allocations e.g. 'Class definition (2); Object definition (2)'.
        """
        raw_parts = [p.strip() for p in marking_guide.split(";") if p.strip()]
        criteria = []
        alloc_nums = []
        if marks_allocation:
            try:
                alloc_nums = [float(x.strip()) for x in marks_allocation.split("+") if x.strip()]
            except Exception:
                alloc_nums = []
        try:
            total_m = float(max_marks_val)
        except Exception:
            total_m = 10.0

        for idx, part in enumerate(raw_parts):
            m = re.match(r'^(.*?)(?:\s*\(([0-9.]+)\))?$', part)
            if m:
                c_name = m.group(1).strip()
                c_marks = float(m.group(2)) if m.group(2) else (alloc_nums[idx] if idx < len(alloc_nums) else (total_m / max(len(raw_parts), 1)))
            else:
                c_name = part
                c_marks = alloc_nums[idx] if idx < len(alloc_nums) else (total_m / max(len(raw_parts), 1))
            criteria.append({
                "criterion": c_name,
                "max_marks": int(c_marks) if c_marks.is_integer() else c_marks,
                "description": f"Evaluates {c_name.lower()} according to marking guidelines.",
                "full_credit": f"Full credit up to {c_marks} marks for accurate, complete response.",
                "partial_credit": "Partial credit for partially correct explanation.",
                "zero_credit": "0 marks for incorrect or missing answer.",
            })
        return criteria

    @staticmethod
    def _build_trust_label(approval_status: str, trust_level: str) -> str:
        """
        Generates an explicit trust/provenance label.
        Approved rubrics are marked as APPROVED_LECTURER_RUBRIC.
        Rejected rubrics are strictly flagged and excluded from trusted knowledge.
        Pending records are ALWAYS clearly marked as unverified draft references.
        ASCII-safe to prevent cp1252 Windows encoding exceptions.
        """
        status_clean = (approval_status or "").strip().lower()
        if status_clean == "approved":
            return "APPROVED_LECTURER_RUBRIC"
        if status_clean == "rejected":
            return (
                "[REJECTED RUBRIC - NEVER TRUSTED] This rubric was rejected by a lecturer and "
                "must NEVER be treated as trusted knowledge or used for student scoring."
            )
        return (
            "[UNVERIFIED DRAFT REFERENCE] This rubric has NOT been approved by a lecturer. "
            f"Approval status: {approval_status or 'Pending'}. "
            f"Trust level: {trust_level or 'DRAFT_REFERENCE_ONLY'}. "
            "Do NOT present as verified ground truth."
        )

    @staticmethod
    def format_document_context(metadata: Dict[str, Any]) -> str:
        """
        Formats a single knowledge document into a comprehensive, readable text block
        including all required fields: question, model answer, criteria, marking guidelines,
        Bloom's level, learning outcome, source file, approval status, and trust level.
        Pending rubrics are clearly marked at the top as unverified draft references.
        Rejected rubrics are explicitly marked as rejected and excluded from trusted knowledge.
        """
        qid = metadata.get("question_id", "")
        topic = metadata.get("rag_topic", "")
        question = metadata.get("question", "")
        model_answer = metadata.get("model_answer", "")
        learning_outcome = metadata.get("learning_outcome", "")
        blooms_level = metadata.get("blooms_level", "")
        blooms_rationale = metadata.get("blooms_rationale", "")
        marking_guide = metadata.get("marking_guide", "")
        marks_allocation = metadata.get("marks_allocation", "")
        max_marks = metadata.get("max_marks", "")
        lecturer_guidelines = metadata.get("lecturer_guidelines", "")
        source_file = metadata.get("source_file", "")
        approval = metadata.get("lecturer_approval", "Pending")
        trust_level = metadata.get("rag_trust_level", "DRAFT_REFERENCE_ONLY")
        is_verified = metadata.get("is_verified", False)
        review_required = metadata.get("review_required", "")
        criteria = metadata.get("criteria", [])

        status_clean = (approval or "").strip().lower()
        # Header with explicit verification banner
        if status_clean == "rejected":
            banner = (
                "======================================================================\n"
                f"[REJECTED RUBRIC - NEVER TRUSTED - NOT GROUND TRUTH - {qid}]\n"
                f"Approval Status: Rejected | Trust Level: REJECTED_UNTRUSTED\n"
                "WARNING: This rubric was formally rejected by a lecturer.\n"
                "======================================================================"
            )
        elif is_verified and status_clean == "approved":
            banner = (
                "======================================================================\n"
                f"[APPROVED LECTURER RUBRIC - {qid}]\n"
                f"Status: Approved | Trust Level: {trust_level}\n"
                "======================================================================"
            )
        else:
            banner = (
                "======================================================================\n"
                f"[UNVERIFIED DRAFT REFERENCE - NOT GROUND TRUTH - {qid}]\n"
                f"Approval Status: {approval} | Trust Level: {trust_level}\n"
                f"Review Required: {review_required or 'Yes - verify with lecturer'}\n"
                "======================================================================"
            )

        # Format criteria breakdown
        criteria_lines = []
        for i, c in enumerate(criteria, 1):
            c_name = c.get("criterion", f"Criterion {i}")
            c_marks = c.get("max_marks", "?")
            c_desc = c.get("description", "")
            c_full = c.get("full_credit", "")
            c_part = c.get("partial_credit", "")
            c_zero = c.get("zero_credit", "")
            criteria_lines.append(
                f"  {i}. {c_name} (Max Marks: {c_marks})\n"
                f"     - Description: {c_desc}\n"
                f"     - Full Credit: {c_full}\n"
                f"     - Partial Credit: {c_part}\n"
                f"     - Zero Credit: {c_zero}"
            )
        criteria_str = "\n".join(criteria_lines) if criteria_lines else "  No criteria defined."

        block = (
            f"{banner}\n"
            f"Question ID: {qid}\n"
            f"RAG Topic: {topic}\n"
            f"Source File: {source_file}\n"
            f"Question: {question}\n"
            f"Model Answer: {model_answer}\n"
            f"Learning Outcome: {learning_outcome}\n"
            f"Bloom's Taxonomy Level: {blooms_level}"
            + (f" — {blooms_rationale}" if blooms_rationale else "") + "\n"
            f"Marking Guide: {marking_guide}\n"
            f"Marks Allocation: {marks_allocation} (Total Max Marks: {max_marks})\n"
            f"Lecturer Guidelines: {lecturer_guidelines}\n"
            f"Rubric Criteria:\n{criteria_str}"
        )
        return block

    @classmethod
    def load_from_csv(cls, csv_path: Optional[str] = None) -> List[KnowledgeDocument]:
        """
        Reads the CSV file and returns a list of KnowledgeDocument objects.
        Each document contains a composite text block suitable for embedding and preserved metadata.
        """
        resolved_path = resolve_csv_path(csv_path)
        if not os.path.isfile(resolved_path):
            raise FileNotFoundError(
                f"RAG knowledge CSV not found at: {resolved_path}. "
                "Ensure 'data/RubriMark_RAG_Lecturer_Rubrics_Draft_v1_1.csv' exists."
            )

        documents: List[KnowledgeDocument] = []

        with open(resolved_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                question_id = (row.get("Question ID") or "").strip()
                if not question_id:
                    continue  # skip empty rows

                question = (row.get("Question") or "").strip()
                model_answer = (row.get("Model Answer") or "").strip()
                learning_outcome = (row.get("Learning Outcome (Proposed)") or "").strip()
                blooms_level = (row.get("Bloom’s Taxonomy Level (Proposed)") or row.get("Bloom's Taxonomy Level (Proposed)") or "").strip()
                blooms_rationale = (row.get("Bloom’s Level Rationale") or row.get("Bloom's Level Rationale") or "").strip()
                marking_guide = (row.get("Marking Guide") or "").strip()
                marks_allocation = (row.get("Marks Allocation") or "").strip()
                max_marks = (row.get("Maximum Marks") or "").strip()
                lecturer_guidelines = (row.get("Lecturer Guidelines") or "").strip()
                # Parse structured criteria
                criteria_raw = row.get("Criterion Details (JSON)", "")
                criteria = cls._parse_criterion_json(criteria_raw)
                if not criteria and marking_guide:
                    criteria = cls._parse_marking_guide_fallback(marking_guide, marks_allocation, max_marks)

                source_file = (row.get("Source File") or os.path.basename(resolved_path)).strip()
                review_required = (row.get("Review Required") or "Yes - verify rubric and criteria with lecturer").strip()
                rag_topic = (row.get("RAG Topic") or "Java OOP").strip()
                retrieval_keywords = (row.get("Retrieval Keywords") or "").strip()
                if not retrieval_keywords:
                    words = re.findall(r'\b[a-zA-Z]{4,}\b', question)
                    retrieval_keywords = ";".join(words[:8])
                rubric_version = (row.get("Rubric Version") or "draft-template-v1").strip()
                lecturer_approval = (row.get("Lecturer Approval") or "Pending").strip()
                rag_trust_level = (row.get("RAG Trust Level") or "DRAFT_REFERENCE_ONLY").strip()

                # Verification flag
                is_verified = lecturer_approval.lower() == "approved"

                # Trust label
                trust_label = cls._build_trust_label(lecturer_approval, rag_trust_level)

                # Metadata
                metadata = {
                    "question_id": question_id,
                    "question": question,
                    "model_answer": model_answer,
                    "learning_outcome": learning_outcome,
                    "blooms_level": blooms_level,
                    "blooms_rationale": blooms_rationale,
                    "marking_guide": marking_guide,
                    "marks_allocation": marks_allocation,
                    "max_marks": max_marks,
                    "lecturer_guidelines": lecturer_guidelines,
                    "rag_topic": rag_topic,
                    "retrieval_keywords": [k.strip() for k in retrieval_keywords.split(";") if k.strip()],
                    "criteria": criteria,
                    "rubric_version": rubric_version,
                    "lecturer_approval": lecturer_approval,
                    "rag_trust_level": rag_trust_level,
                    "is_verified": is_verified,
                    "trust_label": trust_label,
                    "source_file": source_file,
                    "review_required": review_required,
                }

                # Pre-generate formatted context block
                formatted_context = cls.format_document_context(metadata)
                metadata["formatted_context"] = formatted_context

                # Criteria text summary for composite embedding content
                criteria_text_parts = []
                for i, crit in enumerate(criteria, 1):
                    crit_name = crit.get("criterion", "")
                    crit_marks = crit.get("max_marks", "")
                    crit_desc = crit.get("description", "")
                    criteria_text_parts.append(f"{crit_name} ({crit_marks} marks): {crit_desc}")
                criteria_summary = "; ".join(criteria_text_parts)

                # Composite content for embedding
                # Contains question, model answer, criteria, marking guide, Bloom's level, learning outcome, and keywords
                content = (
                    f"Question: {question}\n"
                    f"RAG Topic: {rag_topic}\n"
                    f"Keywords: {retrieval_keywords}\n"
                    f"Model Answer: {model_answer}\n"
                    f"Learning Outcome: {learning_outcome}\n"
                    f"Bloom's Level: {blooms_level}\n"
                    f"Marking Guide: {marking_guide}\n"
                    f"Rubric Criteria: {criteria_summary}"
                )

                documents.append(
                    KnowledgeDocument(
                        doc_id=question_id,
                        content=content,
                        metadata=metadata,
                    )
                )

        logger.info("Loaded %d knowledge documents from %s", len(documents), resolved_path)
        return documents


# ---------------------------------------------------------------------------
# Ollama Embedding Client
# ---------------------------------------------------------------------------

class OllamaEmbeddingClient:
    """
    Communicates with the local Ollama server to obtain text embeddings using nomic-embed-text.
    Handles connection failures, timeouts, and model errors gracefully.
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_EMBED_MODEL,
        timeout: float = OLLAMA_TIMEOUT_SECONDS,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._available: Optional[bool] = None

    def check_availability(self) -> bool:
        """
        Checks whether the Ollama server is reachable and whether the embedding model is available.
        """
        try:
            with httpx.Client(timeout=4.0) as client:
                r = client.get(f"{self.base_url}/api/tags")
                if r.status_code == 200:
                    models_data = r.json().get("models", [])
                    model_names = [m.get("name", "") for m in models_data]
                    # Check if requested model is in model list (ignoring tag if specified without tag)
                    model_match = any(
                        self.model == name or self.model == name.split(":")[0]
                        for name in model_names
                    )
                    if not model_match:
                        logger.warning(
                            "Ollama server is up, but model '%s' was not found in installed models: %s",
                            self.model,
                            model_names,
                        )
                    self._available = True
                    return True
                self._available = False
                return False
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as e:
            logger.warning("Ollama server not reachable at %s: %s", self.base_url, e)
            self._available = False
            return False

    @property
    def is_available(self) -> bool:
        if self._available is None:
            self.check_availability()
        return self._available

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Obtains an embedding vector for the given text from Ollama nomic-embed-text.
        Returns None on failure (connection error, timeout, model error).
        """
        if not text or not text.strip():
            return None

        # 1. Try /api/embeddings (standard Ollama embeddings endpoint)
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("embedding")
                    if embedding and isinstance(embedding, list) and len(embedding) > 0:
                        return embedding
                    logger.warning("Ollama returned empty embedding for model '%s'.", self.model)
                elif response.status_code == 404:
                    # Try /api/embed (newer Ollama format)
                    embed_response = client.post(
                        f"{self.base_url}/api/embed",
                        json={"model": self.model, "input": text},
                    )
                    if embed_response.status_code == 200:
                        data = embed_response.json()
                        embeddings = data.get("embeddings", [])
                        if embeddings and isinstance(embeddings[0], list):
                            return embeddings[0]
                else:
                    logger.warning(
                        "Ollama embedding request failed: HTTP %d — %s",
                        response.status_code,
                        response.text[:200],
                    )
        except httpx.TimeoutException:
            logger.warning("Ollama embedding request timed out after %.0fs.", self.timeout)
        except (httpx.ConnectError, OSError) as e:
            logger.warning("Ollama connection error: %s", e)
            self._available = False
        except Exception as e:
            logger.warning("Unexpected error during Ollama embedding: %s", e)

        return None


# ---------------------------------------------------------------------------
# TF-IDF Fallback Similarity (no external ML dependencies)
# ---------------------------------------------------------------------------

class TFIDFFallback:
    """
    Lightweight TF-IDF keyword-based similarity fallback for when Ollama is unavailable.
    Operates without numpy, scikit-learn, or any ML libraries.
    """

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer with lowercasing."""
        return re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())

    @classmethod
    def compute_tf(cls, tokens: List[str]) -> Dict[str, float]:
        """Computes term frequency for a list of tokens."""
        tf: Dict[str, float] = {}
        total = len(tokens) if tokens else 1
        for t in tokens:
            tf[t] = tf.get(t, 0.0) + 1.0
        return {k: v / total for k, v in tf.items()}

    @classmethod
    def compute_idf(cls, doc_token_lists: List[List[str]]) -> Dict[str, float]:
        """Computes inverse document frequency across all documents."""
        n_docs = len(doc_token_lists)
        if n_docs == 0:
            return {}
        df: Dict[str, int] = {}
        for tokens in doc_token_lists:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[t] = df.get(t, 0) + 1
        return {k: math.log((n_docs + 1) / (v + 1)) + 1.0 for k, v in df.items()}

    @classmethod
    def tfidf_vector(cls, tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
        """Computes a TF-IDF vector for a single document."""
        tf = cls.compute_tf(tokens)
        return {k: v * idf.get(k, 1.0) for k, v in tf.items()}

    @staticmethod
    def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Computes cosine similarity between two sparse vectors."""
        all_keys = set(vec_a.keys()).union(set(vec_b.keys()))
        if not all_keys:
            return 0.0
        dot = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in all_keys)
        mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
        if mag_a * mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# Core RAG Retrieval Service
# ---------------------------------------------------------------------------

class RAGRetrievalService:
    """
    Phase 1 RAG Retrieval Service.

    Loads knowledge documents from the lecturer rubrics CSV, embeds them using
    Ollama nomic-embed-text (or falls back to TF-IDF), and retrieves the most relevant
    documents for a given question using cosine similarity.

    Operates without ChromaDB (vector cosine similarity implemented natively).
    """

    _build_trust_label = staticmethod(RAGKnowledgeLoader._build_trust_label)
    format_document_context = staticmethod(RAGKnowledgeLoader.format_document_context)

    def __init__(
        self,
        csv_path: Optional[str] = None,
        ollama_base_url: str = OLLAMA_BASE_URL,
        ollama_model: str = OLLAMA_EMBED_MODEL,
        ollama_timeout: float = OLLAMA_TIMEOUT_SECONDS,
    ):
        self.csv_path = resolve_csv_path(csv_path)
        self.documents: List[KnowledgeDocument] = []
        self.ollama_client = OllamaEmbeddingClient(
            base_url=ollama_base_url,
            model=ollama_model,
            timeout=ollama_timeout,
        )
        self._initialized = False
        self._embedding_mode: str = "not_initialized"

        # TF-IDF fallback state
        self._idf: Dict[str, float] = {}
        self._doc_tfidf_vectors: List[Dict[str, float]] = []
        self._doc_token_lists: List[List[str]] = []

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def embedding_mode(self) -> str:
        """Returns 'ollama', 'tfidf_fallback', or 'not_initialized'."""
        return self._embedding_mode

    def initialize(self, force_fallback: bool = False) -> Dict[str, Any]:
        """
        Loads knowledge documents from CSV and embeds them.

        If Ollama is available (and force_fallback is False), uses real Ollama nomic-embed-text embeddings.
        Otherwise, builds TF-IDF vectors as a graceful fallback.

        Returns a status summary dict.
        """
        start_time = time.time()

        # Step 1: Load documents from CSV
        self.documents = RAGKnowledgeLoader.load_from_csv(self.csv_path)
        if not self.documents:
            return {
                "status": "error",
                "message": "No documents loaded from CSV.",
                "documents_loaded": 0,
                "embedding_mode": "none",
                "csv_path": self.csv_path,
            }

        # Step 2: Attempt Ollama embeddings
        use_ollama = False
        ollama_status = "skipped"
        embed_failures = 0

        if not force_fallback:
            if self.ollama_client.check_availability():
                logger.info(
                    "Ollama server available. Embedding %d documents with model '%s'...",
                    len(self.documents),
                    self.ollama_client.model,
                )
                ollama_status = "connected"
                use_ollama = True

                for doc in self.documents:
                    embedding = self.ollama_client.get_embedding(doc.content)
                    if embedding is not None:
                        doc.embedding = embedding
                    else:
                        embed_failures += 1
                        logger.warning("Failed to embed document %s via Ollama.", doc.doc_id)

                # If all embeddings failed, fall back
                if embed_failures == len(self.documents):
                    logger.warning("All Ollama embeddings failed. Falling back to TF-IDF.")
                    use_ollama = False
                    ollama_status = "all_embeddings_failed"
            else:
                ollama_status = "unreachable"

        # Step 3: Build TF-IDF fallback (always built for offline resilience)
        self._doc_token_lists = [
            TFIDFFallback._tokenize(doc.content) for doc in self.documents
        ]
        self._idf = TFIDFFallback.compute_idf(self._doc_token_lists)
        self._doc_tfidf_vectors = [
            TFIDFFallback.tfidf_vector(tokens, self._idf)
            for tokens in self._doc_token_lists
        ]

        # Determine active embedding mode
        if use_ollama and embed_failures < len(self.documents):
            self._embedding_mode = "ollama"
        else:
            self._embedding_mode = "tfidf_fallback"

        self._initialized = True
        elapsed = round(time.time() - start_time, 2)

        status_summary = {
            "status": "initialized",
            "documents_loaded": len(self.documents),
            "embedding_mode": self._embedding_mode,
            "ollama_status": ollama_status,
            "ollama_model": self.ollama_client.model,
            "ollama_embed_failures": embed_failures,
            "tfidf_vocabulary_size": len(self._idf),
            "initialization_time_seconds": elapsed,
            "document_ids": [d.doc_id for d in self.documents],
            "csv_path": self.csv_path,
        }
        logger.info("RAG Retrieval Service initialized: %s", status_summary)
        return status_summary

    @staticmethod
    def _cosine_similarity_vectors(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Cosine similarity between two dense float vectors (pure Python, no numpy or chromadb needed).
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = math.sqrt(sum(a * a for a in vec_a))
        mag_b = math.sqrt(sum(b * b for b in vec_b))
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot / (mag_a * mag_b)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Retrieves the top-k most relevant knowledge documents for the given question/query.

        Returns a dictionary with:
        - query: input query string
        - retrieval_mode: 'ollama' or 'tfidf_fallback'
        - ollama_model: model name used if ollama mode
        - results: list of matching records with similarity score, criteria, guidelines, trust level
        - retrieved_context: concatenated formatted context ready for LLM consumption
        - total_documents_searched: total records searched
        - results_returned: count of results matching criteria
        """
        if not self._initialized:
            self.initialize()

        scored_docs: List[Tuple[float, KnowledgeDocument]] = []
        active_mode = self._embedding_mode

        if self._embedding_mode == "ollama":
            query_embedding = self.ollama_client.get_embedding(query)
            if query_embedding is not None:
                for doc in self.documents:
                    if doc.embedding is not None:
                        sim = self._cosine_similarity_vectors(query_embedding, doc.embedding)
                        scored_docs.append((sim, doc))
                    else:
                        # Fallback for this document if its embedding failed
                        idx = next(
                            (i for i, d in enumerate(self.documents) if d.doc_id == doc.doc_id),
                            None,
                        )
                        if idx is not None:
                            q_tokens = TFIDFFallback._tokenize(query)
                            q_vec = TFIDFFallback.tfidf_vector(q_tokens, self._idf)
                            sim = TFIDFFallback.cosine_similarity(q_vec, self._doc_tfidf_vectors[idx])
                            scored_docs.append((sim, doc))
            else:
                # Query embedding failed — fall back to TF-IDF for this query
                logger.warning("Ollama query embedding failed. Falling back to TF-IDF for this query.")
                scored_docs = self._tfidf_retrieve(query)
                active_mode = "tfidf_fallback"
        else:
            scored_docs = self._tfidf_retrieve(query)

        # Sort descending by similarity
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        results = []
        context_blocks = []

        for sim_score, doc in scored_docs[:top_k]:
            if sim_score < min_similarity:
                continue

            meta = doc.metadata
            formatted_ctx = meta.get("formatted_context") or RAGKnowledgeLoader.format_document_context(meta)
            context_blocks.append(formatted_ctx)

            results.append({
                "doc_id": doc.doc_id,
                "question_id": meta.get("question_id", doc.doc_id),
                "similarity_score": round(sim_score, 4),
                "rag_topic": meta.get("rag_topic", ""),
                "question": meta.get("question", ""),
                "model_answer": meta.get("model_answer", ""),
                "learning_outcome": meta.get("learning_outcome", ""),
                "blooms_level": meta.get("blooms_level", ""),
                "blooms_rationale": meta.get("blooms_rationale", ""),
                "marking_guide": meta.get("marking_guide", ""),
                "marks_allocation": meta.get("marks_allocation", ""),
                "max_marks": meta.get("max_marks", ""),
                "lecturer_guidelines": meta.get("lecturer_guidelines", ""),
                "criteria": meta.get("criteria", []),
                "retrieval_keywords": meta.get("retrieval_keywords", []),
                "rubric_version": meta.get("rubric_version", ""),
                "lecturer_approval": meta.get("lecturer_approval", "Pending"),
                "rag_trust_level": meta.get("rag_trust_level", "DRAFT_REFERENCE_ONLY"),
                "is_verified": meta.get("is_verified", False),
                "trust_label": meta.get("trust_label", ""),
                "source_file": meta.get("source_file", ""),
                "review_required": meta.get("review_required", ""),
                "formatted_context": formatted_ctx,
            })

        combined_context = "\n\n".join(context_blocks)

        return {
            "query": query,
            "retrieval_mode": active_mode,
            "ollama_model": self.ollama_client.model if active_mode == "ollama" else None,
            "results": results,
            "total_documents_searched": len(self.documents),
            "results_returned": len(results),
            "retrieved_context": combined_context,
        }

    def _tfidf_retrieve(self, query: str) -> List[Tuple[float, KnowledgeDocument]]:
        """Performs TF-IDF cosine similarity retrieval."""
        query_tokens = TFIDFFallback._tokenize(query)
        query_vec = TFIDFFallback.tfidf_vector(query_tokens, self._idf)
        scored = []
        for i, doc in enumerate(self.documents):
            sim = TFIDFFallback.cosine_similarity(query_vec, self._doc_tfidf_vectors[i])
            scored.append((sim, doc))
        return scored

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Returns a specific knowledge document by its Question ID (e.g. 'Q1')."""
        if not self._initialized:
            self.initialize()
        for doc in self.documents:
            if doc.doc_id.strip().upper() == doc_id.strip().upper():
                meta = dict(doc.metadata)
                meta["has_embedding"] = doc.embedding is not None
                meta["content_preview"] = doc.content[:200]
                return meta
        return None

    def list_all_documents(self) -> List[Dict[str, Any]]:
        """Returns summary metadata for all loaded knowledge documents."""
        if not self._initialized:
            self.initialize()
        return [
            {
                "doc_id": doc.doc_id,
                "question_id": doc.metadata.get("question_id", doc.doc_id),
                "rag_topic": doc.metadata.get("rag_topic", ""),
                "question": doc.metadata.get("question", ""),
                "blooms_level": doc.metadata.get("blooms_level", ""),
                "max_marks": doc.metadata.get("max_marks", ""),
                "criteria_count": len(doc.metadata.get("criteria", [])),
                "lecturer_approval": doc.metadata.get("lecturer_approval", "Pending"),
                "rag_trust_level": doc.metadata.get("rag_trust_level", "DRAFT_REFERENCE_ONLY"),
                "is_verified": doc.metadata.get("is_verified", False),
                "trust_label": doc.metadata.get("trust_label", ""),
                "source_file": doc.metadata.get("source_file", ""),
                "has_embedding": doc.embedding is not None,
            }
            for doc in self.documents
        ]

    def get_status(self) -> Dict[str, Any]:
        """Returns the current service status."""
        return {
            "status": "ready" if self._initialized else "uninitialized",
            "initialized": self._initialized,
            "documents_loaded": len(self.documents),
            "embedding_mode": self._embedding_mode,
            "ollama_model": self.ollama_client.model,
            "ollama_available": self.ollama_client.is_available,
            "csv_path": self.csv_path,
        }


# ---------------------------------------------------------------------------
# Singleton Instance Management
# ---------------------------------------------------------------------------

_rag_singleton: Optional[RAGRetrievalService] = None


def get_rag_service(auto_init: bool = True) -> RAGRetrievalService:
    """
    Returns the singleton RAGRetrievalService instance.
    Optionally initializes it on first access.
    """
    global _rag_singleton
    if _rag_singleton is None:
        _rag_singleton = RAGRetrievalService()
        if auto_init:
            _rag_singleton.initialize()
    return _rag_singleton
