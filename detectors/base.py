"""Core abstractions shared by all detectors.

Design: a single forward pass over a text produces a `TokenStats` object holding
everything every detector needs (per-token log-prob of the realized token, plus the
mean/std of the log-prob distribution over the full vocabulary at each position).
Detectors are pure functions of `TokenStats` (+ the raw text, for zlib). This means:

  * one model forward pass feeds ALL detectors (the runner exploits this), and
  * detectors are unit-testable with a `MockScorer` and need no GPU / model download.

All scores follow the convention: **higher => more "member-like"** (more likely to be
in the training corpus). See ../docs/glossary.md for the formal definitions.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass

import numpy as np


@dataclass
class TokenStats:
    """Per-token statistics from one forward pass of a causal LM over a text.

    All arrays have length ``n_tokens`` = (number of scored tokens) = (sequence
    length - 1), since the first token has no preceding context to be predicted from.

    Attributes
    ----------
    token_logprob : np.ndarray, shape (n,)
        log p_theta(x_t | x_{<t}) for each realized token x_t (natural log).
    mu : np.ndarray, shape (n,)
        E_{z ~ vocab} [ log p_theta(z | x_{<t}) ] : mean over the full vocabulary of
        the next-token log-probabilities at each position. Needed by Min-K%++.
    sigma : np.ndarray, shape (n,)
        Std over the full vocabulary of log p_theta(. | x_{<t}). Needed by Min-K%++.
    """

    token_logprob: np.ndarray
    mu: np.ndarray
    sigma: np.ndarray

    def __post_init__(self) -> None:
        n = len(self.token_logprob)
        if not (len(self.mu) == len(self.sigma) == n):
            raise ValueError("token_logprob, mu, sigma must have equal length")
        if n == 0:
            raise ValueError("TokenStats requires at least one scored token")

    @property
    def n_tokens(self) -> int:
        return len(self.token_logprob)


class ModelScorer(abc.ABC):
    """Produces `TokenStats` for a text under a target language model."""

    @abc.abstractmethod
    def score_tokens(self, text: str) -> TokenStats:  # pragma: no cover - interface
        ...


class Detector(abc.ABC):
    """Uniform detector interface: ``score(text) -> float`` (higher = member-like).

    A detector is bound to a `ModelScorer` at construction. For efficiency the runner
    calls `score_from_stats` with a `TokenStats` computed once and shared across all
    detectors; `score(text)` is the convenience path that computes stats internally.
    """

    name: str = "detector"
    #: minimum adversary access tier this detector needs (see threat model)
    access: str = "gray-box"

    def __init__(self, scorer: ModelScorer | None = None):
        self.scorer = scorer

    @abc.abstractmethod
    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        ...

    def score(self, text: str) -> float:
        if self.scorer is None:
            raise ValueError(f"{self.name}: no scorer bound; pass scorer= at construction")
        return self.score_from_stats(self.scorer.score_tokens(text), text)


def bottom_k_indices(values: np.ndarray, k_percent: float) -> np.ndarray:
    """Indices of the ``ceil(k% * n)`` smallest entries (the Min-K% selection rule).

    At least one token is always selected. ``k_percent`` is in (0, 100].
    """
    if not (0 < k_percent <= 100):
        raise ValueError("k_percent must be in (0, 100]")
    n = len(values)
    k = max(1, int(np.ceil((k_percent / 100.0) * n)))
    # argpartition is O(n); we only need the set of k smallest, order within is irrelevant.
    return np.argpartition(values, k - 1)[:k]
