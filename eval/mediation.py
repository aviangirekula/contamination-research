"""Statistical hardening: non-linear loss controls + rank-based mediation.

Answers the reviewer attack "you only removed loss linearly." Pure numpy. Conventions
match eval/metrics.py and eval/partial.py (higher detector score = more member-like).
See docs/pre_analysis.md (Round 2, St) for the pre-registered plan.
"""
from __future__ import annotations

import numpy as np

from .metrics import _rankdata
from .partial import spearman


# ---------------------------------------------------------------- nonlinear control
def _equal_count_bins(control: np.ndarray, n_bins: int) -> np.ndarray:
    """Assign each item to one of n_bins equal-count bins of `control` (by rank)."""
    r = _rankdata(control)              # 1..n average ranks
    # map ranks to bin index 0..n_bins-1 by quantile of rank
    edges = np.quantile(r, np.linspace(0, 1, n_bins + 1))
    edges[0] -= 1e-9
    return np.clip(np.digitize(r, edges[1:-1]), 0, n_bins - 1)


def decile_stratified_spearman(d, y, control, n_bins=10, min_bin=3):
    """Bin-size-weighted mean within-bin Spearman ρ(d, y), holding `control` fixed.

    Bins with < min_bin items (or no variance) are skipped; weights are bin sizes.
    """
    d = np.asarray(d, float); y = np.asarray(y, float); control = np.asarray(control, float)
    bins = _equal_count_bins(control, n_bins)
    num = 0.0; den = 0.0
    for b in np.unique(bins):
        idx = np.where(bins == b)[0]
        if len(idx) < min_bin:
            continue
        db, yb = d[idx], y[idx]
        if np.ptp(db) == 0 or np.ptp(yb) == 0:
            continue
        num += len(idx) * spearman(db, yb)
        den += len(idx)
    return float(num / den) if den > 0 else 0.0


def stratified_permutation_p(d, y, control, n_bins=10, n_perm=2000, seed=0):
    """Two-sided p for decile_stratified_spearman by permuting y WITHIN each loss bin."""
    d = np.asarray(d, float); y = np.asarray(y, float); control = np.asarray(control, float)
    bins = _equal_count_bins(control, n_bins)
    obs = abs(decile_stratified_spearman(d, y, control, n_bins))
    rng = np.random.default_rng(seed)
    bin_idx = [np.where(bins == b)[0] for b in np.unique(bins)]
    count = 0
    for _ in range(n_perm):
        yp = y.copy()
        for idx in bin_idx:
            yp[idx] = rng.permutation(yp[idx])
        if abs(decile_stratified_spearman(d, yp, control, n_bins)) >= obs - 1e-12:
            count += 1
    return (1 + count) / (n_perm + 1)


def _poly_residuals(v: np.ndarray, control: np.ndarray, degree: int = 3) -> np.ndarray:
    """Residuals of v after OLS regression on a degree-`degree` polynomial of control."""
    v = np.asarray(v, float); c = np.asarray(control, float)
    X = np.vander(c, N=degree + 1, increasing=True)  # [1, c, c^2, c^3]
    coef, *_ = np.linalg.lstsq(X, v, rcond=None)
    return v - X @ coef


def cubic_residual_spearman(d, y, control, degree=3):
    """Spearman of (d residualized on poly(control)) vs (y residualized on poly(control)).

    PRIMARY non-linear loss control (St-1): a degree-`degree` polynomial removes the full
    smooth effect of loss (linear + non-linear), unlike coarse bin stratification which leaves
    residual within-bin confounding. See docs/pre_analysis.md St-1 amendment.
    """
    return spearman(_poly_residuals(d, control, degree), _poly_residuals(y, control, degree))


def cubic_residual_perm_p(d, y, control, degree=3, n_perm=2000, seed=0):
    """Two-sided permutation p for cubic_residual_spearman (permute y, recompute)."""
    d = np.asarray(d, float); y = np.asarray(y, float); control = np.asarray(control, float)
    obs = abs(cubic_residual_spearman(d, y, control, degree))
    rng = np.random.default_rng(seed)
    count = sum(abs(cubic_residual_spearman(d, rng.permutation(y), control, degree)) >= obs - 1e-12
                for _ in range(n_perm))
    return (1 + count) / (n_perm + 1)


# ---------------------------------------------------------------- mediation
def _standardize(a):
    a = np.asarray(a, float)
    s = a.std()
    return (a - a.mean()) / s if s > 0 else a - a.mean()


def rank_mediation(d, y, m):
    """Rank-based mediation: decompose total d->y effect into direct + indirect (via m=loss).

    Variables are rank-transformed then standardized; coefficients via OLS. Returns
    {a, b, direct (c'), indirect (a*b), total, prop_mediated}. prop_mediated is the
    fraction of the total effect carried by the mediator (loss). NaN if total ~ 0.
    """
    rd = _standardize(_rankdata(d)); ry = _standardize(_rankdata(y)); rm = _standardize(_rankdata(m))
    # a: m ~ d  (standardized -> a = corr(d, m))
    a = float((rd * rm).mean())
    # y ~ d + m
    X = np.column_stack([rd, rm, np.ones_like(rd)])
    coef, *_ = np.linalg.lstsq(X, ry, rcond=None)
    cprime, b = float(coef[0]), float(coef[1])
    indirect = a * b
    total = cprime + indirect
    prop = float(indirect / total) if abs(total) > 1e-9 else float("nan")
    return {"a": a, "b": b, "direct": cprime, "indirect": indirect,
            "total": total, "prop_mediated": prop}


def mediation_stat(d, y, m, key):
    """Scalar accessor for bootstrap_ci over a chosen mediation component."""
    return rank_mediation(d, y, m)[key]
