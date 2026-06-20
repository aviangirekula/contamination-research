"""Milestone-0 end-to-end check: the contamination<->leakage correlation analysis wiring.

Synthetic items are given a latent 'contamination strength'. A detector signal and an
extraction outcome are both generated as noisy monotone functions of that strength.
The test asserts the headline analysis (Spearman rho between detector score and
extraction) recovers a strong positive correlation -- i.e. the harness is wired
correctly. This is NOT a scientific result; it validates the pipeline plumbing.
"""
import numpy as np

from detectors import LossDetector, MinKProbDetector, MinKPlusPlusDetector, ZlibRatioDetector
from detectors.base import TokenStats
from eval.metrics import spearman, spearman_ci


def test_contamination_leakage_correlation_wiring():
    rng = np.random.default_rng(7)
    n = 200
    strength = rng.uniform(0, 1, n)  # latent contamination strength per item

    detectors = [LossDetector(), MinKProbDetector(), MinKPlusPlusDetector(), ZlibRatioDetector()]
    det_scores = {d.name: [] for d in detectors}
    extraction_frac = []

    for s in strength:
        ntok = 40
        # stronger contamination => higher token log-probs (lower loss)
        lp = -rng.gamma(2.0, 1.0, ntok) + 3.0 * s
        mu = np.full(ntok, -11.0) + rng.normal(0, 0.3, ntok)
        sigma = rng.uniform(1.5, 3.0, ntok)
        stats = TokenStats(lp, mu, sigma)
        for d in detectors:
            det_scores[d.name].append(d.score_from_stats(stats, "x" * ntok))
        # stronger contamination => more tokens extractable
        extraction_frac.append(np.clip(s + rng.normal(0, 0.15), 0, 1))

    extraction_frac = np.array(extraction_frac)
    for name, scores in det_scores.items():
        rho = spearman(np.array(scores), extraction_frac)
        assert rho > 0.4, f"{name}: weak correlation {rho:.3f}"

    lo, hi = spearman_ci(np.array(det_scores["loss"]), extraction_frac, n_boot=300)
    assert lo > 0.0  # CI excludes zero
