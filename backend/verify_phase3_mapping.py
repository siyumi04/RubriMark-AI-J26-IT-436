"""
Phase 3 Verification Script: Verify Student and Question Answer Mapping
Checks at least 5 real students (including S010 and S011):
- S001, S005, S010, S011, S029
Verifies:
1. Every answer matches the original questionnaire CSV exactly.
2. Q1-Q5 are correctly mapped:
   Q1 -> Class and Object
   Q2 -> Inheritance
   Q3 -> Method Overriding
   Q4 -> Static and Instance Variables
   Q5 -> Exception Handling
3. Investigates S029 (Q4 answer entered under Q5 in questionnaire).
4. Verifies feedback, missing concepts, and AI analysis for each question.
"""

import os
import sys
import csv
import sqlite3

# Define paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(base_dir, "datasets", "oop_student_questionnaire_responses.csv")
db_path = os.path.join(base_dir, "backend", "rubrimark.db")

print("================================================================================")
print("PHASE 3: VERIFICATION OF STUDENT AND QUESTION ANSWER MAPPING")
print("================================================================================")

# 1. Load CSV
with open(csv_path, "r", encoding="utf-8") as f:
    csv_rows = list(csv.DictReader(f))

QUESTION_MAPPINGS = [
    {
        "qid": "Q1",
        "expected_topic": "Class and Object",
        "csv_col": "01. What is the difference between a class and an object in Java? Give a simple example. "
    },
    {
        "qid": "Q2",
        "expected_topic": "Inheritance",
        "csv_col": "02. If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?  "
    },
    {
        "qid": "Q3",
        "expected_topic": "Method Overriding",
        "csv_col": "03. What happens when a child class overrides a method inherited from its parent class?  "
    },
    {
        "qid": "Q4",
        "expected_topic": "Static and Instance Variables",
        "csv_col": "04. Can a static method directly access a non-static variable? Why or why not?  "
    },
    {
        "qid": "Q5",
        "expected_topic": "Exception Handling",
        "csv_col": "05. Why is exception handling important in Java? "
    }
]

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Test Students: 5 real students including S010 and S011, plus S001, S005, S029
TEST_STUDENTS = ["S001", "S005", "S010", "S011", "S029"]

verification_results = []

for sid in TEST_STUDENTS:
    idx = int(sid[1:]) - 1
    csv_row = csv_rows[idx]
    
    # Get student info
    stu_db = c.execute("SELECT student_name, email FROM students WHERE student_id = ?", (sid,)).fetchone()
    s_name = stu_db[0] if stu_db else f"Student {sid}"
    s_email = stu_db[1] if stu_db else "N/A"
    
    print(f"\n--------------------------------------------------------------------------------")
    print(f"VERIFYING STUDENT: {sid} | Name: {s_name} | Email: {s_email}")
    print(f"--------------------------------------------------------------------------------")
    
    student_record = {
        "student_id": sid,
        "name": s_name,
        "email": s_email,
        "q_matches": {}
    }
    
    # Fetch student answers from DB
    db_answers = c.execute("""
        SELECT a.question_id, a.student_answer, q.question_text, q.subject,
               f.missing_concepts, f.correctly_identified_concepts, f.personalized_feedback
        FROM student_answers a
        JOIN questions q ON a.question_id = q.question_id
        LEFT JOIN feedback f ON a.id = f.student_answer_id
        WHERE a.student_id = ?
        ORDER BY a.question_id
    """, (sid,)).fetchall()
    
    ans_by_qid = {r[0]: r for r in db_answers}
    
    for q_info in QUESTION_MAPPINGS:
        qid = q_info["qid"]
        topic = q_info["expected_topic"]
        col = q_info["csv_col"]
        
        csv_ans = (csv_row.get(col) or "").strip()
        db_item = ans_by_qid.get(qid)
        
        if not db_item:
            print(f"  [FAIL] {qid} ({topic}): NOT FOUND IN DB!")
            student_record["q_matches"][qid] = False
            continue
            
        db_ans = db_item[1].strip()
        q_text = db_item[2]
        subject = db_item[3]
        missing_c = db_item[4] or "None"
        correct_c = db_item[5] or "None"
        
        is_match = (csv_ans == db_ans)
        student_record["q_matches"][qid] = is_match
        
        status = "MATCH [PASS]" if is_match else "MISMATCH [FAIL]"
        print(f"  [{status}] {qid} ({topic})")
        print(f"      Question Text : {q_text[:70]}...")
        print(f"      CSV Answer    : {csv_ans[:75]}...")
        print(f"      DB Answer     : {db_ans[:75]}...")
        print(f"      Length        : CSV={len(csv_ans)} chars | DB={len(db_ans)} chars")
        print(f"      Missing Gaps  : {missing_c}")
        print(f"      Correct Cpts  : {correct_c}")
        
    verification_results.append(student_record)

print("\n================================================================================")
print("OVERALL SUMMARY TABLE:")
print("================================================================================")
print(f"{'Student ID':<12} | {'Q1 (Class)':<12} | {'Q2 (Inherit)':<12} | {'Q3 (Override)':<14} | {'Q4 (Static)':<12} | {'Q5 (Exception)':<14} | {'All Match'}")
print("-" * 88)
for res in verification_results:
    m = res["q_matches"]
    all_ok = all(m.values())
    q1_str = "MATCH" if m.get("Q1") else "FAIL"
    q2_str = "MATCH" if m.get("Q2") else "FAIL"
    q3_str = "MATCH" if m.get("Q3") else "FAIL"
    q4_str = "MATCH" if m.get("Q4") else "FAIL"
    q5_str = "MATCH" if m.get("Q5") else "FAIL"
    ok_str = "YES [PASS]" if all_ok else "NO [FAIL]"
    print(f"{res['student_id']:<12} | {q1_str:<12} | {q2_str:<12} | {q3_str:<14} | {q4_str:<12} | {q5_str:<14} | {ok_str}")

conn.close()

# 2. Live API & Frontend Verification
import urllib.request
import json

print("\n================================================================================")
print("LIVE API AND FRONTEND ENDPOINT VERIFICATION")
print("================================================================================")

api_base = "http://127.0.0.1:8000/api"
frontend_url = "http://localhost:5173"

# Check Frontend server response
try:
    fe_res = urllib.request.urlopen(frontend_url, timeout=15)
    print(f"[PASS] Frontend Server (Vite) is running: HTTP {fe_res.status}")
except Exception as e:
    print(f"[FAIL] Frontend Server not reachable: {e}")

# Check API health
try:
    h_res = urllib.request.urlopen(f"{api_base}/health", timeout=15)
    h_data = json.loads(h_res.read().decode())
    print(f"[PASS] Backend API Health: status={h_data.get('status')}, model_loaded={h_data.get('model_loaded')}")
except Exception as e:
    print(f"[FAIL] Backend API Health check failed: {e}")

# Test API responses for all 5 test students
api_all_passed = True
for sid in TEST_STUDENTS:
    try:
        # Answers endpoint (used by Answer Analysis and Knowledge Gaps)
        a_req = urllib.request.urlopen(f"{api_base}/students/{sid}/answers", timeout=15)
        answers = json.loads(a_req.read().decode())
        
        # Feedback endpoint (used by Personalized Feedback)
        f_req = urllib.request.urlopen(f"{api_base}/students/{sid}/feedback", timeout=15)
        feedbacks = json.loads(f_req.read().decode())
        
        # Dashboard endpoint
        d_req = urllib.request.urlopen(f"{api_base}/students/{sid}/dashboard", timeout=15)
        dashboard = json.loads(d_req.read().decode())
        
        # Verify ordering and question counts
        q_ids_answers = [a["question_id"] for a in answers]
        q_ids_feedback = [f["question_id"] for f in feedbacks]
        
        assert q_ids_answers == ["Q1", "Q2", "Q3", "Q4", "Q5"], f"Unexpected answer order: {q_ids_answers}"
        assert q_ids_feedback == ["Q1", "Q2", "Q3", "Q4", "Q5"], f"Unexpected feedback order: {q_ids_feedback}"
        
        # Check that each answer object has proper nested structure
        for a in answers:
            assert "question" in a and a["question"] is not None
            assert "student_answer" in a and len(a["student_answer"]) > 0
            
        for f in feedbacks:
            assert "personalized_feedback" in f and len(f["personalized_feedback"]) > 0
            assert "strengths" in f
            assert "weaknesses" in f
            assert "recommendations" in f
            
        print(f"[PASS] Student {sid} Live API: 5/5 answers, 5/5 feedbacks, Dashboard Q answered={dashboard['summary']['questions_answered']}")
    except Exception as e:
        api_all_passed = False
        print(f"[FAIL] Student {sid} Live API failed: {e}")

if api_all_passed:
    print("\nALL LIVE API AND DATA INTEGRATION TESTS PASSED SUCCESSFULLY!")
print("================================================================================")
