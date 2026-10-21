import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"

tests = [
    ("GET /api/health", "/api/health", "GET", None),
    ("GET /api/model-status", "/api/model-status", "GET", None),
    ("GET /api/students", "/api/students", "GET", None),
    ("GET /api/questions", "/api/questions", "GET", None),
    ("GET /api/concept-dependencies", "/api/concept-dependencies", "GET", None),
    ("GET /api/students/S001/concept-dependencies", "/api/students/S001/concept-dependencies", "GET", None),
    ("GET /api/students/S004/concept-dependencies", "/api/students/S004/concept-dependencies", "GET", None),
    ("GET /api/students/S010/concept-dependencies", "/api/students/S010/concept-dependencies", "GET", None),
    ("GET /api/students/S011/concept-dependencies", "/api/students/S011/concept-dependencies", "GET", None),
    ("GET /api/students/S014/concept-dependencies", "/api/students/S014/concept-dependencies", "GET", None),
    ("GET /api/students/S001/dashboard", "/api/students/S001/dashboard", "GET", None),
    ("GET /api/students/S004/dashboard", "/api/students/S004/dashboard", "GET", None),
    ("GET /api/students/S010/dashboard", "/api/students/S010/dashboard", "GET", None),
    ("GET /api/students/S011/dashboard", "/api/students/S011/dashboard", "GET", None),
    ("GET /api/students/S014/dashboard", "/api/students/S014/dashboard", "GET", None),
    ("POST /api/analyze-answer S001/Q1", "/api/analyze-answer", "POST",
     {"student_id": "S001", "question_id": "Q1",
      "student_answer": "Class is a blueprint and Object is an instance of that class. Example: Car myCar = new Car();",
      "save_to_db": False}),
    ("POST /api/analyze-answer S010/Q4", "/api/analyze-answer", "POST",
     {"student_id": "S010", "question_id": "Q4",
      "student_answer": "i cant remember",
      "save_to_db": False}),
    ("POST /api/analyze-answer S014/Q5", "/api/analyze-answer", "POST",
     {"student_id": "S014", "question_id": "Q5",
      "student_answer": "Prevent sudden crashes, Maintain Normal program flow",
      "save_to_db": False}),
]

results = []
print("=" * 60)
print("TASK A - CORRECTED LIVE API INTEGRATION TEST")
print("=" * 60)

for label, ep, method, body in tests:
    url = f"{BASE}{ep}"
    data = json.dumps(body).encode() if body else None
    hdrs = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            status = r.status
            resp = json.loads(r.read())
        tag = "PASS"
    except urllib.error.HTTPError as e:
        status = e.code
        resp = {}
        tag = "FAIL"
    except Exception as ex:
        status = str(ex)
        resp = {}
        tag = "FAIL"

    results.append((tag, label, status))
    extra = ""
    if tag == "PASS" and "/health" in ep:
        extra = f" model_loaded={resp.get('model_loaded')} db={resp.get('database')}"
    elif tag == "PASS" and "/dashboard" in ep:
        s = resp.get("summary", {})
        extra = f" identified={s.get('concepts_identified')} missing={s.get('missing_concepts')} root_gaps={s.get('root_knowledge_gaps')}"
    elif tag == "PASS" and "/concept-dependencies" in ep and "students" in ep:
        root = resp.get("root_causes", [])
        extra = f" root_causes_count={len(root)}"
    elif tag == "PASS" and "analyze-answer" in ep:
        ai = resp.get("ai_status", "?")
        identified = resp.get("correctly_identified_concepts", [])
        missing = resp.get("missing_concepts", [])
        review = resp.get("requires_human_review", False)
        extra = f" ai_status={ai} review={review} identified={identified} missing={missing}"
    print(f"  [{tag}] {label} -> HTTP {status}{extra}")

print("\n" + "=" * 60)
passed = sum(1 for r in results if r[0] == "PASS")
failed = sum(1 for r in results if r[0] == "FAIL")
print(f"FINAL: {passed}/{len(results)} PASSED  {failed}/{len(results)} FAILED")
print("=" * 60)
