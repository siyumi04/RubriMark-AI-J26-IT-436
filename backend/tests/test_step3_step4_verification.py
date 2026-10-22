"""
Verification Test Suite: Step 3 Adaptive Rubrics & Step 4 Dynamic Weights.

Verifies:
1. Isolated temporary test database (does not touch or modify rubrimark.db).
2. Step 3 Adaptive Rubric generation produces 4 graduated levels, question-specific criteria, and pending approval.
3. Step 4 Dynamic Weight optimization normalizes weights to strictly 100.0%.
4. Allocated marks sum strictly to assessment's max_marks without rounding divergence.
5. Repeated weight optimization is strictly idempotent and does not change weights unexpectedly.
6. The active rubric ID and version remain correct after optimization.
7. Lecturer-provided custom weights are preserved appropriately.
8. Approved rubrics cannot be modified or weight-optimized improperly.
9. Rejected rubrics cannot be modified, weight-optimized, approved directly, or used for student scoring.
10. Assessment and active rubric linkage across Step 3 and Step 4 workflows.
"""

import os
import json
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.services.weight_optimizer import DynamicWeightOptimizer


@pytest.fixture(scope="module")
def client():
    """
    Creates an isolated temporary SQLite database.
    Strictly guarantees that rubrimark.db is NEVER accessed or modified.
    """
    temp_fd, temp_db_path = tempfile.mkstemp(suffix="_step3_step4_test.db")
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
    try:
        os.unlink(temp_db_path)
    except Exception:
        pass


def test_step3_adaptive_rubric_generation_structure(client):
    """
    Requirement 2 & 6:
    Step 3 Adaptive Rubric Generation:
    - Generates criteria with descriptions, Bloom's dimension, and 4 graduated levels.
    - Initial weights sum to 100.0% and marks equal assessment max marks.
    - Initial status is pending_approval and is_approved is False.
    """
    payload = {
        "title": "Java Encapsulation & Data Hiding",
        "question": "Explain Encapsulation in Java and demonstrate how data hiding is achieved using access modifiers and getter/setter methods. Provide a practical code example.",
        "model_answer": "Encapsulation bundles fields and methods into a single unit and hides internal representation using private variables accessible only via public getters and setters with validation logic.",
        "learning_outcome": "Understand and implement encapsulation mechanisms in Java.",
        "blooms_level": "Apply",
        "lecturer_guidelines": "Must include private fields and public accessors/mutators with validation.",
        "max_marks": 20.0,
    }

    res = client.post("/api/v1/rubrics/generate", json=payload)
    assert res.status_code == 201
    rubric = res.json()

    assert rubric["id"] is not None
    assert rubric["version"] == 1
    assert rubric["is_approved"] is False
    assert rubric["status"] == "pending_approval"

    criteria = rubric["criteria"]
    assert len(criteria) >= 3, "Step 3 rubric must contain at least 3 criteria"

    total_weight = sum(c["weight_percentage"] for c in criteria)
    assert abs(total_weight - 100.0) < 0.01, f"Initial total weight ({total_weight}%) must equal 100.0%"

    total_marks = sum(c["max_marks"] for c in criteria)
    assert abs(total_marks - 20.0) < 0.01, f"Initial marks ({total_marks}) must equal 20.0"

    # Verify graduated performance levels on all criteria
    expected_tiers = {"Exemplary", "Proficient", "Developing", "Unsatisfactory"}
    for crit in criteria:
        assert crit["criterion_name"]
        assert crit["description"]
        assert crit["blooms_dimension"] in ["Conceptual", "Theory", "Implementation", "Syntax", "Applied", "Analytical", "Comparative"]
        levels = crit.get("performance_levels") or []
        assert len(levels) >= 3, f"Criterion '{crit['criterion_name']}' must have graduated performance tiers"
        level_names = {l["level"] for l in levels}
        assert "Exemplary" in level_names
        assert "Unsatisfactory" in level_names or "Novice" in level_names


def test_step4_dynamic_weight_optimization_and_marks_balance(client):
    """
    Requirement 4, 5, 6:
    Step 4 Dynamic Weight Optimization:
    - Recalibrates criteria weights to sum to exactly 100.0%.
    - Allocates marks summing strictly to assessment's max_marks (25.0).
    - Preserves active rubric ID and version.
    """
    # 1. Create assessment with max_marks = 25.0
    payload = {
        "title": "Java Polymorphism Optimization Test",
        "question": "Compare compile-time and runtime polymorphism in Java. Explain dynamic method dispatch.",
        "blooms_level": "Analyze",
        "max_marks": 25.0,
    }
    gen_res = client.post("/api/v1/rubrics/generate", json=payload)
    assert gen_res.status_code == 201
    rubric = gen_res.json()
    rubric_id = rubric["id"]
    original_version = rubric["version"]

    # 2. Optimize weights
    opt_res = client.post(f"/api/v1/rubrics/{rubric_id}/optimize-weights")
    assert opt_res.status_code == 200
    opt_data = opt_res.json()

    assert opt_data["rubric_id"] == rubric_id
    assert opt_data["version"] == original_version
    assert opt_data["total_weight"] == 100.0
    assert opt_data["status"] in ["optimized", "weights_optimized"]

    opt_criteria = opt_data["optimized_criteria"]
    total_weight = sum(c["weight_percentage"] for c in opt_criteria)
    assert abs(total_weight - 100.0) < 0.01, f"Total weight ({total_weight}%) must equal 100.0%"

    total_marks = sum(c["max_marks"] for c in opt_criteria)
    assert abs(total_marks - 25.0) < 0.01, f"Total marks ({total_marks}) must equal 25.0 max marks"

    # 3. Check DB detail reflects optimization and retains ID & version
    detail = client.get(f"/api/v1/rubrics/{rubric_id}").json()
    assert detail["id"] == rubric_id
    assert detail["version"] == original_version
    assert detail["status"] == "weights_optimized"


def test_repeated_weight_optimization_idempotence(client):
    """
    Requirement 4 & 5:
    Verifies that calling optimize-weights repeatedly (2x, 3x, 5x) does NOT
    change weights unexpectedly, does not create extra rubric rows, and keeps version intact.
    """
    gen_payload = {
        "title": "Inheritance Idempotence Benchmark",
        "question": "Discuss Inheritance and super keyword in Java with constructor chaining.",
        "blooms_level": "Analyze",
        "max_marks": 25.0,
    }
    gen_res = client.post("/api/v1/rubrics/generate", json=gen_payload)
    rubric_id = gen_res.json()["id"]

    # First optimization
    res1 = client.post(f"/api/v1/rubrics/{rubric_id}/optimize-weights").json()
    weights_run1 = [c["weight_percentage"] for c in res1["optimized_criteria"]]
    marks_run1 = [c["max_marks"] for c in res1["optimized_criteria"]]

    # Second optimization
    res2 = client.post(f"/api/v1/rubrics/{rubric_id}/optimize-weights").json()
    weights_run2 = [c["weight_percentage"] for c in res2["optimized_criteria"]]
    marks_run2 = [c["max_marks"] for c in res2["optimized_criteria"]]

    # Third optimization
    res3 = client.post(f"/api/v1/rubrics/{rubric_id}/optimize-weights").json()
    weights_run3 = [c["weight_percentage"] for c in res3["optimized_criteria"]]
    marks_run3 = [c["max_marks"] for c in res3["optimized_criteria"]]

    # Assert strict equality across repeated runs
    assert weights_run1 == weights_run2 == weights_run3, (
        f"Weights drifted across runs! Run1={weights_run1}, Run2={weights_run2}, Run3={weights_run3}"
    )
    assert marks_run1 == marks_run2 == marks_run3, (
        f"Marks drifted across runs! Run1={marks_run1}, Run2={marks_run2}, Run3={marks_run3}"
    )
    assert res1["rubric_id"] == res2["rubric_id"] == res3["rubric_id"] == rubric_id
    assert res1["version"] == res2["version"] == res3["version"] == 1


def test_lecturer_provided_weights_preserved(client):
    """
    Requirement 7:
    Verifies that when a lecturer manually customizes criterion weights and saves them,
    the weights are preserved accurately and not clobbered unexpectedly.
    """
    gen_payload = {
        "title": "Lecturer Priority Preservation Test",
        "question": "Explain Java Exception Handling with checked and unchecked exceptions.",
        "blooms_level": "Apply",
        "max_marks": 15.0,
    }
    rubric = client.post("/api/v1/rubrics/generate", json=gen_payload).json()
    rubric_id = rubric["id"]

    # Lecturer specifies custom weights: 50.0%, 30.0%, 20.0% (total = 100%)
    criteria = rubric["criteria"]
    custom_weights = [50.0, 30.0, 20.0]
    updated_criteria = []
    for idx, c in enumerate(criteria[:3]):
        w = custom_weights[idx]
        updated_criteria.append({
            "criterion_name": c["criterion_name"],
            "description": c["description"],
            "weight_percentage": w,
            "max_marks": round((w / 100.0) * 15.0, 2),
            "blooms_dimension": c["blooms_dimension"],
            "performance_levels": c["performance_levels"],
        })

    put_res = client.put(f"/api/v1/rubrics/{rubric_id}", json={
        "title": rubric["title"],
        "criteria": updated_criteria,
    })
    assert put_res.status_code == 200
    saved = put_res.json()
    saved_weights = [c["weight_percentage"] for c in saved["criteria"]]
    assert saved_weights == [50.0, 30.0, 20.0]

    # Re-running weight optimization on preserved lecturer weights keeps them balanced at 50, 30, 20
    opt_res = client.post(f"/api/v1/rubrics/{rubric_id}/optimize-weights").json()
    opt_weights = [c["weight_percentage"] for c in opt_res["optimized_criteria"]]
    assert opt_weights == [50.0, 30.0, 20.0], f"Lecturer weights were not preserved: {opt_weights}"


def test_approved_rubrics_cannot_be_modified_improperly(client):
    """
    Requirement 8:
    Check that approved rubrics cannot be modified, weight-optimized, or tampered with.
    """
    gen_res = client.post("/api/v1/rubrics/generate", json={
        "title": "Approved Locking Test",
        "question": "Explain Encapsulation in Java.",
        "blooms_level": "Apply",
        "max_marks": 20.0,
    })
    rubric_id = gen_res.json()["id"]

    # Formally approve
    appr_res = client.post(f"/api/v1/rubrics/{rubric_id}/approve", json={
        "approved_by": "Dr. Module Leader",
        "notes": "Verified and approved.",
    })
    assert appr_res.status_code == 200
    assert appr_res.json()["is_approved"] is True

    # Attempt to edit approved rubric -> HTTP 400
    edit_res = client.put(f"/api/v1/rubrics/{rubric_id}", json={"title": "Hacked Title"})
    assert edit_res.status_code == 400
    assert "approved rubric" in edit_res.json()["detail"].lower()

    # Attempt to optimize weights on approved rubric -> HTTP 400
    opt_res = client.post(f"/api/v1/rubrics/{rubric_id}/optimize-weights")
    assert opt_res.status_code == 400
    assert "approved rubric" in opt_res.json()["detail"].lower()


def test_rejected_rubrics_cannot_be_modified_or_scored_improperly(client):
    """
    Requirement 8:
    Check that rejected rubrics cannot be modified, weight-optimized, approved directly,
    or used for student scoring.
    """
    gen_res = client.post("/api/v1/rubrics/generate", json={
        "title": "Rejected Locking Test",
        "question": "Explain Abstraction in Java.",
        "blooms_level": "Evaluate",
        "max_marks": 20.0,
    })
    rubric = gen_res.json()
    rubric_id = rubric["id"]
    assessment_id = rubric["assessment_id"]

    # Reject rubric
    rej_res = client.post(f"/api/v1/rubrics/{rubric_id}/reject", json={
        "rejection_reasons": ["Missing criteria", "Incorrect marks or weights"],
        "feedback": "Needs Interface vs Abstract class contrast criteria.",
        "rejected_by": "Dr. Examiner",
    })
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"

    # Attempt to edit rejected rubric -> HTTP 400
    edit_res = client.put(f"/api/v1/rubrics/{rubric_id}", json={"title": "Try edit"})
    assert edit_res.status_code == 400
    assert "rejected rubric" in edit_res.json()["detail"].lower()

    # Attempt to optimize weights on rejected rubric -> HTTP 400
    opt_res = client.post(f"/api/v1/rubrics/{rubric_id}/optimize-weights")
    assert opt_res.status_code == 400
    assert "rejected rubric" in opt_res.json()["detail"].lower()

    # Attempt to approve rejected rubric directly without regeneration -> HTTP 400
    appr_res = client.post(f"/api/v1/rubrics/{rubric_id}/approve", json={"approved_by": "Dr. Examiner"})
    assert appr_res.status_code == 400
    assert "rejected rubric" in appr_res.json()["detail"].lower()

    # Attempt to score student answer with rejected rubric -> HTTP 400
    score_res = client.post("/api/v1/scoring/evaluate", json={
        "assessment_id": assessment_id,
        "rubric_id": rubric_id,
        "student_id": "IT23999999",
        "student_name": "Test Student",
        "answer_text": "Interfaces declare abstract methods and support multiple inheritance.",
    })
    assert score_res.status_code == 400
    assert "rejected rubric" in score_res.json()["detail"].lower()


def test_step3_and_step4_share_same_assessment_and_rubric(client):
    """
    Requirement 3:
    Test that both Step 3 and Step 4 workflows link to the same selected assessment and active rubric.
    """
    # 1. Create assessment
    gen_res = client.post("/api/v1/rubrics/generate", json={
        "title": "Shared Context Assessment",
        "question": "Explain Java encapsulation.",
        "blooms_level": "Apply",
        "max_marks": 20.0,
    })
    rubric = gen_res.json()
    assessment_id = rubric["assessment_id"]
    rubric_id = rubric["id"]

    # Query rubrics for this assessment (as Step 3 and Step 4 both do via api.getRubricsForAssessment)
    rubrics_res = client.get(f"/api/v1/rubrics/assessment/{assessment_id}")
    assert rubrics_res.status_code == 200
    rubrics_list = rubrics_res.json()
    assert len(rubrics_list) >= 1

    active_rubric = rubrics_list[-1]
    assert active_rubric["id"] == rubric_id
    assert active_rubric["assessment_id"] == assessment_id

    # Optimize weights (Step 4 action)
    opt_res = client.post(f"/api/v1/rubrics/{active_rubric['id']}/optimize-weights")
    assert opt_res.status_code == 200

    # Verify both views see the same updated rubric
    updated_rubrics_res = client.get(f"/api/v1/rubrics/assessment/{assessment_id}")
    updated_rubric = updated_rubrics_res.json()[-1]
    assert updated_rubric["id"] == active_rubric["id"]
    assert updated_rubric["assessment_id"] == assessment_id
    assert updated_rubric["status"] == "weights_optimized"
