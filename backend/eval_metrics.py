import os
import csv
import joblib
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, classification_report
from sentence_transformers import SentenceTransformer

# Load model
model_path = os.path.join(os.path.dirname(__file__), "ml_models", "rubrimark_oop_model.joblib")
m = joblib.load(model_path)
st = SentenceTransformer(m["embedding_model"])
classes = m["label_classes"]
clfs = m["classifiers"]
threshold = m.get("threshold", 0.5)

csv_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "oop_model_experimental_results.csv")
with open(csv_path, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(f"Total experimental rows: {len(rows)}")

y_true = []
y_pred_model = []

substantive_classes = [c for c in classes if c not in ["None clearly identified", "requires human review"]]

for row in rows:
    ans = row["student_answer"].strip()
    ref_str = row.get("provisional_reference_labels", "").strip()
    ref_labels = set([c.strip() for c in ref_str.replace(";", ",").split(",") if c.strip()])
    
    # Model inference
    emb = st.encode([ans])
    pred_labels = set()
    for c_name, clf in zip(classes, clfs):
        p = float(clf.predict_proba(emb)[0][1])
        if p >= threshold:
            pred_labels.add(c_name)
            
    # Binary vectors over all 15 classes
    y_t = [1 if c in ref_labels else 0 for c in classes]
    y_p = [1 if c in pred_labels else 0 for c in classes]
    y_true.append(y_t)
    y_pred_model.append(y_p)

y_true = np.array(y_true)
y_pred_model = np.array(y_pred_model)

print("\n--- OVERALL 15-CLASS EVALUATION (Against Provisional Reference Labels) ---")
p_micro, r_micro, f1_micro, _ = precision_recall_fscore_support(y_true, y_pred_model, average="micro", zero_division=0)
p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred_model, average="macro", zero_division=0)
print(f"Micro-averaged: Precision = {p_micro:.4f}, Recall = {r_micro:.4f}, F1 = {f1_micro:.4f}")
print(f"Macro-averaged: Precision = {p_macro:.4f}, Recall = {r_macro:.4f}, F1 = {f1_macro:.4f}")

# Substantive concepts only (excluding metadata)
sub_indices = [classes.index(c) for c in substantive_classes]
y_true_sub = y_true[:, sub_indices]
y_pred_sub = y_pred_model[:, sub_indices]

p_sub_micro, r_sub_micro, f1_sub_micro, _ = precision_recall_fscore_support(y_true_sub, y_pred_sub, average="micro", zero_division=0)
p_sub_macro, r_sub_macro, f1_sub_macro, _ = precision_recall_fscore_support(y_true_sub, y_pred_sub, average="macro", zero_division=0)
print("\n--- SUBSTANTIVE 13-CONCEPT EVALUATION (Excluding Metadata Labels) ---")
print(f"Micro-averaged: Precision = {p_sub_micro:.4f}, Recall = {r_sub_micro:.4f}, F1 = {f1_sub_micro:.4f}")
print(f"Macro-averaged: Precision = {p_sub_macro:.4f}, Recall = {r_sub_macro:.4f}, F1 = {f1_sub_macro:.4f}")

print("\n--- PER-CLASS METRICS ---")
for idx, c in enumerate(classes):
    p, r, f1, sup = precision_recall_fscore_support(y_true[:, idx], y_pred_model[:, idx], average="binary", zero_division=0)
    print(f"  {c:55s}: P={p:.3f}, R={r:.3f}, F1={f1:.3f}, Support={int(np.sum(y_true[:, idx]))}")
