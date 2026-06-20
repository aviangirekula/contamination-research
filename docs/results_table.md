# Master Results Table (preliminary, Pythia-160m / CPU)

All numbers are REAL runs on `EleutherAI/pythia-160m`, CPU, seed 0. Every cell traces to a
file in `results/`. Model size is a single `--model` flag, so 1.4B/2.8B on GPU is a config
swap. These are preliminary (smallest model); the scaling caveat is stated per result.

---

## Table 1 — Membership separation (AUC, TPR@low-FPR)

Two ground-truth constructions. **Pile train-vs-val** is confound-clean (members = Pile train
docs, non-members = Pile validation, stratified across 22 subsets). **WikiMIA** carries a known
temporal confound and is shown for contrast + scaling.

| Construction | Model | Detector | AUC [95% CI] | TPR@1% | TPR@0.1% |
|---|---|---|---|---|---|
| Pile train-vs-val (clean) | 160m | loss | 0.454 [0.407, 0.511] | 0.009 | 0.000 |
| Pile train-vs-val (clean) | 160m | min_20_prob | 0.470 [0.410, 0.530] | 0.009 | 0.000 |
| Pile train-vs-val (clean) | 160m | min_20_plusplus | 0.490 [0.439, 0.546] | 0.004 | 0.000 |
| Pile train-vs-val (clean) | 160m | zlib_ratio | 0.484 [0.437, 0.545] | 0.009 | 0.000 |
| WikiMIA-64 (confounded) | 160m | loss | 0.523 | 0.004 | 0.000 |
| WikiMIA-64 (confounded) | 160m | min_20_prob | 0.539 | 0.011 | 0.000 |
| WikiMIA-64 (confounded) | 160m | min_20_plusplus | 0.545 | 0.032 | 0.011 |
| WikiMIA-64 (confounded) | 160m | zlib_ratio | 0.564 | 0.021 | 0.007 |
| WikiMIA-64 (confounded) | **1.4B** | loss | 0.571 [0.526, 0.620] | 0.025 | 0.004 |
| WikiMIA-64 (confounded) | **1.4B** | min_20_prob | 0.580 [0.532, 0.625] | 0.025 | 0.011 |
| WikiMIA-64 (confounded) | **1.4B** | min_20_plusplus | 0.547 [0.497, 0.595] | 0.021 | 0.018 |
| WikiMIA-64 (confounded) | **1.4B** | zlib_ratio | 0.616 [0.565, 0.663] | 0.049 | 0.007 |

**Reading:** (i) on the clean split, 160m is at chance — the WikiMIA "signal" was mostly
temporal confound (key controls result, reproduces Duan et al. 2024); (ii) WikiMIA AUC rises
with scale (160m→1.4B), e.g. zlib 0.564→0.616 — memorization grows with model size
(Carlini et al. 2023). Whether the *clean-split* signal also revives at scale is the open
question for the GPU runs.

---

## Table 2 — HEADLINE: contamination score ↔ extraction/leakage (Spearman ρ)

Pythia-160m, N=300 Pile MEMBERS, detector score (whole item) vs fractional extraction
(prefix_len=32, suffix≤50, greedy). Bootstrap CI n=2000.

| Detector | ρ(frac) [95% CI] | ρ(extracted) | CI excludes 0? |
|---|---|---|---|
| **loss** | **0.275 [0.164, 0.378]** | 0.172 | ✅ |
| min_20_prob | 0.173 [0.061, 0.285] | 0.171 | ✅ |
| zlib_ratio | 0.177 [0.063, 0.295] | 0.164 | ✅ |
| min_20_plusplus | 0.108 [−0.010, 0.220] | 0.169 | ✗ |

> **⚠️ SUPERSEDED BY THE R6 CONTROL — read `docs/controls_report.md`.** These RAW correlations
> do not survive controlling for loss. Partial ρ(detector, leakage | loss): Min-K% −0.178,
> Min-K%++ −0.148 (both FDR-significant, NEGATIVE), zlib −0.04 (n.s.). The positive association
> above is carried ENTIRELY by raw loss; the calibrated detectors add no predictive value beyond
> it. Do not cite the raw numbers below as evidence that the calibrated detectors predict leakage.

**Reading (raw, pre-control):** even though membership *separation* is at chance on the clean
split (Table 1), the raw membership *score* correlates with leakage for 3/4 detectors. But this
is loss-driven (see the R6 control box above): LOSS predicts leakage; Min-K%/Min-K%++/zlib do not
beyond loss. Effect is weak (ρ 0.11–0.28), outcome zero-inflated (mean frac 0.037).
Figure: `figures/correlation_pythia-160m_scatter.png`.

---

## Table 3 — Extraction, PII, and contamination tests

| Measure | Value | Notes |
|---|---|---|
| Extraction rate (exact full suffix) | 0.0100 (3/300) | 160m, 32-tok prefix; expected-low for smallest model |
| Mean fractional extraction | 0.0370 | zero-inflated; 3 fully-extracted items are templated boilerplate |
| Enron-in-Pile: docs with PII in suffix | 8/36 | all `email` type; Enron Emails is a Pile subset (in training) |
| Enron-in-Pile: verbatim PII leakage rate | 0.0000 | aggregate only; 160m doesn't regurgitate the PII at 32-tok prefix |
| n-gram(13) overlap: member vs non-member | 1.000 vs 0.022 | corpus-side; separation +0.978 |
| n-gram(13): non-members with residual overlap | 3/44 | real Pile train↔val near-duplicate leakage |
| Oren permutation test: contaminated vs control p | 0.044 vs 0.124 | dataset-level; contaminated marginally significant, control not (10 short examples — sanity scale) |

---

## Figures produced
- `figures/correlation_pythia-160m_scatter.png` — contamination score vs. extraction (headline).
- `figures/pilemia_pythia-160m_dists.png`, `figures/pilemia_pythia-160m_logroc.png` — clean-split separation.
- `figures/milestone1_wikimia64_dists.png`, `figures/milestone1_wikimia64_logroc.png` — WikiMIA separation.

## Reproduce
```
python scripts/milestone1_pile.py   --model EleutherAI/pythia-160m   # Table 1 clean split
python scripts/milestone1_wikimia.py --model EleutherAI/pythia-160m   # Table 1 WikiMIA
python scripts/extraction_pile.py   --model EleutherAI/pythia-160m   # Table 3 + item set
python scripts/correlation_160m.py  --items results/pile_items_160m.jsonl  # Table 2 headline
python scripts/validate_ngram_oren.py --model EleutherAI/pythia-160m # Table 3 n-gram/Oren
python scripts/pii_enron.py         --model EleutherAI/pythia-160m   # Table 3 PII
```
**Scale-up:** change `--model` to `EleutherAI/pythia-1.4b` / `pythia-2.8b` on a GPU; no code change.
