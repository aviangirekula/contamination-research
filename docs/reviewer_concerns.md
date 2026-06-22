# Reviewer-Adversary Log (Subagent R)

Hostile S&P-style review of our OWN preliminary results (Pythia-160m). Each concern has a
status (✅ resolved / 🟡 partial / 🟡 GPU-gated / ❌ open), the evidence, and the action. The point is to
surface every confound before a real reviewer does. The most dangerous one is **R6** — read it.

> **RECONCILIATION (2026-06-20, Subagent C).** This log was written before the Round-1 controls
> (`docs/controls_report.md`) and Round-2 statistical hardening (`docs/hardening_report.md`) +
> contamination matrix (`docs/contamination_matrix.md`) runs. Statuses below have been UPDATED to
> reflect what is now DONE. Original prose is retained for history; the **STATUS / UPDATE** line on
> each concern is authoritative. Net: R3/R4/R5 resolved (unchanged); **R6 now RESOLVED** (negative,
> survives non-linear control + mediation); R1/R2/R7 addressed; R8/R9 GPU-gated.

---

### R1 — String-frequency confound 🟡 addressed
*"Your detector separates members by web-frequency, not membership."*
- Evidence: `zlib_ratio` explicitly calibrates for compressibility/frequency. On the clean
  split it is also at chance (AUC 0.484), and the raw leakage correlation is similar for it
  (ρ=0.177) — so the leakage link is not purely a frequency artifact.
- **STATUS / UPDATE (addressed, controls_report.md §R1):** a frequency proxy control was run.
  Controlling for the frequency proxy leaves the raw correlations essentially unchanged
  (partial ρ|freq: Min-K% +0.166, Min-K%++ +0.138, zlib +0.193 ≈ their raw values), so
  **frequency is NOT the driver** — the operative confounder is LOSS (R6), not frequency.
  (A middle-tertile freq-matched n=100 subset shows lower ρ, but it is a low-power,
  variance-restricted cut, not a clean frequency effect.) A full reference-LM-perplexity
  frequency-matched split remains a nice-to-have, hence "addressed" not fully "resolved."

### R2 — Deduplication confound 🟡 addressed
*"Duplication, not membership, drives the signal."*
- Evidence: n-gram check found 3/44 non-members with residual train↔val overlap (real
  near-dup). For the HEADLINE (members-only), duplication is part of the causal chain
  (duplication→memorization→extraction, Carlini 2023), not a confound to remove.
- **STATUS / UPDATE (addressed, controls_report.md §R2 + hardening_report.md):** the
  `pythia-160m-deduped` ablation was RUN. (a) Membership separation is at chance with or
  without dedup (deduped AUC: loss 0.452, Min-K% 0.467, Min-K%++ 0.481, zlib 0.485) — the
  chance-level result is not a dedup artifact. (b) The R6 partial-correlation pattern
  reproduces on the deduped model (partial ρ|loss: Min-K% −0.133, Min-K%++ −0.141, both
  FDR-sig negative; zlib −0.016 n.s.), and survives the non-linear control on the deduped arm
  too. Membership AUC unchanged; same negative pattern. Robust to deduplication.

### R3 — Temporal/topic confound ✅ resolved
*"Your MIA is just distribution shift (the WikiMIA artifact)."*
- Evidence: we built the confound-clean **Pile train-vs-val** split (same distribution,
  stratified across 22 subsets). The WikiMIA signal (AUC 0.52–0.56) **collapses to chance
  (0.45–0.49)** on the clean split, and the headline correlation uses the clean member set —
  not WikiMIA. This is our strongest control and pre-empts the objection directly.

### R4 — No confidence intervals / single-run estimates ✅ resolved
- Evidence: every AUC and the headline ρ carry bootstrap CIs (n=500–2000); significance is
  judged by CI-excludes-0. Seeds fixed (0).

### R5 — Length confound ✅ resolved
*"Members and non-members differ in length, not membership."*
- Evidence: clean split truncates to `max_words=100` (length-matched); the correlation set is
  a fixed window (prefix 32 + suffix ≤50 tokens) for every item, so length is held constant.

### R6 — Headline circularity / tautology ✅ RESOLVED (most important; resolved NEGATIVE)
*"LOSS = low per-token loss = memorized; extraction = greedy reproduction = memorized. Of
course they correlate. The headline is mechanically trivial."*
- This was the sharpest threat to the headline's INTERPRETATION, and it was partly fair.
- Honest position: LOSS and extraction are related but distinct (soft likelihood vs. hard
  greedy-decode match), and the security claim is that a *contamination/membership detector's
  score is a usable predictor of concrete leakage*, even when its membership *separation* is at
  chance. We must NOT frame this as a surprising independent discovery.
- The correlation also holds for `zlib_ratio` (frequency-calibrated) and `min_20_prob`, which
  are not raw loss — mild evidence it is not pure tautology.
- **STATUS / UPDATE (RESOLVED — negative; controls_report.md + hardening_report.md):** the
  pre-registered partial-correlation control was RUN, then HARDENED. The headline does NOT
  survive controlling for loss, and this is now confirmed three ways:
  1. **Linear partial ρ|loss** (controls_report.md): Min-K% −0.178, Min-K%++ −0.148 (both
     FDR-significant, NEGATIVE), zlib −0.042 (n.s.). No calibrated detector predicts leakage
     beyond loss; two are inversely related once loss is held fixed.
  2. **Non-linear loss control** (hardening_report.md): cubic-residual ρ Min-K% −0.110
     [−0.234, −0.002], Min-K%++ −0.160 [−0.287, −0.041] (BH-q 0.015), zlib −0.052 [−0.165,
     +0.068]; decile-stratified secondary agrees. REVIVED detectors = NONE. The result is
     **not a linearity artifact**, and Min-K%++ stays FDR-significant NEGATIVE.
  3. **Formal mediation** (hardening_report.md): for every calibrated detector the
     loss-mediated *indirect* effect is significantly positive while the *direct* effect is
     null (zlib) or significantly negative (Min-K%, Min-K%++) — inconsistent/suppression
     mediation; loss carries >100% of the positive association.
  Robust to deduplication (R2); not a frequency (R1) or zero-inflation (R7) artifact. The
  paper is reframed accordingly: contamination→leakage is loss-mediated; the calibrated
  reference-free detectors add no independent leakage-prediction. Resolved.

### R7 — Zero-inflated outcome 🟡 addressed
*"3/300 fully extracted, mean frac 0.037 — ρ is driven by a handful of points."*
- Evidence: scatter shows the high-frac points anchor the trend; bootstrap CI accounts for
  sampling but the effect leans on few high-extraction items.
- **STATUS / UPDATE (addressed, controls_report.md §R7):** Kendall's τ-b was computed
  alongside Spearman and **agrees in sign and relative magnitude throughout** (loss highest at
  τ=0.211; calibrated detectors lower), so the zero-inflated outcome is not creating the
  pattern — the negative R6 verdict is not a tie/zero-inflation artifact. Residual gap: a
  less-degenerate outcome at 1.4B/2.8B (GPU) would sharpen all estimates; the qualitative
  conclusion is already robust to the zero-inflation via τ.

### R8 — Oren/​n-gram statistical power 🟡 GPU-gated (upgraded, still underpowered)
- The Oren test originally ran on 10 short examples (p=0.044 contaminated vs 0.124 control) — a
  *sanity-scale interface demonstration*, NOT a contamination claim. n-gram separation (0.978)
  is strong but trivially so (members are in their own index by construction).
- **STATUS / UPDATE (upgraded but GPU-gated, contamination_matrix.md):** the Oren permutation
  test was re-run at 160m on real benchmark orderings (n_permutations=1000, k=30 items): MMLU
  p=0.001, GSM8K p=0.013, HumanEval p=0.875. The canonical order is favored beyond chance for
  MMLU/GSM8K even at 160m, but we draw **NO contamination conclusion**: the test is
  membership-based, run at sanity scale (small k, smallest model, single permutation-null
  seed), and is subject to a fluency/orientation artifact. It is flagged **GPU-gated** — a real
  benchmark-contamination claim needs larger models, larger k, and a fluency-control baseline.
  Separately, the model-free n-gram overlap was run vs a 10k-doc Pile *sample* (MMLU 0.2%/13-gram,
  GSM8K 0%, HumanEval 0%/13-gram); this is a **lower bound** (sampled reference), not a rate.

### R9 — PII claim not yet empirically supported 🟡 GPU-gated (null at 160m; handled honestly)
- We observed **0.0 verbatim PII leakage** on Enron-in-Pile at 160m (8/36 docs had PII in the
  suffix; none were regurgitated). So the paper's "PII exposure" limb is currently a *designed
  capability with a null result at 160m*, not a demonstrated leak.
- **STATUS / UPDATE (GPU-gated; handled honestly in the paper):** still a NULL at 160m — 0.0
  verbatim leakage, 8/36 docs with PII in the suffix. The paper (limitations.tex, results.tex)
  now states this explicitly as a null at scale and makes **no PII-exposure claim**; extraction
  is the leakage proxy and PII is framed as future/at-scale. No overclaim in the repo. Flagged
  GPU-gated: PII leakage is expected to appear at larger Pythia; claim only when measured.

---

## Significance / methodology checks
- RAW (pre-control) significance: 3/4 detectors' zero-order ρ CIs exclude 0 (LOSS, Min-K%, zlib);
  Min-K%++ does not. **SUPERSEDED by R6:** after controlling for loss, no calibrated detector
  predicts leakage in the positive direction (Min-K%/Min-K%++ FDR-sig negative; zlib n.s.).
- All separations reported with CIs; nulls stated (chance = 0.5 AUC; ρ=0 for correlation).
- Reproducibility: pinned `requirements.txt`, fixed seeds, configs, public datasets, one-command
  scripts (see README). Model size is a single flag.

## Net verdict (honest) — UPDATED 2026-06-20 (post controls + hardening)
Publishable-strength **preliminary** result, now reframed around the CONTROLLED finding rather
than the raw correlation. The confound-clean control (R3) is solid and novel-in-framing. The
former "headline correlation" (raw ρ, R4) is **superseded**: R6 showed it is carried entirely by
loss (calibrated detectors add no independent leakage signal; two are negative), and this is
robust to a non-linear control + mediation (hardening), to dedup (R2), and not a frequency (R1)
or zero-inflation (R7) artifact. The defensible thesis is the **membership-detection-vs-leakage-
prediction divergence**. **Must-clears now CLEARED on CPU:** R6 (resolved negative), R1/R2/R7
(addressed). **Still GPU-gated:** R8 (Oren at real scale w/ fluency control), R9 (PII leakage at
scale), and whether the clean-split membership signal — or any independent detector signal —
revives at 1.4B/2.8B.

---

## Adversary review (Subagent V) — 2026-06-20

A second, harder hostile pass by a reviewer who has read Al Sahili et al. (arXiv:2512.13352) and
Hayes et al. (NeurIPS 2025) and is inclined to REJECT as derivative. Full review:
`docs/adversary_review.md`. New concerns V1..V12 below (some sharpen existing R-items; V3/V5/V7/V8
are genuinely new statistical attacks). Classification: **[FIX-NOW-CPU]** / **[GPU-GATED]** /
**[ACCEPT-AS-LIMITATION]**.

| # | Concern | Severity | Status / classification |
|---|---|---|---|
| V1 | Finding is derivative of Al Sahili (marginal-gains) + Hayes (MIA≠extraction); delta is methodological (partial-ρ vs ranking/zero-order) | HIGH | [ACCEPT-AS-LIMITATION] + [FIX-NOW-CPU reframe] — lead with negative/suppression result (new vs Hayes' null), not "divergence" (Hayes' framing) |
| V2 | Negative result on smallest model in a no-signal regime (AUC≈chance, 3/300 extracted); may not generalize | HIGH | [GPU-GATED] — only the multi-scale replication answers it; reframe as protocol+pilot until then |
| V3 | Detectors are near-algebraic transforms of loss → negative partial-ρ is a **suppression/collinearity artifact**, not inverse prediction; prop_mediated>1 confirms ill-posed decomposition | HIGH | **[FIX-NOW-CPU]** — report loss↔detector corr, VIF/condition number from cached scores; reframe negatives as suppression |
| V4 | Construct validity: `frac_extracted` (greedy, 32-tok prefix) ≈ thresholded suffix-loss → "loss predicts extraction" near-tautological | HIGH | [FIX-NOW-CPU partial] + [ACCEPT-AS-LIMITATION] — report prefix-only-loss vs extraction if cache allows; else state definitional nature |
| V5 | Power: "no independent signal" may be ceiling/low-power, not true null; zlib CI includes 0, Min-K% q=0.058 (n.s.) non-deduped, deduped clears none | MED-HIGH | **[FIX-NOW-CPU]** — add min-detectable-effect/power statement; separate "true null" from "underpowered" |
| V6 | Member-only observational corr; pile-10k selection bias; pooled ρ is a sign-heterogeneous domain-mix (GitHub +0.60 vs PubMed Abs −0.48) | MED | [ACCEPT-AS-LIMITATION] + [FIX-NOW-CPU framing] — flag pooled ρ as domain-mix; name selection bias |
| V7 | Mediation assumptions violated (collinear mediator/predictor, censored 0-infl outcome); "loss carries entire association" not licensed | MED | **[FIX-NOW-CPU]** — demote mediation to descriptive; list violated assumptions; drop causal phrasing |
| V8 | Permutation/bootstrap tie-calibration with ~97% zero outcome; single FDR-sig cell (Min-K%++ q=0.015) may not survive tie-aware test | MED | **[FIX-NOW-CPU]** — verify mid-rank/tie-aware permutation; cross-check w/ Kendall-τ permutation |
| V9 | Oren fluency/orientation artifact undercuts MMLU p=0.001 / GSM8K p=0.013 | MED | [ACCEPT-AS-LIMITATION] — already correctly caveated (no conclusion drawn); optionally move to appendix |
| V10 | n-gram lower bound (0.2%/0%/0% vs 10k sample) is uninformative; padding if listed as contribution | LOW-MED | [FIX-NOW-CPU framing] — drop "we also map n-gram contamination" from abstract contributions |
| V11 | PII pillar (G3 "the concrete harm") is a null at 160m → scope inflation | LOW-MED | [ACCEPT-AS-LIMITATION] — already a disclosed null; ensure framing doesn't promise a demonstrated channel |
| V12 | Overclaim sentences: abstract "carried *entirely* by loss" + "two … negatively associated"; results "Only LOSS predicts leakage" | MED | **[FIX-NOW-CPU]** — soften to "loss-mediated to the resolution of this experiment"; correct to "only Min-K%++ FDR-sig negative non-deduped" |

**Single strongest rejection argument (V):** the only novel empirical content is a negative
partial-correlation that is (a) the same conclusion Al Sahili + Hayes already published, (b) the
mechanically-expected suppression artifact of regressing a thresholded-likelihood outcome on
near-collinear likelihood transforms, and (c) measured only at the smallest model in a near-degenerate
regime where no detector could show signal. Workshop/registered-report grade, not S&P.

**Contribution that survives (V's accepted rebuttal):** sharpens Hayes' *null* into a *significant
negative after loss control* for the field's *deployed reference-free* detectors (which Hayes never
tested), with an actionable auditor takeaway and exemplary pre-registration discipline. A defensible
workshop/second-tier accept now; plausible top-venue after the multi-scale replication.
