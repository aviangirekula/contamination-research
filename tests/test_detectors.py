"""Detector unit tests: interface, validation, and known-positive/known-negative separation."""
import numpy as np
import pytest

from detectors import (
    LossDetector,
    MinKProbDetector,
    MinKPlusPlusDetector,
    MockScorer,
    ZlibRatioDetector,
    build_default_detectors,
    zlib_bits,
)
from detectors.base import TokenStats, bottom_k_indices


def test_bottom_k_indices_selects_smallest():
    v = np.array([5.0, 1.0, 4.0, 2.0, 3.0])
    idx = bottom_k_indices(v, 40.0)  # ceil(0.4*5)=2 -> the two smallest (1.0, 2.0)
    assert set(v[idx]) == {1.0, 2.0}


def test_bottom_k_always_at_least_one():
    v = np.array([3.0, 1.0, 2.0])
    assert len(bottom_k_indices(v, 1.0)) == 1


def test_tokenstats_validation():
    with pytest.raises(ValueError):
        TokenStats(np.array([1.0]), np.array([1.0, 2.0]), np.array([1.0]))
    with pytest.raises(ValueError):
        TokenStats(np.array([]), np.array([]), np.array([]))


def test_detectors_return_floats():
    scorer = MockScorer()
    for det in build_default_detectors(scorer):
        s = det.score("the quick brown fox jumps over the lazy dog")
        assert isinstance(s, float) and np.isfinite(s)


def test_minkpp_uses_mu_sigma():
    # Two stats with identical token_logprob but different mu/sigma must score differently.
    lp = np.array([-1.0, -2.0, -3.0, -4.0])
    a = TokenStats(lp, mu=np.full(4, -5.0), sigma=np.full(4, 1.0))
    b = TokenStats(lp, mu=np.full(4, -5.0), sigma=np.full(4, 2.0))
    det = MinKPlusPlusDetector(k_percent=50.0)
    assert det.score_from_stats(a, "x") != det.score_from_stats(b, "x")


def test_zlib_bits_positive():
    assert zlib_bits("hello world") > 0


def _separation_auc(detector_cls, signal=2.0, n=300):
    from eval.metrics import auc_roc

    members = {f"member sequence number {i} with content" for i in range(n)}
    membership_fn = lambda t: t in members  # noqa: E731
    scorer = MockScorer(membership_fn=membership_fn, signal=signal)
    det = detector_cls(scorer)
    texts = list(members) + [f"heldout non member text item {i}" for i in range(n)]
    y = [1] * n + [0] * n
    scores = [det.score(t) for t in texts]
    return auc_roc(np.array(scores), np.array(y))


@pytest.mark.parametrize("cls", [LossDetector, MinKProbDetector])
def test_separation_above_chance(cls):
    # With an injected membership signal, log-prob-based detectors must separate.
    assert _separation_auc(cls) > 0.75


def test_zlib_separation_above_chance():
    assert _separation_auc(ZlibRatioDetector) > 0.6
