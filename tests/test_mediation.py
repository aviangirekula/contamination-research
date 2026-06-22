"""Integrity tests for St hardening statistics (constructed cases with known answers)."""
import numpy as np
import pytest

from eval.mediation import (
    cubic_residual_spearman,
    decile_stratified_spearman,
    rank_mediation,
    stratified_permutation_p,
)
from eval.partial import spearman


def test_decile_strat_reduces_linear_confound():
    # y and d correlated ONLY through control. Decile stratification is COARSE: it strongly
    # REDUCES the confound (from ~0.7 raw) but, with 10 bins, leaves residual within-bin
    # confounding (~0.18). This is exactly why cubic residualization is the PRIMARY control.
    rng = np.random.default_rng(0)
    c = rng.normal(size=3000)
    d = c + 0.3 * rng.normal(size=3000)
    y = c + 0.3 * rng.normal(size=3000)
    raw = abs(spearman(d, y))
    dec = abs(decile_stratified_spearman(d, y, c, n_bins=10))
    assert raw > 0.6 and dec < 0.30 and dec < raw / 2   # reduces a lot, not fully

def test_cubic_fully_removes_linear_confound():
    # The PRIMARY control removes the linear confound cleanly (residual ~ 0).
    rng = np.random.default_rng(0)
    c = rng.normal(size=3000)
    d = c + 0.3 * rng.normal(size=3000)
    y = c + 0.3 * rng.normal(size=3000)
    assert abs(cubic_residual_spearman(d, y, c)) < 0.12


def test_decile_strat_survives_with_independent_signal():
    rng = np.random.default_rng(1)
    c = rng.normal(size=3000)
    xsig = rng.normal(size=3000)
    d = xsig
    y = c + xsig + 0.3 * rng.normal(size=3000)
    assert decile_stratified_spearman(d, y, c, n_bins=10) > 0.3


def test_decile_strat_survives_nonlinear_control():
    # control affects y NON-linearly; linear partial would leak, decile strat should not.
    rng = np.random.default_rng(2)
    c = rng.uniform(-3, 3, size=4000)
    d = c + 0.3 * rng.normal(size=4000)
    y = c**2 + 0.3 * rng.normal(size=4000)  # nonlinear in c, no independent d signal
    assert abs(decile_stratified_spearman(d, y, c, n_bins=10)) < 0.15


def test_stratified_perm_p_detects_and_nulls():
    rng = np.random.default_rng(3)
    c = rng.normal(size=600)
    xsig = rng.normal(size=600)
    y = c + xsig
    p_sig = stratified_permutation_p(xsig, y, c, n_bins=5, n_perm=500, seed=0)
    p_null = stratified_permutation_p(rng.normal(size=600), y, c, n_bins=5, n_perm=500, seed=0)
    assert p_sig < 0.05 and p_null > 0.05


def test_cubic_residual_removes_nonlinear_control():
    rng = np.random.default_rng(4)
    c = rng.uniform(-3, 3, size=3000)
    d = c + 0.3 * rng.normal(size=3000)
    y = c**2 + 0.3 * rng.normal(size=3000)
    assert abs(cubic_residual_spearman(d, y, c)) < 0.15


def test_mediation_full():
    # d -> m -> y, no direct path: prop_mediated ~ 1, direct ~ 0.
    rng = np.random.default_rng(5)
    d = rng.normal(size=4000)
    m = d + 0.3 * rng.normal(size=4000)
    y = m + 0.3 * rng.normal(size=4000)
    r = rank_mediation(d, y, m)
    assert r["total"] > 0.3
    assert abs(r["direct"]) < 0.1
    assert r["prop_mediated"] > 0.8


def test_mediation_none():
    # d -> y directly, m is independent noise: prop_mediated ~ 0.
    rng = np.random.default_rng(6)
    d = rng.normal(size=4000)
    m = rng.normal(size=4000)
    y = d + 0.3 * rng.normal(size=4000)
    r = rank_mediation(d, y, m)
    assert abs(r["prop_mediated"]) < 0.1
