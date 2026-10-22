"""
FastAPI Router for RAG Retrieval Service (Research Component IT23376472).

Endpoints:
- POST /api/v1/rag/retrieve: Retrieve top-k relevant lecturer rubric examples
- GET  /api/v1/rag/documents: List all loaded knowledge rubric records
- GET  /api/v1/rag/documents/{question_id}: Get full record for a specific Question ID
- GET  /api/v1/rag/status: Check RAG initialization, model, and Ollama status
- POST /api/v1/rag/initialize: Re-index or initialize the knowledge base
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.rag import (
    RAGQueryRequest,
    RAGRetrievalResponse,
    RAGDocumentSummary,
    RAGStatusResponse,
)
from app.services.rag_retrieval_service import get_rag_service

router = APIRouter(prefix="/rag", tags=["RAG Knowledge Retrieval (Phase 1)"])


@router.post("/retrieve", response_model=RAGRetrievalResponse)
def retrieve_relevant_rubrics(request: RAGQueryRequest):
    """
    Phase 1 RAG Retrieval Endpoint.
    Given a subjective question or query, retrieves the top-k most relevant lecturer
    rubric examples using cosine similarity over Ollama nomic-embed-text embeddings
    (or TF-IDF fallback if Ollama is unavailable).

    Returns:
    - Retreived documents with question, model answer, criteria, marking guidelines,
      Bloom's level, learning outcome, source file, approval status, and trust level.
    - All pending rubrics clearly marked as UNVERIFIED DRAFT REFERENCES.
    - Combined formatted context block ready for downstream evaluation.
    """
    service = get_rag_service(auto_init=True)
    try:
        results = service.retrieve(
            query=request.query,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG retrieval failed: {str(e)}",
        )


@router.get("/documents", response_model=List[RAGDocumentSummary])
def list_knowledge_documents():
    """
    Lists summary metadata for all rubric records currently loaded in the RAG knowledge base.
    """
    service = get_rag_service(auto_init=True)
    return service.list_all_documents()


@router.get("/documents/{question_id}")
def get_knowledge_document(question_id: str):
    """
    Retrieves full details of a specific lecturer rubric document by Question ID (e.g. 'Q1').
    """
    service = get_rag_service(auto_init=True)
    doc = service.get_document_by_id(question_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document with Question ID '{question_id}' not found.",
        )
    return doc


@router.get("/status", response_model=RAGStatusResponse)
def get_rag_service_status():
    """
    Returns the operational status of the RAG retrieval service, including
    Ollama connectivity, active model ('nomic-embed-text'), embedding mode,
    and number of loaded documents.
    """
    service = get_rag_service(auto_init=True)
    status_info = service.get_status()
    return status_info


@router.post("/initialize", response_model=RAGStatusResponse)
def initialize_rag_service(force_fallback: bool = Query(default=False)):
    """
    Initializes or re-indexes the RAG retrieval service from the CSV.
    Optionally allows forcing TF-IDF fallback mode.
    """
    service = get_rag_service(auto_init=False)
    service.initialize(force_fallback=force_fallback)
    return service.get_status()
