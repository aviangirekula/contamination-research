# Controls Report — R6 (circularity) + R1/R2/R7/strata

**Date:** 2026-06-19. **Pre-registration:** `docs/pre_analysis.md` (written before any control was
run; only the listed tests were run). **Data:** existing Pythia-160m item set, N=300 Pile members,
leakage outcome = `frac_extracted`. CPU, seed 0, bootstrap/permutation n=2000. Integrity check: the
recomputed raw ρ (loss 0.275, Min-K% 0.173, Min-K%++ 0.108, zlib 0.177) exactly match the prior
correlation run — same scores, no drift.

## Master table — raw vs. partial(|loss) vs. semipartial vs. freq-matched vs. deduped

**Non-deduped (`pythia-160m`):**

| Detector | raw ρ | partial ρ \| loss [95% CI] | semipartial | ρ \| freq (control freq) | freq-matched ρ (n=100) | Kendall τ | BH-q | reject null? |
|---|---|---|---|---|---|---|---|---|
| loss | **+0.275** | — (is the control) | — | — | — | 0.211 | — | — |
| Min-K% | +0.173 | **−0.178 [−0.280, −0.068]** | −0.171 | +0.166 | +0.090 | 0.132 | 0.0045 | **yes (negative)** |
| Min-K%++ | +0.108 | **−0.148 [−0.259, −0.030]** | −0.143 | +0.138 | +0.016 | 0.082 | 0.011 | **yes (negative)** |
| zlib | +0.177 | −0.042 [−0.160, +0.075] | −0.041 | +0.193 | +0.086 | 0.136 | 0.463 | no (≈0) |

**Deduped (`pythia-160m-deduped`) — robustness (R2):**

| Detector | raw ρ | partial ρ \| loss [95% CI] | Kendall τ | BH-q | reject null? |
|---|---|---|---|---|---|
| loss | +0.316 | — | 0.244 | — | — |
| Min-K% | +0.221 | −0.133 [−0.239, −0.011] | 0.168 | 0.033 | yes (negative) |
| Min-K%++ | +0.161 | −0.141 [−0.252, −0.028] | 0.122 | 0.033 | yes (negative) |
| zlib | +0.220 | −0.016 [−0.125, +0.094] | 0.169 | 0.753 | no (≈0) |

## R2 — deduplication (membership separation, Pile train-vs-val, N=464)
| Detector | AUC non-deduped | AUC deduped |
|---|---|---|
| loss | 0.454 | 0.452 |
| Min-K% | 0.470 | 0.467 |
| Min-K%++ | 0.490 | 0.481 |
| zlib | 0.484 | 0.485 |

Membership separation is at chance with or without deduplication — the chance-level result is not a
dedup artifact.

## Stratification — per-domain LOSS↔leakage ρ (n≥5)
Heterogeneous, not driven by one domain: strongly positive in templated/structured domains
(Github +0.60, StackExchange +0.54, Books3 +0.41, ArXiv +0.38, OpenWebText2 +0.31), near-zero in
several (DM Mathematics +0.00, OpenSubtitles +0.01), and **negative** in others (PubMed Abstracts
−0.48, USPTO −0.19, HackerNews −0.09; EuroParl −0.66 at n=6). The pooled loss effect is a mix; the
positive pooled value reflects the structured/boilerplate domains where greedy extraction is easy.

## R1 — frequency
Controlling for the frequency proxy leaves the raw correlations essentially unchanged
(partial ρ\|freq: Min-K% +0.166, Min-K%++ +0.138, zlib +0.193 ≈ their raw values). So **frequency is
not the driver.** (The middle-tertile freq-matched subset shows lower ρ, but that is a low-power,
variance-restricted n=100 cut, not a clean frequency effect.) The operative confounder is LOSS, not
frequency.

## R7 — zero-robustness
Kendall τ-b agrees with Spearman in sign and relative magnitude throughout (loss highest at 0.211;
calibrated detectors lower), so the zero-inflated outcome is not creating the pattern.

---

## VERDICT (R6) — pre-registered decision rule applied honestly

**The contamination→leakage headline does NOT survive controlling for LOSS. The positive
association was carried entirely by raw loss.**

- The pre-registered "survives" condition required a calibrated detector (Min-K%, Min-K%++, or zlib)
  to predict leakage **beyond loss** — i.e. a partial ρ\|loss with CI excluding 0 in the **positive**
  direction. None does. zlib collapses to ≈0 (ρ=−0.04, n.s.). Min-K% and Min-K%++ are FDR-significant
  but **negative** (ρ=−0.18 and −0.15): once loss is held fixed, they are if anything *inversely*
  related to extraction. So the pre-registered "MOSTLY LOSS / must be reframed" branch is the outcome.
- This is **robust to deduplication** (deduped arm shows the identical pattern) and **not explained by
  frequency** (controlling frequency leaves raw ρ intact; controlling loss removes/flips it) **or by
  the zero-inflated outcome** (Kendall agrees).
- Interpretation: the only contamination/membership signal that predicts extraction is **raw LOSS
  itself**, which is the most mechanistically entangled-with-extraction measure (both are
  likelihood/greedy-decode memorization proxies). The sophisticated reference-free detectors the
  field prefers (Min-K%, Min-K%++, zlib) add **no independent** leakage-prediction over loss.

### Recommended reframing (for human review — NOT yet written into the paper)
The honest, defensible claim is narrower than the original headline: *"A model's per-item loss
predicts how extractable that item is; calibrated reference-free membership detectors do not add
predictive value beyond loss, and the loss–extraction link is domain-dependent and partly
mechanistic."* Whether to (a) frame loss–extraction as the result with the circularity stated openly,
(b) re-test at larger scale where extraction is less degenerate (it may change), or (c) pivot the
contribution toward the **evaluation-matrix** angle (detectors disagree / calibration removes
leakage signal — itself a finding) is a decision for Professor Lin.

**STOP. Awaiting human review of this report before any paper writing, assembly, or scale-up.**
