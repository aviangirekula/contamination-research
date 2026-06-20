"""Integrity tests for the controls statistics (constructed cases with known answers)."""
import numpy as np
import pytest

from eval.partial import (
    benjamini_hochberg,
    kendall_tau,
    partial_spearman,
    semipartial_spearman,
    spearman,
)


def test_partial_collapses_when_signal_is_only_through_z():
    # x and y are correlated ONLY through a common cause z -> partial(x,y|z) ~ 0.
    rng = np.random.default_rng(0)
    z = rng.normal(size=2000)
    x = z + 0.3 * rng.normal(size=2000)
    y = z + 0.3 * rng.normal(size=2000)
    assert spearman(x, y) > 0.6           # strong raw correlation
    assert abs(partial_spearman(x, y, z)) < 0.1   # collapses controlling z


def test_partial_survives_when_x_has_independent_signal():
    # y depends on z AND on an x-specific signal -> partial(x,y|z) stays positive.
    rng = np.random.default_rng(1)
    z = rng.normal(size=2000)
    xsig = rng.normal(size=2000)
    x = xsig
    y = z + xsig + 0.3 * rng.normal(size=2000)
    assert partial_spearman(x, y, z) > 0.4


def test_semipartial_between_zero_and_raw():
    rng = np.random.default_rng(2)
    z = rng.normal(size=1500)
    x = z + 0.5 * rng.normal(size=1500)
    y = z + 0.5 * rng.normal(size=1500)
    raw = abs(spearman(x, y))
    sp = abs(semipartial_spearman(x, y, z))
    assert sp <= raw + 1e-9


def test_kendall_monotonic():
    x = np.arange(20.0)
    assert kendall_tau(x, 2 * x + 1) == pytest.approx(1.0)
    assert kendall_tau(x, -x) == pytest.approx(-1.0)


def test_kendall_handles_ties():
    x = np.array([1, 1, 2, 2, 3, 3.0])
    y = np.array([1, 2, 2, 3, 3, 4.0])
    tau = kendall_tau(x, y)
    assert -1.0 <= tau <= 1.0 and tau > 0


def test_bh_basic():
    # one tiny p among large ones -> at least the smallest is rejected
    rejected, q = benjamini_hochberg([0.001, 0.5, 0.6, 0.9], alpha=0.05)
    assert rejected[0] and not rejected[3]
    assert np.all((q >= 0) & (q <= 1))


def test_bh_all_null():
    rejected, q = benjamini_hochberg([0.4, 0.5, 0.9], alpha=0.05)
    assert not rejected.any()
