"""Contamination / membership detectors with a uniform ``score(text) -> float`` API.

All scores follow the convention: higher => more likely a training-set member.
See ../docs/method_selection_memo.md for why these four were selected.
"""
from .base import Detector, ModelScorer, TokenStats, bottom_k_indices
from .loss import LossDetector, PerplexityDetector
from .mink import MinKProbDetector
from .minkpp import MinKPlusPlusDetector
from .ngram_overlap import NGramOverlapDetector
from .oren_permutation import OrenPermutationTest, OrenResult
from .scorers import HFScorer, MockScorer
from .zlib_ratio import ZlibRatioDetector, zlib_bits

#: registry used by the runner / CLI
DETECTOR_REGISTRY = {
    "loss": LossDetector,
    "perplexity": PerplexityDetector,
    "min_k_prob": MinKProbDetector,
    "min_k_plusplus": MinKPlusPlusDetector,
    "zlib_ratio": ZlibRatioDetector,
}


def build_default_detectors(scorer: ModelScorer):
    """The shortlisted *per-text membership* detector suite, bound to a scorer.

    NOTE: this suite intentionally EXCLUDES NGramOverlapDetector and OrenPermutationTest.
    Those two are not per-token membership detectors over a single text -- the n-gram check is
    corpus-side (no model) and the Oren test is a dataset-level permutation test over an
    *ordered set* of examples -- so they have their own honest interfaces (build_index/score
    and test(...)) and must be constructed and called directly, not run through this suite.
    """
    return [
        LossDetector(scorer),
        MinKProbDetector(scorer, k_percent=20.0),
        MinKPlusPlusDetector(scorer, k_percent=20.0),
        ZlibRatioDetector(scorer),
    ]


#: Corpus-/dataset-level contamination tests that are NOT part of the per-text membership
#: suite above. They do not share the Detector/TokenStats interface; see each class's docstring.
CONTAMINATION_TESTS = {
    "ngram_overlap": NGramOverlapDetector,
    "oren_permutation": OrenPermutationTest,
}


__all__ = [
    "Detector",
    "ModelScorer",
    "TokenStats",
    "bottom_k_indices",
    "LossDetector",
    "PerplexityDetector",
    "MinKProbDetector",
    "MinKPlusPlusDetector",
    "ZlibRatioDetector",
    "zlib_bits",
    "HFScorer",
    "MockScorer",
    "DETECTOR_REGISTRY",
    "build_default_detectors",
    # corpus-/dataset-level contamination tests (separate interfaces)
    "NGramOverlapDetector",
    "OrenPermutationTest",
    "OrenResult",
    "CONTAMINATION_TESTS",
]
