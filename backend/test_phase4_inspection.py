import os
import joblib
import csv
from sentence_transformers import SentenceTransformer

# Load model
model_path = os.path.join(os.path.dirname(__file__), "ml_models", "rubrimark_oop_model.joblib")
m = joblib.load(model_path)
st = SentenceTransformer(m["embedding_model"])
classes = m["label_classes"]
clfs = m["classifiers"]
threshold = m.get("threshold", 0.5)

csv_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "oop_student_questionnaire_responses.csv")
with open(csv_path, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

questions = [
    ("Q1", "01. What is the difference between a class and an object in Java? Give a simple example. "),
    ("Q2", "02. If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?  "),
    ("Q3", "03. What happens when a child class overrides a method inherited from its parent class?  "),
    ("Q4", "04. Can a static method directly access a non-static variable? Why or why not?  "),
    ("Q5", "05. Why is exception handling important in Java? ")
]

test_sids = ["S001", "S004", "S010", "S011", "S014"]

print("=" * 80)
print("PHASE 4: RAW MODEL INFERENCE INSPECTION")
print("=" * 80)

for sid in test_sids:
    idx = int(sid[1:]) - 1
    row = rows[idx]
    print(f"\n=================== STUDENT {sid} ===================")
    for qid, qcol in questions:
        ans = (row.get(qcol) or "").strip()
        print(f"\n[{sid}] {qid}: '{ans}'")
        emb = st.encode([ans])
        probs = {}
        active = []
        for c_name, clf in zip(classes, clfs):
            p = float(clf.predict_proba(emb)[0][1])
            probs[c_name] = round(p, 4)
            if p >= threshold:
                active.append((c_name, round(p, 4)))
        print(f"  Active (>= {threshold}): {active}")
        # Top 3 probabilities:
        top_sorted = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"  Top probabilities: {top_sorted}")
