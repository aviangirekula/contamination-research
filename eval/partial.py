"""Partial / semipartial rank correlations, Kendall tau-b, permutation p, BH-FDR.

Used only by the controls run (R6 circularity etc.). Pure numpy; correctness checked
against constructed cases in tests/test_partial.py. Conventions match eval/metrics.py
(higher detector score = more member-like).
"""
from __future__ import annotations

import numpy as np

from .metrics import _rankdata


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    denom = np.sqrt((a**2).sum() * (b**2).sum())
    return 0.0 if denom == 0 else float((a * b).sum() / denom)


def _ranks(x):
    return _rankdata(np.asarray(x, dtype=np.float64))


def spearman(x, y) -> float:
    return _pearson(_ranks(x), _ranks(y))


def partial_spearman(x, y, z) -> float:
    """Partial Spearman corr of x and y controlling for z (Pearson partial on ranks)."""
    rx, ry, rz = _ranks(x), _ranks(y), _ranks(z)
    rxy, rxz, ryz = _pearson(rx, ry), _pearson(rx, rz), _pearson(ry, rz)
    denom = np.sqrt(max(0.0, (1 - rxz**2) * (1 - ryz**2)))
    return 0.0 if denom == 0 else float((rxy - rxz * ryz) / denom)


def semipartial_spearman(x, y, z) -> float:
    """Part correlation: x residualized on z (z removed from x only), correlated with y."""
    rx, ry, rz = _ranks(x), _ranks(y), _ranks(z)
    rxy, rxz, ryz = _pearson(rx, ry), _pearson(rx, rz), _pearson(ry, rz)
    denom = np.sqrt(max(0.0, 1 - rxz**2))
    return 0.0 if denom == 0 else float((rxy - rxz * ryz) / denom)


def kendall_tau(x, y) -> float:
    """Kendall tau-b (tie-corrected). O(n^2); fine for n in the hundreds."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = len(x)
    s = 0
    for i in range(n - 1):
        dx = np.sign(x[i + 1 :] - x[i])
        dy = np.sign(y[i + 1 :] - y[i])
        s += np.sum(dx * dy)
    n0 = n * (n - 1) / 2.0

    def tie_term(v):
        _, counts = np.unique(v, return_counts=True)
        return np.sum(counts * (counts - 1) / 2.0)

    n1 = tie_term(x)
    n2 = tie_term(y)
    denom = np.sqrt((n0 - n1) * (n0 - n2))
    return 0.0 if denom == 0 else float(s / denom)


def permutation_p_partial(x, y, z, n_perm=2000, seed=0) -> float:
    """Two-sided permutation p for partial_spearman(x,y|z): permute y, recompute."""
    x = np.asarray(x, float); y = np.asarray(y, float); z = np.asarray(z, float)
    rng = np.random.default_rng(seed)
    obs = abs(partial_spearman(x, y, z))
    count = 0
    for _ in range(n_perm):
        yp = rng.permutation(y)
        if abs(partial_spearman(x, yp, z)) >= obs - 1e-12:
            count += 1
    return (1 + count) / (n_perm + 1)


def permutation_p_spearman(x, y, n_perm=2000, seed=0) -> float:
    x = np.asarray(x, float); y = np.asarray(y, float)
    rng = np.random.default_rng(seed)
    obs = abs(spearman(x, y))
    count = sum(abs(spearman(x, rng.permutation(y))) >= obs - 1e-12 for _ in range(n_perm))
    return (1 + count) / (n_perm + 1)


def bootstrap_ci(stat_fn, arrays, n_boot=2000, seed=0, alpha=0.05):
    """Percentile bootstrap CI. `arrays` is a tuple of equal-length arrays; stat_fn(*arrays)."""
    arrays = [np.asarray(a, float) for a in arrays]
    n = len(arrays[0])
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        try:
            vals.append(stat_fn(*[a[idx] for a in arrays]))
        except Exception:
            continue
    vals = np.asarray(vals)
    return float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2))


def benjamini_hochberg(pvals, alpha=0.05):
    """Return (rejected_bool_array, qvalues) under BH-FDR at level alpha."""
    p = np.asarray(pvals, dtype=np.float64)
    m = len(p)
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * m / (np.arange(1, m + 1))
    q = np.minimum.accumulate(q[::-1])[::-1]  # enforce monotonicity
    q = np.clip(q, 0, 1)
    qvals = np.empty(m)
    qvals[order] = q
    rejected = qvals <= alpha
    return rejected, qvals
