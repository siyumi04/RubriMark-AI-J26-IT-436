from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "RubriMark AI"
    RESEARCH_COMPONENT: str = (
        "Adaptive AI-Based Rubric Generation and Criterion-Based Scoring System for Subjective Assessments"
    )
    RESEARCH_STUDENT_ID: str = "IT23376472"
    API_V1_STR: str = "/api/v1"
    
    # SQLite Database
    DATABASE_URL: str = "sqlite:///./rubrimark.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # AI Service Configuration
    AI_MODEL_NAME: str = "rubrimark-rubric-engine-v1"
    ENABLE_MOCK_AI: bool = True  # Allows offline testing and deterministic rubric simulation

    # Ollama & RAG Configuration (Phase 1 & Phase 2)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_GEN_MODEL: str = "llama3.2:1b"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0
    OLLAMA_GEN_TIMEOUT_SECONDS: float = 120.0
    ENABLE_RAG_RUBRIC_GENERATION: bool = True
    RAG_KNOWLEDGE_CSV_PATH: str = "../data/RubriMark_RAG_Lecturer_Rubrics_Draft_v1_1.csv"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
