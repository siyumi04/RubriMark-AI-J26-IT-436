"""
Task B – AI Model Evaluation Script
RubriMark OOP Model – Formal Evaluation without retraining.

Key questions answered:
1. Does a genuine held-out test set exist?
2. What are training/test leakage risks?
3. What are real multi-label metrics on the available labeled data?
4. What are the per-concept metrics?
"""
import os
import csv
import json
import joblib
import numpy as np
from sklearn.metrics import (
    precision_recall_fscore_support,
    classification_report,
    accuracy_score
)
from sentence_transformers import SentenceTransformer

print("=" * 70)
print("TASK B – AI MODEL FORMAL EVALUATION")
print("=" * 70)

# ──────────────────────────────────────────────────────────────────────────
# 1. Inspect model artifact
# ──────────────────────────────────────────────────────────────────────────
print("\n[1] MODEL ARTIFACT INSPECTION")
model_path = os.path.join(os.path.dirname(__file__), "ml_models", "rubrimark_oop_model.joblib")
print(f"    Path: {model_path}")
print(f"    File size: {os.path.getsize(model_path):,} bytes")

m = joblib.load(model_path)
classes = m["label_classes"]
classifiers = m["classifiers"]
threshold = float(m.get("threshold", 0.5))
embedding_model = m["embedding_model"]
label_status = m.get("label_status", "Unknown")

print(f"    Embedding model: {embedding_model}")
print(f"    Threshold: {threshold}")
print(f"    Label status: {label_status}")
print(f"    Total label classes ({len(classes)}): {classes}")
print(f"    Number of binary classifiers: {len(classifiers)}")

METADATA_LABELS = {"None clearly identified", "requires human review"}
substantive_classes = [c for c in classes if c not in METADATA_LABELS]
print(f"    Metadata labels (excluded from edu eval): {list(METADATA_LABELS)}")
print(f"    Substantive educational concepts ({len(substantive_classes)}): {substantive_classes}")

# Inspect each classifier
print("\n    Per-Classifier Summary:")
for c_name, clf in zip(classes, classifiers):
    clf_type = type(clf).__name__
    # Get training data size if available
    n_support = "?"
    if hasattr(clf, 'n_iter_'):
        n_iter = clf.n_iter_[0] if hasattr(clf.n_iter_, '__len__') else clf.n_iter_
    else:
        n_iter = "?"
    print(f"      [{clf_type}] '{c_name}'  n_iter={n_iter}")

# ──────────────────────────────────────────────────────────────────────────
# 2. Dataset Analysis
# ──────────────────────────────────────────────────────────────────────────
print("\n[2] DATASET ANALYSIS")
datasets_dir = os.path.join(os.path.dirname(__file__), "..", "datasets")

# Load both CSV files
quest_path = os.path.join(datasets_dir, "oop_student_questionnaire_responses.csv")
exp_path = os.path.join(datasets_dir, "oop_model_experimental_results.csv")

with open(quest_path, "r", encoding="utf-8") as f:
    quest_rows = list(csv.DictReader(f))

with open(exp_path, "r", encoding="utf-8") as f:
    exp_rows = list(csv.DictReader(f))

print(f"    Questionnaire CSV: {len(quest_rows)} rows (63 lines – 1 header = 62 students)")
print(f"    Experimental Results CSV: {len(exp_rows)} rows (50 samples, 10 students × 5 questions)")

# Students in experimental results
exp_student_ids = sorted(set(r["student_id"] for r in exp_rows))
exp_q_ids = sorted(set(r["question_id"] for r in exp_rows))
print(f"\n    Experimental results: {len(exp_student_ids)} unique students: {exp_student_ids}")
print(f"    Questions covered: {exp_q_ids}")

# Check for duplicate answers (leakage indicator)
print("\n[3] TRAINING / TEST LEAKAGE ANALYSIS")
print("    NOTE: No training script exists in this repository.")
print("    The model was trained externally (e.g., Google Colab) and saved as a .joblib file.")
print("    We cannot inspect what data was used during training.")

# Check overlap between questionnaire answers and experimental results
quest_answers = set()
for r in quest_rows:
    for col in [
        "01. What is the difference between a class and an object in Java? Give a simple example. ",
        "02. If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?  ",
        "03. What happens when a child class overrides a method inherited from its parent class?  ",
        "04. Can a static method directly access a non-static variable? Why or why not?  ",
        "05. Why is exception handling important in Java? "
    ]:
        ans = (r.get(col) or "").strip()
        if ans:
            quest_answers.add(ans)

exp_answers = set(r["student_answer"].strip() for r in exp_rows)
overlap = exp_answers & quest_answers
print(f"\n    Questionnaire unique answers: {len(quest_answers)}")
print(f"    Experimental results unique answers: {len(exp_answers)}")
print(f"    Overlap (exp answers found in questionnaire): {len(overlap)}")
if overlap:
    print("    LEAKAGE RISK: Experimental set samples appear in the questionnaire dataset.")
    print("    This means the experimental results CSV is a *subset* of the questionnaire CSV.")
    print("    These are NOT independent held-out test samples.")
else:
    print("    No textual overlap detected between experimental and questionnaire answers.")

# Check for duplicate answers within experimental results
exp_ans_list = [r["student_answer"].strip() for r in exp_rows]
duplicates = [a for a in set(exp_ans_list) if exp_ans_list.count(a) > 1]
print(f"\n    Duplicate answers within experimental results: {len(duplicates)}")
if duplicates:
    for d in duplicates:
        print(f"      DUPLICATE: '{d[:80]}'")

# ──────────────────────────────────────────────────────────────────────────
# 4. Label Quality Analysis
# ──────────────────────────────────────────────────────────────────────────
print("\n[4] LABEL QUALITY ANALYSIS")
print("    Column: provisional_reference_labels")
print("    Status: PROVISIONAL – not independently verified ground-truth")

label_issues = []
all_ref_label_sets = []
for r in exp_rows:
    ref_str = (r.get("provisional_reference_labels") or "").strip()
    ref_labels = [c.strip() for c in ref_str.replace(";", ",").split(",") if c.strip()]
    all_ref_label_sets.append(set(ref_labels))
    
    # Check if label is entirely metadata
    non_meta = [l for l in ref_labels if l not in METADATA_LABELS]
    only_meta = len(ref_labels) > 0 and len(non_meta) == 0
    if only_meta:
        label_issues.append(f"{r['student_id']}/{r['question_id']}: only metadata labels → 'None clearly identified' / 'requires human review'")

print(f"\n    Rows with ONLY metadata labels (unusable for substantive concept eval): {len(label_issues)}")
for li in label_issues[:8]:
    print(f"      {li}")
if len(label_issues) > 8:
    print(f"      ... and {len(label_issues)-8} more")

# Count rows with substantive reference labels
rows_with_substantive = sum(
    1 for s in all_ref_label_sets
    if any(l not in METADATA_LABELS for l in s)
)
print(f"\n    Rows with at least 1 substantive reference label: {rows_with_substantive} / {len(exp_rows)}")
print(f"    Rows only metadata (meaningless for edu concept eval): {len(exp_rows) - rows_with_substantive} / {len(exp_rows)}")

# ──────────────────────────────────────────────────────────────────────────
# 5. Model Evaluation
# ──────────────────────────────────────────────────────────────────────────
print("\n[5] MODEL EVALUATION")
print("    Dataset used: oop_model_experimental_results.csv")
print("    Reference labels: 'provisional_reference_labels' column")
print("    CAUTION: These labels overlap with questionnaire data (likely training data).")
print("    Evaluation is NOT on an independent held-out test set.\n")

# Load SentenceTransformer
print("    Loading SentenceTransformer...")
st = SentenceTransformer(embedding_model)

y_true_all = []
y_pred_all = []
row_details = []

for row in exp_rows:
    ans = row["student_answer"].strip()
    ref_str = (row.get("provisional_reference_labels") or "").strip()
    ref_labels = set(c.strip() for c in ref_str.replace(";", ",").split(",") if c.strip())

    emb = st.encode([ans])
    pred_labels = set()
    pred_probs = {}
    for c_name, clf in zip(classes, classifiers):
        p = float(clf.predict_proba(emb)[0][1])
        pred_probs[c_name] = round(p, 4)
        if p >= threshold:
            pred_labels.add(c_name)

    y_t = [1 if c in ref_labels else 0 for c in classes]
    y_p = [1 if c in pred_labels else 0 for c in classes]
    y_true_all.append(y_t)
    y_pred_all.append(y_p)

    row_details.append({
        "sid": row["student_id"],
        "qid": row["question_id"],
        "ref_labels": ref_labels,
        "pred_labels": pred_labels,
        "exact_match": ref_labels == pred_labels
    })

y_true = np.array(y_true_all)
y_pred = np.array(y_pred_all)

# Overall 15-class metrics
print("  [5a] FULL 15-CLASS METRICS (including metadata labels)")
p_micro, r_micro, f1_micro, _ = precision_recall_fscore_support(y_true, y_pred, average="micro", zero_division=0)
p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
exact_match = sum(1 for d in row_details if d["exact_match"]) / len(row_details)
print(f"    Total samples: {len(exp_rows)}")
print(f"    Exact Match Accuracy (all 15 classes): {exact_match:.4f} ({exact_match*100:.1f}%)")
print(f"    Micro  → P={p_micro:.4f}  R={r_micro:.4f}  F1={f1_micro:.4f}")
print(f"    Macro  → P={p_macro:.4f}  R={r_macro:.4f}  F1={f1_macro:.4f}")

# Substantive 13-concept metrics
sub_idx = [classes.index(c) for c in substantive_classes]
y_true_sub = y_true[:, sub_idx]
y_pred_sub = y_pred[:, sub_idx]
rows_sub_useful = [i for i, s in enumerate(all_ref_label_sets)
                   if any(l not in METADATA_LABELS for l in s)]

print(f"\n  [5b] SUBSTANTIVE {len(substantive_classes)}-CONCEPT METRICS (metadata labels excluded)")
print(f"       (All {len(exp_rows)} rows evaluated; {len(exp_rows)-rows_with_substantive} rows have only-metadata reference = treated as all-zero for substantive)")
p_sub_micro, r_sub_micro, f1_sub_micro, _ = precision_recall_fscore_support(y_true_sub, y_pred_sub, average="micro", zero_division=0)
p_sub_macro, r_sub_macro, f1_sub_macro, _ = precision_recall_fscore_support(y_true_sub, y_pred_sub, average="macro", zero_division=0)

# Exact match for substantive only
exact_sub = []
for i in range(len(exp_rows)):
    ref_sub = set(c for c in row_details[i]["ref_labels"] if c not in METADATA_LABELS)
    pred_sub = set(c for c in row_details[i]["pred_labels"] if c not in METADATA_LABELS)
    exact_sub.append(ref_sub == pred_sub)
exact_sub_acc = sum(exact_sub) / len(exact_sub)

print(f"    Exact Match Accuracy (substantive): {exact_sub_acc:.4f} ({exact_sub_acc*100:.1f}%)")
print(f"    Micro  → P={p_sub_micro:.4f}  R={r_sub_micro:.4f}  F1={f1_sub_micro:.4f}")
print(f"    Macro  → P={p_sub_macro:.4f}  R={r_sub_macro:.4f}  F1={f1_sub_macro:.4f}")

# Per-concept metrics
print(f"\n  [5c] PER-CONCEPT METRICS (all {len(classes)} classes)")
print(f"    {'Concept':<55} {'Type':<12} P      R      F1     Support")
print(f"    {'-'*55} {'-'*12} {'-----'} {'-----'} {'-----'} {'-'*7}")
per_concept_results = []
for idx, c in enumerate(classes):
    p, r, f1, _ = precision_recall_fscore_support(
        y_true[:, idx], y_pred[:, idx], average="binary", zero_division=0
    )
    sup = int(np.sum(y_true[:, idx]))
    ctype = "METADATA" if c in METADATA_LABELS else "edu-concept"
    per_concept_results.append({
        "concept": c, "type": ctype,
        "precision": round(float(p), 4), "recall": round(float(r), 4),
        "f1": round(float(f1), 4), "support": sup
    })
    print(f"    {c:<55} {ctype:<12} {p:.3f}  {r:.3f}  {f1:.3f}  {sup}")

# ──────────────────────────────────────────────────────────────────────────
# 6. Independence assessment
# ──────────────────────────────────────────────────────────────────────────
print("\n[6] DATA INDEPENDENCE ASSESSMENT")
print(f"    Overlap between experimental answers and questionnaire: {len(overlap)} of {len(exp_answers)} answers")
if len(overlap) == len(exp_answers):
    print("    FINDING: ALL experimental answers are a strict subset of the questionnaire CSV.")
    print("    The model was likely trained on the questionnaire CSV (or a superset of it).")
    print("    Therefore these metrics are POTENTIALLY IN-SAMPLE (training data re-evaluation),")
    print("    NOT a genuine held-out test evaluation.")
elif len(overlap) > 0:
    print(f"    FINDING: {len(overlap)} of {len(exp_answers)} experimental answers overlap with questionnaire data.")
    print("    Partial leakage risk – some samples may be in-sample.")
else:
    print("    FINDING: No textual overlap detected – experimental set appears independent.")

# ──────────────────────────────────────────────────────────────────────────
# 7. Build JSON summary
# ──────────────────────────────────────────────────────────────────────────
evaluation_summary = {
    "evaluation_status": "COMPLETED_WITH_LIMITATIONS",
    "independent_test_set_exists": False,
    "reason": "Experimental results CSV is a subset of questionnaire CSV (likely training data). No genuine held-out test set found in repository.",
    "model_artifact": {
        "path": model_path,
        "size_bytes": os.path.getsize(model_path),
        "embedding_model": embedding_model,
        "threshold": threshold,
        "num_classifiers": len(classifiers),
        "label_classes": classes,
        "label_status": label_status,
        "training_script_found": False,
    },
    "dataset": {
        "questionnaire_rows": len(quest_rows),
        "experimental_rows": len(exp_rows),
        "experimental_unique_students": exp_student_ids,
        "overlap_answers_count": len(overlap),
        "overlap_is_full_subset": len(overlap) == len(exp_answers),
        "rows_with_substantive_labels": rows_with_substantive,
        "rows_only_metadata_labels": len(exp_rows) - rows_with_substantive,
        "duplicate_answers": len(duplicates),
    },
    "metrics_15_class": {
        "note": "Evaluated against provisional_reference_labels; likely in-sample data",
        "num_samples": len(exp_rows),
        "exact_match_accuracy": round(exact_match, 4),
        "micro_precision": round(float(p_micro), 4),
        "micro_recall": round(float(r_micro), 4),
        "micro_f1": round(float(f1_micro), 4),
        "macro_precision": round(float(p_macro), 4),
        "macro_recall": round(float(r_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
    },
    "metrics_substantive_13_concept": {
        "note": "Educational concepts only – metadata labels excluded",
        "num_samples": len(exp_rows),
        "exact_match_accuracy": round(exact_sub_acc, 4),
        "micro_precision": round(float(p_sub_micro), 4),
        "micro_recall": round(float(r_sub_micro), 4),
        "micro_f1": round(float(f1_sub_micro), 4),
        "macro_precision": round(float(p_sub_macro), 4),
        "macro_recall": round(float(r_sub_macro), 4),
        "macro_f1": round(float(f1_sub_macro), 4),
    },
    "per_concept_metrics": per_concept_results,
    "limitations": [
        "No training script available in repository – training data unknown.",
        "Experimental results CSV overlaps with questionnaire CSV (all 50 answers found in questionnaire).",
        "provisional_reference_labels column contains many only-metadata rows (unusable for substantive concept evaluation).",
        "Labels marked as 'provisional' – not independently verified ground-truth.",
        "Model was trained externally (Google Colab) – training/validation split details unknown.",
        "Without a genuine independent test set, published metrics reflect possible in-sample performance.",
    ],
    "reproducible_evaluation_plan": [
        "1. Collect ≥30 NEW student answers not in questionnaire CSV, answered post-model-training.",
        "2. Have a domain expert (OOP instructor) annotate each answer with substantive concept labels (Q1-Q5 expected concepts only).",
        "3. Exclude 'None clearly identified' and 'requires human review' from evaluation labels.",
        "4. Run eval_metrics.py (or equivalent) against only the NEW independent labeled set.",
        "5. Report exact-match accuracy, micro/macro P/R/F1, and per-concept metrics.",
        "6. Include inter-annotator agreement (Cohen's Kappa) to validate label reliability.",
    ]
}

# Save JSON
out_path = os.path.join(os.path.dirname(__file__), "task_b_evaluation_result.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(evaluation_summary, f, indent=2)
print(f"\n    Evaluation summary saved: {out_path}")

print("\n" + "=" * 70)
print("TASK B COMPLETE")
print("=" * 70)
