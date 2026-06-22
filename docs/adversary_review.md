# Adversary Review (Subagent V) — the harshest defensible IEEE S&P reviewer

**Date:** 2026-06-20. **Reviewer stance:** an expert who *has read* Al Sahili et al.
(arXiv:2512.13352) and Hayes et al. (NeurIPS 2025) and arrives **inclined to REJECT** as
derivative. This is the hardest *defensible* case against the paper — not a strawman. For each
attack I state the strongest objection AND whether the paper already answers it, then classify the
residual concern as **[FIX-NOW-CPU]**, **[GPU-GATED]**, or **[ACCEPT-AS-LIMITATION]**.

Recommendation as written: **Reject (borderline), with a path to Weak Accept at a second-tier venue
or a workshop.** The single strongest rejection argument is in §"Reasons to REJECT". The contribution
that survives is in §"Reasons this is still a contribution".

---

## Summary of the submission (as I read it)

The paper reframes benchmark contamination as a privacy/security vulnerability, then asks whether
contamination/membership detector scores predict *per-item extraction*. On Pythia-160M with
ground-truth Pile membership (N=300 members), it runs a pre-registered partial-correlation +
mediation analysis controlling for raw per-item loss. Result: the positive zero-order correlations
(loss +0.275, Min-K% +0.173, zlib +0.177, Min-K%++ +0.108) collapse once loss is held fixed —
calibrated reference-free detectors add **zero or negative** residual signal (Min-K% partial −0.178,
Min-K%++ −0.148 FDR-sig negative; zlib ≈0). Survives a cubic-residual non-linear control and dedup.
Framed as a "membership-detection-vs-leakage-prediction divergence." Honest non-contributions: no new
detector/metric; all results preliminary on the smallest model, on CPU.

## Strengths (conceded up front)

- **Genuine methodological discipline.** Pre-registration (`docs/pre_analysis.md`) written before
  the controls, a symmetric decision rule, FDR confined to a declared family of 3, ground-truth
  membership (no post-hoc split), and a number-consistency audit. This is more rigor than most
  submissions in this space.
- **The non-contributions are stated honestly** and the related-work positioning vs Al Sahili /
  Hayes / Chen is explicit rather than buried.
- **The negative result is reported as negative** — the headline was not salvaged by cherry-picking.
- **Reproducibility** is real: seeded scripts, a numbers ledger, one-line config to scale.

These strengths are why this is a *borderline* reject and not a desk reject. They do not, by
themselves, clear the novelty bar for a top venue.

---

## Weaknesses

### W1 — Novelty is incremental over Al Sahili + Hayes. [SEVERITY: HIGH — primary reject driver]
**Objection.** Al Sahili et al. already establish, for targeted extraction, that "complex MIA
techniques yield only marginal improvements over simple likelihood-based ranking." Hayes et al.
already observe "no correlation with MIA success" for extraction and conclude the "two privacy
attacks may capture different signals." The qualitative bottom line of *this* paper — calibrated
detectors don't help beyond loss for extraction — is therefore **already in the literature, twice.**
The paper's own related-work table and Discussion concede the direction "is not surprising." What
remains is a *re-analysis*: "we did partial correlation / mediation instead of ranking-precision /
zero-order correlation." For a TOP venue (S&P), swapping the statistical lens on a conclusion two
prior papers already reached is a contribution of *degree*, not *kind*. A method substitution
(partial-ρ vs ranking-precision) is not itself a research finding unless it overturns or materially
sharpens the prior conclusion — and "zero/negative residual" is a sharper statement of the *same*
conclusion ("they don't help"), not a different one.

**Does the paper answer it?** Partially. The novelty memo (`docs/novelty_memo.md`) verifies that no
prior work does loss-residualization/mediation against an *extraction* outcome on the *reference-free
calibrated* detectors, and the paper targets the detectors the contamination literature actually
deploys (Hayes used LiRA, a reference-model attack). That is a real, defensible distinction of
*object and method*. But it does not rebut the core charge that the **finding** is the same and the
delta is methodological. The "negative residual" (vs Hayes' "no correlation") is the strongest
genuinely-new empirical wrinkle, and the paper underplays it relative to the (derivative) "divergence"
framing.

**Classification: [ACCEPT-AS-LIMITATION] + [FIX-NOW-CPU] (framing).** The novelty ceiling at 160M
cannot be raised on CPU. But the paper can and should (a) foreground the *suppression/negative*
result as the specific thing neither prior work shows (Hayes: null; this: significantly negative
after loss control), and (b) stop leaning on "divergence," which is Hayes' framing. **FIX-NOW-CPU:**
rewrite the contribution sentence to lead with the negative-residual/suppression result, not the
divergence.

### W2 — A negative result on the SMALLEST model in a near-degenerate regime is not publishable at a top venue. [SEVERITY: HIGH]
**Objection.** The entire empirical claim rests on Pythia-160M, where (i) membership separation is
*at chance* (AUC 0.45–0.49) and (ii) extraction is *near-degenerate* (3/300 fully extracted, mean
frac 0.037). The paper itself says memorization grows log-linearly with scale. So the headline —
"calibrated detectors add no signal beyond loss" — is established **precisely in the regime where
there is almost no signal of any kind to add.** A reviewer cannot distinguish "calibrated detectors
genuinely carry no leakage information" from "at 160M nothing carries leakage information, so of
course the residual is null." The result may simply not generalize to the scale where the question
matters. This is the reject-defining tension: the paper asks a scale-dependent question and answers
it at the one scale where the answer is least informative.

**Does the paper answer it?** It is *disclosed* honestly (Limitations bullets 1–3) but **not
resolved.** Disclosure of a fatal-to-generality limitation does not make the result generalize. The
"the pipeline scales with one config change" line is an assertion about engineering, not evidence
about the science.

**Classification: [GPU-GATED].** The only real answer is the 1.4B/2.8B/6.9B replication. Until then
the contribution is a *methodology + a preliminary null*, which is workshop-grade, not S&P-grade.
The paper should be retitled/reframed as a registered protocol + pilot, not a finding.

### W3 — Collinearity makes the "negative partial-ρ" close to mechanically guaranteed, not a discovery. [SEVERITY: HIGH]
**Objection.** Min-K%, Min-K%++, and zlib are **deterministic functions of the same per-token
logprobs that define loss.** Min-K% is an average of the lowest-k% token logprobs; loss is the
average of *all* token logprobs; zlib is loss divided by a compression constant. These are not
"independent predictors that happen to correlate with loss" — they are near-algebraic transforms of
it. When you regress extraction on loss + Min-K%, you are partialling out a variable that *contains*
most of the predictor by construction. A **negative** partial coefficient on Min-K% given loss is
the textbook signature of **suppression between two near-collinear regressors**, not evidence that
Min-K% is "inversely related to leakage." The mediation table makes this explicit and damning:
`prop_mediated > 1` (indirect +0.567 vs total +0.173 for Min-K%) is *inconsistent mediation*, which
is exactly what near-collinear mediator/predictor pairs produce. The paper interprets the negative
direct effect substantively ("if anything inversely related to extraction") when the more
parsimonious reading is **a collinearity artifact.**

**Does the paper answer it?** Partially and self-defeatingly. (a) R6 in `reviewer_concerns.md`
concedes loss and the detectors are "mechanistically entangled" and notes zlib/Min-K% "are not raw
loss — mild evidence it is not pure tautology." (b) The hardening report *reports* the >1
proportion-mediated and correctly declines to print it as a clean fraction. But the paper still
**interprets the negative sign as a finding** ("Min-K%/Min-K%++ are if anything negatively
associated") rather than flagging it as a probable suppression artifact. No collinearity diagnostic
(VIF, condition number, or the correlation between loss and each detector) is reported, so the
reader cannot tell how much of the "negative" is suppression.

**Classification: [FIX-NOW-CPU].** Report, from the already-cached
`results/controls_scores_pythia-160m.jsonl`: (1) the Spearman/Pearson correlation between loss and
each detector (likely |ρ|>0.9), (2) VIF / condition number for the loss+detector regressions, and
(3) reframe the negative direct effect as *consistent with suppression under near-collinearity*, not
as substantive evidence that Min-K% predicts *less* leakage. This is a few lines on existing data
and it is mandatory — without it the headline's strongest-sounding clause is indefensible.

### W4 — Construct validity: the headline is near-tautological by construction. [SEVERITY: HIGH]
**Objection.** The outcome is `frac_extracted` under **greedy decoding at a 32-token prefix.** Greedy
extraction succeeds exactly when the model assigns the continuation high per-token probability — i.e.
when per-token **loss on the suffix is low.** So "loss predicts extraction" (ρ=0.275) is close to
re-measuring the same quantity twice: a soft likelihood proxy vs a hard-thresholded version of the
same likelihood. The paper's central positive result ("loss predicts leakage") is therefore
mechanically near-guaranteed, and the "interesting" part (detectors add nothing beyond loss) reduces
to "transforms of loss add nothing beyond loss" — which is W3. The construct gap between predictor
and outcome that would make this a real prediction problem is thin.

**Does the paper answer it?** R6 names this exactly and offers the only honest defense: loss is a
*whole-item soft* likelihood whereas extraction is a *suffix-only hard greedy* match, so they are
related-but-distinct. That is a fair partial defense (the prefix/suffix split and the
hard-vs-soft distinction are real). But the paper does not *quantify* the gap — e.g. it never reports
loss computed on the *prefix only* vs the *suffix* separately, which would show whether the
correlation is driven by the suffix likelihood (near-tautological) or by something the prefix carries.

**Classification: [FIX-NOW-CPU] (partial) + [ACCEPT-AS-LIMITATION].** From cached data, if
suffix-loss vs whole-item-loss is recoverable, report the correlation of *prefix-only* loss with
extraction to demonstrate the predictor isn't just the suffix likelihood. If not recoverable without
re-inference, state plainly in Limitations that the loss↔extraction link is partly definitional and
that the *novel* content is exclusively the detector-residual comparison (W1).

### W5 — Power / true-null ambiguity at N=300 with a zero-inflated outcome. [SEVERITY: MEDIUM-HIGH]
**Objection.** With 3/300 fully extracted and mean frac 0.037, the outcome is overwhelmingly zeros.
"No independent signal beyond loss" may be a **ceiling/floor + low-power artifact**, not a true null.
A partial-ρ of −0.05 to −0.18 on N=300 with a near-degenerate outcome has wide effective error bars;
the cubic-residual zlib CI [−0.165, +0.068] *includes zero*, and Min-K% non-deduped BH-q=0.058 is
*not* below 0.05 (only Min-K%++ at 0.015 clears). So even the "negative" claim is carried by a single
detector in a single arm; on the deduped arm *no* detector clears FDR (q=0.084 for both Min-K%/++).
The paper's own numbers thus show the "significantly negative" claim is fragile and arm-dependent.
Calling this "no independent leakage-predictive value" overstates what N=300 can establish.

**Does the paper answer it?** Partially: Kendall τ robustness (R7), bootstrap CIs, and a frank
"near-degenerate outcome" limitation. But it does **not** report a power analysis or a
minimum-detectable-effect, and the Results prose ("Min-K%++ remains significantly negative") elevates
the one cell that clears FDR while the abstract generalizes to all detectors ("two of them … are if
anything negatively associated"). zlib is null, and the negative for Min-K% does not survive FDR
non-deduped.

**Classification: [FIX-NOW-CPU].** (1) Add a minimum-detectable-effect / power statement for partial-ρ
at N=300 with this zero-inflation (computable now, no inference). (2) Soften the abstract: only
Min-K%++ is FDR-significant negative *non-deduped*; the deduped arm clears nothing; zlib is null.
State that the negative is detector- and arm-specific. (3) Distinguish "true null" from "underpowered
to detect a small positive" explicitly — at present the paper implies the former.

### W6 — Member-only, observational correlation; no negatives in the headline. [SEVERITY: MEDIUM]
**Objection.** The headline correlation is computed **across known members only** — there are no
non-members in the extraction analysis. The detector scores' meaning is calibrated by member/non-
member *contrast*, but here we correlate them within the member set against extraction. pile-10k is a
non-uniform sample of the Pile (the "members" are whatever NeelNanda/pile-10k happened to include),
so member-selection bias is uncontrolled, and the per-domain table shows the loss↔extraction sign
*flips* across domains (GitHub +0.60 vs PubMed Abstracts −0.48). The pooled ρ is a domain-mix
artifact: it reflects how many structured/boilerplate items the 10k sample contained, not a stable
property.

**Does the paper answer it?** The observational/members-only nature is in Limitations, and the
per-domain heterogeneity is reported (honestly) in the hardening report. But the paper still reports
a *pooled* headline ρ and a pooled mediation, which the per-domain table shows is a weighted average
over sign-discordant strata — i.e. not a coherent single effect.

**Classification: [ACCEPT-AS-LIMITATION] + [FIX-NOW-CPU] (framing).** **FIX-NOW-CPU:** state in
Results that the pooled loss↔extraction ρ is a domain-mix and is sign-heterogeneous across strata
(already computed), so the pooled number should not be read as a universal effect. The member-
selection bias of pile-10k must be named explicitly as a threat to external validity.

### W7 — Mediation assumptions are violated; the mediation analysis is decorative. [SEVERITY: MEDIUM]
**Objection.** Rank/OLS mediation (Baron–Kenny style: a·b decomposition) assumes (i) no
unmeasured confounding of mediator→outcome, (ii) correct functional form, (iii) a meaningful
mediator/predictor distinction. Here loss (mediator) and the detector (predictor) are near-collinear
transforms (W3), the outcome is zero-inflated and bounded (rank-OLS on a 0-inflated [0,1] outcome is
mis-specified), and `prop_mediated > 1` flags the decomposition as ill-posed. A mediation analysis on
collinear mediator/predictor with a censored outcome does not license a causal "loss carries the
entire association" reading; it is a re-description of the regression coefficients.

**Does the paper answer it?** It declines to print the >1 proportion as a fraction (good) and reports
direct/indirect/total with CIs instead. But it still draws the causal-flavored conclusion ("loss
carries >100% of the positive association," "suppression mediation") which the assumptions do not
support.

**Classification: [FIX-NOW-CPU].** Downgrade the mediation from a load-bearing result to a
descriptive companion; explicitly list the violated assumptions (collinearity, censored outcome) and
drop any "carries the entire association" causal phrasing. No new computation needed.

### W8 — Permutation/bootstrap validity with ties in a zero-inflated outcome. [SEVERITY: MEDIUM]
**Objection.** With ~97% of `frac_extracted` at or near a small set of values (heavy ties),
permutation tests on Spearman/partial-ρ and percentile bootstrap CIs can be miscalibrated:
permuting a tie-dominated outcome under-disperses the null, inflating significance, and percentile
bootstrap CIs on rank statistics with massive ties are known to be anti-conservative. The single
FDR-significant cell (Min-K%++ q=0.015) may not survive a tie-aware (mid-rank / exact) permutation
scheme.

**Does the paper answer it?** Kendall τ-b (tie-corrected) is reported and "agrees in sign and
magnitude," which is the right instinct and a partial defense. But there is no explicit
demonstration that the permutation null and bootstrap CIs are tie-calibrated; τ-b agreement on the
*point estimate* does not establish *p-value* calibration.

**Classification: [FIX-NOW-CPU].** On cached data: (1) verify the permutation uses mid-ranks / a
tie-aware statistic and report it; (2) cross-check the Min-K%++ q with a Kendall-τ-based permutation
test; (3) if the single FDR-significant result is sensitive to the tie scheme, downgrade the
"significantly negative" claim accordingly.

### W9 — Oren permutation: fluency/orientation artifact undercuts the only benchmark-level "signal." [SEVERITY: MEDIUM]
**Objection.** MMLU p=0.001 and GSM8K p=0.013 "canonical order favored" can arise with **zero
contamination**: the canonical ordering of a benchmark is simply more fluent/coherent than a random
shuffle, so its concatenation has higher log-likelihood under *any* competent LM. Without a
fluency-control baseline (e.g. a model demonstrably not trained on the benchmark, or a
within-item-shuffle control), these p-values are uninterpretable as contamination evidence.

**Does the paper answer it?** **Yes, adequately.** The paper draws *no* contamination conclusion,
explicitly names the fluency/orientation artifact, and flags the test GPU-gated pending a
fluency-control baseline. This is handled correctly. The only residual issue is that the Results
table still *displays* the p-values prominently, inviting over-reading.

**Classification: [ACCEPT-AS-LIMITATION].** Already correctly caveated; optionally move the Oren row
to an appendix so a skimming reader cannot misread it.

### W10 — n-gram lower bound is uninformative and arguably should be cut. [SEVERITY: LOW-MEDIUM]
**Objection.** Overlap against a 10k-doc *sample* of a ~210M-doc corpus yielding 0.2%/0%/0% is
not a measurement of anything — it is a near-vacuous lower bound that "certifies overlap is at least
~0%." Including it as a "contribution" ("we also map model-free n-gram contamination") borders on
padding; a reviewer reads it as a result that says nothing.

**Does the paper answer it?** It is honestly labeled a lower bound and "uninformative about true
contamination." But the abstract still lists "we also map model-free n-gram contamination across
standard benchmarks" as if it were a contribution.

**Classification: [FIX-NOW-CPU] (framing) / [ACCEPT-AS-LIMITATION].** Drop the n-gram mapping from the
abstract's contribution list (it maps essentially nothing at this reference size); keep it only as a
disclosed-null/infrastructure note. Full-Pile index is infra-gated, not part of this submission.

### W11 — PII limb is a designed-but-null capability presented as a threat-model pillar. [SEVERITY: LOW-MEDIUM]
**Objection.** The threat model elevates PII (G3) as "the concrete harm," but the measurement is a
*zero* (0/8 PII-containing docs regurgitated). A threat-model pillar with a null measurement reads as
scope inflation: the paper claims a privacy/security framing whose flagship harm it cannot
demonstrate at the only scale it runs.

**Does the paper answer it?** Yes — reported as a null, no PII-exposure claim, flagged GPU-gated.
Handled honestly. The residual concern is purely rhetorical: the framing promises more than the
evidence delivers.

**Classification: [ACCEPT-AS-LIMITATION].** Keep the null; ensure the abstract/intro do not imply a
demonstrated PII channel (they currently do not, but the threat-model prose leans hard on PII as "the
concrete harm").

### W12 — Overclaim audit (specific sentences). [SEVERITY: MEDIUM]
Specific lines that outrun the logged evidence:
- **Abstract:** "the calibrated reference-free detectors add no independent predictive value beyond
  it, and two of them … are *negatively* associated with extraction once loss is held fixed." →
  Overstates: only Min-K%++ is FDR-significant negative *non-deduped*; Min-K% is q=0.058 (not <0.05)
  non-deduped and q=0.084 deduped; zlib is null. "Two of them … negatively associated" is not
  FDR-supported for Min-K% non-deduped. [FIX-NOW-CPU]
- **Abstract / Conclusion:** "carried *entirely* by loss." → "entirely" is a strong universal that a
  collinearity-confounded, N=300, near-degenerate-outcome pilot cannot license. Soften to "to the
  resolution of this experiment, the positive association is loss-mediated." [FIX-NOW-CPU]
- **Results:** "Only LOSS predicts leakage." (table caption) → Given W3/W4 this is close to "only the
  variable most definitionally tied to greedy extraction predicts greedy extraction." Reword to avoid
  implying a discovery. [FIX-NOW-CPU]
- **related_work.tex:242 "To our knowledge it is the only study that pairs a per-item extraction
  outcome with a partial-correlation/mediation control for raw loss on calibrated reference-free
  detectors."** → Defensible *as stated* (narrow, method+object specific; novelty memo backs it), but
  it is a claim of method-novelty, not finding-novelty, and should not be read by the authors as a
  shield against W1. Keep but do not lean on it. [ACCEPT-AS-LIMITATION]
- **Intro:** the "contamination → memorization → leakage chain [as] the object of empirical study"
  is only partially delivered: the *contamination→memorization* link is asserted (members are
  contaminated by definition) and only the *memorization→extraction* (≈loss↔greedy) link is measured.
  The "chain" framing promises a benchmark-contamination→leakage result the paper does not produce
  (the benchmark-level tests are GPU-gated/uninformative). [FIX-NOW-CPU framing]

**Classification: [FIX-NOW-CPU]** for the four softenings; the "to our knowledge" line is
[ACCEPT-AS-LIMITATION].

---

## Detailed comments (cross-cutting)

- The paper's greatest vulnerability is that **W1 (derivative), W3 (collinearity), and W4
  (tautology) compound**: the genuinely new content is the *negative residual*, but that residual is
  the predicted signature of regressing extraction on two near-identical likelihood transforms in a
  no-signal regime. A skeptical reviewer collapses the whole headline into "transforms of loss don't
  beat loss at predicting a thresholded version of loss, measured where almost nothing is
  extractable." Defeating this requires *either* the collinearity diagnostics + reframing (W3, CPU)
  *and* the scale replication (W2, GPU), *or* a candid repositioning as a registered protocol + pilot.
- The pre-registration is the paper's best asset and should be foregrounded; it is what separates this
  from a fishing expedition and is the honest answer to "why isn't this p-hacked."
- The per-domain sign-flip (W6) is, ironically, more interesting than the pooled headline and is
  buried in a report. A version of this paper organized around "the loss↔extraction link is
  domain-structured (code/boilerplate positive, prose negative)" would be more novel than the
  divergence framing — but that, too, needs scale and more per-domain N.

---

## Reasons to REJECT (the single strongest argument, stated plainly)

**The paper's only novel empirical content is a negative partial-correlation that is (a) the same
qualitative conclusion two prior papers already published, (b) the mechanically-expected artifact of
regressing a thresholded-likelihood outcome on near-collinear likelihood transforms, and (c)
measured exclusively at the smallest model in a near-degenerate regime where no detector — calibrated
or not — could plausibly show signal.** Strip away the (correctly disclosed) GPU-gated and null
components, and what is left for S&P is: a known conclusion, re-derived with a different statistic, on
data where the statistic's value is close to predetermined by construction and collinearity, with the
one FDR-significant cell fragile to the dedup arm and to tie-aware permutation. That is a competent
workshop pilot or a registered-report protocol — not a top-venue finding. **Recommend reject**;
encourage resubmission after the multi-scale replication, with the collinearity diagnostics in place
and the contribution re-centered on the negative/suppression result (the one thing prior work does
not show) rather than the "divergence" (which Hayes already framed).

## Reasons this is still a contribution (the rebuttal I would accept)

- **It sharpens, not merely repeats, prior work.** Hayes reports a *null* (no correlation); this
  paper reports a *significant negative after loss control* for the field's *deployed reference-free*
  detectors (Min-K%/++ /zlib), which Hayes (LiRA, reference-model) never tested. "Calibration that
  improves membership AUC actively discards the loss-magnitude signal that predicts leakage" is a
  crisper, more actionable claim than "two attacks capture different signals." That actionable
  auditor takeaway — *measure loss/extractability directly; don't trust a high Min-K% score as
  leakage risk* — is a genuine, if modest, security contribution.
- **The discipline is exemplary** (pre-registration, ground-truth membership, FDR family declared,
  symmetric decision rule, honest nulls). The field is littered with post-hoc-split MIA papers; a
  rigorously pre-registered ground-truth study is itself worth something and directly answers the
  Das/Meeus critiques.
- **It is honestly scoped:** no overclaimed detector, no salvaged headline, GPU/PII limbs flagged.
- With W3 (collinearity diagnostics + reframing) and W5/W8 (power + tie-aware) fixed on CPU, and the
  abstract softened (W12), the paper is a defensible **workshop / second-tier** acceptance now, and a
  plausible top-venue paper *after* the multi-scale replication (W2) lands.

---

## Weakness × severity × classification (at a glance)

| # | Weakness | Severity | Classification |
|---|---|---|---|
| W1 | Derivative of Al Sahili + Hayes (finding-novelty) | HIGH | ACCEPT-AS-LIMITATION + FIX-NOW-CPU (reframe) |
| W2 | Negative result at smallest model / no-signal regime | HIGH | GPU-GATED |
| W3 | Collinearity → negative partial-ρ is suppression artifact | HIGH | FIX-NOW-CPU |
| W4 | Construct: outcome ≈ thresholded loss (near-tautology) | HIGH | FIX-NOW-CPU (partial) + ACCEPT-AS-LIMITATION |
| W5 | Power / true-null vs ceiling at N=300, zero-inflated | MED-HIGH | FIX-NOW-CPU |
| W6 | Member-only observational; pile-10k selection; domain-mix | MED | ACCEPT-AS-LIMITATION + FIX-NOW-CPU (framing) |
| W7 | Mediation assumptions violated; prop_mediated>1 | MED | FIX-NOW-CPU |
| W8 | Permutation/bootstrap tie-calibration | MED | FIX-NOW-CPU |
| W9 | Oren fluency/orientation artifact | MED | ACCEPT-AS-LIMITATION (already caveated) |
| W10 | n-gram lower bound uninformative | LOW-MED | FIX-NOW-CPU (framing) / ACCEPT-AS-LIMITATION |
| W11 | PII pillar is a null | LOW-MED | ACCEPT-AS-LIMITATION |
| W12 | Overclaim sentences (abstract "entirely"/"two negatively") | MED | FIX-NOW-CPU |

## [FIX-NOW-CPU] action list for the orchestrator (no GPU, mostly on cached data)

1. **W3 (mandatory):** report loss↔detector correlations (expect |ρ|>0.9), VIF/condition number for
   loss+detector regressions, from `results/controls_scores_pythia-160m.jsonl`; reframe negative
   direct effects as *suppression under near-collinearity*, not substantive inverse prediction.
2. **W5:** add a minimum-detectable-effect / power statement for partial-ρ at N=300 with this
   zero-inflation; explicitly separate "true null" from "underpowered for a small positive."
3. **W8:** confirm permutation uses mid-ranks / tie-aware statistic; cross-check Min-K%++ q with a
   Kendall-τ permutation; downgrade the "significantly negative" claim if it is tie-scheme-sensitive.
4. **W7:** demote mediation to descriptive; list violated assumptions (collinearity, censored
   outcome); delete "carries the entire association" causal phrasing.
5. **W12 (abstract/results prose):** soften "carried *entirely* by loss" → "loss-mediated to the
   resolution of this experiment"; correct "two … negatively associated" to "only Min-K%++ is
   FDR-significant negative (non-deduped); deduped clears none; zlib null"; reword table caption
   "Only LOSS predicts leakage."
6. **W4 (if recoverable from cache):** report prefix-only-loss vs extraction to show the link isn't
   purely the suffix likelihood; else state the partial-definitional nature in Limitations.
7. **W6:** state the pooled headline ρ is a sign-heterogeneous domain-mix; name pile-10k member-
   selection bias as an external-validity threat.
8. **W1 (reframe):** lead the contribution with the negative/suppression result (new vs Hayes' null),
   not the "divergence" (Hayes' framing).
9. **W10:** drop "we also map model-free n-gram contamination" from the abstract's contributions.

**[GPU-GATED] (cannot be cleared now):** W2 (multi-scale replication is the only real answer; also
re-tests whether calibrated detectors gain independent signal once extraction is non-degenerate and
membership separation is non-trivial). Oren-with-fluency-control and PII-at-scale (W9/W11) ride along.

**[ACCEPT-AS-LIMITATION] (must remain stated in Limitations):** W1 finding-novelty ceiling, W4
partial-definitional link, W6 observational/members-only/selection, W9 (already), W11 (already).
