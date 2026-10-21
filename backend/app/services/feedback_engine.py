from typing import List, Dict, Any, Optional
from app.schemas.schemas import RecommendationBase
from app.services.concept_dependency import OOP_CONCEPT_DAG
from app.services.lecture_catalog import get_recommendation_for_concept, VERIFIED_CONCEPT_LECTURE_MAP

# Expected concepts for the 5 standardized OOP curriculum questions
QUESTION_EXPECTED_CONCEPTS: Dict[str, List[str]] = {
    "Q1": [
        "Class as blueprint/template",
        "Object as class instance",
        "Concrete class-object example"
    ],
    "Q2": [
        "Inheritance of accessible fields",
        "Inheritance of accessible methods"
    ],
    "Q3": [
        "Child provides overriding implementation",
        "Child implementation executes on child object"
    ],
    "Q4": [
        "Static belongs to class",
        "instance variable belongs to object",
        "No direct instance-variable access from static method",
        "Instance reference required for access"
    ],
    "Q5": [
        "Handles runtime exceptions/errors",
        "Prevents abrupt termination or supports graceful recovery"
    ]
}


class FeedbackEngine:
    """
    Synthesizes authentic, evidence-based academic feedback and matches
    verified SLIIT IT2030 lecture recommendations based on:
    - Original student answer
    - Question prompt
    - Available rubric/marks evidence
    - AI-predicted missing concepts vs correctly identified concepts
    - Concept dependency root-cause diagnosis
    """

    @staticmethod
    def detect_question_id(question_text: str) -> str:
        """Helper to identify question ID (Q1-Q5) from question text."""
        q_clean = question_text.lower()
        if "difference between a class and an object" in q_clean or "01." in q_clean or "blueprint" in q_clean:
            return "Q1"
        elif "car class extends a vehicle" in q_clean or "02." in q_clean or "car class get from the vehicle" in q_clean:
            return "Q2"
        elif "overrides a method" in q_clean or "03." in q_clean or "child class overrides" in q_clean:
            return "Q3"
        elif "static method directly access" in q_clean or "04." in q_clean or "non-static variable" in q_clean:
            return "Q4"
        elif "exception handling" in q_clean or "05." in q_clean or "crashes" in q_clean:
            return "Q5"
        return "Q1"

    @classmethod
    def evaluate_student_answer_evidence(cls, q_id: str, student_answer: str) -> Dict[str, Any]:
        """
        Extracts direct empirical evidence from authentic student response text for Q1-Q5 expected concepts.
        """
        ans_lower = student_answer.lower()
        demonstrated = []
        evidence = {}

        if q_id == "Q1":
            if any(k in ans_lower for k in ["blueprint", "template", "prototype", "defines properties", "logical structure", "defines the structure"]):
                demonstrated.append("Class as blueprint/template")
                evidence["Class as blueprint/template"] = "Articulated class as blueprint/template"
            if any(k in ans_lower for k in ["instance", "real-world entity", "occupies memory", "created from", "concrete"]):
                demonstrated.append("Object as class instance")
                evidence["Object as class instance"] = "Identified object as an instance of a class"
            if any(k in ans_lower for k in ["car", "mycar", "vehicle", "house", "student", "s1", "new car", "example", "ex:", "for example"]):
                demonstrated.append("Concrete class-object example")
                evidence["Concrete class-object example"] = "Provided concrete illustrative example"

        elif q_id == "Q2":
            if any(k in ans_lower for k in ["variable", "attribute", "field", "property", "properties", "speed", "wheels", "data"]):
                demonstrated.append("Inheritance of accessible fields")
                evidence["Inheritance of accessible fields"] = "Identified inheritance of accessible fields/variables"
            if any(k in ans_lower for k in ["method", "behavior", "behaviour", "function", "action", "drive", "startengine", "operation"]):
                demonstrated.append("Inheritance of accessible methods")
                evidence["Inheritance of accessible methods"] = "Identified inheritance of accessible methods/behaviors"

        elif q_id == "Q3":
            if any(k in ans_lower for k in ["own version", "own implementation", "replaces", "changes behavior", "modifies", "overriding", "redefines", "different definition"]):
                demonstrated.append("Child provides overriding implementation")
                evidence["Child provides overriding implementation"] = "Explained child providing overriding implementation"
            if any(k in ans_lower for k in ["executes", "runs", "called on child", "runtime", "child object", "instead of parent", "invoked on", "dynamic", "called on"]):
                demonstrated.append("Child implementation executes on child object")
                evidence["Child implementation executes on child object"] = "Clarified runtime execution on child instance"

        elif q_id == "Q4":
            if any(k in ans_lower for k in ["cannot", "no", "can not", "not directly", "cannot directly", "no direct"]):
                demonstrated.append("No direct instance-variable access from static method")
                evidence["No direct instance-variable access from static method"] = "Correctly stated direct access is not possible"
            if any(k in ans_lower for k in ["static belongs to the class", "belongs to class", "class level", "class itself", "class memory", "static method belongs to the class"]):
                demonstrated.append("Static belongs to class")
                evidence["Static belongs to class"] = "Clarified static members belong to class"
            if any(k in ans_lower for k in ["non-static belongs to object", "variable belongs to an object", "instance variable", "belongs to specific object", "object level", "belongs to objects"]):
                demonstrated.append("instance variable belongs to object")
                evidence["instance variable belongs to object"] = "Clarified non-static variables belong to object instance"
            if any(k in ans_lower for k in ["object reference", "instance reference", "create an object", "instantiate", "new", "through an instance", "instance of the class"]):
                demonstrated.append("Instance reference required for access")
                evidence["Instance reference required for access"] = "Explained instance reference is required for access"

        elif q_id == "Q5":
            if any(k in ans_lower for k in ["handle errors", "handling errors", "catch errors", "runtime error", "try catch", "deal with errors", "manage errors", "catch", "throws", "handle"]):
                demonstrated.append("Handles runtime exceptions/errors")
                evidence["Handles runtime exceptions/errors"] = "Addressed error/exception handling mechanism"
            if any(k in ans_lower for k in ["crashing", "crashes", "prevent program crashes", "terminate", "termination", "graceful", "continue running", "abrupt", "normal flow", "stopping unexpectedly"]):
                demonstrated.append("Prevents abrupt termination or supports graceful recovery")
                evidence["Prevents abrupt termination or supports graceful recovery"] = "Explained resilience and preventing sudden termination"

        return {"demonstrated": demonstrated, "evidence": evidence}

    @classmethod
    def generate_feedback_and_recommendations(
        cls,
        student_answer: str,
        question_text: str,
        obtained_marks: Optional[float],
        total_marks: Optional[float],
        missing_concepts: List[str],
        ai_available: bool,
        question_id: Optional[str] = None,
        ai_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        q_id = question_id or cls.detect_question_id(question_text)
        expected_concepts = QUESTION_EXPECTED_CONCEPTS.get(q_id, [])

        # Evaluate textual evidence directly from authentic student answer
        evidence_eval = cls.evaluate_student_answer_evidence(q_id, student_answer)
        text_demonstrated = evidence_eval["demonstrated"]

        # Clean raw missing concepts: strictly exclude metadata labels (Requirement 4)
        EXCLUDED_META = {"none clearly identified", "requires human review"}
        raw_gaps = [
            c.strip() for c in missing_concepts
            if c.strip() and c.strip().lower() not in EXCLUDED_META
        ]

        # Isolate out-of-domain cross-question concepts (Requirement 7)
        # e.g., 'Handles runtime exceptions/errors' appearing under Q4
        unrelated_cross_question = [c for c in raw_gaps if c not in expected_concepts]
        domain_relevant_gaps = [c for c in raw_gaps if c in expected_concepts]

        # Uncertainty flags (Requirement 5)
        has_review_flag = any(c.strip().lower() == "requires human review" for c in missing_concepts)
        has_none_flag = any(c.strip().lower() == "none clearly identified" for c in missing_concepts)
        if ai_details and ai_details.get("is_uncertain"):
            has_review_flag = True

        # Reconcile demonstrated vs missing concepts
        # A concept is correctly identified if demonstrated in answer text or not flagged as missing
        is_empty_or_non_answer = len(student_answer.strip().split()) <= 3 and any(
            w in student_answer.lower() for w in ["cant", "can't", "remember", "dont", "don't", "know", "no idea"]
        )

        if is_empty_or_non_answer:
            correctly_identified = []
            substantive_gaps = list(expected_concepts)
            expected_undetected = list(expected_concepts)
        else:
            # Concepts positively evidenced in text are demonstrated
            correctly_identified = [c for c in expected_concepts if c in text_demonstrated]
            # Concepts not demonstrated are gaps
            expected_undetected = [c for c in expected_concepts if c not in correctly_identified]
            # Combine text-undetected with domain-relevant gaps from AI model
            substantive_gaps = list(dict.fromkeys(expected_undetected + domain_relevant_gaps))

        # 1. Strengths (Evidence-Based from student's actual text) - Requirement 9
        strengths_list = []
        if is_empty_or_non_answer:
            strengths_list.append(f"Response submitted: '{student_answer.strip()}'. (Engaged with the assessment interface).")
        elif correctly_identified:
            concept_str = ", ".join([f"[{c}]" for c in correctly_identified])
            strengths_list.append(f"You successfully articulated and demonstrated understanding of: {concept_str}.")
            # Add specific evidence notes
            if q_id == "Q1" and "Class as blueprint/template" in correctly_identified and "Object as class instance" in correctly_identified:
                strengths_list.append("Your explanation clearly contrasts the blueprint nature of a class with an instantiated object.")
            elif q_id == "Q2" and len(correctly_identified) == 2:
                strengths_list.append("You comprehensively covered both fields (attributes) and methods (behaviors) accessible via inheritance.")
            elif q_id == "Q3" and "Child provides overriding implementation" in correctly_identified:
                strengths_list.append("You accurately explained that the child class provides its own specialized method implementation.")
            elif q_id == "Q4" and "No direct instance-variable access from static method" in correctly_identified:
                strengths_list.append("You correctly stated that a static method cannot directly access non-static instance variables.")
            elif q_id == "Q5" and "Handles runtime exceptions/errors" in correctly_identified:
                strengths_list.append("You clearly explained the primary purpose of exception handling in managing runtime errors.")
        else:
            strengths_list.append("Your response engaged with the question topic.")

        strengths_text = " ".join(strengths_list)

        # 2. Specific Weaknesses - Requirement 9
        weaknesses_list = []
        if is_empty_or_non_answer:
            weaknesses_list.append(
                f"Your response ('{student_answer.strip()}') does not provide technical explanations. "
                f"Expected concepts not addressed: {', '.join([f'[{c}]' for c in expected_concepts])}."
            )
        elif substantive_gaps:
            weaknesses_list.append(
                f"Areas requiring conceptual reinforcement: {', '.join([f'[{c}]' for c in substantive_gaps])}."
            )
            # Add tailored reasoning grounded in the question
            if q_id == "Q1" and "Concrete class-object example" in substantive_gaps:
                weaknesses_list.append(
                    "Your answer provides definitions but omits a concrete illustrative code example or real-world analog (e.g., 'Car is a class, myCar is an object') requested by the prompt."
                )
            if q_id == "Q1" and "Class as blueprint/template" in substantive_gaps:
                weaknesses_list.append(
                    "Your response focuses on the object but does not explicitly define what a class represents (a blueprint or template)."
                )
            if q_id == "Q2" and "Inheritance of accessible fields" in substantive_gaps:
                weaknesses_list.append(
                    "You highlighted methods but did not explicitly mention inheritance of accessible instance variables/fields."
                )
            if q_id == "Q3" and "Child implementation executes on child object" in substantive_gaps:
                weaknesses_list.append(
                    "Your explanation does not explicitly describe runtime polymorphic dispatch—that when invoked on a child instance, the child's overriding version executes."
                )
            if q_id == "Q4" and "Instance reference required for access" in substantive_gaps:
                weaknesses_list.append(
                    "Your answer notes that direct access is prohibited, but does not explain the resolution: accessing non-static variables requires an explicit object instance reference."
                )
            if q_id == "Q5" and "Prevents abrupt termination or supports graceful recovery" in substantive_gaps:
                weaknesses_list.append(
                    "Your explanation omits the runtime stability benefit: preventing abrupt program termination and enabling graceful recovery."
                )
        else:
            weaknesses_list.append("Full conceptual alignment demonstrated across all expected curriculum benchmarks for this question.")

        # Document any isolated cross-question anomalies transparently
        if unrelated_cross_question:
            weaknesses_list.append(
                f"(Note: AI model detected unrelated concept(s) [{', '.join(unrelated_cross_question)}] "
                f"which belong to another question domain and have been filtered out of your knowledge gap profile)."
            )

        # Flag model uncertainty transparently (Requirement 5)
        if has_review_flag:
            weaknesses_list.append(
                "Model Assessment Status: This answer has been flagged as requiring instructor verification to confirm nuance alignment."
            )

        weaknesses_text = " ".join(weaknesses_list)

        # 3. Marks / Rubric Evidence - Requirement 10 (Do NOT fabricate marks)
        if obtained_marks is not None and total_marks and total_marks > 0:
            marks_pct = int((obtained_marks / total_marks) * 100)
            if substantive_gaps:
                deduction_reason = (
                    f"Awarded {obtained_marks}/{total_marks} marks ({marks_pct}%). "
                    f"Marks deducted due to omission of key rubric criteria: {', '.join(substantive_gaps)}."
                )
            else:
                deduction_reason = (
                    f"Awarded {obtained_marks}/{total_marks} marks ({marks_pct}%). "
                    "Full rubric alignment demonstrated across expected conceptual benchmarks."
                )
        else:
            deduction_reason = "Assessment marks not yet available."

        # 4. Individual Improvement Suggestions - Requirement 9
        suggestions_list = []
        if substantive_gaps:
            for gap in substantive_gaps:
                if q_id == "Q1" and gap == "Concrete class-object example":
                    suggestions_list.append("Practice writing paired class and object declarations (e.g., class Car { String model; } Car myCar = new Car();).")
                elif q_id == "Q1" and gap == "Class as blueprint/template":
                    suggestions_list.append("Always define a class as the structural blueprint or user-defined data type from which objects are instantiated.")
                elif q_id == "Q2":
                    suggestions_list.append("Review Java access modifiers (public, protected, package-private) and how subclasses inherit non-private fields and methods.")
                elif q_id == "Q3":
                    suggestions_list.append("Study runtime dynamic method dispatch and practice using the @Override annotation on inherited methods.")
                elif q_id == "Q4":
                    suggestions_list.append("Remember that static methods execute in class memory without a 'this' context; instantiate an object to access instance variables.")
                elif q_id == "Q5":
                    suggestions_list.append("Practice implementing try-catch-finally blocks and handle specific exceptions rather than generic errors.")

            # Prerequisite advice from DAG
            for gap in substantive_gaps:
                if gap in OOP_CONCEPT_DAG and OOP_CONCEPT_DAG[gap].get("prerequisites"):
                    prereq = OOP_CONCEPT_DAG[gap]["prerequisites"][0]
                    suggestions_list.append(f"Review prerequisite '{prereq}' to solidify your foundation for '{gap}'.")
        else:
            suggestions_list.append("Maintain your thorough technical precision and continue supporting definitions with concrete code examples.")

        # Deduplicate suggestions
        seen_sug = set()
        unique_sug = []
        for s in suggestions_list:
            if s not in seen_sug:
                seen_sug.add(s)
                unique_sug.append(s)

        improvement_suggestions_text = " ".join(unique_sug)

        # 5. Formulate Comprehensive Personalized Feedback
        feedback_lines = [
            f"Assessment Evaluation for: '{question_text.strip()}'",
            f"Status: {deduction_reason}",
            f"What You Answered Correctly:\n{strengths_text}",
            f"What You Missed / Areas for Growth:\n{weaknesses_text}",
            f"Actionable Next Steps:\n{improvement_suggestions_text}"
        ]
        personalized_feedback_text = "\n\n".join(feedback_lines)

        # 6. Generate Personalized IT2030 Lecture Recommendations
        recommendations: List[RecommendationBase] = []
        target_concepts = substantive_gaps if substantive_gaps else correctly_identified[:1]
        for concept in target_concepts:
            rec_info = get_recommendation_for_concept(concept)
            if rec_info:
                recommendations.append(
                    RecommendationBase(
                        concept_name=concept,
                        resource_title=rec_info["resource_title"],
                        resource_type="SLIIT IT2030 Lecture PDF",
                        resource_url=rec_info["resource_url"],
                        priority_level=rec_info["learning_priority"],
                        lecture_number=rec_info["lecture_number"],
                        verified_page=rec_info["verified_page"],
                        reason=rec_info["reason"],
                        practice_activity=rec_info["practice_activity"],
                        download_url=rec_info["download_url"],
                        frontend_view_url=rec_info["frontend_view_url"]
                    )
                )

        if not recommendations:
            recommendations.append(
                RecommendationBase(
                    concept_name="OOP Architecture",
                    resource_title="Lecture 02: Java Classes and Objects (Slide 9)",
                    resource_type="SLIIT IT2030 Lecture PDF",
                    resource_url="/api/lectures/Lecture%2002%20-%20Classes%20and%20Objects.pdf#page=9",
                    priority_level="Low",
                    lecture_number="Lecture 02",
                    verified_page=9,
                    reason="Comprehensive overview of core Java Object-Oriented Programming structures and design principles.",
                    practice_activity="Review Lecture 02 Slide 12 Hospital Management System exercise.",
                    download_url="/api/lectures/Lecture%2002%20-%20Classes%20and%20Objects.pdf?download=true",
                    frontend_view_url="/lectures/Lecture%2002%20-%20Classes%20and%20Objects.pdf#page=9"
                )
            )

        return {
            "strengths": strengths_text,
            "weaknesses": weaknesses_text,
            "correctly_identified_concepts": correctly_identified,
            "substantive_missing_concepts": substantive_gaps,
            "expected_undetected_concepts": expected_undetected,
            "unrelated_cross_question_concepts": unrelated_cross_question,
            "requires_human_review": has_review_flag,
            "mark_deduction_reason": deduction_reason,
            "improvement_suggestions": improvement_suggestions_text,
            "personalized_feedback": personalized_feedback_text,
            "recommendations": recommendations
        }


feedback_engine = FeedbackEngine()
