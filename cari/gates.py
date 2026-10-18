"""Hard, non-compensatory gates: any fired gate forces LECTURER_VALIDATION regardless of CARI."""
from __future__ import annotations
from .contract import AssessmentCase
from .config import CariConfig


def gates(case: AssessmentCase, cfg: CariConfig) -> list[str]:
    g: list[str] = []
    if case.c1 is None or case.c3 is None or case.c4 is None:
        return ["missing_component"]
    c1, c3, c4 = case.c1, case.c3, case.c4
    if not c3.rubric_approved:
        g.append("rubric_not_approved")
    if abs(sum(c.points for c in c3.criteria) - c3.ai_score) > 1e-6:
        g.append("total_mismatch")
    if any(c.points < 0 or c.points > c.max_points for c in c3.criteria) or not (0 <= c3.ai_score <= c3.max_score):
        g.append("points_out_of_range")
    if not c3.runs:
        g.append("no_repeated_runs")
    if not c4.claims:
        g.append("missing_explanation")
    if c4.stated_score is not None and abs(c4.stated_score - c3.ai_score) > 1e-6:
        g.append("c4_grade_mismatch")
    if c1.nli.con > cfg.con_gate and c3.ai_score / c3.max_score >= cfg.high_score_frac:
        g.append("contradiction_high_score")
    return g
