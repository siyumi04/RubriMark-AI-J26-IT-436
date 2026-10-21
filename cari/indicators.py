"""Reliability indicators. All reliability-oriented indicators are in [0,1]; higher = more reliable.
NaN means "cannot be computed" (missing component) and is handled downstream.

Sources: consistency [8] SURE; evidence validity [9] GradeAgentOps; semantic features [1] Cong et al.;
rubric/semantic-grade agreement and explanation support are project-specific adaptations (to be justified).
"""
from __future__ import annotations
import math
from collections import Counter
from typing import Callable, Optional
import numpy as np
from sklearn.linear_model import Ridge
from .contract import AssessmentCase, C1Output, C3Output, C4Output
from .config import CariConfig
from .textutil import span_grounded

NAN = float("nan")
EntailmentScorer = Callable[[str, str], float]   # (criterion_text, student_answer) -> P(entailment)

INDICATORS = [
    "c1_model_agreement", "c1_no_contradiction", "c1_typicality",
    "c3_consistency", "c3_evidence_validity", "c3_rubric_agreement",
    "c4_explanation_support", "c4_gap_precision",
    "x_semantic_grade_agreement", "x_gap_overlap",
]
COMPONENTS = {
    "R1": ["c1_model_agreement", "c1_no_contradiction", "c1_typicality"],
    "R3": ["c3_consistency", "c3_evidence_validity", "c3_rubric_agreement"],
    "R4": ["c4_explanation_support", "c4_gap_precision"],
    "X": ["x_semantic_grade_agreement", "x_gap_overlap"],
}


def _isnan(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def mode_score(runs: list[float]) -> float:
    c = Counter(runs)
    top = max(c.values())
    cands = [v for v, n in c.items() if n == top]
    m = float(np.mean(runs))
    return min(cands, key=lambda v: abs(v - m))


def consistency(runs: list[float]) -> float:
    """[8] share of repeated gradings agreeing with the modal score."""
    if not runs:
        return NAN
    return max(Counter(runs).values()) / len(runs)


def evidence_validity(c3: C3Output, answer: str, fuzzy: Optional[float]) -> float:
    """[9] share of covered criteria whose evidence span is recoverable from the student answer."""
    covered = [c for c in c3.criteria if c.points > 0]
    if not covered:
        return 1.0   # nothing to ground; false zeros are caught by rubric agreement / semantic agreement
    ok = sum(1 for c in covered if c.evidence_span and span_grounded(c.evidence_span, answer, fuzzy))
    return ok / len(covered)


def rubric_agreement(c3: C3Output, answer: str, entail: EntailmentScorer) -> float:
    """Do awarded points agree with an independent entailment check of each criterion?
    R = sum_c w_c * (1 - |points_c/max_c - P_ent(c)|) / sum_c w_c"""
    num = den = 0.0
    for c in c3.criteria:
        f = c.points / c.max_points
        z = float(np.clip(entail(c.description, answer), 0, 1))
        num += c.weight * (1 - abs(f - z))
        den += c.weight
    return num / den if den > 0 else NAN


def explanation_support(c3: C3Output, c4: C4Output, answer: str, fuzzy: Optional[float]) -> float:
    """Share of C4 claims that cite a real criterion, match the awarded points, and (if 'met') are grounded."""
    if not c4.claims:
        return NAN
    by_id = {c.id: c for c in c3.criteria}
    ok = 0
    for cl in c4.claims:
        crit = by_id.get(cl.criterion_id)
        if crit is None:
            continue
        if (cl.outcome == "met") != (crit.points > 0):
            continue
        if cl.outcome == "met" and not (cl.span and span_grounded(cl.span, answer, fuzzy)):
            continue
        ok += 1
    return ok / len(c4.claims)


def gap_precision(c1: C1Output, c3: C3Output, c4: C4Output) -> float:
    """Share of gaps stated by C4 that C1 or C3 also report as missing."""
    if not c4.direct_gaps:
        return 1.0
    known = set(c1.missing_concepts) | {c.concept_id for c in c3.criteria if c.points <= 0}
    return sum(1 for g in c4.direct_gaps if g in known) / len(c4.direct_gaps)


def gap_overlap(c1: C1Output, c3: C3Output) -> float:
    """Jaccard overlap between C1 missing concepts and C3 missed criteria."""
    a = set(c1.missing_concepts)
    b = {c.concept_id for c in c3.criteria if c.points <= 0}
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


class SemanticGradeModel:
    """Predicts the normalised grade from C1 features only (fit on development data).
    Reliability signal = agreement between this semantic grade and the awarded grade."""

    def __init__(self, alpha: float = 1.0):
        self.model = Ridge(alpha=alpha)
        self.fitted = False

    @staticmethod
    def features(c1: C1Output) -> list[float]:
        return [c1.cos_bi, c1.cross_enc, c1.nli.ent, 1 - c1.nli.con, c1.knn_typicality,
                1 - len(c1.missing_concepts) / c1.n_concepts]

    def fit(self, c1_list: list[C1Output], gold_norm: list[float]) -> "SemanticGradeModel":
        self.model.fit(np.array([self.features(c) for c in c1_list]), np.array(gold_norm))
        self.fitted = True
        return self

    def predict(self, c1: C1Output) -> float:
        return float(np.clip(self.model.predict([self.features(c1)])[0], 0, 1))


def compute_indicators(case: AssessmentCase, entail: EntailmentScorer,
                       sem: SemanticGradeModel, cfg: CariConfig) -> dict[str, float]:
    ind = {k: NAN for k in INDICATORS}
    c1, c3, c4, ans = case.c1, case.c3, case.c4, case.student_response
    if c1:
        ind["c1_model_agreement"] = 1 - abs(c1.cos_bi - c1.cross_enc)
        ind["c1_no_contradiction"] = 1 - c1.nli.con
        ind["c1_typicality"] = c1.knn_typicality
    if c3:
        ind["c3_consistency"] = consistency(c3.runs)
        ind["c3_evidence_validity"] = evidence_validity(c3, ans, cfg.fuzzy_threshold)
        ind["c3_rubric_agreement"] = rubric_agreement(c3, ans, entail)
    if c3 and c4:
        ind["c4_explanation_support"] = explanation_support(c3, c4, ans, cfg.fuzzy_threshold)
    if c1 and c3 and c4:
        ind["c4_gap_precision"] = gap_precision(c1, c3, c4)
    if c1 and c3:
        ind["x_gap_overlap"] = gap_overlap(c1, c3)
        if sem.fitted:
            ind["x_semantic_grade_agreement"] = float(np.clip(
                1 - abs(sem.predict(c1) - c3.ai_score / c3.max_score), 0, 1))
    return ind


def component_scores(ind: dict[str, float]) -> dict[str, float]:
    out = {}
    for comp, names in COMPONENTS.items():
        vals = [ind[n] for n in names if not _isnan(ind[n])]
        out[comp] = float(np.mean(vals)) if vals else NAN
    return out
