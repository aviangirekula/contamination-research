# Phase 1 controls: is the extraction outcome memorization or predictability?

Model: Pythia-160M, CPU, seed 0. Members N=300, non-members N=300.
Scripts: `scripts/extraction_pile.py --source nonmembers`, `scripts/phase1_controls.py`.
Raw output: `results/phase1_controls_pythia-160m.json`.

## Why this was run

The paper's outcome variable is prefix-continuation extraction: give the model the first
32 tokens of a training document and check whether it reproduces the next 50. That
outcome was being read as evidence of memorization. Three independent sources questioned
whether it can carry that reading:

1. The advisor, who noted that a membership detector may not be the right instrument for
   predicting extractability and that memorization is a more direct starting point.
2. An adversarial review, which observed that the detector score is computed over the
   full 82-token window while the outcome lives in the final 50 tokens, so predictor and
   outcome share 61 percent of their support.
3. Cooper et al. 2026 (arXiv 2607.12649), which argues that extractable-memorization
   measurement requires a matched comparison against non-training sequences, otherwise
   the measurement partly reflects ordinary predictability.

Two controls address this directly.

## Control A: members versus non-members

Identical pipeline, identical settings, identical seed. Members are Pile train documents
(`NeelNanda/pile-10k`). Non-members are Pile validation documents
(`mit-han-lab/pile-val-backup`), which are held out from Pythia's training data. The
non-member arm was drawn to match the member arm's per-subset counts exactly, so the two
arms are domain-controlled. All 22 subset quotas were filled with no shortfall.

| Quantity | Members | Non-members |
|---|---|---|
| N | 300 | 300 |
| Exact full-suffix extraction | 3 | 2 |
| Mean matched tokens | 1.850 | **1.957** |
| Median matched tokens | 0.0 | 1.0 |
| Mean fractional extraction | 0.0370 | **0.0391** |
| Items with >=3 matched | 41 | **50** |
| Items with >=5 matched | 20 | **23** |

Rank-mean difference (members minus non-members): **-12.95**.
Permutation p, one-sided, members greater: **0.836**.

Per domain, across the 17 subsets with at least 8 member items, non-members score higher
in 12. The largest member advantage is Pile-CC at +1.12 mean matched tokens, which is
within noise. The largest non-member advantage is FreeLaw at -3.82.

**Reading.** At 160M there is no detectable memorization signal. Documents the model was
trained on are reproduced no more than documents it has never seen, and the point estimate
runs slightly the other way. The outcome is measuring how predictable the text is.

This is consistent with what the three fully extracted member items actually are: an XHTML
DOCTYPE header, a run of scanned-page image references with an incrementing counter, and a
book table of contents listing consecutive chapter numbers. All three are completable
without having seen the document.

**Power caveat.** With N=300 per arm and a heavily zero-inflated outcome, this is evidence
of no *appreciable* member advantage. It does not establish an exact zero.

## Control B: predictor and outcome on disjoint text

Detectors rescored using only the 32-token prefix, so the predictor shares no tokens with
the extraction target.

| Detector | Spearman rho, full window | Spearman rho, prefix only | Change |
|---|---|---|---|
| LOSS | 0.275 | 0.139 | -0.135 |
| Min-K% | 0.173 | 0.098 | -0.075 |
| Min-K%++ | 0.108 | 0.042 | -0.066 |
| zlib ratio | 0.177 | 0.082 | -0.096 |

Partial correlation given prefix-only loss: Min-K% **-0.043**, Min-K%++ **-0.104**,
zlib **-0.035**.

**Reading.** Roughly half of the headline association was an artifact of the shared window.
The paper's central claim survives the stricter construction: the calibrated detectors add
no positive predictive value beyond loss when predictor and outcome are computed from
disjoint text. That result is now better supported than it was under the pre-registered
analysis.

## Consequences

1. The incremental-value result stands and is strengthened.
2. The memorization and privacy framing is not supported at this scale. The paper cannot
   claim its outcome reflects memorization without a member versus non-member gap.
3. Assumption A1 of the chain (Section 2.5) is not merely unsupported for the calibrated
   detectors. At this scale the outcome itself does not separate members from non-members,
   so the premise the chain starts from is unavailable here.

## Control C: which properties predict reproduction, in both arms

This is the advisor's suggested analysis (compare the properties of documents that get
reproduced against those that do not), run on both arms so the two explanations separate.
A property that predicts reproduction in both arms describes predictable text. A property
that predicts reproduction only in the trained-on arm describes something the model
retained.

Script: `scripts/phase1_features.py`. Raw output: `results/phase1_features_pythia-160m.json`.

| Property | rho, members | p | rho, non-members | p |
|---|---|---|---|---|
| prefix loss score | +0.142 | 0.016 | +0.185 | 0.002 |
| repeated lines | **+0.184** | **0.0004** | -0.026 | 0.660 |
| punctuation fraction | +0.151 | 0.007 | +0.093 | 0.107 |
| digit fraction | +0.099 | 0.082 | +0.119 | 0.039 |
| compressibility | -0.063 | 0.260 | -0.011 | 0.861 |
| type-token ratio | +0.008 | 0.883 | +0.020 | 0.738 |
| word commonness | -0.103 | 0.071 | -0.084 | 0.151 |

Comparing a significant result in one arm against a null in the other is not itself a test
of difference, so each candidate was checked with a bootstrap confidence interval on the
difference between arms (4000 resamples).

| Property | rho difference | 95% CI | Verdict |
|---|---|---|---|
| repeated lines | +0.210 | [+0.032, +0.358] | arms differ |
| punctuation fraction | +0.057 | [-0.111, +0.220] | not distinguishable |
| digit fraction | -0.020 | [-0.182, +0.138] | not distinguishable |

**Reading.** The strongest single predictor of reproduction, the model's loss on the
opening tokens, behaves the same in both arms, which is what a predictability effect looks
like. The punctuation and digit effects are also present in both arms once tested properly.

One property does behave differently. Documents containing repeated lines are reproduced
more often, but only when the model was trained on them. Internal repetition is a plausible
proxy for corpus-level duplication, which is the best-established driver of memorization,
so this is the one hint of a member-specific effect in the data.

**How much weight to put on it.** Not much yet. The interaction interval reaches to +0.032,
so it barely excludes zero, seven properties were tested and the interaction test is not
corrected for that, and N is 300 per arm. This is a hypothesis worth testing, not a result.
The natural test is the deduplicated-model comparison the advisor suggested, since it
targets duplication directly, and repeating the analysis at larger scale.

The per-domain pattern points the same way as Control A. The domains where reproduction is
highest are the same in both arms: Github 5.76 against 6.38, PubMed Central 3.87 against
4.00, HackerNews 3.00 against 4.85. Reproduction tracks the kind of text, not whether the
model trained on it.

**Not computable here.** Duplication count needs an index of the whole Pile, which is why
it is deferred to the deduplicated-model comparison. Prefix and suffix lengths are fixed at
32 and 50 in this item set, so they have no variance to analyse and would need runs that
vary them.

## Reproducibility note

Re-running the member extraction after the `--source` refactor reproduced all 300 items
exactly, both the document selection and the per-item outcomes (300/300 identical).

## Next step

Repeat both controls at Pythia-1.4B. Memorization grows with model scale, so the
open question is the scale at which a member versus non-member gap appears. The pipeline
runs unchanged apart from the model flag, and `docs/scaleup_runbook.md` covers the free
cloud GPU path.
