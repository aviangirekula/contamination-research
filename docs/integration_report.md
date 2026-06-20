# Integration Report — Headline result + consistency round

**Date:** 2026-06-19. **Repo:** `~/contamination-research`. **Model this round:** Pythia-160m, CPU.

## Headline (the thesis as a number)
On real Pythia-160m, the contamination/membership score **significantly predicts extraction/
leakage** even though membership *separation* is at chance on the confound-clean split:

| | clean-split membership AUC | leakage correlation ρ [95% CI] |
|---|---|---|
| loss | 0.454 (chance) | **0.275 [0.164, 0.378]** ✅ |
| min_20_prob | 0.470 (chance) | 0.173 [0.061, 0.285] ✅ |
| zlib_ratio | 0.484 (chance) | 0.177 [0.063, 0.295] ✅ |
| min_20_plusplus | 0.490 (chance) | 0.108 [−0.010, 0.220] ✗ |

This is the contamination→memorization→leakage link, with CIs, on ground-truth Pile members.
Full numbers in `docs/results_table.md`; figure `figures/correlation_pythia-160m_scatter.png`.

## What is now publishable-strength
- **The confound-clean control (R3).** WikiMIA's 0.52–0.56 collapses to chance (0.45–0.49) on the
  same-distribution Pile train-vs-val split. Directly pre-empts "your MIA is just distribution
  shift." Strong, reviewer-ready.
- **The headline correlation with CIs (R4/R5).** Real, significant for 3/4 detectors, length- and
  seed-controlled, bootstrap CIs.
- **Methods↔paper consistency.** All 8 evaluated methods (LOSS, Min-K%, Min-K%++, zlib, n-gram,
  Oren, extractable memorization, Enron PII) are implemented, tested (46/46), and run; everything
  else is framed in the paper as "related, not evaluated." Spine rule holds.
- **Lit review.** background/related_work/evaluation/introduction finalized to S&P standard,
  datasets table rendered, all [VERIFY] debts cleared (lone exception: BLOOM's 392-author cite,
  intentional). MIA lineage + DP-defense subsections added.
- **Reproducibility.** Pinned `requirements.txt`, `configs/*.yaml`, one-command scripts, fixed
  seeds, public datasets, committed repo.

## What still needs the GPU scale-up (honestly NOT yet shown)
- **R6 — headline circularity (TOP priority).** LOSS↔extraction partly co-measure memorization.
  Must add the **partial correlation controlling for raw LOSS** to show Min-K%/zlib retain
  predictive power. Until then, scope the claim. This is a CPU-doable analysis, not a compute gate
  — next on the list.
- **R7 — zero-inflated outcome.** 3/300 fully extracted; ρ leans on few points. Larger models
  extract more (Carlini 2023) → de-degenerates the outcome. Add Kendall τ.
- **R9 — PII not demonstrated.** 0.0 verbatim PII leakage at 160m. The "PII exposure" limb is a
  designed capability with a null result at 160m; claim only when measured at scale.
- **Clean-split scaling.** Does the membership signal revive at 1.4B/2.8B on the *clean* split?
  WikiMIA AUC rises with scale (zlib 0.564→0.616 at 1.4B) but that split is confounded.
- **R2 — dedup ablation** (pythia-160m-deduped) and **R8 — Oren at real benchmark scale.**

## Compute posture
Everything is a single `--model` flag away from GPU scale-up (`configs/pythia1.4b_gpu.yaml`).
2.8B on CPU declined this round (prohibitively slow, out of the 160m/CPU scope).

## Round DONE-criteria status
1. ✅ Real contamination↔leakage correlation with CIs + master table + ROC/scatter figures.
2. ✅ n-gram + Oren implemented, tested, run.
3. ✅ related_work/background/evaluation/introduction finalized; described == implemented; [VERIFY] cleared.
4. ✅ Pinned env + one-command repro + committed repo.
5. ✅ Reviewer log R1–R9 (R3/R4/R5 resolved; R1/R2 partial; R6/R7/R8/R9 open with actions).
6. ✅ This report.

**Single most important next step:** the R6 partial-correlation control (CPU-doable), then the
GPU scale-up to revive the clean-split signal and actually observe PII leakage.
