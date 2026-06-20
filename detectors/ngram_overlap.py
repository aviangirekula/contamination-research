"""Corpus-side n-gram contamination check (Brown et al. 2020, GPT-3, App. C).

This is NOT a per-token membership detector and does NOT use a language model. It is the
*data-side* contamination test: given access to a (training) corpus, build an index of all
length-``n`` n-grams it contains, then for any candidate text report the fraction of the
candidate's n-grams that already appear in that index. GPT-3 used 13-gram overlap to flag
benchmark examples that had leaked into the training crawl.

Because it interrogates the corpus rather than the model, it deliberately does NOT implement
the :class:`~detectors.base.Detector` ABC (which is bound to a ``ModelScorer`` and consumes
``TokenStats``). It has its own honest interface: ``build_index`` then ``score`` /
``contains_overlap``.

Tokenization choice
-------------------
The default tokenizer is **whitespace splitting** (``text.split()``). This is simple,
model-free, reproducible, and matches the spirit of the GPT-3 word-level n-gram filter. It is
*not* lowercased or punctuation-stripped, so the check is case- and punctuation-sensitive; a
caller wanting looser matching should normalize texts before passing them in.

A tokenizer-based variant (e.g. feeding a model's BPE token ids instead of whitespace words)
would make the n-grams align with the units the model actually sees and is the right choice
when reproducing a specific model's contamination report. To use it, pass a ``tokenize``
callable ``str -> list[str]`` at construction (e.g. one wrapping a HF tokenizer's
``.tokenize``); the index/scoring logic is identical. Whitespace is the documented default.
"""
from __future__ import annotations

from typing import Callable, Iterable, List, Sequence, Set, Tuple


def _whitespace_tokenize(text: str) -> List[str]:
    """Split on runs of whitespace (the documented default tokenizer)."""
    return text.split()


def _ngrams(tokens: Sequence[str], n: int) -> List[Tuple[str, ...]]:
    """All contiguous length-``n`` n-grams of ``tokens`` (empty if fewer than n tokens)."""
    if len(tokens) < n:
        return []
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


class NGramOverlapDetector:
    """Fraction-of-n-grams-seen-in-corpus contamination check.

    Parameters
    ----------
    n : int
        n-gram length. Default 13 (the GPT-3 value).
    tokenize : Callable[[str], list[str]] | None
        Tokenizer mapping a string to a list of string tokens. Defaults to whitespace
        splitting (see module docstring). Pass a HF-tokenizer wrapper for a token-level
        variant.

    Usage
    -----
    >>> det = NGramOverlapDetector(n=3)
    >>> det.build_index(["the quick brown fox jumps over the lazy dog"])
    >>> det.score("the quick brown fox")        # all 3-grams seen -> 1.0
    1.0
    >>> det.score("completely unrelated text here")   # none seen -> 0.0
    0.0
    """

    def __init__(self, n: int = 13, tokenize: Callable[[str], List[str]] | None = None):
        if n < 1:
            raise ValueError("n must be >= 1")
        self.n = n
        self.tokenize = tokenize or _whitespace_tokenize
        self._index: Set[Tuple[str, ...]] = set()
        self._built = False

    def build_index(self, corpus_texts: Iterable[str]) -> "NGramOverlapDetector":
        """Store the set of all n-grams occurring in ``corpus_texts``.

        Idempotent-ish: may be called more than once; each call *adds* to the index, so a
        corpus can be streamed in chunks. Returns ``self`` for chaining.
        """
        for text in corpus_texts:
            self._index.update(_ngrams(self.tokenize(text), self.n))
        self._built = True
        return self

    @property
    def index_size(self) -> int:
        """Number of distinct n-grams currently in the index."""
        return len(self._index)

    def score(self, text: str) -> float:
        """Fraction of ``text``'s n-grams that appear in the corpus index, in [0, 1].

        Returns 0.0 when ``text`` is shorter than ``n`` tokens (no n-grams to match), which
        is the conservative "no detected overlap" answer for too-short inputs.
        """
        if not self._built:
            raise ValueError("build_index(...) must be called before score(...)")
        grams = _ngrams(self.tokenize(text), self.n)
        if not grams:
            return 0.0
        hits = sum(1 for g in grams if g in self._index)
        return hits / len(grams)

    def contains_overlap(self, text: str, threshold: float = 0.0) -> bool:
        """True iff the overlap fraction for ``text`` exceeds ``threshold``.

        With the default ``threshold=0.0`` this flags any text sharing at least one n-gram
        with the corpus (the strict GPT-3-style "any 13-gram match is contamination" rule).
        Raise the threshold to require a larger contaminated fraction.
        """
        return self.score(text) > threshold
