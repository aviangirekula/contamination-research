# Contamination Matrix (Mx) — model-free n-gram + Oren permutation (small scale)

**Date:** 2026-06-20. Pre-registered: `docs/pre_analysis.md` (Round 2, Mx). Seed 0, Pythia-160m, CPU.
Run: `python scripts/contamination_matrix.py --model EleutherAI/pythia-160m --device cpu`.
Raw: `results/contamination_matrix.json`.

Loaders used (verified at runtime): MMLU = `cais/mmlu` config `all` test (14,042 items; 500 sampled;
text = question+choices); GSM8K = `openai/gsm8k` main test (1,319; 500 sampled; text = question);
HumanEval = `openai_humaneval` test (164; all; text = prompt).

## Mx-1 — n-gram/substring overlap vs the Pile (SCALE-INVARIANT method, but LOWER-BOUND reference)
Reference index = `NeelNanda/pile-10k` (10,000 docs; 13-gram index 8.84M grams, 8-gram 8.83M).
**Caveat (pre-registered):** this is a *sample* of the Pile (~210M docs), so the numbers below are a
**loose LOWER BOUND** on true benchmark↔Pile overlap, not a contamination rate of the full corpus. A
full-Pile index (infra-gated, not model-gated) is required for a real rate.

| Benchmark | items | 13-gram rate | 13-gram mean frac | 8-gram rate | 8-gram mean frac | 8-gram max frac |
|---|---|---|---|---|---|---|
| MMLU | 500 | 0.2% (1) | 0.0003 | 0.8% (4) | 0.0005 | 0.21 |
| GSM8K | 500 | 0.0% (0) | 0.000 | 0.0% (0) | 0.000 | 0.00 |
| HumanEval | 164 | 0.0% (0) | 0.000 | 1.8% (3) | 0.0004 | 0.03 |

**Reading (honest):** against a 10k-doc Pile sample, measured overlap is near-zero for all three
benchmarks. This is expected from the sample size and is **uninformative about true contamination** —
it only certifies that overlap is *at least* this much. The method is scale-invariant; the *reference*
is the bottleneck. Do not report these as contamination rates.

## Mx-2 — Oren permutation/exchangeability test (UNDERPOWERED at 160m; GPU-gated)
Pythia-160m, n_permutations=1000, k=30 items/benchmark, 20 words/item. One-sided p = fraction of
random orderings whose concatenation log-likelihood ≥ the canonical order's.

| Benchmark | p-value | canonical LL | null mean ± std |
|---|---|---|---|
| MMLU | 0.001 | −2894.9 | −2975.4 ± 17.7 |
| GSM8K | 0.013 | −2974.4 | −3020.5 ± 21.4 |
| HumanEval | 0.875 | −2152.8 | −2125.7 ± 23.4 |

**Reading (honest, pre-registered):** MMLU and GSM8K show the canonical order favored beyond chance
(p<0.05) even at 160m; HumanEval does not. **We draw NO contamination conclusion from this.** The test
is membership-based and run at sanity scale (small k, smallest model, single seed of the permutation
null), and is subject to an orientation/ordering artifact (a benchmark whose canonical concatenation
is simply more fluent than a shuffle can score low p without training-time contamination). It is
flagged **GPU-gated**: a real benchmark-contamination claim requires larger models, larger k, and a
fluency-control baseline. Reported here only to upgrade the earlier 10-example sanity demo (R8) and to
exercise the harness end-to-end.

## Matrix cell status
| Cell | Scale-invariant? | Status |
|---|---|---|
| n-gram overlap (method) | yes | computed; **reference is a lower-bound sample** → needs full-Pile index |
| Oren permutation | no (membership-based) | computed at 160m; **underpowered, GPU-gated, no conclusion** |
