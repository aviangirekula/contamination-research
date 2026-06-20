"""Min-K% Prob (Shi et al. 2024, ICLR).

Average the log-probabilities of the k% lowest-probability tokens. Intuition: a
non-member is more likely to contain a few very-low-probability ("surprising") tokens,
so the mean over the worst k% separates members (higher) from non-members (lower).
Reference-free; needs only per-token log-probabilities (gray-box).
"""
from __future__ import annotations

import numpy as np

from .base import Detector, TokenStats, bottom_k_indices


class MinKProbDetector(Detector):
    name = "min_k_prob"
    access = "gray-box"

    def __init__(self, scorer=None, k_percent: float = 20.0):
        super().__init__(scorer)
        self.k_percent = k_percent
        self.name = f"min_{int(k_percent)}_prob"

    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        lp = stats.token_logprob
        idx = bottom_k_indices(lp, self.k_percent)
        return float(np.mean(lp[idx]))  # higher => member-like
