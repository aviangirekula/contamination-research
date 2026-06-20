"""LOSS / Perplexity-threshold membership inference (Yeom et al. 2018).

Score = negative mean per-token NLL = mean token log-prob. Members (training data)
tend to have lower loss => higher (less negative) mean log-prob => higher score.
This is the mandatory baseline that anchors the overfitting <-> privacy connection.
"""
from __future__ import annotations

import numpy as np

from .base import Detector, TokenStats


class LossDetector(Detector):
    name = "loss"
    access = "gray-box"

    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        # mean log p(x_t | x_<t) ; equals -cross_entropy ; higher => member-like
        return float(np.mean(stats.token_logprob))


class PerplexityDetector(Detector):
    """Same ranking as LossDetector, reported as -perplexity for interpretability."""

    name = "perplexity"
    access = "gray-box"

    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        ce = -float(np.mean(stats.token_logprob))  # cross-entropy (nats)
        return -float(np.exp(ce))  # -perplexity ; higher => member-like
