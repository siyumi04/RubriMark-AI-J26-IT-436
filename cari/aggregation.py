"""Candidate aggregation methods. Every aggregator maps an (n x d) feature matrix in [0,1]
(NaN allowed = missing) to CARI in [0,1], higher = more reliable.

M0 single indicator | M1 equal-weight SAW | M2 logistic regression (supervised baseline)
M3 AHP-weighted SAW | M4 TOPSIS (fixed ideal/anti-ideal) | M5 ELECTRE-style concordance + veto
M1/M3/M4/M5 follow standard MCDA definitions; M5 is a project-specific adaptation for binary sorting.
"""
from __future__ import annotations
import numpy as np
from sklearn.linear_model import LogisticRegression

# Placeholder importance priorities (Saaty-style 1..9 scale). Replace with expert pairwise elicitation.
DEFAULT_PRIORITIES = {
    "c3_consistency": 3, "c3_evidence_validity": 3, "c3_rubric_agreement": 3, "c1_no_contradiction": 3,
    "c4_explanation_support": 2, "x_semantic_grade_agreement": 2, "c1_typicality": 1,
    "c1_model_agreement": 1, "c4_gap_precision": 1, "x_gap_overlap": 1,
    "R1": 3, "R3": 4, "R4": 2, "X": 1,
}
_RI = {1: 0, 2: 0, 3: .58, 4: .90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


def ahp_weights(A: np.ndarray) -> tuple[np.ndarray, float]:
    """Principal-eigenvector weights and consistency ratio CR = CI/RI, CI = (lambda_max - n)/(n - 1)."""
    n = len(A)
    vals, vecs = np.linalg.eig(A)
    k = int(np.argmax(vals.real))
    w = np.abs(vecs[:, k].real)
    w = w / w.sum()
    ci = (vals[k].real - n) / (n - 1) if n > 1 else 0.0
    ri = _RI.get(n, 1.49)
    return w, (ci / ri if ri > 0 else 0.0)


def ahp_from_priorities(p: np.ndarray) -> tuple[np.ndarray, float]:
    p = np.asarray(p, dtype=float)
    return ahp_weights(np.outer(p, 1 / p))   # perfectly consistent matrix (CR ~ 0); placeholder for elicited matrix


def wmean(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    """NaN-aware weighted mean: weights are renormalised over the available indicators."""
    mask = ~np.isnan(X)
    num = (np.where(mask, X, 0.0) * w).sum(1)
    den = (mask * w).sum(1)
    return np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)


class Aggregator:
    name = "base"

    def fit(self, X, y, cols):
        self.cols = list(cols)
        return self

    def score(self, X) -> np.ndarray:
        raise NotImplementedError


class Single(Aggregator):
    def __init__(self, col):
        self.col = col
        self.name = f"M0_single[{col}]"

    def fit(self, X, y, cols):
        self.cols = list(cols)
        self.i = self.cols.index(self.col)
        return self

    def score(self, X):
        return X[:, self.i]


class EqualWeight(Aggregator):
    name = "M1_equal_weight"

    def score(self, X):
        return wmean(X, np.ones(X.shape[1]))


class Logistic(Aggregator):
    name = "M2_logistic"

    def fit(self, X, y, cols):
        self.cols = list(cols)
        self.fill = np.nanmean(X, axis=0)
        self.m = LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000)
        self.m.fit(np.where(np.isnan(X), self.fill, X), y)
        return self

    def score(self, X):
        return 1 - self.m.predict_proba(np.where(np.isnan(X), self.fill, X))[:, 1]


class AHPWeighted(Aggregator):
    name = "M3_ahp_saw"

    def __init__(self, priorities=None):
        self.priorities = priorities or DEFAULT_PRIORITIES

    def fit(self, X, y, cols):
        self.cols = list(cols)
        self.w, self.cr = ahp_from_priorities(np.array([self.priorities[c] for c in self.cols]))
        return self

    def score(self, X):
        return wmean(X, self.w)


class Topsis(Aggregator):
    """C = D- / (D+ + D-) with fixed ideal (all ones) and anti-ideal (all zeros); weights from AHP priorities."""
    name = "M4_topsis"

    def __init__(self, priorities=None):
        self.priorities = priorities or DEFAULT_PRIORITIES

    def fit(self, X, y, cols):
        self.cols = list(cols)
        self.w = ahp_from_priorities(np.array([self.priorities[c] for c in self.cols]))[0]
        return self

    def score(self, X):
        mask = ~np.isnan(X)
        w = mask * self.w
        s = w.sum(1, keepdims=True)
        w = np.where(s > 0, w / np.where(s > 0, s, 1), 0)
        Xf = np.where(mask, X, 0.0)
        dp = np.sqrt((w * (1 - Xf) ** 2).sum(1))
        dm = np.sqrt((w * Xf ** 2).sum(1))
        tot = dp + dm
        return np.where(tot > 0, dm / np.where(tot > 0, tot, 1), np.nan)


class ElectreStyle(Aggregator):
    """Concordance with a reference profile b (low quantile of reliable dev cases) and a veto threshold.
    score = weighted share of indicators with x >= b, forced to 0 if any indicator falls below its veto."""
    name = "M5_electre_style"

    def __init__(self, priorities=None, q_profile=0.20, q_veto=0.01):
        self.priorities, self.qp, self.qv = priorities or DEFAULT_PRIORITIES, q_profile, q_veto

    def fit(self, X, y, cols):
        self.cols = list(cols)
        self.w = ahp_from_priorities(np.array([self.priorities[c] for c in self.cols]))[0]
        R = X[np.asarray(y) == 0]
        self.b = np.nanquantile(R, self.qp, axis=0)
        self.v = np.nanquantile(R, self.qv, axis=0)
        return self

    def score(self, X):
        mask = ~np.isnan(X)
        conc = wmean(np.where(mask, (X >= self.b - 1e-12).astype(float), np.nan), self.w)
        veto = ((X < self.v - 1e-12) & mask).any(1)
        return np.where(veto, 0.0, conc)


def make_aggregators(cols: list[str]) -> dict[str, Aggregator]:
    aggs: dict[str, Aggregator] = {
        "M1_equal": EqualWeight(), "M2_logistic": Logistic(), "M3_ahp": AHPWeighted(),
        "M4_topsis": Topsis(), "M5_electre": ElectreStyle(),
    }
    if "c3_consistency" in cols:
        aggs["M0_consistency_only"] = Single("c3_consistency")   # SURE-style baseline C
    return aggs
