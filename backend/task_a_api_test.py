"""
Task A – Live API Integration Test
Tests all major endpoints against the running FastAPI server (port 8000).
"""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
results = []

def req(method, endpoint, body=None):
    url = f"{BASE}{endpoint}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    req_obj = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req_obj, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.reason}
    except Exception as e:
        return None, {"error": str(e)}

def check(label, status, data, expect_status=200, key_check=None):
    ok = status == expect_status
    key_ok = True
    if key_check and ok:
        for k in key_check:
            if k not in data:
                key_ok = False
    passed = ok and key_ok
    tag = "PASS" if passed else "FAIL"
    results.append((tag, label, status, expect_status))
    detail = ""
    if key_check and not key_ok:
        detail = f" [missing keys: {key_check}]"
    print(f"  [{tag}] {label} -> HTTP {status} (expected {expect_status}){detail}")
    return passed, data

print("=" * 70)
print("TASK A – LIVE API INTEGRATION TEST")
print(f"Target: {BASE}")
print("=" * 70)

# ── 1. Health ─────────────────────────────────────────────────────────────
print("\n[1] Health Check")
status, data = req("GET", "/api/health")
passed, _ = check("GET /api/health", status, data, 200, ["status", "model_loaded", "database"])
if passed:
    print(f"      status={data['status']}  model_loaded={data['model_loaded']}  db={data['database']}")
    print(f"      model_status: {data.get('model_status','')[:80]}")

# ── 2. Model Status ────────────────────────────────────────────────────────
print("\n[2] Model Status")
status, data = req("GET", "/api/model-status")
passed, _ = check("GET /api/model-status", status, data, 200, ["model_loaded", "model_metadata"])
if passed:
    meta = data.get("model_metadata", {})
    print(f"      loaded={data['model_loaded']}  classifiers={meta.get('num_classifiers')}  classes={meta.get('num_classes')}")
    print(f"      embedding={meta.get('embedding_model')}  threshold={meta.get('threshold')}")

# ── 3. Students list ───────────────────────────────────────────────────────
print("\n[3] Students")
status, data = req("GET", "/api/students")
check("GET /api/students", status, data, 200)
if status == 200 and isinstance(data, list):
    print(f"      {len(data)} students found: {[s['student_id'] for s in data[:8]]}")
    student_ids = [s["student_id"] for s in data]
else:
    student_ids = ["S001", "S004", "S010", "S011", "S014"]

# ── 4. Questions ───────────────────────────────────────────────────────────
print("\n[4] Questions")
status, data = req("GET", "/api/questions")
check("GET /api/questions", status, data, 200)
if status == 200:
    print(f"      {len(data)} questions: {[q['question_id'] for q in data]}")

# ── 5. Per-student endpoints (5 students) ─────────────────────────────────
TEST_STUDENTS = ["S001", "S004", "S010", "S011", "S014"]
print(f"\n[5] Per-Student Endpoints ({len(TEST_STUDENTS)} students)")

for sid in TEST_STUDENTS:
    print(f"\n  ── Student {sid} ──")

    # GET /api/students/{id}
    status, data = req("GET", f"/api/students/{sid}")
    passed, _ = check(f"GET /students/{sid}", status, data, 200, ["student_id", "student_name"])
    if passed:
        print(f"      Name: {data.get('student_name')}  Answers: {data.get('answers_count')}")

    # GET /api/students/{id}/answers
    status, ans_data = req("GET", f"/api/students/{sid}/answers")
    passed, _ = check(f"GET /students/{sid}/answers", status, ans_data, 200)
    if passed and isinstance(ans_data, list):
        print(f"      Answers: {len(ans_data)}", end="")
        for a in ans_data[:2]:
            qid = a.get("question_id", "?")
            snippet = (a.get("student_answer", "") or "")[:50]
            print(f"\n        Q{qid}: '{snippet}...'", end="")
        print()
        # Verify student_id, question_id, answer are present
        for a in ans_data:
            assert a.get("student_id") == sid, f"Wrong student_id in answer: {a.get('student_id')}"
            assert a.get("question_id"), "Missing question_id"
            assert a.get("student_answer"), "Missing student_answer"
        print(f"      ✓ student_id/question_id/answer fields verified for all {len(ans_data)} answers")

    # GET /api/students/{id}/feedback
    status, fb_data = req("GET", f"/api/students/{sid}/feedback")
    passed, _ = check(f"GET /students/{sid}/feedback", status, fb_data, 200)
    if passed and isinstance(fb_data, list):
        print(f"      Feedback entries: {len(fb_data)}")
        # Check no metadata labels leak
        for fb in fb_data:
            for concept_list in [fb.get("missing_concepts", []), fb.get("correctly_identified_concepts", [])]:
                for c in concept_list:
                    if c.strip().lower() in ["none clearly identified", "requires human review"]:
                        print(f"      [FAIL] Metadata label leaked: '{c}'")
        print(f"      ✓ No metadata label leaks in feedback")

    # GET /api/students/{id}/dashboard
    status, dash_data = req("GET", f"/api/students/{sid}/dashboard")
    passed, _ = check(f"GET /students/{sid}/dashboard", status, dash_data, 200, ["student_id", "summary"])
    if passed:
        s = dash_data.get("summary", {})
        print(f"      Dashboard: concepts_identified={s.get('concepts_identified')}  missing={s.get('missing_concepts')}  root_gaps={s.get('root_knowledge_gaps')}")

    # GET /api/students/{id}/concept-dependency
    status, dep_data = req("GET", f"/api/students/{sid}/concept-dependency")
    passed, _ = check(f"GET /students/{sid}/concept-dependency", status, dep_data, 200)
    if passed:
        root_causes = dep_data.get("root_causes", [])
        print(f"      Root causes: {[r.get('concept','?') for r in root_causes[:3]]}")

# ── 6. Analyze-answer (live AI inference) ─────────────────────────────────
print("\n[6] POST /api/analyze-answer – Live AI Inference")
test_cases = [
    ("S001", "Q1", "Class is a blueprint and Object is an instance of that class. Example: Car myCar = new Car();"),
    ("S004", "Q3", "The child class provides its own implementation. When the method is called on a child object, the child version runs."),
    ("S010", "Q2", "properties and actions that are common to all vehicles like number of wheels and drive action"),
    ("S011", "Q4", "No. Static methods belong to the class, while non-static variables belong to objects. You need an object instance."),
    ("S014", "Q5", "Prevent sudden crashes, Maintain Normal program flow"),
]
for sid, qid, ans in test_cases:
    body = {"student_id": sid, "question_id": qid, "student_answer": ans, "save_to_db": False}
    status, resp = req("POST", "/api/analyze-answer", body)
    passed, _ = check(f"POST /analyze-answer [{sid}/{qid}]", status, resp, 200,
                      ["student_id", "question_id", "missing_concepts", "strengths", "weaknesses"])
    if passed:
        # Verify student_id, question_id, answer echoed back correctly
        assert resp.get("student_id") == sid, f"student_id mismatch: {resp.get('student_id')} != {sid}"
        assert resp.get("question_id") == qid, f"question_id mismatch: {resp.get('question_id')} != {qid}"
        assert resp.get("student_answer") == ans, "student_answer mismatch"
        # Check no metadata labels in missing_concepts
        for c in resp.get("missing_concepts", []):
            if c.lower() in ["none clearly identified", "requires human review"]:
                print(f"      [FAIL] metadata label in missing_concepts: '{c}'")
        ai_status = resp.get("ai_status", "?")
        review = resp.get("requires_human_review", False)
        expected = resp.get("expected_concepts", [])
        identified = resp.get("correctly_identified_concepts", [])
        missing = resp.get("missing_concepts", [])
        print(f"      {sid}/{qid}: ai_status={ai_status}  review={review}")
        print(f"        Expected: {expected}")
        print(f"        Identified: {identified}  Missing: {missing}")

# ── 7. Summary ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
passed_n = sum(1 for r in results if r[0] == "PASS")
failed_n = sum(1 for r in results if r[0] == "FAIL")
print(f"TASK A SUMMARY: {passed_n} PASSED / {failed_n} FAILED / {len(results)} TOTAL")
print("=" * 70)
for tag, label, status, exp in results:
    sym = "[OK]" if tag == "PASS" else "[XX]"
    print(f"  {sym} [{tag}] {label} -> HTTP {status}")
