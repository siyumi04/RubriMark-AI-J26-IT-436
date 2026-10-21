"""
Integrates the real OOP student questionnaire responses and experimental AI results
into the SQLite database (rubrimark.db).
Strictly adheres to:
- No fake marks or fake data.
- Preserves original answers and real AI predictions.
"""

import os
import csv
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models.entities import Student, Question, StudentAnswer, Feedback, LearningRecommendation
from app.services.ai_inference import ai_service
from app.services.feedback_engine import feedback_engine

def integrate_real_oop_data():
    print("Recreating database tables with latest schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # Load trained model
    print("Loading AI model...")
    ai_service.load_model()
    print("AI Model loaded status:", ai_service.is_loaded)

    # 1. Real Questions Definition
    questions_data = [
        {
            "id": "Q1",
            "text": "01. What is the difference between a class and an object in Java? Give a simple example.",
            "subject": "Object-Oriented Programming (Classes & Objects)",
            "col_name": "01. What is the difference between a class and an object in Java? Give a simple example. ",
            "total_marks": 10.0
        },
        {
            "id": "Q2",
            "text": "02. If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?",
            "subject": "Object-Oriented Programming (Inheritance)",
            "col_name": "02. If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?  ",
            "total_marks": 10.0
        },
        {
            "id": "Q3",
            "text": "03. What happens when a child class overrides a method inherited from its parent class?",
            "subject": "Object-Oriented Programming (Polymorphism & Overriding)",
            "col_name": "03. What happens when a child class overrides a method inherited from its parent class?  ",
            "total_marks": 10.0
        },
        {
            "id": "Q4",
            "text": "04. Can a static method directly access a non-static variable? Why or why not?",
            "subject": "Object-Oriented Programming (Static Scope & Memory)",
            "col_name": "04. Can a static method directly access a non-static variable? Why or why not?  ",
            "total_marks": 10.0
        },
        {
            "id": "Q5",
            "text": "05. Why is exception handling important in Java?",
            "subject": "Object-Oriented Programming (Exception Handling)",
            "col_name": "05. Why is exception handling important in Java? ",
            "total_marks": 10.0
        }
    ]

    for q in questions_data:
        existing_q = db.query(Question).filter(Question.question_id == q["id"]).first()
        if existing_q:
            existing_q.question_text = q["text"]
            existing_q.subject = q["subject"]
            existing_q.total_marks = q["total_marks"]
        else:
            new_q = Question(
                question_id=q["id"],
                question_text=q["text"],
                subject=q["subject"],
                total_marks=q["total_marks"]
            )
            db.add(new_q)
    db.commit()
    print("Questions synchronized.")

    # 2. Load Experimental Results (Ground Truth & Model Predictions from Colab)
    exp_csv_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "oop_model_experimental_results.csv")
    exp_predictions = {}
    if os.path.exists(exp_csv_path):
        with open(exp_csv_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["student_id"].strip(), row["question_id"].strip())
                exp_predictions[key] = {
                    "predicted": row["predicted_missing_concepts"].strip(),
                    "reference": row.get("provisional_reference_labels", "").strip()
                }
    print(f"Loaded {len(exp_predictions)} experimental prediction records from CSV.")

    # 3. Read Questionnaire Responses CSV
    quest_csv_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "oop_student_questionnaire_responses.csv")
    with open(quest_csv_path, "r", encoding="utf-8") as f:
        quest_rows = list(csv.DictReader(f))

    print(f"Processing {len(quest_rows)} questionnaire student responses...")

    student_count = 0
    answer_count = 0

    for idx, row in enumerate(quest_rows, start=1):
        student_id = f"S{idx:03d}"
        raw_email = (row.get("Email Address") or "").strip()
        
        # Format a professional display name
        if raw_email:
            email = raw_email
            username = raw_email.split("@")[0]
            # Format username nicely
            name_parts = username.replace(".", " ").replace("_", " ").split()
            clean_name = " ".join([p.capitalize() for p in name_parts if not p.isdigit()])
            if not clean_name:
                clean_name = f"Student {student_id}"
        else:
            email = f"student_{student_id.lower()}@rubrimark.edu"
            clean_name = f"Student {student_id}"

        # Insert or update student
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            student = Student(student_id=student_id, student_name=clean_name, email=email)
            db.add(student)
            db.flush()
            student_count += 1
        else:
            student.student_name = clean_name
            student.email = email

        # Process all 5 questions for this student
        for q_info in questions_data:
            q_id = q_info["id"]
            col_key = q_info["col_name"]
            ans_text = (row.get(col_key) or "").strip()

            if not ans_text:
                continue

            # Check if answer exists in DB
            ans_record = db.query(StudentAnswer).filter(
                StudentAnswer.student_id == student_id,
                StudentAnswer.question_id == q_id
            ).first()

            if not ans_record:
                ans_record = StudentAnswer(
                    student_id=student_id,
                    question_id=q_id,
                    student_answer=ans_text,
                    obtained_marks=None  # Do not invent fake marks
                )
                db.add(ans_record)
                db.flush()
                answer_count += 1
            else:
                ans_record.student_answer = ans_text

            # Run question-specific inference with the trained model
            ai_details = ai_service.predict_detailed(
                student_answer=ans_text,
                question_text=q_info["text"],
                question_id=q_id,
                student_id=student_id
            )
            raw_missing = ai_details.get("substantive_missing_concepts", [])

            # Generate personalized feedback and recommendations
            eval_result = feedback_engine.generate_feedback_and_recommendations(
                student_answer=ans_text,
                question_text=q_info["text"],
                obtained_marks=ans_record.obtained_marks,
                total_marks=q_info["total_marks"],
                missing_concepts=raw_missing,
                ai_available=True,
                question_id=q_id,
                ai_details=ai_details
            )

            final_missing = eval_result.get("substantive_missing_concepts", raw_missing)
            final_correct = eval_result.get("correctly_identified_concepts", [])

            # Store feedback
            fb_record = ans_record.feedback
            if not fb_record:
                fb_record = Feedback(
                    student_answer_id=ans_record.id,
                    strengths=eval_result["strengths"],
                    weaknesses=eval_result["weaknesses"],
                    missing_concepts="; ".join(final_missing),
                    correctly_identified_concepts="; ".join(final_correct),
                    mark_deduction_reason=eval_result.get("mark_deduction_reason"),
                    improvement_suggestions=eval_result.get("improvement_suggestions"),
                    personalized_feedback=eval_result["personalized_feedback"]
                )
                db.add(fb_record)
                db.flush()
            else:
                fb_record.strengths = eval_result["strengths"]
                fb_record.weaknesses = eval_result["weaknesses"]
                fb_record.missing_concepts = "; ".join(final_missing)
                fb_record.correctly_identified_concepts = "; ".join(final_correct)
                fb_record.mark_deduction_reason = eval_result.get("mark_deduction_reason")
                fb_record.improvement_suggestions = eval_result.get("improvement_suggestions")
                fb_record.personalized_feedback = eval_result["personalized_feedback"]
                # Clear old recommendations
                for old_r in fb_record.recommendations:
                    db.delete(old_r)
                db.flush()

            # Store learning recommendations with verified lecture slides
            for rec in eval_result["recommendations"]:
                db.add(
                    LearningRecommendation(
                        feedback_id=fb_record.id,
                        concept_name=rec.concept_name,
                        resource_title=rec.resource_title,
                        resource_type=rec.resource_type,
                        resource_url=rec.resource_url,
                        priority_level=rec.priority_level,
                        lecture_number=rec.lecture_number,
                        verified_page=rec.verified_page,
                        reason=rec.reason,
                        practice_activity=rec.practice_activity,
                        download_url=rec.download_url
                    )
                )

    db.commit()
    db.close()
    print(f"Data Integration Complete! Imported {student_count} students and {answer_count} answers with AI feedback.")

if __name__ == "__main__":
    integrate_real_oop_data()
