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
