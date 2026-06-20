# Reviewer-Adversary Log (Subagent R)

Hostile S&P-style review of our OWN preliminary results (Pythia-160m). Each concern has a
status (✅ resolved / 🟡 partial / ❌ open), the evidence, and the action. The point is to
surface every confound before a real reviewer does. The most dangerous one is **R6** — read it.

---

### R1 — String-frequency confound 🟡 partial
*"Your detector separates members by web-frequency, not membership."*
- Evidence: `zlib_ratio` explicitly calibrates for compressibility/frequency. On the clean
  split it is also at chance (AUC 0.484), and in the headline it still predicts leakage
  (ρ=0.177, CI excludes 0) — so the leakage link is not purely a frequency artifact.
- **Action (open):** add a frequency-matched control — match members/non-members on zlib bits
  (and a reference-LM perplexity) and re-run. Not yet done.

### R2 — Deduplication confound 🟡 partial
*"Duplication, not membership, drives the signal."*
- Evidence: n-gram check found 3/44 non-members with residual train↔val overlap (real
  near-dup). For the HEADLINE (members-only), duplication is part of the causal chain
  (duplication→memorization→extraction, Carlini 2023), not a confound to remove.
- **Action (open):** run the `pythia-160m-deduped` ablation for the membership-separation
  tables. Designed in experiment_design.md §6; pending compute.

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

### R6 — Headline circularity / tautology ❌ OPEN (most important)
*"LOSS = low per-token loss = memorized; extraction = greedy reproduction = memorized. Of
course they correlate. The headline is mechanically trivial."*
- This is the sharpest threat to the headline's INTERPRETATION, and it is partly fair.
- Honest position: LOSS and extraction are related but distinct (soft likelihood vs. hard
  greedy-decode match), and the security claim is that a *contamination/membership detector's
  score is a usable predictor of concrete leakage*, even when its membership *separation* is at
  chance. We must NOT frame this as a surprising independent discovery.
- The correlation also holds for `zlib_ratio` (frequency-calibrated) and `min_20_prob`, which
  are not raw loss — mild evidence it is not pure tautology.
- **Action (top priority next):** report the **partial correlation** of each detector with
  extraction *controlling for raw LOSS* (and/or token length). If Min-K%/Min-K%++/zlib retain
  predictive power beyond LOSS, the link is non-trivial; if not, we scope the claim to "LOSS
  is the operative signal." This single control is the difference between a defensible and an
  overclaimed headline. NOT yet done.

### R7 — Zero-inflated outcome ❌ open
*"3/300 fully extracted, mean frac 0.037 — ρ is driven by a handful of points."*
- Evidence: scatter shows the high-frac points anchor the trend; bootstrap CI accounts for
  sampling but the effect leans on few high-extraction items.
- **Action:** larger models extract more (Carlini 2023), de-degenerating the outcome; rerun at
  1.4B/2.8B. Also report Kendall's τ (robust to ties) alongside Spearman.

### R8 — Oren/​n-gram statistical power ❌ open (scoped honestly)
- The Oren test ran on 10 short examples (p=0.044 contaminated vs 0.124 control) — a
  *sanity-scale interface demonstration*, NOT a contamination claim. n-gram separation (0.978)
  is strong but trivially so (members are in their own index by construction).
- **Action:** run Oren on real benchmark sets (MMLU/GSM8K orderings) at proper scale before any
  contamination claim about a specific benchmark.

### R9 — PII claim not yet empirically supported ❌ open (do not overclaim)
- We observed **0.0 verbatim PII leakage** on Enron-in-Pile at 160m (8/36 docs had PII in the
  suffix; none were regurgitated). So the paper's "PII exposure" limb is currently a *designed
  capability with a null result at 160m*, not a demonstrated leak.
- **Action:** the paper must state this honestly — PII leakage is expected to appear at scale
  (larger Pythia memorize more); claim it only when measured. Until then, frame extraction as
  the leakage proxy and PII as future/at-scale.

---

## Significance / methodology checks
- Headline significance: 3/4 detectors' ρ CIs exclude 0 (LOSS, Min-K%, zlib); Min-K%++ does not.
- All separations reported with CIs; nulls stated (chance = 0.5 AUC; ρ=0 for correlation).
- Reproducibility: pinned `requirements.txt`, fixed seeds, configs, public datasets, one-command
  scripts (see README). Model size is a single flag.

## Net verdict (honest)
Publishable-strength **preliminary** result: the confound-clean control (R3) and the headline
correlation with CIs (R4) are solid and novel-in-framing. Before submission, the **must-clears**
are R6 (partial correlation vs LOSS), R1 (frequency-matched control), and the scale-up (R7/R9)
to show the link strengthens and PII actually leaks. R2/R8 are standard ablations.
