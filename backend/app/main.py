import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.api.v1 import api_router
from app.models.assessment import Assessment
from app.models.rubric import Rubric, RubricCriterion
from app.models.submission import StudentSubmission, CriterionScore


def seed_initial_demo_data(db: Session):
    """Seeds starter assessment, rubric, and sample submission for initial exploration."""
    if db.query(Assessment).count() == 0:
        demo_assessment = Assessment(
            title="Software Architecture: Microservices vs Monolith Trade-offs",
            course_code="IT4360",
            question_text=(
                "Critically analyze the architectural trade-offs between Microservices and Monolithic patterns. "
                "Evaluate scalability constraints, team autonomy, deployment overhead, and failure isolation."
            ),
            reference_answer=(
                "Monoliths provide simplified deployment and ACID transactional integrity but scale as a single unit. "
                "Microservices decouple business capabilities and enable independent scaling and fault isolation, "
                "at the cost of distributed networking latency, eventual consistency, and operational monitoring complexity."
            ),
            max_marks=100.0,
            blooms_level="Analyze",
            cognitive_complexity="High",
        )
        db.add(demo_assessment)
        db.commit()
        db.refresh(demo_assessment)

        # Seed approved rubric
        demo_rubric = Rubric(
            assessment_id=demo_assessment.id,
            title="Standard Evaluative Rubric for Distributed Architectures",
            version=1,
            status="approved",
            validation_status="valid",
            validation_score=1.0,
            validation_messages=json.dumps(["All checks passed.", "Weights sum to 100.0%"]),
            is_approved=True,
            approved_by="Dr. K. Perera (Module Leader)",
            approval_notes="Validated against Bloom's Analyze taxonomy requirements."
        )
        db.add(demo_rubric)
        db.commit()
        db.refresh(demo_rubric)

        criteria = [
            RubricCriterion(
                rubric_id=demo_rubric.id,
                criterion_name="Domain Knowledge & Architecture Fundamentals",
                description="Understanding of monolithic vs microservice core concepts and architectural topologies.",
                weight_percentage=25.0,
                max_marks=25.0,
                blooms_dimension="Conceptual",
                performance_levels=json.dumps([
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Accurate definitions of both paradigms with clear boundary distinctions."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Solid understanding with minor omissions in non-critical nuances."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Superficial grasp; confuses modular monoliths with distributed components."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Inaccurate or missing conceptual definitions."}
                ])
            ),
            RubricCriterion(
                rubric_id=demo_rubric.id,
                criterion_name="Comparative Trade-off Analysis",
                description="Rigorous side-by-side evaluation of scalability, operational overhead, and fault tolerance.",
                weight_percentage=35.0,
                max_marks=35.0,
                blooms_dimension="Analytical",
                performance_levels=json.dumps([
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Thorough comparative analysis across all requested dimensions."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Covers primary trade-offs with logical arguments."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "One-sided comparison or lists bullet points without synthesis."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "No comparative analysis provided."}
                ])
            ),
            RubricCriterion(
                rubric_id=demo_rubric.id,
                criterion_name="Practical Context & Failure Scenarios",
                description="Application of concrete operational scenarios, network partitioning, and cascading failure mitigations.",
                weight_percentage=25.0,
                max_marks=25.0,
                blooms_dimension="Applied",
                performance_levels=json.dumps([
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Contextualizes with realistic distributed systems failure scenarios."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Mentions reasonable practical considerations."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Generic statements without technical operational backing."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "No practical context."}
                ])
            ),
            RubricCriterion(
                rubric_id=demo_rubric.id,
                criterion_name="Academic Structure & Clarity",
                description="Logical discourse, coherent transitions, and concise technical vocabulary.",
                weight_percentage=15.0,
                max_marks=15.0,
                blooms_dimension="Communicative",
                performance_levels=json.dumps([
                    {"level": "Exemplary", "score_percentage": 100.0, "description": "Logical flow, elegant prose, and flawless academic terminology."},
                    {"level": "Proficient", "score_percentage": 80.0, "description": "Clear presentation with minor stylistic shortcomings."},
                    {"level": "Developing", "score_percentage": 50.0, "description": "Disjointed narrative; needs better flow."},
                    {"level": "Unsatisfactory", "score_percentage": 20.0, "description": "Unstructured or incoherent."}
                ])
            )
        ]
        db.add_all(criteria)
        db.commit()

        # Seed sample evaluated student submission
        sample_sub = StudentSubmission(
            assessment_id=demo_assessment.id,
            student_id="IT21045820",
            student_name="Nethmi Jayawardena",
            answer_text=(
                "Monolithic applications package all software components into a single executable unit, "
                "which simplifies initial setup and deployment. However, scaling a monolith requires duplicating "
                "the entire stack, leading to resource inefficiency. In contrast, microservices break the system "
                "into bounded context services that communicate via lightweight protocols like REST or gRPC. "
                "This allows targeted scaling and improves fault isolation—a bug in payment service won't bring down "
                "catalog browsing. However, microservices introduce distributed system complexity, such as network latency, "
                "eventual consistency trade-offs, and service discovery overhead."
            ),
            total_score=88.5,
            max_marks=100.0,
            percentage=88.5,
            status="scored",
            overall_feedback="Excellent comparative analysis with solid technical depth. Clear understanding of distributed trade-offs."
        )
        db.add(sample_sub)
        db.commit()
        db.refresh(sample_sub)

        # Seed criterion score breakdown
        db.add_all([
            CriterionScore(
                submission_id=sample_sub.id,
                criterion_id=criteria[0].id,
                criterion_name=criteria[0].criterion_name,
                score_awarded=23.5,
                max_score=25.0,
                weight_percentage=25.0,
                performance_level="Exemplary",
                feedback="Accurate definitions of both architectural paradigms.",
                confidence_score=0.92
            ),
            CriterionScore(
                submission_id=sample_sub.id,
                criterion_id=criteria[1].id,
                criterion_name=criteria[1].criterion_name,
                score_awarded=31.0,
                max_score=35.0,
                weight_percentage=35.0,
                performance_level="Proficient",
                feedback="Balanced contrast across scalability and isolation.",
                confidence_score=0.89
            ),
            CriterionScore(
                submission_id=sample_sub.id,
                criterion_id=criteria[2].id,
                criterion_name=criteria[2].criterion_name,
                score_awarded=21.0,
                max_score=25.0,
                weight_percentage=25.0,
                performance_level="Proficient",
                feedback="Mentioned REST/gRPC and payment service failure isolation.",
                confidence_score=0.86
            ),
            CriterionScore(
                submission_id=sample_sub.id,
                criterion_id=criteria[3].id,
                criterion_name=criteria[3].criterion_name,
                score_awarded=13.0,
                max_score=15.0,
                weight_percentage=15.0,
                performance_level="Proficient",
                feedback="Logical structure and clean terminology.",
                confidence_score=0.94
            )
        ])
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create SQLite database tables on startup
    Base.metadata.create_all(bind=engine)

    # Ensure new columns exist in SQLite tables
    try:
        with engine.connect() as conn:
            cursor = conn.connection.cursor()
            cursor.execute("PRAGMA table_info(assessments)")
            existing_cols = [c[1] for c in cursor.fetchall()]
            if "learning_outcome" not in existing_cols:
                cursor.execute("ALTER TABLE assessments ADD COLUMN learning_outcome TEXT")
            if "lecturer_guidelines" not in existing_cols:
                cursor.execute("ALTER TABLE assessments ADD COLUMN lecturer_guidelines TEXT")

            cursor.execute("PRAGMA table_info(student_submissions)")
            sub_cols = [c[1] for c in cursor.fetchall()]
            if "scoring_method" not in sub_cols:
                cursor.execute("ALTER TABLE student_submissions ADD COLUMN scoring_method VARCHAR(64) DEFAULT 'semantic'")
            if "semantic_engine" not in sub_cols:
                cursor.execute("ALTER TABLE student_submissions ADD COLUMN semantic_engine VARCHAR(64) DEFAULT 'local_semantic_nlp'")

            cursor.execute("PRAGMA table_info(criterion_scores)")
            crit_cols = [c[1] for c in cursor.fetchall()]
            if "conceptual_alignment" not in crit_cols:
                cursor.execute("ALTER TABLE criterion_scores ADD COLUMN conceptual_alignment FLOAT DEFAULT 0.0")
            if "evidence_quote" not in crit_cols:
                cursor.execute("ALTER TABLE criterion_scores ADD COLUMN evidence_quote TEXT")

            cursor.execute("PRAGMA table_info(rubrics)")
            rubric_cols = [c[1] for c in cursor.fetchall()]
            if "generation_mode" not in rubric_cols:
                cursor.execute("ALTER TABLE rubrics ADD COLUMN generation_mode VARCHAR(64) DEFAULT 'rule_based'")
            if "rag_context_used" not in rubric_cols:
                cursor.execute("ALTER TABLE rubrics ADD COLUMN rag_context_used TEXT")
            if "rejection_reasons" not in rubric_cols:
                cursor.execute("ALTER TABLE rubrics ADD COLUMN rejection_reasons TEXT")
            if "rejection_feedback" not in rubric_cols:
                cursor.execute("ALTER TABLE rubrics ADD COLUMN rejection_feedback TEXT")
            if "rejected_at" not in rubric_cols:
                cursor.execute("ALTER TABLE rubrics ADD COLUMN rejected_at DATETIME")
            if "rejected_by" not in rubric_cols:
                cursor.execute("ALTER TABLE rubrics ADD COLUMN rejected_by VARCHAR(128)")
            if "parent_rubric_id" not in rubric_cols:
                cursor.execute("ALTER TABLE rubrics ADD COLUMN parent_rubric_id INTEGER")

            conn.connection.commit()
    except Exception as e:
        print(f"Schema migration check notice: {e}")

    db = SessionLocal()
    try:
        seed_initial_demo_data(db)
    finally:
        db.close()

    # Pre-initialize RAG Knowledge Retrieval Service
    try:
        from app.services.rag_retrieval_service import get_rag_service
        get_rag_service(auto_init=True)
    except Exception as e:
        print(f"RAG service pre-initialization notice: {e}")

    yield


app = FastAPI(
    title="RubriMark AI - Adaptive Rubric & Criterion Scoring System",
    description=(
        "Research Project Backend for: Adaptive AI-Based Rubric Generation and Criterion-Based "
        "Scoring System for Subjective Assessments (IT23376472)"
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "research_component": settings.RESEARCH_COMPONENT,
        "researcher_id": settings.RESEARCH_STUDENT_ID,
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }


@app.get(f"{settings.API_V1_STR}/health")
async def healthcheck():
    return {
        "status": "healthy",
        "service": "RubriMark AI Core Backend",
        "database": "SQLite (Connected)",
        "research_component": settings.RESEARCH_COMPONENT,
        "research_student_id": settings.RESEARCH_STUDENT_ID,
        "active_features": [
            "1. Lecturer Assessment Creation",
            "2. AI Question Analysis",
            "3. Adaptive Rubric Generation",
            "4. Dynamic Weight Optimization",
            "5. Rubric Validation",
            "6. Lecturer Rubric Editing and Approval",
            "7. Criterion-Based Student Answer Scoring",
            "8. Assessment Results",
            "9. RAG Knowledge Retrieval Service (Phase 1)",
        ]
    }
