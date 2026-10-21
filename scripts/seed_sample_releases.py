"""Seed a small, clearly labelled automatic-release cohort for local UI testing.

This does not represent real model output. It updates only the first five OOP
student cohorts so the final-release table can be demonstrated end-to-end.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from cari.db import Assessment, make_session_factory

QUESTION_IDS = (
    "oop_q1_class_object",
    "oop_q2_inheritance",
    "oop_q3_overriding",
    "oop_q4_static_instance",
    "oop_q5_exceptions",
)
SAMPLE_SCORES = (
    (5, 4, 4, 5, 4),
    (4, 5, 3, 4, 5),
    (5, 5, 5, 4, 5),
    (3, 4, 4, 3, 4),
    (4, 3, 5, 5, 4),
)


def student_id(assessment_id: str) -> str:
    match = re.match(r"^(.*?_\d{3})_", assessment_id)
    return match.group(1) if match else assessment_id.rsplit("_", 1)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--students", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.students <= len(SAMPLE_SCORES):
        raise SystemExit(f"--students must be between 1 and {len(SAMPLE_SCORES)}")

    db = make_session_factory()()
    try:
        rows = db.query(Assessment).filter(Assessment.assessment_id.like("oop_%")).all()
        by_student = {}
        for row in rows:
            by_student.setdefault(student_id(row.assessment_id), {})[row.question_id] = row
        selected = sorted(by_student)[:args.students]
        changed = 0
        for index, sid in enumerate(selected):
            question_rows = by_student[sid]
            for question_index, question_id in enumerate(QUESTION_IDS):
                row = question_rows.get(question_id)
                if row is None:
                    continue
                score = float(SAMPLE_SCORES[index][question_index])
                payload = dict(row.payload)
                c3 = dict(payload.get("c3") or {})
                c3["ai_score"] = score
                c3["runs"] = [score, score, score, score, score]
                payload["c3"] = c3
                payload["sample_data"] = True
                row.payload = payload
                row.cari = 0.93
                row.tau = 0.80
                row.decision = "AUTO_RELEASE"
                row.gates = []
                row.reason = "Sample automatic release for dashboard testing; not a real model decision."
                row.status = "released"
                changed += 1
        db.commit()
        print(f"Seeded {changed} sample automatic releases for {len(selected)} students: {', '.join(selected)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
