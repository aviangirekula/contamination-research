# findings.md — shared numbers ledger (orchestrator-owned)

**Rule:** every quantitative claim in the paper must trace to a row here, and every
row here must come from a harness run (or be explicitly marked as a literature value).
Nothing is "described that isn't measured." Update this file when results land.

## Status legend
- ⬜ planned / not yet run
- 🟡 mocked or tiny-scale (sanity only, not a paper number)
- ✅ real run, reproducible (seed + config + commit recorded)
- 📚 value cited from literature (not our measurement)

## Milestone 0 — code scaffold + tiny/mock validation
| Item | Status | Value | Source |
|---|---|---|---|
| Detector interface `score(text)->float` for LOSS, Min-K%, Min-K%++, zlib | 🟡 | unit-tested on a tiny random-init GPT-NeoX model | `tests/` |
| Metrics (AUC, TPR@FPR) numerically correct | 🟡 | validated vs. closed-form on synthetic scores | `tests/test_metrics.py` |

## Milestone 1 — first runnable (Pythia + WikiMIA in/out separation)
Run: `scripts/milestone1_wikimia.py --model EleutherAI/pythia-160m --length 64 --device cpu`,
WikiMIA-64, N=542 (284 member / 258 non-member), CPU, seed 0, bootstrap n=500.
Ground truth = WikiMIA (public; carries temporal confound) — MIMIR (confound-clean) is gated
and pending HF auth. Numbers are REAL but on the smallest model, so near-chance is expected.
| Item | Status | Value | Source |
|---|---|---|---|
| Pythia-160m loads, full pipeline runs end-to-end on real data | ✅ | 542 examples scored, 4 detectors | `results/wikimia64_pythia-160m.jsonl` |
| LOSS AUC | ✅ | 0.523 [0.477, 0.568] | `results/wikimia64_summary.json` |
| Min-K% AUC | ✅ | 0.539 [0.492, 0.585] | same |
| Min-K%++ AUC | ✅ | 0.545 [0.498, 0.592] | same |
| zlib AUC | ✅ | 0.564 [0.517, 0.610] | same |
| TPR@1% / TPR@0.1% (best: zlib / Min-K%++) | ✅ | ≤3.2% / ≤1.1% | same |
| Detector ordering matches theory (zlib/Min-K%++ > Min-K% > LOSS) | ✅ | yes | analysis |
| Separation is near-chance at 160m (consistent with Duan et al.) | ✅ | CIs span 0.5 | `duan2024mia` |
| Score-distribution + log-ROC plots | ✅ | `figures/milestone1_wikimia64_*.png` | — |

**Interpretation (honest):** the pipeline is validated (correct relative ordering, sensible
CIs, runs end-to-end on real data), but 160m barely separates members from non-members. This is
the EXPECTED result, not a failure: memorization scales with model size (`carlini2023quantifying`)
and MIAs are near-chance on small Pythia (`duan2024mia`). Demonstrating CLEAN separation requires
either (a) a larger Pythia (1.4B/2.8B) or (b) the confound-clean MIMIR splits. Both are gated on a
decision (compute was scoped to "160m only"; MIMIR needs HF auth).

## Milestone 1b — confound-controlled ground truth WITHOUT MIMIR (Pile train vs. val)
MIMIR is gated (HF auth unavailable). Built equivalent ground truth from public mirrors:
members = Pile *train* (`NeelNanda/pile-10k`), non-members = Pile *validation*
(`mit-han-lab/pile-val-backup`), stratified across 22 Pile subsets to match domain
distribution. Run: `scripts/milestone1_pile.py --model EleutherAI/pythia-160m --n-per-class 300
--max-words 100`. N=464 (232/232), CPU, seed 0, bootstrap n=500.
| Detector | Status | AUC [95% CI] | Source |
|---|---|---|---|
| loss | ✅ | 0.454 [0.407, 0.511] | `results/pilemia_pythia-160m_summary.json` |
| min_20_prob | ✅ | 0.470 [0.410, 0.530] | same |
| min_20_plusplus | ✅ | 0.490 [0.439, 0.546] | same |
| zlib_ratio | ✅ | 0.484 [0.437, 0.545] | same |

**KEY FINDING (headline-worthy controls result):** on the confound-clean same-distribution
split, ALL detectors are at **chance** at 160m (CIs straddle 0.5), whereas the same model on
**WikiMIA-64 scored AUC 0.52–0.56**. The WikiMIA "signal" was largely the temporal/topic
confound (members pre-cutoff vs non-members post-cutoff), not membership. This directly
reproduces and concretizes `duan2024mia`: apparent MIA success on LLMs is confound-driven, and
true membership signal is near-zero at small scale. Whether scale (1.4B/2.8B) revives it on the
clean split is the open scaling question (1.4B run in progress).
Artifacts: `figures/pilemia_pythia-160m_dists.png`, `figures/pilemia_pythia-160m_logroc.png`.

## Milestone 2 — contamination/membership score ↔ extraction/leakage
> ⚠️ **SUPERSEDED by R6 control (docs/controls_report.md).** The raw ρ below are loss-driven and
> do NOT survive controlling for loss (partial ρ|loss: Min-K% −0.18, Min-K%++ −0.15 FDR-sig
> negative; zlib ≈0). Keep these raw numbers only as the pre-control record; the operative
> finding is the loss/calibration divergence in the controls report.

Real Pythia-160m, CPU. N=300 Pile MEMBERS (canonical set `results/pile_items_160m.jsonl`),
prefix_len=32, suffix≤50, greedy extraction. Detector score (whole item) vs fractional
extraction; Spearman ρ + bootstrap CI (n=2000, seed 0). Run: `scripts/correlation_160m.py
--items results/pile_items_160m.jsonl`.
| Detector | ρ(frac) [95% CI] | ρ(extracted) | Significant |
|---|---|---|---|
| loss | **0.275 [0.164, 0.378]** | 0.172 | ✅ CI excludes 0 |
| min_20_prob | 0.173 [0.061, 0.285] | 0.171 | ✅ CI excludes 0 |
| zlib_ratio | 0.177 [0.063, 0.295] | 0.164 | ✅ CI excludes 0 |
| min_20_plusplus | 0.108 [-0.010, 0.220] | 0.169 | ✗ includes 0 |

**THESIS AS A NUMBER:** on the confound-clean split, membership *separation* is at chance
(AUC 0.45–0.49) yet membership *score still predicts leakage* (3/4 detectors, CI excludes 0).
Contamination signal tracks privacy leakage even where membership AUC looks useless. Honest
nuances: effect is weak-moderate (ρ 0.11–0.28), zero-inflated outcome (mean frac 0.037, 3/300
fully extracted); LOSS (crudest proxy) is the STRONGEST leakage predictor, Min-K%++ (best
membership detector) the weakest/non-significant. Artifacts: `figures/correlation_pythia-160m_scatter.png`,
`results/correlation_pythia-160m.json`. Scaling to 1.4B/2.8B (GPU) is a `--model` swap.

## Milestone 1c — supporting real-data results (160m unless noted)
| Measure | Value | Source |
|---|---|---|
| Extraction rate (exact full-suffix) | 0.0100 (3/300) | `results/pile_items_160m.jsonl` |
| Mean fractional extraction | 0.0370 | same |
| Enron-in-Pile PII: docs w/ PII in suffix | 8/36 | `results/pii_enron_160m.jsonl` |
| Enron-in-Pile PII: verbatim leakage rate | 0.0000 | same (aggregate; no PII strings stored) |
| n-gram(13) overlap: member vs non-member mean | 1.000 vs 0.022 (sep +0.978) | `scripts/validate_ngram_oren.py` |
| n-gram residual: non-members w/ some overlap | 3/44 (real train↔val near-dup leakage) | same |
| Oren permutation (10-ex sanity demo; SUPERSEDED by Mx below) | 0.044 vs 0.124 | same |
| Oren permutation @160m, real benchmarks (n_perm=1000, k=30) | MMLU 0.001 / GSM8K 0.013 / HumanEval 0.875 | `results/contamination_matrix.json` (GPU-gated, no conclusion) |
| n-gram(13) overlap rate vs 10k-Pile sample (lower bound) | MMLU 0.2% / GSM8K 0% / HumanEval 0% | same |
| WikiMIA-64 AUC scaling 160m→1.4B (zlib) | 0.564 → 0.616 | `results/wikimia64_summary.json` (1.4B), findings M1 (160m) |
| WikiMIA-64 AUC scaling 160m→1.4B (loss) | 0.523 → 0.571 | same |

## Literature anchor values (for calibration / sanity, NOT our results)
| Claim | Status | Value | Source |
|---|---|---|---|
| MIAs barely beat chance on pretrained LLMs (Pile/Pythia) | 📚 | AUC ≈ 0.5–0.6 | duan2024mia |
| Min-K% improves AUC over prior best on WikiMIA | 📚 | +7.4% AUC | shi2024detecting |
| Min-K%++ over runner-up (reference-free) on WikiMIA | 📚 | +6.2–10.5% AUROC | zhang2025minkpp |
| GPT-J memorizes ≥1% of the Pile (extractable) | 📚 | ≥1% | carlini2023quantifying |
| LiRA gain at low FPR vs. prior attacks | 📚 | ~10× TPR @ low FPR | carlini2022lira |

## Round 2 — St statistical hardening (docs/hardening_report.md; pre-registered)
Cached per-example data, N=300, no new inference. PRIMARY non-linear control = cubic-residual
(decile = coarse secondary). FDR over 3 cubic-residual permutation p-values.
| Detector | zero-order ρ | linear partial ρ\|loss | cubic-residual ρ [95% CI] | BH-q | mediation: direct \| indirect |
|---|---|---|---|---|---|
| Min-K% | +0.173 | −0.178 | −0.110 [−0.234, −0.002] | 0.058 | −0.394 [−0.62,−0.15] \| +0.567 [0.35,0.77] |
| Min-K%++ | +0.108 | −0.148 | −0.160 [−0.287, −0.041] | **0.015** | −0.213 [−0.38,−0.04] \| +0.321 [0.20,0.45] |
| zlib | +0.177 | −0.042 | −0.052 [−0.165, +0.068] | 0.331 | −0.061 [−0.23,+0.11] \| +0.238 [0.11,0.37] |

**Collinearity (W3, `results/collinearity_pythia-160m.json`):** detector~loss Spearman 0.90/0.74/0.74,
VIF 6.2/2.6/2.4 → Min-K%'s negative partial is a likely SUPPRESSION artifact; claim only "no positive
residual beyond loss," not "negatively predicts." Mediation reported descriptively, not causally.

**St VERDICT:** the negative/null SURVIVES the non-linear loss control — REVIVED detectors = NONE
(non-deduped AND deduped). Mediation: indirect (loss-mediated) effect significantly POSITIVE for all
three; direct effect null (zlib) or significantly NEGATIVE (Min-K%, Min-K%++) → inconsistent/
suppression mediation, loss carries >100% of the positive association. Robust to dedup. The
contamination→leakage link is loss, not the calibrated detectors — confirmed, not a linearity artifact.
Artifacts: `results/hardening_pythia-160m{,-deduped}.json`, `figures/hardening_pythia-160m_forest.png`.

## Novelty (docs/novelty_memo.md; Subagent N, web-verified)
Verdict: adjacent-but-distinct / novel framing+method (NOT reproduction). Added verified cites:
alsahili2025effectiveness (arXiv:2512.13352, closest prior work — ranking/AdaBoost "marginal gains",
NOT residualization), hayes2025strong (NeurIPS 2025, "Exploring the Limits of Strong MIA on LLMs";
MIA≠extraction via LiRA direct correlation), chen2025statistical (ACL 2025; detectors do not ROBUSTLY
beat loss — within-seed-variance; domain/token-diversity dependence), das2024blind, meeus2025sok.
[VERIFY] remaining: Chen ACL Anthology id, Das workshop proceedings string, carlini2023 verbatim def.

## Reviewer-concerns ledger (full log in docs/reviewer_concerns.md)
| # | Concern | Status | Resolution / evidence |
|---|---|---|---|
| R1 | Frequency confound | 🟡 partial | zlib (freq-calibrated) is at chance on clean split AND still predicts leakage; frequency-matched control still TODO |
| R2 | Dedup confound | 🟡 partial | found 3/44 residual train↔val overlap; deduped-Pythia ablation pending compute |
| R3 | Temporal/topic shift (WikiMIA) | ✅ resolved | clean Pile train-vs-val collapses WikiMIA's 0.52–0.56 to chance 0.45–0.49; headline uses clean set |
| R4 | No CIs / single-run | ✅ resolved | bootstrap CIs on all AUCs + headline ρ; significance via CI-excludes-0 |
| R5 | Length confound | ✅ resolved | clean split length-matched (max_words); correlation set fixed window |
| R6 | **Headline circularity (LOSS≈extraction)** | ⛔ RESOLVED — NEGATIVE (see docs/controls_report.md) | Partial ρ\|loss: Min-K% −0.178, Min-K%++ −0.148 (FDR-sig, NEGATIVE), zlib −0.04 (n.s.). Headline does NOT survive: positive signal was entirely LOSS; calibrated detectors add no independent leakage-prediction. Robust to dedup; not a frequency or zero-inflation artifact. Needs reframing. |
| R7 | Zero-inflated outcome | ❌ open | ρ leans on few high-frac items; scale up + report Kendall τ |
| R8 | Oren/n-gram power | ❌ open | Oren at sanity scale (10 ex); run on real benchmark orderings |
| R9 | PII not yet shown | ❌ open | 0.0 verbatim PII leakage at 160m — do NOT claim PII leak until measured at scale |
