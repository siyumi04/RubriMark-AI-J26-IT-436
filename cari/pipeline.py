"""CariEngine: fit on development data, then assess() one AssessmentCase -> ReliabilityResult.
assess() receives ONLY an AssessmentCase (never labels), and is deterministic for stored inputs (NFR-01)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .contract import AssessmentCase, ReliabilityResult
from .config import CariConfig
from .gates import gates
from .indicators import (INDICATORS, COMPONENTS, SemanticGradeModel, compute_indicators, component_scores, EntailmentScorer)
from .aggregation import Aggregator, make_aggregators
from .thresholds import choose_tau
from .labels import LabelRecord


def feature_cols(level: str) -> list[str]:
    return list(COMPONENTS) if level == "component" else list(INDICATORS)


def fit_semantic_model(cases: list[AssessmentCase], labels: dict[str, LabelRecord]) -> SemanticGradeModel:
    pairs = [(c.c1, labels[c.assessment_id].gold_norm) for c in cases if c.c1 is not None]
    return SemanticGradeModel().fit([p[0] for p in pairs], [p[1] for p in pairs])


def build_table(cases, entail: EntailmentScorer, sem: SemanticGradeModel, cfg: CariConfig,
                y: dict | None = None) -> pd.DataFrame:
    rows = []
    for c in cases:
        ind = compute_indicators(c, entail, sem, cfg)
        comp = component_scores(ind)
        g = gates(c, cfg)
        row = {"assessment_id": c.assessment_id, "question_id": c.question_id, **ind, **comp,
               "gates": ";".join(g), "gate": bool(g)}
        if y is not None:
            row["y"] = int(y[c.assessment_id])
        rows.append(row)
    return pd.DataFrame(rows)


class CariEngine:
    def __init__(self, cfg: CariConfig, entail: EntailmentScorer, aggregator: Aggregator):
        self.cfg, self.entail, self.agg = cfg, entail, aggregator
        self.sem = SemanticGradeModel()
        self.tau = 0.5
        self.cols = feature_cols(cfg.level)

    def fit(self, cases, labels: dict[str, LabelRecord], y: dict) -> "CariEngine":
        self.sem = fit_semantic_model(cases, labels)
        tab = build_table(cases, self.entail, self.sem, self.cfg, y)
        X = tab[self.cols].to_numpy(float)
        self.agg.fit(X, tab["y"].to_numpy(), self.cols)
        cari = np.nan_to_num(self.agg.score(X), nan=0.0)
        self.tau = choose_tau(cari, tab["y"], self.cfg.tau_policy, recall_target=self.cfg.recall_target,
                              c_fn=self.cfg.c_fn, c_fp=self.cfg.c_fp)
        return self

    def assess(self, case: AssessmentCase) -> ReliabilityResult:
        ind = compute_indicators(case, self.entail, self.sem, self.cfg)
        comp = component_scores(ind)
        feats = {**ind, **comp}
        x = np.array([[feats[c] for c in self.cols]], float)
        raw = float(self.agg.score(x)[0])
        cari = None if np.isnan(raw) else raw
        g = gates(case, self.cfg)
        low = cari is None or cari < self.tau
        decision = "LECTURER_VALIDATION" if (g or low) else "AUTO_RELEASE"
        scored = sorted(((k, v) for k, v in ind.items() if not np.isnan(v)), key=lambda kv: kv[1])
        weakest = [f"{k}={v:.2f}" for k, v in scored[:3]]
        if g:
            reason = "Gate(s) fired: " + ", ".join(g)
        elif low:
            reason = f"CARI {cari if cari is not None else float('nan'):.2f} below threshold {self.tau:.2f}; weakest: " + ", ".join(weakest)
        else:
            reason = f"CARI {cari:.2f} >= threshold {self.tau:.2f}; no gates fired"
        clean = lambda d: {k: (None if np.isnan(v) else float(v)) for k, v in d.items()}
        return ReliabilityResult(assessment_id=case.assessment_id, cari=cari, decision=decision, gates_fired=g,
                                 indicators=clean(ind), component_scores=clean(comp), weakest=weakest,
                                 reason=reason, config_id=self.cfg.config_id, tau=float(self.tau))
