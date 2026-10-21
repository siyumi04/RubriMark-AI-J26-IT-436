import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.api.endpoints import router as api_router
from app.services.ai_inference import ai_service
from app.services.dataset_service import dataset_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rubrimark")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)

    # Attempt to load trained AI model
    logger.info("Checking for trained AI model artifact...")
    ai_service.load_model()

    # Pre-seed sample academic benchmark data if DB empty
    db = SessionLocal()
    try:
        seeded = dataset_service.seed_initial_academic_dataset(db)
        if seeded:
            logger.info("Initial academic benchmark dataset seeded successfully.")
    except Exception as e:
        logger.warning(f"Note on initial seeding: {e}")
    finally:
        db.close()

    yield
    # Shutdown
    logger.info("RubriMark AI Backend shutting down.")


app = FastAPI(
    title="RubriMark AI - Personalized Feedback API",
    description="Explainable AI Framework for Automated Short-Answer Assessment: Feedback, Knowledge Gap Detection, and Learning Recommendations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    FRONTEND_URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router)


@app.get("/")
def welcome_root():
    return {
        "message": "Welcome to RubriMark AI - Personalized Feedback & Learning Recommendation API",
        "documentation": "/docs",
        "health_check": "/api/health",
        "status": "online"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
