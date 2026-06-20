"""Extraction-harness tests using stub greedy generators (no model needed)."""
import numpy as np
import pytest

from extraction import (
    extraction_rate,
    fractional_extraction,
    is_extractable,
)


def perfect_generator(full_sequence):
    """A generator that perfectly reproduces the held suffix (memorized case)."""
    def generate(prefix_ids, n_new):
        return full_sequence[len(prefix_ids): len(prefix_ids) + n_new]
    return generate


def garbage_generator(prefix_ids, n_new):
    return [999_999] * n_new  # never matches


def test_perfect_extraction():
    seq = [10, 11, 12, 13, 14, 15]
    r = is_extractable(seq, prefix_len=3, generate=perfect_generator(seq))
    assert r.extracted is True
    assert r.matched_tokens == 3 and r.suffix_len == 3


def test_no_extraction():
    seq = [10, 11, 12, 13, 14, 15]
    r = is_extractable(seq, prefix_len=3, generate=garbage_generator)
    assert r.extracted is False
    assert r.matched_tokens == 0


def test_partial_extraction_counts_prefix():
    seq = [1, 2, 3, 4, 5, 6]
    # generator matches first suffix token then diverges
    def gen(prefix_ids, n_new):
        return [4, 0, 0][:n_new]
    r = is_extractable(seq, prefix_len=3, generate=gen)
    assert r.extracted is False
    assert r.matched_tokens == 1
    assert fractional_extraction([r])[0] == pytest.approx(1 / 3)


def test_extraction_rate_mix():
    seq = [10, 11, 12, 13, 14, 15]
    results = [
        is_extractable(seq, 3, perfect_generator(seq)),
        is_extractable(seq, 3, garbage_generator),
    ]
    assert extraction_rate(results) == pytest.approx(0.5)


def test_invalid_prefix_len():
    with pytest.raises(ValueError):
        is_extractable([1, 2, 3], prefix_len=0, generate=garbage_generator)
    with pytest.raises(ValueError):
        is_extractable([1, 2, 3], prefix_len=3, generate=garbage_generator)
