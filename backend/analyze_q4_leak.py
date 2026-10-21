import os
import joblib
import csv
from sentence_transformers import SentenceTransformer

model_path = os.path.join(os.path.dirname(__file__), "ml_models", "rubrimark_oop_model.joblib")
m = joblib.load(model_path)
st = SentenceTransformer(m["embedding_model"])
classes = m["label_classes"]
clfs = m["classifiers"]
idx_eh = classes.index("Handles runtime exceptions/errors")
clf_eh = clfs[idx_eh]

csv_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "oop_student_questionnaire_responses.csv")
with open(csv_path, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

q4_col = "04. Can a static method directly access a non-static variable? Why or why not?  "

q4_eh_flags = []
for idx, r in enumerate(rows, start=1):
    sid = f"S{idx:03d}"
    ans = (r.get(q4_col) or "").strip()
    if not ans:
        continue
    emb = st.encode([ans])
    p_eh = float(clf_eh.predict_proba(emb)[0][1])
    if p_eh >= 0.5:
        q4_eh_flags.append((sid, p_eh, ans))

print(f"Total students with Q4 answers: {len(rows)}")
print(f"Number of Q4 answers where 'Handles runtime exceptions/errors' >= 0.5: {len(q4_eh_flags)}")
print("\nSamples flagged:")
for sid, p, ans in q4_eh_flags[:10]:
    print(f"  {sid} (prob={p:.4f}): '{ans[:70]}...'")
