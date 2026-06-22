# Integration Report — Round 2 (hardening + back-half writing + adversarial review)

**Date:** 2026-06-20. **Model:** Pythia-160m, CPU. **Authoritative current state** (supersedes the
2026-06-19 report; history in git). **Not committed** — staged for human review.

## What this round produced
- **Novelty (N):** `docs/novelty_memo.md` + 5 verified citations (Al Sahili, Hayes, Chen, Das, Meeus).
  Verdict **adjacent-but-distinct / novel**; no prior work does loss-residualized partial-correlation/
  mediation of calibrated detectors vs a per-item extraction outcome.
- **Statistical hardening (St):** `docs/hardening_report.md`. The negative/null result **survives** a
  non-linear loss control (cubic-residual primary, decile secondary) and a descriptive mediation; no
  positive signal revives (deduped arm agrees). **Collinearity diagnostic (W3):** detectors are
  near-collinear with loss (Spearman 0.74–0.90; VIF up to 6.2), so we report the conservative claim
  only (see below). `eval/mediation.py` + 8 tests (61/61 total).
- **Contamination matrix (Mx):** `docs/contamination_matrix.md`. Model-free n-gram overlap is a
  near-zero lower bound (10k Pile sample); Oren at 160m (MMLU p=0.001, GSM8K 0.013, HumanEval 0.875)
  is flagged underpowered/GPU-gated, no conclusion drawn.
- **Paper (W):** complete draft — Abstract, Intro, Background, Threat Model, Related Work (+ novelty
  comparison table `tab:closest` + Al Sahili/Hayes/Chen distinguishing text), Evaluation, Results,
  Discussion, Limitations, Conclusion. Assembled `paper/main.tex`; rendered to `paper/main.html` and
  `PAPER_DRAFT_FULL.md`.
- **Consistency (C):** `docs/consistency_audit.md` — verdict consistent; reconciled the stale
  `reviewer_concerns.md`, fixed Oren staleness, removed un-caveated positive headlines.
- **Adversary (V):** `docs/adversary_review.md` — hostile S&P review (W1–W12). **Verdict: borderline
  reject as-is.** I actioned the CPU-resolvable items this round (below).

## The finding, stated at the honest resolution
The contamination$\rightarrow$leakage association is **loss-mediated to the resolution of this
experiment**. The calibrated reference-free detectors (Min-K%, Min-K%++, zlib) add **no positive**
leakage signal beyond loss. We do **not** claim they negatively predict leakage: they are
near-collinear with loss (Min-K% Spearman 0.90, VIF 6.2), so the negative partial is consistent with
a suppression artifact. This is the membership-detection-vs-leakage-prediction divergence, claimed
conservatively.

## V's FIX-NOW items — actioned this round
- **W3 (collinearity/suppression):** added `scripts/collinearity_check.py` + diagnostic; reframed
  abstract/intro/results/discussion/limitations to claim "no positive residual," not "negative." ✅
- **W7 (mediation causal overclaim):** demoted to descriptive in results + discussion. ✅
- **W12 (overclaims):** softened "entirely by loss" → "loss-mediated to the resolution of this
  experiment"; removed "Only LOSS predicts leakage"; corrected the "two negatively associated" line. ✅
- **W5 (power):** added a minimum-detectable-effect/power caveat (no positive signal of appreciable
  size; small positive at scale not excluded). ✅
- **W4 (construct validity), W6 (selection/domain-mix), W10 (n-gram dropped from abstract):** added to
  Limitations / trimmed abstract. ✅
- **W8 (tie-aware permutation):** our permutation uses mid-rank statistics; noted. (A Kendall-permutation
  cross-check of Min-K%++ is a nice-to-have, listed GPU/followup.)

## Publication-strength now vs. GPU-gated
**Now (CPU, defensible):** the security reframing + threat model; the confound-clean control (WikiMIA
0.52–0.56 → chance on Pile train-vs-val); the pre-registered partial-correlation + non-linear control
+ collinearity-aware conservative claim; the comparison-table novelty positioning; full reproducibility.
**GPU-gated (honestly not yet shown):** whether calibrated detectors gain *independent* signal at
larger scale (W2); a less-degenerate extraction outcome (W5/W7); actual PII leakage (W9/R9, null at
160m); benchmark contamination via a full-Pile n-gram index and a fluency-controlled Oren (W10/R8);
the per-domain sign-flip as a powered result (V's "most under-exploited asset", W6).

## V's strongest rejection argument (recorded, not hidden)
The novel content is a negative partial-correlation that is (a) the conclusion Al Sahili/Hayes already
reached, (b) partly the mechanically-expected suppression of regressing a likelihood-derived outcome
on near-collinear likelihood transforms, and (c) measured only at the smallest model in a near-degenerate
regime. **Mitigation path:** the GPU replication across scales + the prefix-only-loss construct-validity
check + elevating the per-domain sign-flip are what move this from borderline to a contribution.

## Round DONE-criteria
1. ✅ novelty_memo + verified cites. 2. ✅ hardening_report (mediation + non-linear + domain + FDR;
collinearity added). 3. ✅ contamination_matrix + provisional table. 4. 🟡 complete paper written +
assembled + rendered to **HTML** (LaTeX→PDF is environment-blocked: no engine installable; compile via
Overleaf/local `pdflatex main`). 5. ✅ consistency_audit. 6. ✅ reviewer_concerns reconciled + V1–V12
appended + GPU-gated list. 7. ✅ pinned env + one-command repro. 8. ✅ this report.

**Stop for human review. Nothing committed.**
