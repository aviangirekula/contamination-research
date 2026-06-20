"""Min-K%++ (Zhang et al. 2025, ICLR Spotlight).

Improves Min-K% by z-scoring each token's log-prob against the *full* next-token
distribution at that position before taking the bottom-k% mean:

    z_t = ( log p(x_t | x_<t) - mu_t ) / sigma_t

where mu_t = E_{z in vocab}[log p(z | x_<t)] and sigma_t = std over the vocabulary.
Rationale: training samples sit at local maxima of the modeled distribution, so the
signal is how peaked the realized token is relative to the whole vocabulary, not its
raw probability. Requires the full next-token distribution => white-box logit access.
"""
from __future__ import annotations

import numpy as np

from .base import Detector, TokenStats, bottom_k_indices


class MinKPlusPlusDetector(Detector):
    name = "min_k_plusplus"
    access = "white-box"

    def __init__(self, scorer=None, k_percent: float = 20.0, eps: float = 1e-6):
        super().__init__(scorer)
        self.k_percent = k_percent
        self.eps = eps
        self.name = f"min_{int(k_percent)}_plusplus"

    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        z = (stats.token_logprob - stats.mu) / (stats.sigma + self.eps)
        idx = bottom_k_indices(z, self.k_percent)
        return float(np.mean(z[idx]))  # higher => member-like
