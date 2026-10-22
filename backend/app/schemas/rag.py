"""
Pydantic Schemas for RAG Knowledge Retrieval Service (Research Component IT23376472).
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    query: str = Field(
        ...,
        description="The query text (e.g. a subjective assessment question or topic) to find relevant rubric examples for.",
        json_schema_extra={"example": "What is the difference between a class and an object in Java? Give a simple example."}
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of relevant rubric documents to retrieve."
    )
    min_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold for retrieved results."
    )


class RAGCriterion(BaseModel):
    criterion: str
    max_marks: float
    description: Optional[str] = ""
    full_credit: Optional[str] = ""
    partial_credit: Optional[str] = ""
    zero_credit: Optional[str] = ""


class RAGSearchResult(BaseModel):
    doc_id: str
    question_id: str
    similarity_score: float
    rag_topic: str
    question: str
    model_answer: str
    learning_outcome: str
    blooms_level: str
    blooms_rationale: Optional[str] = ""
    marking_guide: str
    marks_allocation: str
    max_marks: str
    lecturer_guidelines: str
    criteria: List[Dict[str, Any]]
    retrieval_keywords: List[str]
    rubric_version: str
    lecturer_approval: str
    rag_trust_level: str
    is_verified: bool
    trust_label: str
    source_file: str
    review_required: Optional[str] = ""
    formatted_context: str


class RAGRetrievalResponse(BaseModel):
    query: str
    retrieval_mode: str
    ollama_model: Optional[str] = None
    results: List[RAGSearchResult]
    total_documents_searched: int
    results_returned: int
    retrieved_context: str


class RAGDocumentSummary(BaseModel):
    doc_id: str
    question_id: str
    rag_topic: str
    question: str
    blooms_level: str
    max_marks: str
    criteria_count: int
    lecturer_approval: str
    rag_trust_level: str
    is_verified: bool
    trust_label: str
    source_file: str
    has_embedding: bool


class RAGStatusResponse(BaseModel):
    status: str
    initialized: bool
    documents_loaded: int
    embedding_mode: str
    ollama_model: str
    ollama_available: bool
    csv_path: str
