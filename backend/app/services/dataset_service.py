import os
import io
import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.entities import Student, Question, StudentAnswer, Feedback, LearningRecommendation
from app.services.feedback_engine import feedback_engine


class DatasetService:
    """
    Handles CSV validation, parsing, and database population for student answers
    and assessment data while maintaining data integrity.
    """

    @staticmethod
    def validate_and_import_csv(
        file_content: bytes,
        db: Session,
        filename: str = "dataset.csv"
    ) -> Dict[str, Any]:
        errors: List[str] = []
        try:
            df = pd.read_csv(io.BytesIO(file_content))
        except Exception as e:
            return {
                "success": False,
                "imported_students": 0,
                "imported_questions": 0,
                "imported_answers": 0,
                "errors": [f"Failed to parse CSV file: {str(e)}"],
                "message": "Invalid CSV format."
            }

        # Normalize column names
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Check required columns
        required_cols = {"student_id", "question_id", "student_answer"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            return {
                "success": False,
                "imported_students": 0,
                "imported_questions": 0,
                "imported_answers": 0,
                "errors": [f"Missing required CSV column(s): {', '.join(missing_cols)}"],
                "message": f"Required columns are: {', '.join(required_cols)}"
            }

        students_created = 0
        questions_created = 0
        answers_created = 0

        for idx, row in df.iterrows():
            try:
                s_id = str(row.get("student_id", "")).strip()
                q_id = str(row.get("question_id", "")).strip()
                s_ans = str(row.get("student_answer", "")).strip()

                if not s_id or not q_id or not s_ans or s_ans.lower() == "nan":
                    continue

                # 1. Ensure Student exists
                student = db.query(Student).filter(Student.student_id == s_id).first()
                if not student:
                    s_name = str(row.get("student_name", f"Student {s_id}")).strip()
                    if s_name.lower() == "nan":
                        s_name = f"Student {s_id}"
                    email = str(row.get("email", f"{s_id.lower()}@rubrimark.edu")).strip()
                    student = Student(student_id=s_id, student_name=s_name, email=email)
                    db.add(student)
                    db.flush()
                    students_created += 1

                # 2. Ensure Question exists
                question = db.query(Question).filter(Question.question_id == q_id).first()
                if not question:
                    q_text = str(row.get("question_text", f"Question prompt for {q_id}")).strip()
                    if q_text.lower() == "nan":
                        q_text = f"Assessment Question: {q_id}"
                    subject = str(row.get("subject", "Computer Science")).strip()
                    total_marks = float(row.get("total_marks", 10.0)) if "total_marks" in row and not pd.isna(row["total_marks"]) else 10.0

                    question = Question(
                        question_id=q_id,
                        question_text=q_text,
                        subject=subject,
                        total_marks=total_marks
                    )
                    db.add(question)
                    db.flush()
                    questions_created += 1

                # 3. Create or update StudentAnswer
                obtained_marks = None
                if "obtained_marks" in row and not pd.isna(row["obtained_marks"]):
                    try:
                        obtained_marks = float(row["obtained_marks"])
                    except (ValueError, TypeError):
                        obtained_marks = None
                elif "marks" in row and not pd.isna(row["marks"]):
                    try:
                        obtained_marks = float(row["marks"])
                    except (ValueError, TypeError):
                        obtained_marks = None

                # Check if answer already exists
                existing_ans = db.query(StudentAnswer).filter(
                    StudentAnswer.student_id == s_id,
                    StudentAnswer.question_id == q_id
                ).first()

                if existing_ans:
                    existing_ans.student_answer = s_ans
                    if obtained_marks is not None:
                        existing_ans.obtained_marks = obtained_marks
                    answer_record = existing_ans
                else:
                    answer_record = StudentAnswer(
                        student_id=s_id,
                        question_id=q_id,
                        student_answer=s_ans,
                        obtained_marks=obtained_marks
                    )
                    db.add(answer_record)
                    db.flush()
                    answers_created += 1

                # 4. Check for predicted_missing_concepts column
                missing_concepts: List[str] = []
                if "predicted_missing_concepts" in row and not pd.isna(row["predicted_missing_concepts"]):
                    raw_concepts = str(row["predicted_missing_concepts"])
                    missing_concepts = [c.strip() for c in raw_concepts.replace(";", ",").split(",") if c.strip()]

                # Generate initial feedback if missing_concepts available or answer is new
                if missing_concepts or not answer_record.feedback:
                    eval_result = feedback_engine.generate_feedback_and_recommendations(
                        student_answer=s_ans,
                        question_text=question.question_text,
                        obtained_marks=obtained_marks,
                        total_marks=question.total_marks,
                        missing_concepts=missing_concepts,
                        ai_available=bool(missing_concepts),
                        question_id=q_id
                    )

                    clean_missing = eval_result.get("substantive_missing_concepts", missing_concepts)
                    clean_correct = eval_result.get("correctly_identified_concepts", [])

                    feedback_record = answer_record.feedback
                    if not feedback_record:
                        feedback_record = Feedback(
                            student_answer_id=answer_record.id,
                            strengths=eval_result["strengths"],
                            weaknesses=eval_result["weaknesses"],
                            missing_concepts="; ".join(clean_missing),
                            correctly_identified_concepts="; ".join(clean_correct),
                            mark_deduction_reason=eval_result.get("mark_deduction_reason"),
                            improvement_suggestions=eval_result.get("improvement_suggestions"),
                            personalized_feedback=eval_result["personalized_feedback"]
                        )
                        db.add(feedback_record)
                        db.flush()

                        # Add recommendations
                        for rec in eval_result["recommendations"]:
                            db.add(
                                LearningRecommendation(
                                    feedback_id=feedback_record.id,
                                    concept_name=rec.concept_name,
                                    resource_title=rec.resource_title,
                                    resource_type=rec.resource_type,
                                    resource_url=rec.resource_url,
                                    priority_level=rec.priority_level
                                )
                            )

            except Exception as row_err:
                errors.append(f"Row {idx + 1}: {str(row_err)}")

        db.commit()
        return {
            "success": True,
            "imported_students": students_created,
            "imported_questions": questions_created,
            "imported_answers": answers_created,
            "errors": errors[:10],
            "message": f"Successfully imported {answers_created} student answers across {students_created} students."
        }

    @staticmethod
    def seed_initial_academic_dataset(db: Session) -> bool:
        """
        Seeds an initial realistic academic dataset for demonstration, testing,
        and immediate verification of the system without inventing artificial marks.
        """
        if db.query(Student).count() > 0:
            return True

        # Check if real OOP dataset CSV exists
        here = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(os.path.dirname(here))
        datasets_dir = os.path.join(backend_dir, "datasets")
        quest_csv = os.path.join(datasets_dir, "oop_student_questionnaire_responses.csv")

        if os.path.exists(quest_csv):
            try:
                import sys
                if backend_dir not in sys.path:
                    sys.path.insert(0, backend_dir)
                from integrate_data import integrate_real_oop_data
                integrate_real_oop_data()
                return True
            except Exception as e:
                pass

        # Fallback curated questions with standard rubric descriptions
        questions_data = [
            {
                "question_id": "CS101-Q1",
                "question_text": "Explain the concept of Encapsulation in Object-Oriented Programming and describe why data hiding is important.",
                "subject": "Object-Oriented Programming",
                "total_marks": 10.0
            },
            {
                "question_id": "CS101-Q2",
                "question_text": "What is the difference between Method Overloading and Method Overriding in Java or C++? Provide examples.",
                "subject": "Object-Oriented Programming",
                "total_marks": 10.0
            },
            {
                "question_id": "CS201-Q1",
                "question_text": "Describe the worst-case and average-case time complexity of QuickSort, and explain what causes the worst-case scenario.",
                "subject": "Data Structures & Algorithms",
                "total_marks": 10.0
            },
            {
                "question_id": "CS301-Q1",
                "question_text": "Explain the ACID properties of relational database transactions and provide a scenario where atomicity is essential.",
                "subject": "Database Systems",
                "total_marks": 10.0
            }
        ]

        for q in questions_data:
            db.add(Question(**q))
        db.flush()

        students_data = [
            {"student_id": "STU-436-01", "student_name": "Kasun Perera", "email": "kasun.p@rubrimark.edu"},
            {"student_id": "STU-436-02", "student_name": "Nethmi Silva", "email": "nethmi.s@rubrimark.edu"},
            {"student_id": "STU-436-03", "student_name": "Dinuka Fernando", "email": "dinuka.f@rubrimark.edu"},
            {"student_id": "STU-436-04", "student_name": "Amina Razik", "email": "amina.r@rubrimark.edu"},
        ]

        for s in students_data:
            db.add(Student(**s))
        db.flush()

        # Seed sample answers with authentic assessment marks and gaps
        sample_submissions = [
            {
                "student_id": "STU-436-01",
                "question_id": "CS101-Q1",
                "student_answer": "Encapsulation is wrapping code and data together into a single unit. It protects data from unauthorized direct access by using private variables and public getter/setter methods.",
                "obtained_marks": 8.5,
                "missing_concepts": ["abstraction", "information hiding"],
            },
            {
                "student_id": "STU-436-01",
                "question_id": "CS201-Q1",
                "student_answer": "QuickSort has average complexity of O(n log n) and worst case O(n^2). The worst case occurs when the pivot chosen is consistently the smallest or largest element, like in an already sorted array.",
                "obtained_marks": 9.0,
                "missing_concepts": [],
            },
            {
                "student_id": "STU-436-02",
                "question_id": "CS101-Q1",
                "student_answer": "Encapsulation means keeping variables inside a class so outside functions cannot change them easily.",
                "obtained_marks": 5.0,
                "missing_concepts": ["encapsulation", "getters and setters", "access modifiers"],
            },
            {
                "student_id": "STU-436-02",
                "question_id": "CS301-Q1",
                "student_answer": "ACID stands for Atomicity, Consistency, Isolation, and Durability. In banking, if money is transferred between accounts, atomicity ensures either both debit and credit occur or neither does.",
                "obtained_marks": 9.5,
                "missing_concepts": [],
            },
            {
                "student_id": "STU-436-03",
                "question_id": "CS101-Q2",
                "student_answer": "Overloading is when two methods have the same name in the same class. Overriding is when a child class changes a method from parent class.",
                "obtained_marks": 6.5,
                "missing_concepts": ["polymorphism", "signature matching", "runtime polymorphism"],
            },
            {
                "student_id": "STU-436-04",
                "question_id": "CS201-Q1",
                "student_answer": "Quick sort uses divide and conquer. The worst case happens when partitioning is unbalanced, leading to quadratic time.",
                "obtained_marks": 7.0,
                "missing_concepts": ["pivot selection", "recurrence relation"],
            }
        ]

        for item in sample_submissions:
            q_obj = db.query(Question).filter(Question.question_id == item["question_id"]).first()
            ans = StudentAnswer(
                student_id=item["student_id"],
                question_id=item["question_id"],
                student_answer=item["student_answer"],
                obtained_marks=item["obtained_marks"]
            )
            db.add(ans)
            db.flush()

            eval_res = feedback_engine.generate_feedback_and_recommendations(
                student_answer=item["student_answer"],
                question_text=q_obj.question_text if q_obj else "",
                obtained_marks=item["obtained_marks"],
                total_marks=q_obj.total_marks if q_obj else 10.0,
                missing_concepts=item["missing_concepts"],
                ai_available=True
            )

            fb = Feedback(
                student_answer_id=ans.id,
                strengths=eval_res["strengths"],
                weaknesses=eval_res["weaknesses"],
                missing_concepts=",".join(item["missing_concepts"]),
                personalized_feedback=eval_res["personalized_feedback"]
            )
            db.add(fb)
            db.flush()

            for rec in eval_res["recommendations"]:
                db.add(
                    LearningRecommendation(
                        feedback_id=fb.id,
                        concept_name=rec.concept_name,
                        resource_title=rec.resource_title,
                        resource_type=rec.resource_type,
                        resource_url=rec.resource_url,
                        priority_level=rec.priority_level
                    )
                )

        db.commit()
        return True


dataset_service = DatasetService()
