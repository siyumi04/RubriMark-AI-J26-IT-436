import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def get_json(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def post_json(endpoint, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

TEST_STUDENTS = ["S010", "S011", "S001", "S004", "S014"]

print("=" * 80)
print("PHASE 4: FIVE REAL STUDENTS TESTING & EVALUATION")
print("=" * 80)

summary_results = []

for sid in TEST_STUDENTS:
    print(f"\n######################################################################")
    print(f"STUDENT: {sid}")
    print(f"######################################################################")
    
    answers = get_json(f"/api/students/{sid}/answers")
    feedback_list = get_json(f"/api/students/{sid}/feedback")
    dash = get_json(f"/api/students/{sid}/dashboard")
    
    print(f"Student: {dash.get('student_name')} ({dash.get('student_id')})")
    print(f"Total Answers: {len(answers)}")
    print(f"Total Identified Concepts: {dash['summary']['concepts_identified']}")
    print(f"Total Missing Concepts: {dash['summary']['missing_concepts']}")
    print(f"Root Knowledge Gaps: {dash['summary']['root_knowledge_gaps']}")
    
    for ans in answers:
        qid = ans["question_id"]
        q_text = ans["question"]["question_text"] if ans.get("question") else ""
        s_ans = ans["student_answer"]
        fb = ans.get("feedback")
        
        # Test direct prediction via analyze-answer as well
        direct_eval = post_json("/api/analyze-answer", {
            "student_id": sid,
            "question_id": qid,
            "student_answer": s_ans,
            "save_to_db": False
        })
        
        print(f"\n--------------------------------------------------")
        print(f"[{sid}] Question {qid}:")
        print(f"  Prompt: '{q_text}'")
        print(f"  Student Answer: '{s_ans}'")
        print(f"  Expected Concepts:")
        for ec in direct_eval.get("expected_concepts", []):
            print(f"    * {ec}")
        print(f"  Model-Detected Concepts (Raw AI Model):")
        for dc in direct_eval.get("missing_concepts", []):
            print(f"    * {dc}")
        print(f"  Expected-But-Undetected Concepts:")
        for euc in direct_eval.get("expected_undetected_concepts", []):
            print(f"    * {euc}")
        print(f"  Correctly Demonstrated Concepts:")
        for cc in direct_eval.get("correctly_identified_concepts", []):
            print(f"    * {cc}")
            
        unrelated = direct_eval.get("unrelated_cross_question_concepts", [])
        if unrelated:
            print(f"  Unrelated Cross-Question Concepts (Safely Filtered): {unrelated}")
            
        print(f"  Confidence / Uncertainty Info:")
        print(f"    - Requires Human Review: {direct_eval.get('requires_human_review')}")
        print(f"    - Uncertainty Details: {direct_eval.get('uncertainty_info')}")
        print(f"    - AI Status: {direct_eval.get('ai_status')}")
        
        print(f"  Generated Feedback Relevance:")
        print(f"    Strengths: {direct_eval.get('strengths')[:120]}...")
        print(f"    Weaknesses: {direct_eval.get('weaknesses')[:120]}...")
        print(f"    Marks Status: {direct_eval.get('mark_deduction_reason')}")
        print(f"    Actionable Steps: {direct_eval.get('improvement_suggestions')[:120]}...")
        
        # Metadata check
        for m in ["None clearly identified", "requires human review"]:
            assert m not in direct_eval.get("missing_concepts", []), f"Metadata label '{m}' leaked in missing_concepts!"
            assert m not in direct_eval.get("correctly_identified_concepts", []), f"Metadata label '{m}' leaked in correctly_identified!"

print("\n" + "=" * 80)
print("ALL 5 STUDENTS TESTED SUCCESSFULLY WITH ZERO METADATA LEAKS")
print("=" * 80)
