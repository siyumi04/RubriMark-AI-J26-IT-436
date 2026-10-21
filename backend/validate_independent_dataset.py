"""
Independent Dataset Validator for RubriMark AI.
Validates 'datasets/independent_eval_template.csv' against rubric criteria:
1. Required columns exist.
2. Question IDs are valid (Q1–Q5).
3. Concept labels strictly match the 13 saved educational concepts (or 'None').
4. Verified rows have non-empty student answers and non-empty human-reviewed labels.
5. Flags duplicate (student_id, question_id) entries.
6. Filters out empty, draft, or pending rows from active evaluation.
"""

import os
import csv
import sys
from typing import List, Set, Dict, Tuple

# Exact 13 educational concept labels aligned with the saved AI model
VALID_EDUCATIONAL_CONCEPTS: Set[str] = {
    "Child implementation executes on child object",
    "Child provides overriding implementation",
    "Class as blueprint/template",
    "Concrete class-object example",
    "Handles runtime exceptions/errors",
    "Inheritance of accessible fields",
    "Inheritance of accessible methods",
    "Instance reference required for access",
    "No direct instance-variable access from static method",
    "Object as class instance",
    "Prevents abrupt termination or supports graceful recovery",
    "Static belongs to class",
    "instance variable belongs to object"
}

VALID_QUESTION_IDS: Set[str] = {"Q1", "Q2", "Q3", "Q4", "Q5"}

REQUIRED_COLUMNS: List[str] = [
    "student_id",
    "question_id",
    "question_text",
    "student_answer",
    "human_verified_present_concepts",
    "human_verified_missing_concepts",
    "reviewer_name",
    "reviewer_role",
    "review_status",
    "notes"
]


def validate_concepts(raw_concept_str: str) -> List[str]:
    """Parses semicolon-delimited concept string and returns list of invalid concepts."""
    cleaned = raw_concept_str.strip()
    if not cleaned or cleaned.lower() == "none":
        return []
    
    concepts = [c.strip() for c in cleaned.split(";") if c.strip()]
    invalid = [c for c in concepts if c not in VALID_EDUCATIONAL_CONCEPTS]
    return invalid


def validate_csv(csv_path: str) -> bool:
    print("=" * 70)
    print(f"RUBRIMARK AI – INDEPENDENT DATASET VALIDATION")
    print(f"File: {csv_path}")
    print("=" * 70)

    if not os.path.exists(csv_path):
        print(f"[FAIL] Target file does not exist: {csv_path}")
        return False

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        # 1. Check required columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in headers]
        if missing_cols:
            print(f"[FAIL] Missing required columns: {missing_cols}")
            return False
        print(f"[PASS] All {len(REQUIRED_COLUMNS)} required columns present.")

        rows = list(reader)

    if not rows:
        print("[INFO] CSV template contains 0 data rows (empty template ready for data collection).")
        print("[PASS] Template schema is valid and ready.")
        return True

    print(f"[INFO] Inspecting {len(rows)} row(s)...")

    errors: List[str] = []
    seen_pairs: Dict[Tuple[str, str], int] = {}
    verified_rows_count = 0
    pending_or_empty_count = 0

    for idx, row in enumerate(rows, start=2):  # 1-based, row 1 is header
        sid = (row.get("student_id") or "").strip()
        qid = (row.get("question_id") or "").strip()
        answer = (row.get("student_answer") or "").strip()
        present = (row.get("human_verified_present_concepts") or "").strip()
        missing = (row.get("human_verified_missing_concepts") or "").strip()
        status = (row.get("review_status") or "").strip()

        # Check if entire row is empty
        if not any([sid, qid, answer, present, missing, status]):
            continue

        # 5. Check duplicate student/question pairs
        if sid and qid:
            pair = (sid, qid)
            if pair in seen_pairs:
                errors.append(f"Line {idx}: Duplicate entry for student '{sid}' and question '{qid}' (first seen at Line {seen_pairs[pair]}).")
            else:
                seen_pairs[pair] = idx

        # 2. Check Question IDs
        if qid and qid not in VALID_QUESTION_IDS:
            errors.append(f"Line {idx}: Invalid question_id '{qid}'. Must be one of {sorted(list(VALID_QUESTION_IDS))}.")

        # 3. Check Concept Labels match exact 13 educational labels
        invalid_present = validate_concepts(present)
        if invalid_present:
            errors.append(f"Line {idx}: Unrecognized present concepts: {invalid_present}")

        invalid_missing = validate_concepts(missing)
        if invalid_missing:
            errors.append(f"Line {idx}: Unrecognized missing concepts: {invalid_missing}")

        # 6. Check review status
        is_verified = status.lower() in {"verified", "completed", "approved"}

        if not is_verified:
            pending_or_empty_count += 1
            # Empty / Pending rows are excluded from strict verified validation
            continue

        verified_rows_count += 1

        # 4. Verified rows must have non-empty student answers and human labels
        if not answer:
            errors.append(f"Line {idx}: Verified row has an empty 'student_answer'.")

        if not present and not missing:
            errors.append(f"Line {idx}: Verified row has no concept labels specified (both present and missing are empty).")

    print(f"\n--- Summary ---")
    print(f"Total Rows Evaluated: {len(rows)}")
    print(f"Verified Rows (Ready for Evaluation): {verified_rows_count}")
    print(f"Pending/Draft/Empty Rows Skipped: {pending_or_empty_count}")

    if errors:
        print(f"\n[FAIL] Found {len(errors)} validation error(s):")
        for err in errors:
            print(f"  - {err}")
        return False

    print("\n[PASS] All validation checks passed successfully.")
    return True


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "datasets", "independent_eval_template.csv"
    )
    success = validate_csv(target)
    sys.exit(0 if success else 1)
