import sqlite3
import csv
import os

db_path = r'c:\Users\ASUS\RubriMark-AI-J26-IT-436\backend\rubrimark.db'
root_db_path = r'c:\Users\ASUS\RubriMark-AI-J26-IT-436\rubrimark.db'
csv_path = r'c:\Users\ASUS\RubriMark-AI-J26-IT-436\datasets\oop_student_questionnaire_responses.csv'

conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=== CHECKING STUDENTS S010 AND S011 IN DB ===")
for row in c.execute("SELECT student_id, question_id, student_answer FROM student_answers WHERE student_id IN ('S010', 'S011') ORDER BY student_id, question_id").fetchall():
    print(f"[{row[0]}] {row[1]}: {row[2][:60]}...")

print("\n=== CHECKING CSV FOR ROWS 10 AND 11 ===")
print("\n=== CHECKING FEEDBACK TABLE FOR METADATA LABELS ===")
meta_rows = c.execute("SELECT student_answer_id, missing_concepts FROM feedback WHERE missing_concepts LIKE '%None clearly identified%' OR missing_concepts LIKE '%requires human review%'").fetchall()
print(f"Feedback rows with metadata labels: {len(meta_rows)}")
for r in meta_rows[:5]:
    print(f"  ans_id {r[0]}: {r[1]}")


print("\n=== UPDATING S039 NAME IF NEEDED ===")
c.execute("UPDATE students SET student_name = 'Student S039' WHERE student_id = 'S039'")
conn.commit()
print("S039 updated to neutral name 'Student S039'.")


print("\n=== COMPREHENSIVE CSV VS DB CHECK ===")
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = list(csv.DictReader(f))

cols = [
    ('Q1', '01. What is the difference between a class and an object in Java? Give a simple example. '),
    ('Q2', '02. If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?  '),
    ('Q3', '03. What happens when a child class overrides a method inherited from its parent class?  '),
    ('Q4', '04. Can a static method directly access a non-static variable? Why or why not?  '),
    ('Q5', '05. Why is exception handling important in Java? ')
]

mismatches = []
for idx, row in enumerate(reader, start=1):
    sid = f'S{idx:03d}'
    for qid, col in cols:
        csv_ans = (row.get(col) or '').strip()
        db_row = c.execute('SELECT student_answer FROM student_answers WHERE student_id = ? AND question_id = ?', (sid, qid)).fetchone()
        db_ans = db_row[0].strip() if db_row else None
        if csv_ans != db_ans:
            mismatches.append((sid, qid, csv_ans, db_ans))

print(f"Total mismatches: {len(mismatches)}")
for sid, qid, csv_ans, db_ans in mismatches:
    print(f"\nMismatch in {sid} {qid}:")
    print(f"  CSV: {csv_ans[:80]}")
    print(f"  DB:  {db_ans[:80] if db_ans else 'None'}")

print("\n=== S029 IN DB (Q4 AND Q5) ===")
for r in c.execute("SELECT question_id, student_answer, id FROM student_answers WHERE student_id = 'S029' ORDER BY question_id").fetchall():
    print(f"  {r[0]} (id={r[2]}): {r[1]}")
    fb = c.execute("SELECT missing_concepts, personalized_feedback FROM feedback WHERE student_answer_id = ?", (r[2],)).fetchone()
    if fb:
        print(f"    missing_concepts: {fb[0]}")
        print(f"    feedback preview: {fb[1][:80]}...")

print("\n=== FIXING S017 Q1 IN BACKEND DB TO RESTORE ORIGINAL CSV ANSWER ===")
# CSV Q1 for S017:
s17_q1_csv = reader[16][cols[0][1]].strip()
print(f"Original CSV Q1 text: {s17_q1_csv}")
c.execute("UPDATE student_answers SET student_answer = ? WHERE student_id = 'S017' AND question_id = 'Q1'", (s17_q1_csv,))
conn.commit()

# Also update root DB if it exists so both stay in perfect sync
if os.path.exists(root_db_path):
    conn_root = sqlite3.connect(root_db_path)
    c_root = conn_root.cursor()
    c_root.execute("UPDATE student_answers SET student_answer = ? WHERE student_id = 'S017' AND question_id = 'Q1'", (s17_q1_csv,))
    conn_root.commit()
    conn_root.close()

print("\n=== SYNCING S017 Q1 FEEDBACK IN BACKEND DB ===")
if os.path.exists(root_db_path):
    conn_root = sqlite3.connect(root_db_path)
    c_root = conn_root.cursor()
    fb_root = c_root.execute("SELECT strengths, weaknesses, missing_concepts, correctly_identified_concepts, mark_deduction_reason, improvement_suggestions, personalized_feedback FROM feedback WHERE student_answer_id = 81").fetchone()
    if fb_root:
        c.execute("""
            UPDATE feedback
            SET strengths = ?, weaknesses = ?, missing_concepts = ?, correctly_identified_concepts = ?,
                mark_deduction_reason = ?, improvement_suggestions = ?, personalized_feedback = ?
            WHERE student_answer_id = 81
        """, fb_root)
        
        # Also sync learning recommendations for ans_id 81
        fb_id_backend = c.execute("SELECT id FROM feedback WHERE student_answer_id = 81").fetchone()[0]
        fb_id_root = c_root.execute("SELECT id FROM feedback WHERE student_answer_id = 81").fetchone()[0]
        c.execute("DELETE FROM learning_recommendations WHERE feedback_id = ?", (fb_id_backend,))
        
        recs_root = c_root.execute("""
            SELECT concept_name, resource_title, resource_type, resource_url, priority_level, lecture_number, verified_page, reason, practice_activity, download_url
            FROM learning_recommendations WHERE feedback_id = ?
        """, (fb_id_root,)).fetchall()
        
        for rec in recs_root:
            c.execute("""
                INSERT INTO learning_recommendations
                (feedback_id, concept_name, resource_title, resource_type, resource_url, priority_level, lecture_number, verified_page, reason, practice_activity, download_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fb_id_backend, *rec))
            
        conn.commit()
        print("S017 Q1 feedback and recommendations synced successfully.")
    conn_root.close()

