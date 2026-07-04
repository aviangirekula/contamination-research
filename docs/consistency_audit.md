# Consistency Audit (Subagent C), repo-wide spine + number reconciliation

**Date:** 2026-06-20. **Scope:** read-heavy audit + small reconciling edits only (statuses,
stale numbers, missing caveats). No paper-prose rewrites. No edits to `eval/`, `detectors/`,
`scripts/`, `references.bib`, `novelty_memo.md`. Verdict at bottom.

## Verdict: **consistent: yes** (after the fixes below)

All four tasks pass. Key numbers match across `findings.md`, `controls_report.md`,
`hardening_report.md`, `results_table.md`, and `paper/{results,introduction,abstract}.tex`.
The whole repo now tells one story: contamination→leakage is **loss-mediated / negative for the
calibrated detectors**, not a positive headline. `reviewer_concerns.md` reconciled. Two staleness
issues and one un-caveated positive box were FIXED.

---

## Task 1, reviewer_concerns.md reconciliation (FIXED, all in `docs/reviewer_concerns.md`)

The file was STALE (predated controls + hardening). Updated every concern's status. Original
prose retained for history, authoritative `STATUS / UPDATE` line added per concern.

| Concern | Old status | New status | Evidence cited |
|---|---|---|---|
| R1 frequency | 🟡 partial (control TODO) | 🟡 **addressed** | partial ρ\|freq ≈ raw (Min-K% +0.166, zlib +0.193) → loss is confounder, not frequency |
| R2 dedup | 🟡 partial (pending compute) | 🟡 **addressed** | deduped run done: AUC unchanged (chance), same negative partial-ρ pattern, survives non-linear control |
| R3 temporal/topic | ✅ resolved | ✅ resolved (unchanged) | clean Pile train-vs-val |
| R4 CIs | ✅ resolved | ✅ resolved (unchanged) | bootstrap everywhere |
| R5 length | ✅ resolved | ✅ resolved (unchanged) | length-matched / fixed window |
| R6 circularity | ❌ OPEN | ✅ **RESOLVED (negative)** | linear partial + cubic-residual + decile + mediation. REVIVED detectors = NONE. Min-K%++ FDR-sig negative |
| R7 zero-robustness | ❌ open | 🟡 **addressed** | Kendall τ agrees in sign/magnitude |
| R8 Oren power | ❌ open | 🟡 **GPU-gated** | upgraded to 160m real benchmarks (MMLU p=0.001, GSM8K 0.013, HumanEval 0.875). Sanity-scale, no conclusion |
| R9 PII | ❌ open | 🟡 **GPU-gated** | still null at 160m (0.0 leakage, 8/36 docs w/ PII). Paper makes no PII claim |

Also updated the file's status legend, added a reconciliation banner, and rewrote the bottom
"Significance / methodology checks" + "Net verdict" sections (they still described the raw
positive headline as a publishable result. Now point to the R6-superseded/divergence framing).

## Task 2, number-consistency check (PASS. One staleness FIXED)

| Number | Files checked | Status |
|---|---|---|
| partial ρ\|loss: Min-K% −0.178, Min-K%++ −0.148, zlib −0.042 | findings, controls_report, hardening_report, results_table, paper/results, reviewer_concerns | ✅ match everywhere |
| cubic-residual: Min-K% −0.110 [−0.234,−0.002], Min-K%++ −0.160 [−0.287,−0.041] BH-q 0.015, zlib −0.052 | findings, hardening_report, paper/results | ✅ match |
| clean-split AUC 0.454/0.470/0.490/0.484 (0.45–0.49) | findings, results_table, controls_report, integration_report, paper/results, paper/limitations | ✅ match |
| extraction rate 0.010 (3/300), mean frac 0.037 | findings, results_table, paper/results, paper/limitations | ✅ match |
| PII 0.0 leakage, 8/36 docs w/ PII | findings, results_table, paper/results, paper/limitations, reviewer_concerns | ✅ match |
| contamination matrix MMLU 13-gram 0.2%, GSM8K 0%, Oren MMLU p=0.001 | contamination_matrix, paper/results | ✅ match |
| zero-order ρ: loss +0.275, Min-K% +0.173, Min-K%++ +0.108, zlib +0.177 | findings, controls_report, hardening_report, results_table, paper/results | ✅ match |

**MISMATCH found & FIXED (staleness, not a wrong value):** the **Oren** numbers in
`findings.md` (Milestone-1c) and `docs/results_table.md` (Table 3) still listed ONLY the old
10-example sanity demo (`0.044 vs 0.124`), whereas the paper (`results.tex`) and
`contamination_matrix.md` use the upgraded Mx run (MMLU p=0.001 / GSM8K 0.013 / HumanEval 0.875,
n_perm=1000, k=30) that explicitly supersedes the sanity demo (per R8). A reader of the ledger
would not have found the numbers the paper reports.
- **FIX:** in both files, relabeled the 10-example row "SUPERSEDED by the Mx run" and added the
  real Mx Oren row + the n-gram lower-bound row (MMLU 0.2% / GSM8K 0% / HumanEval 0%), so the
  ledger now traces the exact numbers the paper cites.

## Task 3, spine rule (PASS, no edit needed)

Every method named as EVALUATED is implemented + has a run script:
| Method | Detector/impl | Run script |
|---|---|---|
| LOSS | `detectors/loss.py` | `correlation_160m.py`, `milestone1_*.py` |
| Min-K% | `detectors/mink.py` | same |
| Min-K%++ | `detectors/minkpp.py` | same |
| zlib | `detectors/zlib_ratio.py` | same |
| n-gram overlap | `detectors/ngram_overlap.py` | `validate_ngram_oren.py`, `contamination_matrix.py` |
| Oren permutation | `detectors/oren_permutation.py` | same |
| extractable memorization | `extraction/extract.py` | `extraction_pile.py` |
| Enron PII | `extraction/pii.py` | `pii_enron.py` |

Everything else (guided prompting, neighbourhood, LiRA-as-attack, shadow models, DP) is framed in
`related_work.tex` / `evaluation.tex` / `threat_model.tex` as "related, not evaluated" and has NO
implementation file. **No violation.**

## Task 4, no un-caveated positive headline (PASS after one FIX)

| Surface | Status |
|---|---|
| `results_table.md` Table 2 | ✅ has SUPERSEDED-by-R6 box |
| `findings.md` Milestone 2 | ✅ has SUPERSEDED note |
| paper (abstract/intro/results/discussion/conclusion/limitations) | ✅ all present result as loss-mediated/negative. "predicts leakage" always carries "only through loss"/"beyond loss" |
| README.md | ✅ describes the link as object of study, no positive-result claim |
| `integration_report.md` "Headline" box | ⚠️ **was un-caveated positive** → **FIXED** |

**FIX:** `docs/integration_report.md` opens with a "Headline (the thesis as a number)" box that
read *"the contamination/membership score **significantly predicts extraction/leakage**"* with a
✅-marked table, a positive headline. The superseding note existed but only 11 lines lower. Added
a SUPERSEDED-framing banner directly above the box, relabeled the table "RAW (pre-control)", and
marked the ✅ as "raw-ρ CI-excludes-0 only," so the box can no longer be read as a positive finding
in isolation.

---

## Edits made (small reconciling only)
1. `docs/reviewer_concerns.md`, reconciled all 9 concerns + legend + banner + verdict/significance.
2. `findings.md`, replaced stale Oren sanity row with superseded-label + real Mx Oren + n-gram rows.
3. `docs/results_table.md`, same Oren/n-gram staleness fix in Table 3.
4. `docs/integration_report.md`, added SUPERSEDED banner + "raw"/pre-control labels to the headline box.

## Flagged for orchestrator (needs prose decision, NOT edited by me)
- **None blocking.** Optional polish only: `integration_report.md` is dated 2026-06-19 and frames
  the round around the (now-superseded) raw headline. The banner now makes it safe, but the
  orchestrator may want to retitle the doc's "Headline" section to the divergence framing for a
  fully forward-looking read. Left as prose, not touched.
