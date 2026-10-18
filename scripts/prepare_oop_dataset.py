"""Prepare API-ready sample cases from the OOP questionnaire CSV.

The form contains a few rows where respondents answered a different question set
after the questionnaire changed. Those rows are excluded by topic matching.
Emails are intentionally not copied into the generated dataset.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from cari.contract import (
    AssessmentCase,
    C1Output,
    C3Output,
    C4Output,
    Claim,
    Criterion,
    NLIProbs,
    Provenance,
)


QUESTION_SPECS = [
    {
        "id": "oop_q1_class_object",
        "text": "What is the difference between a class and an object in Java? Give a simple example.",
        "reference": "A class is a blueprint that defines fields and methods. An object is an instance of a class created in memory, such as Car myCar = new Car().",
        "required": (("class", "blueprint", "template"), ("object", "instance")),
        "criteria": [
            ("class_definition", ("class", "blueprint", "template"), "Defines a class as a blueprint or template.", 2),
            ("object_definition", ("object", "instance"), "Defines an object as an instance.", 2),
            ("java_example", ("example", "new", "car", "mycar"), "Gives a relevant Java example.", 1),
        ],
    },
    {
        "id": "oop_q2_inheritance",
        "text": "If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?",
        "reference": "Car can inherit accessible fields and methods from Vehicle. Private members are not directly accessible and constructors are not inherited.",
        "required": (("car", "vehicle"), ("inherit", "inheritance", "extends")),
        "criteria": [
            ("inherited_members", ("inherit", "inheritance", "extends"), "Identifies inheritance from the parent class.", 2),
            ("fields_methods", ("field", "variable", "attribute", "method"), "Identifies accessible fields or methods.", 2),
            ("access_control", ("public", "protected", "private", "accessible"), "Recognises access control limits.", 1),
        ],
    },
    {
        "id": "oop_q3_overriding",
        "text": "What happens when a child class overrides a method inherited from its parent class?",
        "reference": "The child class supplies its own implementation. When the method is called on a child object, the child implementation runs instead of the parent implementation.",
        "required": (("child", "override", "overridden"), ("method", "implementation")),
        "criteria": [
            ("own_implementation", ("own", "provides", "specific", "implementation", "version"), "Explains that the child supplies its own implementation.", 2),
            ("child_dispatch", ("child", "called", "runs", "executed"), "Explains that child dispatch uses the overridden implementation.", 2),
            ("parent_relation", ("parent", "inherited", "instead"), "Relates the override to the parent method.", 1),
        ],
    },
    {
        "id": "oop_q4_static_instance",
        "text": "Can a static method directly access a non-static variable? Why or why not?",
        "reference": "No. A static method belongs to the class, while a non-static variable belongs to an object, so an object reference is required.",
        "required": (("static",), ("non-static", "nonstatic", "instance")),
        "criteria": [
            ("static_class", ("static", "class"), "Explains that a static method belongs to the class.", 2),
            ("instance_object", ("non-static", "nonstatic", "instance", "object"), "Explains that the variable belongs to an object.", 2),
            ("object_reference", ("object", "reference", "directly", "cannot"), "States the need for an object reference or restriction.", 1),
        ],
    },
    {
        "id": "oop_q5_exceptions",
        "text": "Why is exception handling important in Java?",
        "reference": "Exception handling detects and manages runtime errors so a program can avoid unexpected termination, recover safely, and maintain normal flow.",
        "required": (("exception", "error"), ("handle", "handling", "crash", "program", "runtime")),
        "criteria": [
            ("runtime_errors", ("exception", "error", "runtime"), "Identifies errors during program execution.", 2),
            ("prevent_crash", ("prevent", "crash", "stop", "termination", "continue"), "Explains prevention of unexpected termination.", 2),
            ("safe_recovery", ("handle", "handling", "recover", "graceful", "try", "catch"), "Explains safe handling or recovery.", 1),
        ],
    },
]


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def matches_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def is_oop_row(row: dict[str, str], answer_columns: list[str]) -> bool:
    answers = [normalise(row.get(column, "")) for column in answer_columns]
    return all(
        all(matches_any(answer, group) for group in spec["required"])
        for answer, spec in zip(answers, QUESTION_SPECS)
    )


def make_case(row_number: int, question: dict, answer: str) -> AssessmentCase:
    text = normalise(answer)
    criteria = []
    claims = []
    total = 0.0
    for criterion_id, terms, description, max_points in question["criteria"]:
        met = matches_any(text, terms)
        points = float(max_points if met else 0)
        total += points
        criteria.append(Criterion(
            id=f"c_{criterion_id}",
            concept_id=criterion_id,
            description=description,
            weight=max_points / 5,
            points=points,
            max_points=float(max_points),
            evidence_span=answer[:240] if met else None,
        ))
        claims.append(Claim(
            criterion_id=f"c_{criterion_id}",
            outcome="met" if met else "not_met",
            span=answer[:240] if met else None,
        ))

    coverage = total / 5.0
    # "No" is the correct answer for the static-method question, so only mark
    # explicit contradictory claims as contradiction evidence.
    negative = any(phrase in text for phrase in (
        "yes, a static method", "can directly access non-static",
        "both parent and child methods always", "not needed because",
    ))
    c1 = C1Output(
        cos_bi=round(0.25 + 0.7 * coverage, 4),
        cross_enc=round(0.2 + 0.75 * coverage, 4),
        nli=NLIProbs(ent=round(coverage, 4), con=0.7 if negative else round(1 - coverage, 4), neu=0.1),
        missing_concepts=[criterion_id for criterion_id, terms, _, _ in question["criteria"]
                          if not matches_any(text, terms)],
        n_concepts=len(question["criteria"]),
        knn_typicality=round(0.35 + 0.55 * coverage, 4),
    )
    runs = [max(0.0, min(5.0, total + delta)) for delta in (0.0, 0.0, 0.5 if coverage > 0.8 else -0.5, 0.0, 0.0)]
    c3 = C3Output(
        rubric_id=f"rubric_{question['id']}",
        rubric_version=1,
        rubric_approved=True,
        max_score=5.0,
        runs=runs,
        ai_score=round(total, 2),
        criteria=criteria,
    )
    c4 = C4Output(
        claims=claims,
        direct_gaps=[criterion_id for criterion_id, terms, _, _ in question["criteria"]
                     if not matches_any(text, terms)],
        stated_score=round(total, 2),
    )
    return AssessmentCase(
        assessment_id=f"oop_{row_number:03d}_{question['id']}",
        question_id=question["id"],
        student_response=answer.strip(),
        reference_answer=question["reference"],
        student_email=f"student_{row_number:03d}@example.edu",
        c1=c1,
        c3=c3,
        c4=c4,
        provenance=Provenance(model="oop-keyword-standin", version="1.0"),
    )


def prepare(source: Path, output_dir: Path) -> tuple[int, int]:
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        answer_columns = headers[3:8]
        if len(answer_columns) != 5:
            raise ValueError("Expected five answer columns after timestamp, email, and score")
        rows = list(reader)

    cases: list[AssessmentCase] = []
    normalized_rows: list[dict[str, str]] = []
    kept = 0
    for row_number, row in enumerate(rows, start=1):
        if not is_oop_row(row, answer_columns):
            continue
        kept += 1
        for question, column in zip(QUESTION_SPECS, answer_columns):
            answer = (row.get(column) or "").strip()
            case = make_case(row_number, question, answer)
            cases.append(case)
            normalized_rows.append({
                "assessment_id": case.assessment_id,
                "question_id": case.question_id,
                "question": question["text"],
                "student_response": answer,
                "reference_answer": question["reference"],
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "oop_assessment_cases.jsonl").open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(case.model_dump_json() + "\n")
    with (output_dir / "oop_assessment_cases.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(normalized_rows[0]) if normalized_rows else
                                ["assessment_id", "question_id", "question", "student_response", "reference_answer"])
        writer.writeheader()
        writer.writerows(normalized_rows)
    (output_dir / "oop_dataset_summary.json").write_text(json.dumps({
        "source": source.name,
        "rows_read": len(rows),
        "student_rows_kept": kept,
        "assessment_cases": len(cases),
        "excluded_rows": len(rows) - kept,
        "privacy": "Email addresses and form scores were not copied.",
    }, indent=2) + "\n", encoding="utf-8")
    return kept, len(cases)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    kept, cases = prepare(args.source, args.output_dir)
    print(f"Prepared {cases} assessment cases from {kept} OOP response rows.")
