# Statistical Hardening Report (St) — non-linear loss control + mediation

**Date:** 2026-06-20. Pre-registered: `docs/pre_analysis.md` (Round 2, St; incl. the 2026-06-20
amendment swapping cubic-residualization to PRIMARY after synthetic validation). Data: cached
per-example scores `results/controls_scores_pythia-160m{,-deduped}.jsonl`, N=300 Pile members, no
new inference. Seed 0, bootstrap/permutation n=2000. Outcome = `frac_extracted`; control = `loss`.

## Headline
**The Round-1 negative result survives a non-linear loss control and a formal mediation analysis.**
No calibrated detector predicts leakage beyond loss; the contamination→leakage association is
loss-mediated, with detector direct effects null-to-negative. The result is NOT a linearity artifact.

## St-1 — non-linear loss control (PRIMARY = cubic-residual; SECONDARY = decile)
Spearman ρ(detector, frac_extracted) under progressively stricter loss control. Cubic CI = bootstrap
95%; BH-q over the 3 cubic-residual permutation p-values (confirmatory family).

**Non-deduped (`pythia-160m`):**
| Detector | zero-order ρ | linear partial ρ\|loss | **cubic-residual ρ [95% CI]** | decile ρ (coarse) | BH-q |
|---|---|---|---|---|---|
| Min-K% | +0.173 | −0.178 | **−0.110 [−0.234, −0.002]** | −0.111 | 0.058 |
| Min-K%++ | +0.108 | −0.148 | **−0.160 [−0.287, −0.041]** | −0.109 | **0.015** |
| zlib | +0.177 | −0.042 | −0.052 [−0.165, +0.068] | −0.018 | 0.331 |

**Deduped (`pythia-160m-deduped`, robustness):**
| Detector | zero-order ρ | linear partial ρ\|loss | cubic-residual ρ [95% CI] | decile ρ | BH-q |
|---|---|---|---|---|---|
| Min-K% | +0.221 | −0.133 | −0.101 [−0.222, +0.011] | −0.069 | 0.084 |
| Min-K%++ | +0.161 | −0.141 | −0.111 [−0.241, +0.004] | −0.099 | 0.084 |
| zlib | +0.220 | −0.016 | −0.018 [−0.134, +0.108] | +0.041 | 0.719 |

**St-1 verdict (pre-registered decision rule):** REVIVED detectors = **NONE** in either arm (no
calibrated detector has a positive cubic-residual ρ with CI excluding 0 and FDR-significant). The
positive zero-order correlations collapse to ≈0 or significantly negative under the clean non-linear
control. The Round-1 finding is **confirmed not to be a linearity artifact.** Min-K%++ remains
significantly negative (FDR-sig) non-deduped; effects attenuate but never reverse sign on deduped.

## St-1b — collinearity diagnostic (reviewer concern W3; `results/collinearity_pythia-160m.json`)
The calibrated detectors are deterministic transforms of the same per-token log-probabilities as
loss, hence collinear with it: Spearman ρ(loss,·) = **0.90** (Min-K%), **0.74** (Min-K%++), **0.74**
(zlib); VIF = **6.2 / 2.6 / 2.4**; condition number of [loss, detector] = 4.8 / 2.9 / 2.7.
**Implication:** the strongest negative partial (Min-K%, VIF 6.2) is consistent with a *suppression
artifact* of near-collinearity, not substantive inverse prediction. We therefore claim only the
conservative result — the calibrated detectors carry **no positive** leakage signal independent of
loss — and do NOT assert they negatively predict leakage. Min-K%++/zlib (VIF < 3) are less
collinearity-confounded; their residuals are null/near-null. Mediation (St-2) is reported descriptively
for the same reason. Power: with N=300 and a near-degenerate outcome (3/300), the analysis is
well-powered only for moderate-to-large positive residuals; a small positive effect at scale is not
excluded (→ GPU).

## St-2 — formal mediation (loss as mediator), non-deduped [DESCRIPTIVE]
Rank-based decomposition of the total detector→leakage effect into direct + indirect (through loss).
| Detector | total [95% CI] | direct (c′) [95% CI] | indirect (loss-mediated) [95% CI] |
|---|---|---|---|
| Min-K% | +0.173 [0.061, 0.285] | **−0.394 [−0.622, −0.151]** | **+0.567 [0.352, 0.770]** |
| Min-K%++ | +0.108 [−0.010, 0.220] | **−0.213 [−0.377, −0.044]** | **+0.321 [0.195, 0.451]** |
| zlib | +0.177 [0.063, 0.295] | −0.061 [−0.233, +0.108] | **+0.238 [0.113, 0.369]** |

**Interpretation:** for every calibrated detector the **indirect (loss-mediated) effect is
significantly positive**, while the **direct effect is null (zlib) or significantly negative**
(Min-K%, Min-K%++). This is *inconsistent / suppression* mediation: loss accounts for **more than
100%** of the positive total association (hence the >1 "proportion mediated" point estimates), and
the detectors' own residual contribution is null-to-negative. This is a stronger statement than
"fully mediated": the calibrated detectors carry **no** independent positive leakage signal, and
Min-K%/Min-K%++ carry a small negative one. (Per pre-registration, the proportion-mediated scalar is
not reported as a clean fraction because the direct/total signs differ; we report direct/indirect/
total with CIs instead.)

## St-3 — per-domain breakdown (descriptive; low per-domain power)
Spearman ρ(·, frac_extracted) within Pile domains with n≥10 (non-deduped). The loss↔leakage link is
strongly **heterogeneous** and detectors track loss within domains:
| Domain | n | loss | Min-K% | Min-K%++ | zlib |
|---|---|---|---|---|---|
| Github | 21 | +0.598 | +0.530 | +0.378 | +0.429 |
| StackExchange | 21 | +0.544 | +0.589 | +0.589 | +0.602 |
| ArXiv | 14 | +0.382 | +0.362 | −0.122 | +0.323 |
| NIH ExPorter | 13 | +0.321 | +0.395 | −0.074 | +0.124 |
| Wikipedia (en) | 19 | +0.302 | +0.083 | −0.187 | +0.032 |
| OpenWebText2 | 27 | +0.306 | +0.092 | +0.067 | +0.075 |
| PubMed Central | 15 | +0.253 | +0.265 | +0.359 | −0.018 |
| Enron Emails | 13 | +0.171 | +0.018 | +0.132 | +0.533 |
| Pile-CC | 26 | +0.154 | +0.014 | +0.047 | +0.298 |
| FreeLaw | 17 | +0.092 | −0.065 | +0.192 | +0.143 |
| DM Mathematics | 13 | +0.003 | −0.059 | +0.138 | −0.235 |
| OpenSubtitles | 13 | +0.009 | −0.142 | −0.104 | −0.309 |
| HackerNews | 13 | −0.093 | −0.070 | −0.421 | −0.387 |
| YoutubeSubtitles | 11 | −0.095 | −0.164 | −0.140 | −0.394 |
| USPTO Backgrounds | 17 | −0.190 | −0.020 | −0.130 | −0.079 |
| PubMed Abstracts | 21 | −0.484 | −0.597 | −0.588 | −0.475 |

**Reading (honest):** the loss↔extraction correlation is strongest in templated/structured domains
(GitHub +0.60, StackExchange +0.54) and reverses in some prose/abstract domains (PubMed Abstracts
−0.48). Detectors mostly co-move with loss within a domain rather than adding independent signal.
**Caveat:** per-domain n is small (11–27), so these are directional, not powered estimates; no
per-domain FDR claim is made. NOTE: this per-domain heterogeneity concerns the detector↔*extraction*
correlation, which is a different axis than the detector-vs-loss *membership-AUC* domain effect
reported by Chen/Han/Miyao (arXiv:2412.13475); the relationship is suggestive and will be tied to
that literature only as far as Subagent N's verification supports (do not overclaim corroboration).

## Artifacts
`results/hardening_pythia-160m.json`, `results/hardening_pythia-160m-deduped.json`,
`figures/hardening_pythia-160m_forest.png` (zero-order vs linear-partial vs cubic-residual, with CIs).
Reproduce: `python scripts/hardening_160m.py --scores results/controls_scores_pythia-160m.jsonl --tag pythia-160m`.
