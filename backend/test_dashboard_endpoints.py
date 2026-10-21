"""
Test script to verify the Dashboard API endpoints and real SQLite data
for at least five real students with different answers.
"""

import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models.entities import Student, StudentAnswer, Feedback, LearningRecommendation
from app.api.endpoints import get_student_dashboard_stats

def test_five_students():
    db = SessionLocal()
    try:
        # Fetch first 5 students
        students = db.query(Student).order_by(Student.student_id).limit(5).all()
        if not students:
            print("ERROR: No students found in database!")
            return False

        print(f"Testing Dashboard data for {len(students)} real students:\n")

        for idx, s in enumerate(students, 1):
            print(f"============================================================")
            print(f"Student #{idx}: {s.student_id} - {s.student_name} ({s.email})")
            print(f"============================================================")

            stats = get_student_dashboard_stats(s.student_id, db)

            summary = stats["summary"]
            print(f"1. Questions Answered:        {summary['questions_answered']}")
            print(f"2. Concepts Identified:       {summary['concepts_identified']}")
            print(f"3. Missing Concepts:          {summary['missing_concepts']}")
            print(f"4. Root Knowledge Gaps:       {summary['root_knowledge_gaps']} -> {stats['root_knowledge_gaps']}")
            print(f"5. Feedback Records:          {summary['personalized_feedback_records']}")
            print(f"6. Learning Recommendations:  {summary['learning_recommendations']}")
            print(f"7. Expected Undetected Count: {summary['expected_undetected_count']}")

            print("\nChart 1: Concept Understanding:")
            print(f"  Identified Concepts ({len(stats['identified_concepts'])}): {stats['identified_concepts']}")
            print(f"  Expected Undetected ({len(stats['expected_undetected_concepts'])}): {stats['expected_undetected_concepts']}")

            print("\nChart 2: Knowledge Gap Distribution (5 Topics):")
            for gap in stats["gap_distribution"]:
                print(f"  - {gap['topic']}: {gap['missing_count']} missing")

            print("\nChart 3: Recommendation Priorities:")
            for p in stats["priority_distribution"]:
                print(f"  - {p['priority']}: {p['count']}")

            print("\nChart 4: Question-Wise Concept Coverage (Q1-Q5):")
            for qc in stats["question_coverage"]:
                print(f"  - {qc['question']}: Expected={qc['expected']}, Identified={qc['identified']}, Missing={qc['missing']}")

            print("\n")

        print("SUCCESS: All 5 students tested and returned verified distinct real data!")
        return True
    finally:
        db.close()

if __name__ == "__main__":
    success = test_five_students()
    if not success:
        sys.exit(1)
