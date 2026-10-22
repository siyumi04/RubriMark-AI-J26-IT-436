from fastapi import APIRouter
from app.api.v1.assessments import router as assessments_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.rubrics import router as rubrics_router
from app.api.v1.scoring import router as scoring_router
from app.api.v1.results import router as results_router
from app.api.v1.dataset import router as dataset_router
from app.api.v1.rag import router as rag_router

api_router = APIRouter()
api_router.include_router(assessments_router)
api_router.include_router(analysis_router)
api_router.include_router(rubrics_router)
api_router.include_router(scoring_router)
api_router.include_router(results_router)
api_router.include_router(dataset_router)
api_router.include_router(rag_router)

