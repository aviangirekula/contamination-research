"""Unit tests for the corpus-side n-gram overlap check and the Oren permutation test.

These two contamination tests have their own interfaces (not the Detector/TokenStats ABC),
so they are tested separately from the per-text membership detectors in test_detectors.py.
"""
import numpy as np
import pytest

from detectors import NGramOverlapDetector, OrenPermutationTest, MockScorer
from detectors.base import ModelScorer, TokenStats


# --------------------------------------------------------------------------------------
# n-gram overlap
# --------------------------------------------------------------------------------------

CORPUS = [
    "the quick brown fox jumps over the lazy dog near the old stone bridge today",
    "a completely separate document about machine learning and data contamination metrics",
]


def test_substring_text_scores_high():
    det = NGramOverlapDetector(n=3).build_index(CORPUS)
    # An exact contiguous slice of a corpus document: every 3-gram is in the index.
    sub = "the quick brown fox jumps over the lazy dog"
    assert det.score(sub) == pytest.approx(1.0)
    assert det.contains_overlap(sub)


def test_disjoint_text_scores_zero():
    det = NGramOverlapDetector(n=3).build_index(CORPUS)
    disjoint = "zebra penguin orbit saxophone volcano umbrella"
    assert det.score(disjoint) == pytest.approx(0.0)
    assert not det.contains_overlap(disjoint)


def test_partial_overlap_is_fractional():
    det = NGramOverlapDetector(n=3).build_index(CORPUS)
    # 4 tokens -> two 3-grams. "the quick brown" is in corpus; "quick brown zzz" is not.
    text = "the quick brown zzz"
    assert det.score(text) == pytest.approx(0.5)


def test_text_shorter_than_n_scores_zero():
    det = NGramOverlapDetector(n=13).build_index(CORPUS)
    # Fewer than n tokens -> no n-grams -> conservative 0.0, no crash.
    assert det.score("only five tokens here now") == 0.0
    assert det.score("") == 0.0


def test_default_n_is_13():
    assert NGramOverlapDetector().n == 13


def test_score_before_build_raises():
    det = NGramOverlapDetector(n=3)
    with pytest.raises(ValueError):
        det.score("anything at all here")


def test_index_can_be_built_in_chunks():
    det = NGramOverlapDetector(n=2)
    det.build_index(["alpha beta gamma"])
    det.build_index(["gamma delta epsilon"])
    # n-grams from both chunks are present.
    assert det.score("alpha beta") == pytest.approx(1.0)
    assert det.score("delta epsilon") == pytest.approx(1.0)


def test_custom_tokenizer_variant():
    # Token-level variant note: a caller can inject any str->list[str] tokenizer.
    det = NGramOverlapDetector(n=2, tokenize=lambda s: list(s.replace(" ", "")))
    det.build_index(["abc"])
    assert det.score("abc") == pytest.approx(1.0)  # char bigrams "ab","bc" both seen


# --------------------------------------------------------------------------------------
# Oren permutation test
# --------------------------------------------------------------------------------------


class CanonicalFavoringScorer(ModelScorer):
    """Deterministic scorer that rewards one specific concatenation (the canonical order).

    Simulates a model that memorized the canonical ordering: the canonical concatenation gets
    a high total log-likelihood; every other ordering gets a lower (more negative) baseline.
    Per-token logprobs are returned (one per whitespace token) so summing them gives the
    sequence log-likelihood the Oren test consumes.
    """

    def __init__(self, examples, sep="\n"):
        self._canonical_text = sep.join(examples)

    def score_tokens(self, text: str) -> TokenStats:
        n = max(2, len(text.split()))
        per_token = 0.0 if text == self._canonical_text else -2.0
        lp = np.full(n, per_token, dtype=np.float64)
        mu = np.full(n, -10.0)
        sigma = np.full(n, 2.0)
        return TokenStats(lp, mu, sigma)


def test_oren_canonical_favored_gives_small_p():
    examples = ["first example text", "second example text", "third example text",
                "fourth example text", "fifth example text"]
    scorer = CanonicalFavoringScorer(examples)
    test = OrenPermutationTest(scorer)
    res = test.test(examples, n_permutations=200, seed=0)
    # Canonical is strictly above every permutation -> p = 1/(N+1), clearly significant.
    assert res["p_value"] < 0.05
    assert res["canonical_loglik"] > res["null_mean"]


def test_oren_exchangeable_gives_nonsignificant_p():
    # MockScorer scores each ordering independently of any "true" order: no canonical signal.
    # Use distinct example tokens so permutations produce genuinely varied concatenations.
    examples = [f"example number {i} body content alpha" for i in range(6)]
    scorer = MockScorer()
    test = OrenPermutationTest(scorer)
    res = test.test(examples, n_permutations=300, seed=1)
    # No order memorization -> canonical is a typical draw -> p should not be significant.
    assert res["p_value"] > 0.05


def test_oren_p_value_in_unit_interval_and_reproducible():
    examples = ["alpha beta", "gamma delta", "epsilon zeta", "eta theta"]
    scorer = MockScorer()
    t = OrenPermutationTest(scorer)
    r1 = t.test(examples, n_permutations=100, seed=7)
    r2 = t.test(examples, n_permutations=100, seed=7)
    assert 0.0 < r1["p_value"] <= 1.0
    assert r1 == r2  # deterministic given seed


def test_oren_requires_two_examples():
    scorer = MockScorer()
    t = OrenPermutationTest(scorer)
    with pytest.raises(ValueError):
        t.test(["only one example"], n_permutations=10)
