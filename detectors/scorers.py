"""Concrete `ModelScorer` implementations.

`HFScorer`   -- real causal LM via Hugging Face transformers (used for Pythia/OLMo).
`MockScorer` -- deterministic, torch-free; lets the whole pipeline + tests run on CPU
                with no model download. Useful for CI and for milestone-0 validation.
"""
from __future__ import annotations

import hashlib

import numpy as np

from .base import ModelScorer, TokenStats


class HFScorer(ModelScorer):
    """Per-token statistics from a Hugging Face causal LM.

    Parameters
    ----------
    model_name : str
        e.g. "EleutherAI/pythia-160m".
    revision : str | None
        Pinned model revision (commit hash / step tag) for reproducibility.
    device : str
        "cpu", "cuda", or "mps".
    max_length : int
        Truncate inputs to this many tokens (memory bound; mu/sigma are O(vocab) per pos).
    """

    def __init__(
        self,
        model_name: str,
        revision: str | None = None,
        device: str = "cpu",
        max_length: int = 1024,
    ):
        # Lazy imports so importing this module (and running mock tests) needs no torch.
        import torch  # noqa: F401
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.model_name = model_name
        self.revision = revision
        self.device = device
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, revision=revision)
        self.model.to(device).eval()

    def score_tokens(self, text: str) -> TokenStats:
        import torch

        enc = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
        )
        input_ids = enc["input_ids"].to(self.device)
        if input_ids.shape[1] < 2:
            raise ValueError("text must tokenize to >= 2 tokens to be scored")

        with torch.no_grad():
            logits = self.model(input_ids).logits[0]  # (seq, vocab)
            logprobs = torch.log_softmax(logits.float(), dim=-1)  # (seq, vocab)

        # logits at position j predict token j+1 (standard causal shift).
        pred = logprobs[:-1]                  # (seq-1, vocab)
        targets = input_ids[0, 1:]            # (seq-1,)
        token_logprob = pred.gather(1, targets.unsqueeze(1)).squeeze(1)  # (seq-1,)
        mu = pred.mean(dim=-1)                # (seq-1,)
        sigma = pred.std(dim=-1)              # (seq-1,)

        return TokenStats(
            token_logprob=token_logprob.cpu().numpy().astype(np.float64),
            mu=mu.cpu().numpy().astype(np.float64),
            sigma=sigma.cpu().numpy().astype(np.float64),
        )


class MockScorer(ModelScorer):
    """Deterministic, torch-free scorer for tests / CI / dry-runs.

    Generates reproducible per-token statistics from a hash of the text. An optional
    `membership_fn(text) -> bool` lets tests simulate a separating signal: "member"
    texts get systematically higher token log-probs (lower loss), mimicking the
    train/non-train separation the real pipeline measures.
    """

    def __init__(self, vocab_size: int = 50_304, membership_fn=None, signal: float = 1.0):
        self.vocab_size = vocab_size
        self.membership_fn = membership_fn
        self.signal = signal

    def _rng(self, text: str) -> np.random.Generator:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(h[:8], "little")
        return np.random.default_rng(seed)

    def score_tokens(self, text: str) -> TokenStats:
        rng = self._rng(text)
        n = max(2, min(256, len(text.split()) + 5))
        # Baseline: log-probs of realized tokens are mildly negative.
        base = -rng.gamma(shape=2.0, scale=1.0, size=n)
        if self.membership_fn is not None and self.membership_fn(text):
            base = base + self.signal  # members: higher log-prob (lower loss)
        # mu/sigma summarize a plausible vocab log-prob distribution at each position.
        mu = -np.log(self.vocab_size) + rng.normal(0, 0.5, size=n)
        sigma = rng.uniform(1.5, 3.0, size=n)
        return TokenStats(
            token_logprob=base.astype(np.float64),
            mu=mu.astype(np.float64),
            sigma=sigma.astype(np.float64),
        )
