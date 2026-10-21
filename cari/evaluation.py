from __future__ import annotations
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score
from .thresholds import confusion


def evaluate(cari, gate, y, tau) -> dict:
    """Final decision = gate fired OR CARI < tau. Positive class (y=1) = AI grade is wrong."""
    cari = np.nan_to_num(np.asarray(cari, float), nan=0.0)
    gate, y = np.asarray(gate, bool), np.asarray(y, int)
    flag = gate | (cari < tau)
    tp, fp = int((flag & (y == 1)).sum()), int((flag & (y == 0)).sum())
    fn, tn = int((~flag & (y == 1)).sum()), int((~flag & (y == 0)).sum())
    n = len(y)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return {
        "precision": prec, "recall": rec, "f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
        "workload": (tp + fp) / n, "coverage": (tn + fn) / n,
        "released_error": fn / (tn + fn) if tn + fn else 0.0, "n": n, "base_rate": float(y.mean()),
    }


def auc(cari, y) -> float:
    """ROC-AUC of the continuous score for detecting unreliable cases (low CARI = unreliable)."""
    cari = np.nan_to_num(np.asarray(cari, float), nan=0.0)
    return float(roc_auc_score(y, -cari)) if len(set(y)) == 2 else float("nan")


def pr_auc(cari, y) -> float:
    cari = np.nan_to_num(np.asarray(cari, float), nan=0.0)
    return float(average_precision_score(y, -cari))


def risk_coverage(cari, y):
    """Release the most reliable cases first; risk = error rate among released cases at each coverage."""
    cari = np.nan_to_num(np.asarray(cari, float), nan=0.0)
    order = np.argsort(-cari, kind="stable")
    ys = np.asarray(y)[order]
    cov = np.arange(1, len(ys) + 1) / len(ys)
    risk = np.cumsum(ys) / np.arange(1, len(ys) + 1)
    return cov, risk


def aurc(cari, y) -> float:
    return float(risk_coverage(cari, y)[1].mean())   # lower is better
