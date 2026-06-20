"""Validate the metrics layer against closed-form / hand-computable cases."""
import numpy as np
import pytest

from eval.metrics import (
    auc_roc,
    bootstrap_ci,
    mia_report,
    roc_curve,
    spearman,
    tpr_at_fpr,
    _rankdata,
)


def test_auc_perfect_separation():
    scores = np.array([0.1, 0.2, 0.9, 1.0])
    y = np.array([0, 0, 1, 1])
    assert auc_roc(scores, y) == pytest.approx(1.0)


def test_auc_perfectly_wrong():
    scores = np.array([0.9, 1.0, 0.1, 0.2])
    y = np.array([0, 0, 1, 1])
    assert auc_roc(scores, y) == pytest.approx(0.0)


def test_auc_tie_is_half():
    # all identical scores -> AUC 0.5 (mid-rank handling)
    scores = np.array([0.5, 0.5, 0.5, 0.5])
    y = np.array([0, 1, 0, 1])
    assert auc_roc(scores, y) == pytest.approx(0.5)


def test_auc_known_value():
    # positives at ranks giving U = 3 of 4 pairs concordant -> 0.75
    scores = np.array([0.2, 0.4, 0.3, 0.5])
    y = np.array([0, 1, 0, 1])  # pos={0.4,0.5}, neg={0.2,0.3}
    # pairs: (0.4>0.2),(0.4>0.3),(0.5>0.2),(0.5>0.3) all concordant -> 1.0
    assert auc_roc(scores, y) == pytest.approx(1.0)


def test_tpr_at_fpr_monotone():
    rng = np.random.default_rng(0)
    pos = rng.normal(2.0, 1.0, 500)
    neg = rng.normal(0.0, 1.0, 500)
    scores = np.r_[pos, neg]
    y = np.r_[np.ones(500), np.zeros(500)]
    t01 = tpr_at_fpr(scores, y, 0.001)
    t1 = tpr_at_fpr(scores, y, 0.01)
    t10 = tpr_at_fpr(scores, y, 0.1)
    assert 0.0 <= t01 <= t1 <= t10 <= 1.0


def test_roc_endpoints():
    scores = np.array([0.1, 0.2, 0.9, 1.0])
    y = np.array([0, 0, 1, 1])
    fpr, tpr, _ = roc_curve(scores, y)
    assert fpr[0] == pytest.approx(0.0) and tpr[0] == pytest.approx(0.0)
    assert fpr[-1] == pytest.approx(1.0) and tpr[-1] == pytest.approx(1.0)


def test_rankdata_ties():
    a = np.array([1.0, 2.0, 2.0, 3.0])
    # ranks: 1, 2.5, 2.5, 4
    assert np.allclose(_rankdata(a), [1.0, 2.5, 2.5, 4.0])


def test_spearman_monotonic():
    x = np.arange(10.0)
    y = 2 * x + 1
    assert spearman(x, y) == pytest.approx(1.0)
    assert spearman(x, -y) == pytest.approx(-1.0)


def test_mia_report_fields():
    rng = np.random.default_rng(1)
    scores = np.r_[rng.normal(3, 1, 200), rng.normal(0, 1, 200)]
    y = np.r_[np.ones(200), np.zeros(200)]
    rep = mia_report(scores, y)
    assert rep.n_pos == 200 and rep.n_neg == 200
    assert 0.5 < rep.auc <= 1.0


def test_bootstrap_ci_brackets_point_estimate():
    rng = np.random.default_rng(2)
    scores = np.r_[rng.normal(2, 1, 300), rng.normal(0, 1, 300)]
    y = np.r_[np.ones(300), np.zeros(300)]
    point = auc_roc(scores, y)
    lo, hi = bootstrap_ci(auc_roc, scores, y, n_boot=300, seed=3)
    assert lo <= point <= hi


def test_metrics_reject_degenerate():
    with pytest.raises(ValueError):
        auc_roc(np.array([1.0, 2.0]), np.array([1, 1]))  # no negatives
