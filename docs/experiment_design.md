# Experiment Design (Phase 2)

**Project:** Benchmark contamination as a privacy/security vulnerability in LLMs.
Written before coding the full matrix. Citation keys → `../references.bib`.

---

## 1. Threat model

We frame contamination detection as a **membership/exposure attack** and define the adversary
explicitly (per the S&P reviewer checklist; `carlini2022lira`).

**Adversary goals (in increasing severity):**
- **G1 — Membership inference:** decide whether a specific sequence $x$ (a benchmark item, a
  document, a record) was in $X_{\text{train}}$.
- **G2 — Contamination confirmation:** decide whether a *benchmark* (set of items) was trained
  on, with a controlled false-positive rate.
- **G3 — Extraction / leakage:** recover verbatim content (and, on the controlled corpus, PII)
  that was in $X_{\text{train}}$.

**Adversary knowledge:** knows the model family and tokenizer; for ground-truth experiments we
(the auditors) additionally know the public training corpus (the Pile). The *attacker* in the
threat model does not need corpus access for G1/G3 (likelihood-based), but does for the
corpus-side n-gram labels we use to validate ground truth.

**Adversary access levels (we evaluate each detector at its minimum tier):**
- **Black-box:** text in, text out. (Guided prompting; deferred.)
- **Gray-box:** per-token logprobs / loss. (LOSS, Min-K%, zlib.)
- **White-box:** full next-token logits / weights. (Min-K%++ primary; extraction.)

**Success criteria:**
- G1: TPR @ 0.1%/1% FPR significantly above the FPR (i.e., above chance) with non-overlapping
  bootstrap CI; AUC reported secondarily.
- G2: permutation-test p-value < 0.05 with controlled FPR (`oren2024proving`).
- G3: non-zero extraction rate; for the headline, a significant positive correlation between
  per-item contamination score and per-item extraction/leakage outcome.

**Out of scope (stated to pre-empt reviewers):** we do not attack closed production models for
real third-party PII; we do not train or fine-tune models; we do not claim a novel detector.

---

## 2. Models

| Role | Model | Sizes | Corpus | Why |
|---|---|---|---|---|
| **Primary** | Pythia (`biderman2023pythia`) | 160M, 1.4B, 2.8B, (6.9B if compute allows) | The Pile (`gao2020pile`) | Public corpus + reconstructible batch order + 154 checkpoints + deduped/non-deduped variants = exact ground truth |
| **Dedup ablation** | Pythia-*-deduped | matched sizes | Pile (deduped) | Isolates the duplication confound (reviewer concern R2) |
| **Replication / contrast** | OLMo (`groeneveld2024olmo`) on Dolma (`soldaini2024dolma`) | 1B/7B | Dolma | Shows results generalize beyond the Pile; also fully open with checkpoints |

Checkpoints: use the final checkpoint for the main results; use intermediate Pythia checkpoints
(`step*`) for a memorization-vs-training-step analysis if time permits. GPT-2 is **excluded** as
ground truth (WebText never released).

**Scaling axis:** running ≥3 Pythia sizes lets us report whether the contamination→leakage link
strengthens with scale, mirroring the memorization scaling law of `carlini2023quantifying`.

---

## 3. Data: ground-truth positives vs. negatives

**Members (positives):** sequences sampled from the **public Pile** (so we *know* they are in
Pythia's training data). Sample across Pile subsets (web, books, code, papers) to avoid a
domain monoculture.

**Non-members (negatives):** the hard part. Options, in preference order:
1. **MIMIR splits (`duan2024mia`):** their released member/non-member sets for Pythia/Pile,
   constructed to control n-gram overlap between splits — the cleanest available ground truth.
2. **Temporal hold-out:** text created after the Pile's collection cutoff (used cautiously;
   the WikiMIA temporal confound is exactly what `duan2024mia` warns about).
3. **Within-corpus held-out:** documents from the same sources excluded from training (requires
   the training-order reconstruction tooling).

**Benchmark contamination sets:** MMLU (`hendrycks2021mmlu`), GSM8K (`cobbe2021gsm8k`), HellaSwag
(`zellers2019hellaswag`), TruthfulQA (`lin2022truthfulqa`), BoolQ (`clark2019boolq`), HumanEval
(`chen2021humaneval`). For each item we compute corpus-side **n-gram overlap with the Pile**
(`brown2020gpt3`) to get a ground-truth contamination label, then test whether detectors and
extraction recover it.

**Confound controls baked into data construction:**
- **R1 frequency:** match members/non-members on a frequency proxy (zlib bits and/or reference-LM
  perplexity) so detectors can't win by exploiting "this string is common."
- **R2 dedup:** run the full matrix on both deduped and non-deduped Pythia.
- **R3 temporal:** prefer corpus-membership ground truth over time-split benchmarks; if temporal
  data is used, report it separately and flagged.

---

## 4. Methods matrix (Models × Detectors × Datasets)

Detectors (rows): **LOSS, Min-K%, Min-K%++, zlib** (membership); plus **n-gram overlap**
(corpus-side label) and **Oren permutation test** (benchmark-level). Extraction
(prefix-continuation) runs alongside as the leakage outcome.

| | Pile member/non-member | MMLU | GSM8K | HellaSwag | TruthfulQA | BoolQ | HumanEval |
|---|---|---|---|---|---|---|---|
| Pythia-160m | ✔ all detectors + extraction | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Pythia-1.4b | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Pythia-2.8b | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Pythia-*-deduped (ablation) | ✔ | — | — | — | — | — | — |
| OLMo (replication) | ✔ | ✔ | ✔ | — | — | — | — |

Each cell caches: per-item detector scores, extraction outcome, and ground-truth label. The
runner (`run.py`) is resumable via result caching so partial matrices survive interruption.

---

## 5. Metrics (each with a justification — required by advisor)

| Metric | What it measures | Why it's the right metric here |
|---|---|---|
| **TPR @ FPR ∈ {0.1%, 1%}** (PRIMARY) | True positives caught while almost never false-accusing | A privacy breach = confidently identifying *some* members with few false alarms. Average accuracy/AUC hide whether the attack works in this regime (`carlini2022lira`). For "this item was in training," a false positive wrongly accuses a provider of contamination — exactly the asymmetry low-FPR TPR captures. |
| **log-scale ROC** | Full operating-characteristic, low-FPR legible | Linear ROC crushes the low-FPR region to invisibility; log-log axes are the S&P-expected figure (`carlini2022lira`). |
| **AUC-ROC** (secondary) | Threshold-free ranking quality | Continuity with prior MIA work and the MIMIR baseline (`duan2024mia`); reported but never the sole claim. |
| **Contamination / flag rate** | Fraction of benchmark items flagged at $\tau$ | Quantifies how much of a benchmark is implicated; ties detectors to the "evaluation is invalid" concern. |
| **Extraction rate** | Fraction of prefixes whose greedy continuation matches the held suffix | The concrete **leakage outcome** (`carlini2023quantifying`); deterministic and reproducible under greedy decoding. |
| **Contamination ↔ leakage correlation** (HEADLINE) | Whether per-item detector score predicts per-item extraction/leakage | This is the paper's thesis as a number: contamination is not just metric inflation but predicts privacy leakage. Spearman ρ (rank-based, robust to score-scale differences across detectors) with **bootstrap 95% CI**. |
| **Statistical significance** | Robustness of every headline number | ≥3 seeds; bootstrap CIs on TPR@FPR and ρ; permutation-test p-values for benchmark contamination (`oren2024proving`). Pre-empts the "single-run point estimate" objection (R4). |

---

## 6. Ablations / controls (pre-empting reviewer objections)

- **Dedup:** deduped vs non-deduped Pythia — does the signal survive deduplication? (R2)
- **Frequency confound:** detector AUC on frequency-matched vs unmatched splits. (R1)
- **Scale:** does the contamination→leakage correlation strengthen with model size? (ties to
  `carlini2023quantifying`)
- **Duplication count:** using Pythia's known training-data multiplicity, does extraction rate
  rise log-linearly with occurrence count? (validates ground-truth validity)
- **Checkpoint/temporal:** intermediate-checkpoint memorization growth (optional).

---

## 7. Ethics & reproducibility

**Ethics.** All PII/leakage analysis is performed on the **public, controlled Pile corpus** and
on **open-weight Pythia** — we never attempt to extract real private individuals' PII from
production systems. PII found in extraction is reported only in aggregate (counts/rates), never
reproduced verbatim in the paper. No model training, so no new memorization is induced. An ethics
statement and (for any future closed-model contrast) a responsible-disclosure note will be
included.

**Reproducibility.** Pinned environment (`requirements.txt`, exact `transformers`/`torch`/`datasets`
versions), fixed seeds, recorded model revisions (Hugging Face commit hashes for each Pythia
checkpoint), recorded hardware, and a one-command repro path (`python run.py --config configs/<x>.yaml`).
Every number in the paper traces to a row in `findings.md` with its config + git commit. Result
caching makes runs resumable and deterministic.

**Hardware plan.** Milestone-0 (scaffold + tests) runs on CPU with a tiny random-init model.
Milestone-1 (Pythia-160m perplexity + Min-K% separation) runs on CPU or a single consumer GPU.
The full matrix (≥2.8B, multiple datasets) targets a single A100/H100-class GPU or equivalent;
sizes above 2.8B are gated on available compute.
