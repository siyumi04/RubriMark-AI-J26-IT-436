import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.services.weight_optimizer import DynamicWeightOptimizer
from app.services.ai_service import AIService


@pytest.fixture(scope="module")
def client():
    """
    Creates an isolated temporary SQLite database for test_java_oop_rubrics.
    Strictly guarantees that rubrimark.db is NEVER accessed or modified.
    """
    temp_fd, temp_db_path = tempfile.mkstemp(suffix="_java_oop_test.db")
    os.close(temp_fd)

    test_engine = create_engine(
        f"sqlite:///{temp_db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)
    test_engine.dispose()
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass

# ==============================================================================
# The Five Java OOP Benchmark Questions (From Google Colab Prototype)
# ==============================================================================

JAVA_OOP_QUESTIONS = [
    {
        "id": "Q1_Encapsulation",
        "title": "Java Encapsulation & Data Hiding",
        "question": "Explain Encapsulation in Java and demonstrate how data hiding is achieved using access modifiers and getter/setter methods. Provide a practical code example.",
        "model_answer": "Encapsulation bundles fields and methods into a single unit and hides the internal representation using private variables accessible only via public getters and setters with validation logic.",
        "learning_outcome": "Understand and implement encapsulation and data protection mechanisms in Java.",
        "blooms_level": "Apply",
        "lecturer_guidelines": "Must include a complete Java class with private variables and public getter/setter methods with validation logic.",
        "max_marks": 20.0,
        "expected_domain": "encapsulation",
        "expected_key_criterion": "Encapsulation Concepts & Data Hiding",
    },
    {
        "id": "Q2_Inheritance",
        "title": "Java Inheritance & Method Overriding",
        "question": "Discuss Inheritance in Java with emphasis on code reusability and method overriding. How does the 'super' keyword operate within constructor chaining and method invocation? Include a code example with a superclass and subclass.",
        "model_answer": "Inheritance allows subclasses to inherit state and behavior from superclasses using 'extends'. The 'super()' call invokes the parent constructor, and methods can be overridden with @Override.",
        "learning_outcome": "Demonstrate class hierarchies and polymorphic method overriding using inheritance.",
        "blooms_level": "Analyze",
        "lecturer_guidelines": "Focus on constructor chaining, super keyword usage, and the @Override annotation.",
        "max_marks": 25.0,
        "expected_domain": "inheritance",
        "expected_key_criterion": "Constructor Chaining & Super Keyword Usage",
    },
    {
        "id": "Q3_Polymorphism",
        "title": "Java Polymorphism & Dynamic Method Dispatch",
        "question": "Compare and contrast compile-time polymorphism (method overloading) and runtime polymorphism (method overriding) in Java. Explain the mechanism of Dynamic Method Dispatch with a code demonstration.",
        "model_answer": "Compile-time polymorphism is static binding achieved through method overloading. Runtime polymorphism is dynamic binding achieved through method overriding, where the JVM resolves calls at runtime based on the actual object instance.",
        "learning_outcome": "Analyze different polymorphic behaviors in Java and explain dynamic binding.",
        "blooms_level": "Analyze",
        "lecturer_guidelines": "Provide explicit side-by-side comparison of method signatures, binding times, and execution mechanics.",
        "max_marks": 25.0,
        "expected_domain": "polymorphism",
        "expected_key_criterion": "Dynamic Method Dispatch Mechanics",
    },
    {
        "id": "Q4_Abstraction",
        "title": "Java Abstraction: Abstract Classes vs Interfaces",
        "question": "Evaluate the differences between Abstract Classes and Interfaces in Java 8+. Under what design scenarios should a software developer choose an interface over an abstract class? Support your answer with code snippets.",
        "model_answer": "Abstract classes allow partial implementation with state and constructors, supporting single inheritance. Interfaces define pure contracts, support multiple inheritance, and can include default and static methods in Java 8+.",
        "learning_outcome": "Evaluate OOP abstraction techniques and select appropriate design contracts.",
        "blooms_level": "Evaluate",
        "lecturer_guidelines": "Cover multiple inheritance through interfaces, default methods, and state encapsulation differences.",
        "max_marks": 20.0,
        "expected_domain": "abstraction",
        "expected_key_criterion": "Comparative Analysis: Abstract Classes vs Interfaces",
    },
    {
        "id": "Q5_ExceptionHandling",
        "title": "Java Exception Handling & Robust Design",
        "question": "Explain the hierarchy of Exceptions in Java. Contrast checked and unchecked exceptions, and explain how custom exception classes improve defensive programming in object-oriented systems. Provide a code example using try-catch-finally and a custom exception.",
        "model_answer": "Exceptions inherit from Throwable. Checked exceptions are verified by the compiler, while unchecked exceptions extend RuntimeException. Custom exceptions provide domain-specific error handling, and finally blocks guarantee cleanup.",
        "learning_outcome": "Design and implement robust exception handling mechanisms within Java OOP applications.",
        "blooms_level": "Apply",
        "lecturer_guidelines": "Emphasis on proper resource cleanup in finally blocks and meaningful custom exception creation.",
        "max_marks": 15.0,
        "expected_domain": "exception_handling",
        "expected_key_criterion": "Custom Exception Design & Defensive Programming",
    },
]


# ==============================================================================
# Unit & Algorithm Tests: Weight Optimizer & Rubric Engine
# ==============================================================================

def test_dynamic_weight_optimizer_normalization():
    """Verifies that weights are mathematically normalized to strictly 100.0%."""
    raw_criteria = [
        {"criterion_name": "Criterion A", "weight_percentage": 33.3},
        {"criterion_name": "Criterion B", "weight_percentage": 33.3},
        {"criterion_name": "Criterion C", "weight_percentage": 33.3},
    ]
    normalized = DynamicWeightOptimizer.normalize_weights(raw_criteria)
    total = sum(c["weight_percentage"] for c in normalized)
    assert abs(total - 100.0) < 0.001


def test_dynamic_weight_optimizer_marks_allocation():
    """Verifies that allocated marks sum exactly to max_marks across non-standard totals."""
    raw_criteria = [
        {"criterion_name": "Criterion 1", "weight_percentage": 35.0},
        {"criterion_name": "Criterion 2", "weight_percentage": 30.0},
        {"criterion_name": "Criterion 3", "weight_percentage": 20.0},
        {"criterion_name": "Criterion 4", "weight_percentage": 15.0},
    ]
    allocated = DynamicWeightOptimizer.allocate_marks(raw_criteria, max_marks=25.0)
    total_marks = sum(c["max_marks"] for c in allocated)
    assert abs(total_marks - 25.0) < 0.001


def test_duplicate_criteria_detection():
    """Verifies that duplicate criteria are detected, merged, and flagged."""
    dup_criteria = [
        {"criterion_name": "Code Syntax & Structure", "weight_percentage": 50.0},
        {"criterion_name": "code syntax & structure", "weight_percentage": 50.0},
    ]
    unique, warnings = DynamicWeightOptimizer.check_and_deduplicate_criteria(dup_criteria)
    assert len(unique) == 1
    assert len(warnings) == 1


# ==============================================================================
# Integration Tests: Five Java OOP Questions Rubric Generation
# ==============================================================================

@pytest.mark.parametrize("q_data", JAVA_OOP_QUESTIONS)
def test_java_oop_question_rubric_generation(client, q_data):
    """
    Tests rule-based rubric generation for each of the five Java OOP questions:
    - Accepts question, model answer, learning outcome, Bloom's level, guidelines, max marks.
    - Selects question-specific criteria.
    - Dynamically optimizes weights to 100.0%.
    - Allocates marks summing strictly to max_marks.
    - Checks for no duplicate criteria.
    - Sets approval status as Pending (is_approved=False).
    """
    payload = {
        "title": q_data["title"],
        "question": q_data["question"],
        "model_answer": q_data["model_answer"],
        "learning_outcome": q_data["learning_outcome"],
        "blooms_level": q_data["blooms_level"],
        "lecturer_guidelines": q_data["lecturer_guidelines"],
        "max_marks": q_data["max_marks"],
        "generation_mode": "rule_based",
        "force_fallback": True,
    }

    response = client.post("/api/v1/rubrics/generate", json=payload)
    assert response.status_code == 201, f"Failed for {q_data['id']}: {response.text}"
    rubric = response.json()

    # Requirement 6: Keep lecturer approval status as Pending upon generation
    assert rubric["is_approved"] is False
    assert rubric["status"] == "pending_approval"
    assert "pending" in rubric["approval_notes"].lower()

    # Check criteria count & uniqueness
    criteria = rubric["criteria"]
    assert len(criteria) >= 3, "Rubric must contain at least 3 criteria"
    crit_names = [c["criterion_name"].strip().lower() for c in criteria]
    assert len(crit_names) == len(set(crit_names)), "Must contain no duplicate criteria"

    # Check question-specific criteria matching
    found_key = any(q_data["expected_key_criterion"].lower() in name for name in crit_names)
    assert found_key, f"Expected key criterion '{q_data['expected_key_criterion']}' in generated criteria: {crit_names}"

    # Requirement 3 & 4: Weights sum to 100%
    total_weight = sum(c["weight_percentage"] for c in criteria)
    assert abs(total_weight - 100.0) < 0.01, f"Total weights ({total_weight}%) must equal 100.0%"

    # Requirement 4: Allocated marks sum exactly to max_marks
    total_marks = sum(c["max_marks"] for c in criteria)
    assert abs(total_marks - q_data["max_marks"]) < 0.05, (
        f"Total marks ({total_marks}) must equal max_marks ({q_data['max_marks']})"
    )

    # Performance levels completeness
    for c in criteria:
        assert len(c["performance_levels"]) >= 3, f"Criterion '{c['criterion_name']}' lacks performance tiers"
        levels = [p["level"] for p in c["performance_levels"]]
        assert "Exemplary" in levels
        assert "Unsatisfactory" in levels


# ==============================================================================
# Security & Workflow Tests: Lecturer Approval & Scoring Protection
# ==============================================================================

def test_unapproved_rubric_cannot_score_student_answer(client):
    """
    Requirement 7: Do not allow unapproved rubrics to be used for official student scoring.
    Verifies that calling /scoring/evaluate with an unapproved rubric returns HTTP 400.
    """
    # 1. Generate an unapproved rubric
    gen_payload = {
        "title": "Encapsulation Unapproved Test",
        "question": "Explain Encapsulation in Java with getters and setters.",
        "blooms_level": "Apply",
        "max_marks": 20.0,
        "generation_mode": "rule_based",
        "force_fallback": True,
    }
    gen_res = client.post("/api/v1/rubrics/generate", json=gen_payload)
    assert gen_res.status_code == 201
    rubric = gen_res.json()
    rubric_id = rubric["id"]
    assessment_id = rubric["assessment_id"]
    assert rubric["is_approved"] is False

    # 2. Attempt to evaluate student answer with unapproved rubric -> Must fail with HTTP 400
    score_payload = {
        "assessment_id": assessment_id,
        "rubric_id": rubric_id,
        "student_id": "IT23000001",
        "student_name": "Test Student",
        "answer_text": "Encapsulation uses private variables and public getters and setters to protect data.",
    }
    score_res = client.post("/api/v1/scoring/evaluate", json=score_payload)
    assert score_res.status_code == 400
    assert "unapproved rubric" in score_res.json()["detail"].lower()

    # 3. Explicitly approve the rubric
    approve_res = client.post(
        f"/api/v1/rubrics/{rubric_id}/approve",
        json={"approved_by": "Dr. Lecturer Lead", "notes": "Officially verified and approved."}
    )
    assert approve_res.status_code == 200
    approved_rubric = approve_res.json()
    assert approved_rubric["is_approved"] is True
    assert approved_rubric["status"] == "approved"

    # 4. Attempt scoring again with the approved rubric -> Must succeed with HTTP 201
    score_res_after = client.post("/api/v1/scoring/evaluate", json=score_payload)
    assert score_res_after.status_code == 201
    eval_result = score_res_after.json()
    assert eval_result["total_score"] > 0
    assert len(eval_result["criterion_scores"]) > 0


def test_rubric_validation_endpoint(client):
    """
    Requirement 4 & 5: Validate weights, criteria, and total marks via /rubrics/{id}/validate.
    """
    gen_payload = {
        "title": "Inheritance Validation Test",
        "question": "Discuss Inheritance and super keyword in Java.",
        "blooms_level": "Analyze",
        "max_marks": 25.0,
        "generation_mode": "rule_based",
        "force_fallback": True,
    }
    gen_res = client.post("/api/v1/rubrics/generate", json=gen_payload)
    assert gen_res.status_code == 201
    rubric_id = gen_res.json()["id"]

    val_res = client.post(f"/api/v1/rubrics/{rubric_id}/validate")
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["is_valid"] is True
    assert val_data["status"] == "valid"
    assert val_data["validation_score"] == 1.0


def test_ollama_rag_rubric_generation_structure(client):
    """
    Separate test for Ollama + RAG generation mode:
    Verifies that when RAG/LLM mode is invoked, it adheres to schema requirements,
    normalizes weights strictly to 100%, and allocates valid marks.
    """
    gen_payload = {
        "title": "Java Polymorphism RAG Test",
        "question": "Compare and contrast compile-time and runtime polymorphism in Java.",
        "blooms_level": "Analyze",
        "max_marks": 25.0,
        "generation_mode": "ollama_rag",
        "use_rag": True,
    }
    res = client.post("/api/v1/rubrics/generate", json=gen_payload)
    assert res.status_code == 201
    rubric = res.json()
    assert rubric["is_approved"] is False
    assert len(rubric["criteria"]) >= 3
    total_weights = sum(c["weight_percentage"] for c in rubric["criteria"])
    assert abs(total_weights - 100.0) < 0.1
    total_marks = sum(c["max_marks"] for c in rubric["criteria"])
    assert abs(total_marks - 25.0) < 0.1

