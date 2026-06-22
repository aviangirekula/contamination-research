# Pre-Analysis Plan (pre-registered BEFORE running the controls)

**Date:** 2026-06-19. **Scope:** controls-only run on EXISTING Pythia-160m data. No paper
prose, no GPU. Written before any control statistic is computed; only the tests listed here
are run. Every number is from a logged run with a fixed seed; null/weak results are reported
prominently with effect sizes and CIs. No detector is dropped, no test added post hoc.

## Data
- **Item set:** the 300 Pile MEMBER documents in `results/pile_items_160m.jsonl` (seed 0,
  stratified across 22 Pile subsets). Leakage outcomes (`frac_extracted`, `extracted`,
  `pile_set_name`) are reused as-is. Per-example detector scores were NOT persisted by the
  prior correlation run, so they are recomputed by re-scoring the identical `text` field with
  Pythia-160m (deterministic; we verify the recomputed raw ρ matches the prior run's
  0.275/0.173/0.177/0.108 as an integrity check).
- **Dedup arm (R2):** the SAME 300 documents (item selection is deterministic from seed 0),
  re-run through `EleutherAI/pythia-160m-deduped` for both extraction outcomes and detector
  scores (same size, CPU — new inference, explicitly authorized).

## Variables
- **Outcome (leakage):** `frac_extracted` ∈ [0,1] (PRIMARY, continuous); `extracted` ∈ {0,1}
  (SECONDARY, robustness). Members only.
- **Predictors (contamination/membership scores, higher = more member-like):** `loss`,
  `min_20_prob` (Min-K%), `min_20_plusplus` (Min-K%++), `zlib_ratio`.
- **Control variable (R6):** the raw `loss` score (mean per-token log-prob).
- **Frequency proxy (R1):** per-item mean unigram log-frequency of the item's whitespace
  tokens, with unigram counts estimated over the union of all 300 item texts (self-contained).
  Lower = rarer.

## Hypotheses & tests

### R6 — circularity (PRIMARY, confirmatory)
For each calibrated detector D ∈ {Min-K%, Min-K%++, zlib}:
- **H1 (partial):** partial Spearman ρ(D, frac_extracted | loss) ≠ 0.
- semipartial (part) correlation ρ(D, frac ; D residualized on loss) — descriptive companion.
- **Primary p-value:** permutation test (permute frac, recompute partial ρ, n=2000, seed 0),
  two-sided.
- **Multiple comparisons:** Benjamini–Hochberg FDR at q=0.05 across exactly these **3**
  confirmatory partial-correlation p-values (the R6 family). Nothing else enters this family.

### R1 — frequency (secondary)
Re-estimate raw Spearman ρ(D, frac) on the **frequency-matched subset** = middle tertile of the
frequency proxy (≈100 items, holding frequency roughly constant). Also report partial ρ
controlling for the frequency proxy. Descriptive (bootstrap CI; uncorrected p, labeled).

### R2 — deduplication (secondary)
On `pythia-160m-deduped`: (a) membership-separation AUC on the Pile train-vs-val split vs the
non-deduped model; (b) raw and partial(|loss) ρ(D, frac) vs non-deduped. Descriptive comparison.

### R7 — zero-robustness (secondary)
Report **Kendall's τ-b** alongside Spearman for raw and partial correlations (robust to the
zero-inflated outcome).

### Stratification (secondary)
Per-Pile-domain raw Spearman ρ(D, frac) with per-domain n, so we can see whether one domain
drives the pooled effect. Low per-domain n is expected; flagged, not over-interpreted.

## Statistics
- Partial Spearman: Pearson partial correlation on rank-transformed variables.
- Semipartial: residualize predictor ranks on control ranks, correlate with outcome ranks.
- Kendall τ-b with tie correction.
- Bootstrap 95% CIs: resample items with replacement, n=2000, seed 0, percentile interval.
- p-values: permutation (primary, R6) and analytic correlation t-test (secondary); BH-FDR on
  the R6 family only. All non-R6 p-values reported uncorrected and labeled exploratory.

## Pre-registered decision rule (R6 verdict)
- **HEADLINE SURVIVES** iff ≥1 detector in {Min-K%, Min-K%++, zlib} has partial ρ(D, frac|loss)
  whose bootstrap 95% CI **excludes 0** AND whose BH-FDR-corrected p < 0.05. Interpretation: that
  detector predicts leakage **beyond loss alone** (the link is not purely LOSS).
- **HEADLINE IS MOSTLY LOSS** iff all three partial ρ collapse toward 0 (CIs include 0 / not
  FDR-significant). Interpretation: the contamination→leakage signal was largely raw loss, and the
  headline must be reframed.
- Effect magnitudes (weak/moderate) are reported with CIs regardless of the binary verdict; a
  weak-but-nonzero surviving partial ρ is reported as exactly that — weak but nonzero.

## What this run will NOT do
No paper writing, no assembly/compile, no GPU, no model larger than 160m, no test outside this
list. Output is `docs/controls_report.md` + a verdict, then STOP for human review.

---

# Pre-Analysis Plan — Round 2 (statistical hardening + contamination matrix)

**Date:** 2026-06-20. Pre-registered BEFORE running. Same data as Round 1: the cached per-example
scores `results/controls_scores_pythia-160m.jsonl` (and `..._pythia-160m-deduped.jsonl`), each row
`{item_id, frac_extracted, pile_set_name, loss, min_20_prob, min_20_plusplus, zlib_ratio}`, N=300
Pile members. No new model inference. Outcome = `frac_extracted` (primary). Control = `loss`.
Calibrated detectors D ∈ {min_20_prob, min_20_plusplus, zlib_ratio}. Seed 0, bootstrap/permutation
n=2000.

## St — statistical hardening (does the negative survive a NON-LINEAR loss control + mediation?)

### St-1 (confirmatory) — non-linear loss control
The Round-1 partial correlation removed loss *linearly* (Pearson partial on ranks). We test whether
the null/negative survives a flexible loss control.

> **PRE-REGISTRATION AMENDMENT (2026-06-20, BEFORE running on real data).** Synthetic validation
> (tests/test_mediation.py) showed that 10-bin decile stratification is too COARSE: on a pure-linear-
> confound simulation it leaves residual within-bin confounding (ρ≈0.18 from a raw ρ≈0.7), so it can
> leak a spurious positive and is unfit as the primary control. Cubic-polynomial residualization
> removed the same confound cleanly (ρ<0.12). We therefore SWAP: PRIMARY control = cubic residualization;
> decile stratification retained as a coarser, model-free SECONDARY check. This change is driven by the
> synthetic method-check, NOT by any real-data outcome.

- **PRIMARY control: cubic-polynomial residualization.** Residualize D and frac each on a degree-3
  polynomial in `loss` (OLS), then Spearman of the residuals. Removes the full smooth (linear +
  non-linear) effect of loss. Significance via permutation (permute frac, recompute, n=2000); bootstrap
  95% CI (n=2000).
- **SECONDARY control: decile stratification.** Bin items into 10 equal-count bins of `loss`; bin-size-
  weighted mean within-bin Spearman ρ(D, frac); stratified permutation p (permute frac WITHIN each loss
  bin). Reported descriptively, with the caveat that 10-bin stratification incompletely removes strong
  linear confounds.
- **Confirmatory family + FDR:** the 3 cubic-residual permutation p-values (one per calibrated
  detector), Benjamini–Hochberg at q=0.05.
- **DECISION RULE (pre-registered, symmetric):** for any calibrated detector, if the nonlinear-partial
  ρ has a bootstrap 95% CI that EXCLUDES 0 and is POSITIVE and FDR-significant → an independent signal
  **REVIVES** under the nonlinear control → report immediately as a finding and flag for human review
  (this would change the headline). If CIs include 0 or are negative → the Round-1 null/negative is
  **confirmed not to be a linearity artifact**.

### St-2 (descriptive) — formal mediation (loss as mediator)
For each calibrated detector D, decompose the total D→frac association into direct + indirect (through
loss), on standardized rank variables (rank-based mediation):
- a = OLS coef of loss ~ D;  b = OLS coef of frac ~ loss + D;  c' (direct) = coef of D in frac ~ loss + D;
  indirect = a·b;  total = c' + a·b;  proportion mediated = indirect / total.
- Bootstrap percentile CIs (n=2000, seed 0) for direct, indirect, total, proportion mediated.
- Report proportion mediated ONLY when the total-effect CI excludes 0; otherwise report "total effect
  not distinguishable from 0; proportion-mediated undefined." Descriptive (not in the FDR family).

### St-3 (descriptive) — side-by-side + per-domain
- Table per detector: zero-order ρ | linear-partial ρ|loss (Round 1) | nonlinear-partial ρ (decile) |
  mediation: direct/indirect/proportion — all with 95% CIs.
- Per-domain: for each Pile domain with n≥10, Spearman ρ(loss, frac) and ρ(D, frac) with bootstrap
  CIs; tie the code-positive vs prose-negative pattern to token-diversity (cite Chen/Han/Miyao).
  Descriptive; low per-domain power explicitly flagged; no per-domain FDR claim.
- Robustness: repeat St-1 on the deduped arm.

**Outputs:** `docs/hardening_report.md`, regenerated figure(s), `findings.md` updated. Report any
revival the moment it appears.

## Mx — contamination matrix at small scale (model-free n-gram + Oren sanity)

### Mx-1 (scale-invariant) — n-gram/substring overlap of benchmarks vs the Pile
- Benchmarks: MMLU, GSM8K, HumanEval (sample up to 500 items each, seed 0).
- Pile reference: a public Pile SAMPLE (`NeelNanda/pile-10k`); build the set of its N-grams.
  **Caveat (pre-registered):** this is a SAMPLE of the Pile, so measured overlap is a LOWER BOUND on
  true benchmark↔Pile overlap; report as such, not as the contamination rate of the full corpus.
- Metric: per item, fraction of its N-grams found in the Pile-sample index; contamination flag =
  any-N-gram-overlap (the GPT-3 13-gram rule). N=13 primary, N=8 secondary. Report per-benchmark
  contamination rate + overlap-fraction distribution. Scale-invariant (model-free).

### Mx-2 (underpowered, flagged) — Oren permutation at 160m
- Run the Oren exchangeability test (permutations ≥1000) on each benchmark's canonical ordering at
  Pythia-160m. Report p-values but mark EXPLICITLY as sanity-scale/underpowered at 160m (membership-
  based ⇒ GPU-gated); do not draw contamination conclusions from it.

**Outputs:** `docs/contamination_matrix.md` + provisional matrix table; which cells are scale-invariant
vs GPU-gated stated explicitly.
