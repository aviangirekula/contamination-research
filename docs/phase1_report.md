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

## Reproducibility note

Re-running the member extraction after the `--source` refactor reproduced all 300 items
exactly, both the document selection and the per-item outcomes (300/300 identical).

## Next step

Repeat both controls at Pythia-1.4B. Memorization grows with model scale, so the
open question is the scale at which a member versus non-member gap appears. The pipeline
runs unchanged apart from the model flag, and `docs/scaleup_runbook.md` covers the free
cloud GPU path.
