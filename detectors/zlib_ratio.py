"""zlib-entropy ratio (Carlini et al. 2021, USENIX Security).

Score = - (summed NLL of the text under the model) / (zlib-compressed size in bits).
The zlib size estimates the text's intrinsic entropy, so dividing calibrates away
"text that is simply predictable/compressible to any model" -- the cheapest control
for the string-frequency confound. Members have low model loss relative to their
intrinsic entropy => low ratio => high (negated) score.
"""
from __future__ import annotations

import zlib

import numpy as np

from .base import Detector, TokenStats


def zlib_bits(text: str) -> int:
    """Length in bits of the zlib-compressed UTF-8 encoding of ``text``."""
    compressed = zlib.compress(text.encode("utf-8"))
    return len(compressed) * 8


class ZlibRatioDetector(Detector):
    name = "zlib_ratio"
    access = "gray-box"

    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        nll_sum_nats = -float(np.sum(stats.token_logprob))  # summed NLL (nats)
        bits = max(1, zlib_bits(text))
        return -(nll_sum_nats / bits)  # higher => member-like
