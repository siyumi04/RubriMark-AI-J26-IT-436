"""Routing threshold policies. A case is flagged (sent to a lecturer) when CARI < tau. Positive class = unreliable."""
from __future__ import annotations
import numpy as np


def _candidates(cari: np.ndarray) -> np.ndarray:
    u = np.unique(cari[~np.isnan(cari)])
    return np.concatenate([u, [u.max() + 1e-9]]) if len(u) else np.array([0.5])


def confusion(cari, y, tau):
    flag = cari < tau
    y = np.asarray(y).astype(bool)
    return int((flag & y).sum()), int((flag & ~y).sum()), int((~flag & ~y).sum()), int((~flag & y).sum())  # tp, fp, tn, fn


def f1_at(cari, y, tau) -> float:
    tp, fp, tn, fn = confusion(cari, y, tau)
    return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0


def tau_f1(cari, y) -> float:
    c = _candidates(cari)
    return float(c[int(np.argmax([f1_at(cari, y, t) for t in c]))])   # SURE-style: maximise F1 on dev


def tau_recall(cari, y, target=0.95) -> float:
    """Smallest tau (least lecturer workload) that still flags >= target of the unreliable cases."""
    for t in _candidates(cari):
        tp, fp, tn, fn = confusion(cari, y, t)
        if tp + fn and tp / (tp + fn) >= target:
            return float(t)
    return float(_candidates(cari)[-1])


def tau_cost(cari, y, c_fn=5.0, c_fp=1.0) -> float:
    c = _candidates(cari)
    costs = [c_fn * confusion(cari, y, t)[3] + c_fp * confusion(cari, y, t)[1] for t in c]
    return float(c[int(np.argmin(costs))])


def choose_tau(cari, y, policy="recall", **kw) -> float:
    cari = np.nan_to_num(np.asarray(cari, float), nan=0.0)
    if policy == "f1":
        return tau_f1(cari, y)
    if policy == "cost":
        return tau_cost(cari, y, kw.get("c_fn", 5.0), kw.get("c_fp", 1.0))
    return tau_recall(cari, y, kw.get("recall_target", 0.95))
