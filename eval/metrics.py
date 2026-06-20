"""Security-venue evaluation metrics.

Primary metric is **TPR at low fixed FPR** (0.1%, 1%) with log-scale ROC, per
Carlini et al. 2022 (S&P): average-case AUC/accuracy hide whether an attack can
*confidently* identify any members. AUC is reported as a secondary/continuity metric.

Implemented in pure numpy (no sklearn/scipy) so the metrics layer is dependency-light
and its correctness is auditable against closed-form synthetic cases in the tests.

Score convention: higher score => more "member-like"; ``y_true`` is 1 for members
(positives), 0 for non-members (negatives).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _check(scores: np.ndarray, y_true: np.ndarray):
    scores = np.asarray(scores, dtype=np.float64)
    y_true = np.asarray(y_true, dtype=np.int64)
    if scores.shape != y_true.shape:
        raise ValueError("scores and y_true must have the same shape")
    if not set(np.unique(y_true)).issubset({0, 1}):
        raise ValueError("y_true must be binary (0/1)")
    if y_true.sum() == 0 or y_true.sum() == len(y_true):
        raise ValueError("need at least one positive and one negative")
    return scores, y_true


def roc_curve(scores: np.ndarray, y_true: np.ndarray):
    """Return (fpr, tpr, thresholds), sorted by increasing FPR.

    Uses every distinct score as a threshold (predict member iff score >= thr).
    """
    scores, y_true = _check(scores, y_true)
    P = y_true.sum()
    N = len(y_true) - P
    order = np.argsort(-scores, kind="mergesort")  # high score first
    s_sorted = scores[order]
    y_sorted = y_true[order]
    tp = np.cumsum(y_sorted)
    fp = np.cumsum(1 - y_sorted)
    # collapse ties: keep last index of each distinct score
    distinct = np.r_[np.diff(s_sorted) != 0, True]
    tpr = np.r_[0.0, tp[distinct] / P]
    fpr = np.r_[0.0, fp[distinct] / N]
    thr = np.r_[np.inf, s_sorted[distinct]]
    return fpr, tpr, thr


def auc_roc(scores: np.ndarray, y_true: np.ndarray) -> float:
    """AUC-ROC via the Mann-Whitney U statistic (handles ties with mid-ranks)."""
    scores, y_true = _check(scores, y_true)
    ranks = _rankdata(scores)
    P = y_true.sum()
    N = len(y_true) - P
    sum_ranks_pos = ranks[y_true == 1].sum()
    u = sum_ranks_pos - P * (P + 1) / 2.0
    return float(u / (P * N))


def tpr_at_fpr(scores: np.ndarray, y_true: np.ndarray, target_fpr: float) -> float:
    """Max TPR achievable at FPR <= ``target_fpr`` (the S&P low-FPR operating point)."""
    fpr, tpr, _ = roc_curve(scores, y_true)
    mask = fpr <= target_fpr + 1e-12
    if not mask.any():
        return 0.0
    return float(tpr[mask].max())


@dataclass
class MIAReport:
    auc: float
    tpr_at_0p1: float  # TPR @ 0.1% FPR
    tpr_at_1: float     # TPR @ 1% FPR
    n_pos: int
    n_neg: int


def mia_report(scores, y_true) -> MIAReport:
    scores, y_true = _check(scores, y_true)
    return MIAReport(
        auc=auc_roc(scores, y_true),
        tpr_at_0p1=tpr_at_fpr(scores, y_true, 0.001),
        tpr_at_1=tpr_at_fpr(scores, y_true, 0.01),
        n_pos=int(y_true.sum()),
        n_neg=int(len(y_true) - y_true.sum()),
    )


def bootstrap_ci(metric_fn, scores, y_true, n_boot: int = 1000, seed: int = 0, alpha: float = 0.05):
    """Stratified bootstrap (resample positives and negatives separately) CI for a metric."""
    scores = np.asarray(scores, dtype=np.float64)
    y_true = np.asarray(y_true, dtype=np.int64)
    rng = np.random.default_rng(seed)
    pos = np.where(y_true == 1)[0]
    neg = np.where(y_true == 0)[0]
    vals = []
    for _ in range(n_boot):
        bp = rng.choice(pos, size=len(pos), replace=True)
        bn = rng.choice(neg, size=len(neg), replace=True)
        idx = np.concatenate([bp, bn])
        try:
            vals.append(metric_fn(scores[idx], y_true[idx]))
        except ValueError:
            continue
    vals = np.asarray(vals)
    lo = float(np.quantile(vals, alpha / 2))
    hi = float(np.quantile(vals, 1 - alpha / 2))
    return lo, hi


def _rankdata(a: np.ndarray) -> np.ndarray:
    """Average ranks (1-based), ties shared — equivalent to scipy.stats.rankdata."""
    a = np.asarray(a, dtype=np.float64)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), dtype=np.float64)
    sorted_a = a[order]
    i = 0
    n = len(a)
    while i < n:
        j = i
        while j + 1 < n and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # 1-based average rank
        ranks[order[i : j + 1]] = avg
        i = j + 1
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation (Pearson on ranks). The headline contamination<->leakage stat."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("need equal-length vectors of length >= 2")
    rx = _rankdata(x)
    ry = _rankdata(y)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = np.sqrt((rx**2).sum() * (ry**2).sum())
    if denom == 0:
        return 0.0
    return float((rx * ry).sum() / denom)


def spearman_ci(x, y, n_boot: int = 1000, seed: int = 0, alpha: float = 0.05):
    """Bootstrap CI for Spearman rho (paired resampling)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    rng = np.random.default_rng(seed)
    n = len(x)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        try:
            vals.append(spearman(x[idx], y[idx]))
        except ValueError:
            continue
    vals = np.asarray(vals)
    return float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2))
