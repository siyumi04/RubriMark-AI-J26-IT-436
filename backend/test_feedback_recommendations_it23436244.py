"""
Test Suite for IT23436244 Research Component:
Personalized Feedback & Learning Recommendations Evaluation.

Evaluates:
1. Correct answer feedback generation (strengths identified, no false missing concepts).
2. Partially correct answer feedback (both strengths and missing concept weaknesses captured).
3. Incorrect / non-answer feedback (clean handling of ungrounded responses without crash).
4. Model uncertainty handling (transparent flagging of triage/review status).
5. Cross-question concept isolation (filters out out-of-domain concepts).
6. Lecture recommendation matching (exact 1-to-1 concept to verified IT2030 lecture PDF alignment).
7. Learning pathway prerequisite-first topological sequence in recommendations.
"""

import sys
from app.services.feedback_engine import feedback_engine, QUESTION_EXPECTED_CONCEPTS
from app.services.concept_dependency import concept_dependency_service, OOP_CONCEPT_DAG
from app.services.lecture_catalog import VERIFIED_CONCEPT_LECTURE_MAP, get_recommendation_for_concept

def run_feedback_tests():
    print("=" * 80)
    print("IT23436244 COMPONENT EVALUATION: FEEDBACK & LEARNING RECOMMENDATIONS")
    print("=" * 80)

    passed_tests = 0
    failed_tests = 0

    def record(name: str, passed: bool, details: str = ""):
        nonlocal passed_tests, failed_tests
        status = "[PASS]" if passed else "[FAIL]"
        if passed:
            passed_tests += 1
        else:
            failed_tests += 1
        print(f"{status} - {name}")
        if details:
            print(f"       Details: {details}")

    # TEST 1: Correct Student Answer (Q1)
    ans_correct = (
        "A class is a blueprint or template that defines properties and methods. "
        "An object is a real-world entity and an instance created from a class that occupies memory. "
        "For example, Car is a class and myCar is an object."
    )
    fb_correct = feedback_engine.generate_feedback_and_recommendations(
        student_answer=ans_correct,
        question_text="01. What is the difference between a class and an object in Java? Give a simple example.",
        obtained_marks=5.0,
        total_marks=5.0,
        missing_concepts=[],
        ai_available=True,
        question_id="Q1"
    )
    t1_pass = (
        len(fb_correct["correctly_identified_concepts"]) == 3 and
        len(fb_correct["substantive_missing_concepts"]) == 0 and
        "blueprint" in fb_correct["strengths"].lower()
    )
    record(
        "TEST 1: Correct Student Answer Feedback (Strengths articulated, 0 gaps)",
        t1_pass,
        f"Demonstrated: {fb_correct['correctly_identified_concepts']}, Gaps: {fb_correct['substantive_missing_concepts']}"
    )

    # TEST 2: Partially Correct Answer (Q2 - misses methods)
    ans_partial = "The Car class inherits all the accessible variables, attributes and fields from the Vehicle class."
    fb_partial = feedback_engine.generate_feedback_and_recommendations(
        student_answer=ans_partial,
        question_text="02. If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?",
        obtained_marks=2.5,
        total_marks=5.0,
        missing_concepts=["Inheritance of accessible methods"],
        ai_available=True,
        question_id="Q2"
    )
    t2_pass = (
        "Inheritance of accessible fields" in fb_partial["correctly_identified_concepts"] and
        "Inheritance of accessible methods" in fb_partial["substantive_missing_concepts"] and
        "methods" in fb_partial["weaknesses"].lower()
    )
    record(
        "TEST 2: Partially Correct Answer Feedback (Strengths and missing concepts both captured)",
        t2_pass,
        f"Correct: {fb_partial['correctly_identified_concepts']}, Missing: {fb_partial['substantive_missing_concepts']}"
    )

    # TEST 3: Incorrect / Non-Answer ("I don't know")
    ans_empty = "I don't remember"
    fb_empty = feedback_engine.generate_feedback_and_recommendations(
        student_answer=ans_empty,
        question_text="05. Why is exception handling important in Java?",
        obtained_marks=0.0,
        total_marks=5.0,
        missing_concepts=["Handles runtime exceptions/errors", "Prevents abrupt termination or supports graceful recovery"],
        ai_available=True,
        question_id="Q5"
    )
    t3_pass = (
        len(fb_empty["correctly_identified_concepts"]) == 0 and
        len(fb_empty["substantive_missing_concepts"]) == 2 and
        "does not provide technical explanations" in fb_empty["weaknesses"]
    )
    record(
        "TEST 3: Incorrect / Non-Answer Handling (Ungrounded response gracefully diagnosed)",
        t3_pass,
        f"Gaps identified: {fb_empty['substantive_missing_concepts']}"
    )

    # TEST 4: Model Uncertainty / Triage Flag
    ans_uncertain = "Overriding is when a child class changes a method."
    fb_uncertain = feedback_engine.generate_feedback_and_recommendations(
        student_answer=ans_uncertain,
        question_text="03. What happens when a child class overrides a method inherited from its parent class?",
        obtained_marks=3.0,
        total_marks=5.0,
        missing_concepts=["requires human review"],
        ai_available=True,
        question_id="Q3"
    )
    t4_pass = (
        fb_uncertain["requires_human_review"] is True and
        "requires human review" not in fb_uncertain["substantive_missing_concepts"] and
        "instructor verification" in fb_uncertain["weaknesses"].lower()
    )
    record(
        "TEST 4: Model Uncertainty & Human Review Flag (Transparently communicated, metadata excluded)",
        t4_pass,
        f"Flagged for human review: {fb_uncertain['requires_human_review']}"
    )

    # TEST 5: Cross-Question Out-of-Domain Concept Isolation
    # Under Q4 (Static variables), if model hallucinated Q5's 'Handles runtime exceptions/errors'
    ans_q4 = "A static method cannot access non-static variables because static belongs to the class."
    fb_cross = feedback_engine.generate_feedback_and_recommendations(
        student_answer=ans_q4,
        question_text="04. Can a static method directly access a non-static variable? Why or why not?",
        obtained_marks=3.0,
        total_marks=5.0,
        missing_concepts=["Handles runtime exceptions/errors", "Instance reference required for access"],
        ai_available=True,
        question_id="Q4"
    )
    t5_pass = (
        "Handles runtime exceptions/errors" in fb_cross["unrelated_cross_question_concepts"] and
        "Handles runtime exceptions/errors" not in fb_cross["substantive_missing_concepts"] and
        "Instance reference required for access" in fb_cross["substantive_missing_concepts"]
    )
    record(
        "TEST 5: Cross-Question Concept Isolation (Filters out off-topic concepts)",
        t5_pass,
        f"Cross-question concepts isolated: {fb_cross['unrelated_cross_question_concepts']}"
    )

    # TEST 6: Lecture Recommendation Matching for all 13 concepts
    all_recs_matched = True
    unmatched = []
    for concept in OOP_CONCEPT_DAG.keys():
        rec = get_recommendation_for_concept(concept)
        if not rec or not rec.get("resource_url") or not rec.get("verified_page"):
            all_recs_matched = False
            unmatched.append(concept)
    record(
        "TEST 6: Verified IT2030 Lecture PDF Recommendation Matching (100% Concept Coverage)",
        all_recs_matched,
        f"All 13 educational concepts have verified slide numbers and PDF URLs. Unmatched: {unmatched}"
    )

    # TEST 7: Prerequisite-First Ordering in Learning Recommendations
    # Multi-gap student: missing both 'Static belongs to class' (prerequisite) and 'Instance reference required for access' (dependent)
    gaps_dep = ["Instance reference required for access", "Static belongs to class"]
    diag = concept_dependency_service.analyze_student_profile(gaps_dep)
    remed_path = diag["remediation_learning_path"]
    step1 = remed_path[0]["concept"]
    step2 = remed_path[1]["concept"]
    t7_pass = (step1 == "Static belongs to class" and step2 == "Instance reference required for access")
    record(
        "TEST 7: Prerequisite-First Topological Sequence in Remediation Pathway",
        t7_pass,
        f"Step 1: '{step1}', Step 2: '{step2}'"
    )

    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed_tests} PASSED, {failed_tests} FAILED out of {passed_tests + failed_tests} tests.")
    print("=" * 80)
    return failed_tests == 0

if __name__ == "__main__":
    success = run_feedback_tests()
    sys.exit(0 if success else 1)
