# Benchmark Contamination as a Privacy/Security Vulnerability in LLMs

Empirical security study: does **benchmark/training-data contamination** in LLMs
constitute a **privacy vulnerability** (unintended memorization, PII/proprietary-data
leakage) that evades existing detection? Target venues: IEEE S&P, USENIX Security, CCS, NDSS.

**Contribution (honest scope):** *not* a novel detector or metric. We (a) reframe
contamination as a privacy/security vulnerability with an explicit threat model, (b)
run a systematic comparative evaluation of existing detectors under the S&P low-FPR
protocol on ground-truth Pile membership, and (c) establish the empirical
**contamination → memorization → leakage** link. See
[`docs/method_selection_memo.md`](docs/method_selection_memo.md).

## Repository layout

```
detectors/    LOSS, Min-K%, Min-K%++, zlib  (uniform score(text)->float interface)
extraction/   prefix-continuation (extractable) memorization harness
eval/         AUC, TPR@low-FPR, log-ROC, bootstrap CIs, Spearman correlation
scripts/      milestone1_separation.py  (first real-compute milestone)
run.py        Models x Detectors x Datasets runner with result caching
tests/        full CPU test suite (no model download required)
docs/         method_selection_memo.md, experiment_design.md, glossary.md
references.bib verified bibliography (every entry has a verification comment)
findings.md   shared numbers ledger: every paper claim traces to a row here
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install numpy pytest          # enough for tests + self-test
pytest -q                         # full suite, runs on CPU, no downloads
python run.py --self-test         # mock end-to-end (Models x Detectors x Datasets)
```

Real runs (Milestone 1+, needs the full `requirements.txt`):

```bash
pip install -r requirements.txt
python scripts/milestone1_separation.py \
    --members-file data/pile_members.txt \
    --nonmembers-file data/nonmembers.txt --device cpu
```

Ground-truth member/non-member text must be **real Pile membership** (or the released
MIMIR splits from Duan et al. 2024) — the scripts will not invent data.

## Method shortlist (derived in Phase 1)

| Detector | Access | Role | Source |
|---|---|---|---|
| LOSS / Perplexity | gray-box | mandatory baseline | Yeom et al. 2018 |
| Min-K% Prob | gray-box | strong reference-free baseline | Shi et al. 2024 (ICLR) |
| Min-K%++ | white-box | **primary** (SOTA reference-free) | Zhang et al. 2025 (ICLR) |
| zlib ratio | gray-box | frequency-confound control | Carlini et al. 2021 (USENIX) |
| extractable memorization | white-box | leakage outcome | Carlini et al. 2023 (ICLR) |

Evaluation protocol: **TPR @ 0.1%/1% FPR + log-scale ROC** (Carlini et al. 2022, S&P),
AUC secondary; ground truth = **Pythia + The Pile** (Biderman et al. 2023; Gao et al. 2020).

## Status

- [x] Phase 1 — literature research, method-selection memo, verified `references.bib`
- [x] Phase 2 — experiment design (threat model, matrix, metrics, ethics)
- [x] Phase 3 scaffold — tested detectors/extraction/eval/runner (CPU, mock-validated)
- [ ] Milestone 1 — real Pythia Pile in/out separation (gated on compute)
- [ ] Full matrix + figures + correlation analysis
- [ ] Paper sections (`paper/related_work.tex`, `paper/background.tex`) — pending source drafts

## Ethics

All leakage/PII analysis runs only on the **public Pile** corpus and **open-weight
Pythia** — never on production systems for real third-party PII. No model training.
See [`docs/experiment_design.md`](docs/experiment_design.md) §7.
