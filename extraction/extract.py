"""Extractable (prefix-continuation) memorization (Carlini et al. 2023).

A string s is *extractable with k tokens of context* if a length-k prefix p drawn
from a training sequence [p || s] makes the model greedily regenerate s. The
**extraction rate** -- fraction of sampled sequences that are extractable -- is the
concrete leakage outcome we correlate against per-item contamination scores.

This module defines the metric and a model-agnostic harness; the greedy-generation
backend is injected (HF-backed for real runs, a stub for tests), so the logic is
unit-testable without a GPU.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


@dataclass
class ExtractionResult:
    extracted: bool          # did greedy continuation exactly match the held suffix?
    prefix_len: int          # k, tokens of context
    suffix_len: int          # tokens the model had to reproduce
    matched_tokens: int      # length of the matching prefix of the continuation


#: a GreedyGenerator maps (prefix_token_ids, n_new_tokens) -> generated_token_ids
GreedyGenerator = Callable[[Sequence[int], int], Sequence[int]]


def is_extractable(
    token_ids: Sequence[int],
    prefix_len: int,
    generate: GreedyGenerator,
) -> ExtractionResult:
    """Test whether [prefix || suffix] is extractable from `generate` given `prefix_len`.

    Splits ``token_ids`` at ``prefix_len``; the suffix is the target to reproduce.
    Exact-match extraction (the strict definition) is reported, alongside the count of
    leading matched tokens (a softer signal useful for the correlation analysis).
    """
    token_ids = list(token_ids)
    if not (0 < prefix_len < len(token_ids)):
        raise ValueError("prefix_len must satisfy 0 < prefix_len < len(token_ids)")
    prefix = token_ids[:prefix_len]
    suffix = token_ids[prefix_len:]
    gen = list(generate(prefix, len(suffix)))[: len(suffix)]
    matched = 0
    for a, b in zip(suffix, gen):
        if a == b:
            matched += 1
        else:
            break
    return ExtractionResult(
        extracted=(matched == len(suffix)),
        prefix_len=prefix_len,
        suffix_len=len(suffix),
        matched_tokens=matched,
    )


def extraction_rate(results: Sequence[ExtractionResult]) -> float:
    """Fraction of sampled sequences that were exactly extractable."""
    if not results:
        return 0.0
    return float(np.mean([r.extracted for r in results]))


def fractional_extraction(results: Sequence[ExtractionResult]) -> np.ndarray:
    """Per-item matched-token fraction in [0, 1] (soft leakage signal for correlation)."""
    return np.array(
        [r.matched_tokens / r.suffix_len if r.suffix_len else 0.0 for r in results],
        dtype=np.float64,
    )


def hf_greedy_generator(model_name: str, revision: str | None = None, device: str = "cpu") -> GreedyGenerator:
    """Build an HF-backed greedy generator (lazy import; not needed for tests)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_name, revision=revision)
    model = AutoModelForCausalLM.from_pretrained(model_name, revision=revision).to(device).eval()

    def generate(prefix_ids, n_new):
        ids = torch.tensor([list(prefix_ids)], device=device)
        with torch.no_grad():
            out = model.generate(
                ids,
                max_new_tokens=n_new,
                do_sample=False,
                num_beams=1,
                pad_token_id=tok.eos_token_id,
            )
        return out[0, len(prefix_ids):].tolist()

    return generate
