# Method-Selection Memo (Phase 1)

**Project:** Benchmark contamination as a privacy/security vulnerability in LLMs.
**Target venues:** IEEE S&P, USENIX Security, ACM CCS, NDSS.
**Date:** 2026-06-19. **Status:** decided — shortlist locked for implementation.

This memo derives the method list from the literature rather than assuming it. It
(i) ranks candidate detection methods, (ii) justifies a shortlist of methods to
implement, and (iii) records which methods were rejected and why. All citation keys
resolve to verified entries in `../references.bib`. Where the literature subagents
could not fully verify a field, it is flagged `[VERIFY]` in the .bib and must be
confirmed before camera-ready.

---

## 0. Decision summary (TL;DR)

**Implement (membership/contamination detectors):**
1. **LOSS / Perplexity threshold** — `yeom2018privacy` (mandatory baseline, anchors the overfitting↔privacy link).
2. **Min-K% Prob** — `shi2024detecting` (strong reference-free baseline; logprob-only).
3. **Min-K%++** — `zhang2025minkpp` (SOTA reference-free; our primary detector; needs full logits, which we have on Pythia).
4. **zlib-entropy ratio** — `carlini2021extracting` (cheap calibrated baseline; controls the "text is just compressible/common" confound).

**Implement (memorization/leakage side):**
5. **Extractable (prefix-continuation) memorization** — `carlini2023quantifying` (greedy-continuation extraction rate; the leakage outcome variable).

**Evaluation protocol (not a detector, but a hard requirement):**
- Ground-truth member/non-member splits on **Pythia + The Pile**, using the **MIMIR** setup from `duan2024mia`.
- Report **TPR @ 0.1% and 1% FPR with log-scale ROC** (`carlini2022lira`), AUC secondary.

**Headline analysis:** per-item **contamination score ↔ extraction/leakage outcome** correlation
(Spearman ρ + bootstrap CI). This is the contamination→memorization→leakage chain that makes
the paper a *security* result rather than a metric-inflation note.

**Rationale for the shortlist size (4 detectors + 1 extractor):** S&P reviewers expect a
*comparative* evaluation with at least one mandatory baseline (LOSS), the current SOTA
(Min-K%++), and a calibration control (zlib) that pre-empts the most obvious confound. More
than ~4 detectors dilutes the comparison without adding a distinct access-tier or confound-control
story; fewer leaves an obvious "why didn't you compare to X" hole.

---

## 1. Candidate ranking (all methods surveyed)

Ranked by fit to our setting: **ground-truth-auditable membership on Pythia/Pile, with
logit access available, framed as a security/privacy evaluation.** "Access" = minimum
adversary capability the method needs.

| Rank | Method | Access | Ground-truth fit | Citation strength | Decision |
|---|---|---|---|---|---|
| 1 | **Min-K%++** `zhang2025minkpp` | white-box (full logits) | evaluated on Pile/MIMIR | ICLR'25 Spotlight | **IMPLEMENT (primary)** |
| 2 | **Min-K% Prob** `shi2024detecting` | gray-box (logprobs) | defines WikiMIA; reproducible | ICLR'24 | **IMPLEMENT** |
| 3 | **LOSS / PPL** `yeom2018privacy` | gray-box (loss) | trivial on Pythia | CSF'18, foundational | **IMPLEMENT (baseline)** |
| 4 | **zlib ratio** `carlini2021extracting` | gray-box (perplexity) | in MIMIR's suite | USENIX'21, foundational | **IMPLEMENT (control)** |
| 5 | **Neighborhood** `mattern2023neighbourhood` | gray-box + masker | reference-free | ACL'23 Findings | DEFER (ablation/optional) |
| 6 | **Reference-model / LiRA** `carlini2022lira` | shadow models | impractical at Pile scale | S&P'22, foundational | REJECT as attack; ADOPT its metric |
| 7 | **Proving Test Set Contamination** `oren2024proving` | seq-logprob | benchmark-order, not per-example membership | ICLR'24 | IMPLEMENT (complementary, benchmark-level) |
| 8 | **Guided prompting** `golchin2024timetravel` | black-box text | closed-model contamination | ICLR'24 | DEFER (closed-model contrast only) |
| 9 | **n-gram / 13-gram overlap** `brown2020gpt3` | corpus access | corpus-side decontamination | NeurIPS'20 | IMPLEMENT (ground-truth construction aid) |
| 10 | **Canary / Secret Sharer** `carlini2019secret` | requires training injection | N/A (we don't train) | USENIX'19 | REJECT (needs control over training) |

---

## 2. Annotated bibliography (methods we implement or build on)

### 2.1 Detectors

**LOSS / Perplexity threshold — `yeom2018privacy`.**
Score $x$ by its loss under $f_\theta$; predict "member" iff loss < $\tau$. The paper
formalizes *membership advantage* = TPR − FPR and ties MIA success to the generalization
gap (overfitting). *Access:* gray-box loss. *Why include:* universal baseline; without it
reviewers cannot calibrate whether fancier detectors add anything. *Known weakness:* a
single global threshold over-flags intrinsically high-likelihood (short, frequent) text →
high FPR exactly in the low-overfitting LLM-on-Pile regime (`duan2024mia`). This weakness is
itself part of our story.

**Min-K% Prob — `shi2024detecting`.**
Average the log-probabilities of the $k\%$ lowest-probability tokens; members have a higher
(less negative) mean over their worst tokens. Reference-free, logprob-only. Introduces the
**WikiMIA** benchmark. Reports +7.4% AUC over prior best on WikiMIA. *Why include:* the
standard strong reference-free baseline; cheap and reproducible on Pythia. *Weakness:* still
a single-sample likelihood signal; WikiMIA's temporal split confounds membership with topic
drift (motivates our controlled-Pile ground truth).

**Min-K%++ — `zhang2025minkpp` (PRIMARY).**
Normalizes each token's log-prob by the mean/variance of the *full* next-token distribution
at that position (a z-score), then averages the bottom-$k\%$. Motivation: training samples
are local maxima of the modeled distribution, so the right signal is how peaked the target
token is relative to the whole vocabulary, not its raw probability. SOTA among reference-free
methods (+6.2–10.5% AUROC over runner-up on WikiMIA; gains on the harder Pile/MIMIR setting).
*Access:* white-box (full logits) — **we have this on Pythia.** *Why primary:* best
reference-free performance, directly evaluated on our exact ground-truth setting (Pile).

**zlib-entropy ratio — `carlini2021extracting`.**
Score = model perplexity divided by the zlib-compressed length (bits) of $x$. The compressor
estimates intrinsic text entropy, so dividing calibrates away "text any model finds
predictable." *Access:* gray-box perplexity + a standard compressor. *Why include:* the cheapest
possible **confound control** for the string-frequency/compressibility objection (reviewer
concern R1). Originally an *extraction* ranking signal, repurposed here as a calibrated
membership baseline (as in MIMIR's suite).

### 2.2 Memorization / leakage (the outcome variable)

**Extractable memorization — `carlini2023quantifying`.**
A string $s$ is *extractable with $k$ tokens of context* if a length-$k$ prefix from the
training data greedily regenerates $s$. Extraction rate = fraction of sampled training
sequences that are extractable. Establishes the three log-linear laws (scale, duplication,
context length) and the "GPT-J memorizes ≥1% of the Pile" headline. *Why central:* this is the
**leakage outcome** we correlate against contamination/detector scores. Greedy decoding makes
it deterministic and cheap to measure on Pythia.

**Supporting leakage definitions:** $k$-eidetic memorization (`carlini2021extracting`),
divergence/extraction at scale (`nasr2025scalable`), canary exposure (`carlini2019secret`),
counterfactual memorization (`zhang2023counterfactual`), and PII-leakage games
(`lukas2023pii`, `huang2022leaking`, `kim2023propile`). We use these for definitions and
framing; only extractable memorization is measured directly in the core pipeline. PII analysis
is run **only on the controlled Pile corpus** (ethics — see experiment design).

### 2.3 Evaluation protocol & ground truth

**MIMIR / "Do MIAs Work on LLMs?" — `duan2024mia`.**
Large-scale audit of LOSS, zlib, Min-K%, Neighborhood, reference-MIA on **Pythia (160M–12B) /
The Pile** with explicit member/non-member splits. Finding: MIAs barely beat chance (AUC
≈ 0.5–0.6) and apparent "success" often reflects temporal/distribution shift. *Why central:*
it is simultaneously our **ground-truth harness** (member/non-member construction on exactly
our model+corpus) and our honesty anchor (we must not overclaim detector power). Our
contribution is orthogonal: we ask whether the *weak* contamination signal still **predicts
privacy leakage**, which membership AUC alone does not address.

**MIA from First Principles / LiRA — `carlini2022lira`.**
We adopt its **evaluation methodology** (TPR at low FPR, log-scale ROC; average-case AUC is
misleading for a privacy threat) but **not** its attack (shadow-model training is infeasible at
Pile scale).

**Proving Test Set Contamination — `oren2024proving`.**
Permutation/exchangeability test giving a *provable*, FPR-controlled certificate that a
benchmark (in its canonical order) was trained on. Complementary to per-example membership: it
operates at the **benchmark** level. We implement it as a second, statistically rigorous lens
on benchmark contamination.

**n-gram / 13-gram overlap — `brown2020gpt3`.**
Corpus-side decontamination (flag a benchmark item sharing a 13-gram with the corpus). Needs
corpus access — feasible because the Pile is public. We use it to **construct and validate
ground-truth contamination labels** for benchmark items, not as a membership detector for the
model.

---

## 3. Rejected methods (and why)

- **Reference-model / shadow-model attacks (LiRA, `carlini2022lira`; Shokri et al.
  `shokri2017membership`) as our primary attack.** Rejected: they require training many shadow
  models on the training distribution. At Pile/Pythia scale this is computationally
  infeasible and would dominate the project budget. *We keep LiRA's metric, drop its attack.*
  A cheap single-reference-model variant (e.g., a smaller Pythia as the reference) is retained
  only as an optional ablation.

- **Canary / Secret Sharer (`carlini2019secret`).** Rejected for the core pipeline: it requires
  *injecting* canaries into training and retraining, i.e. control over the training process. We
  use pretrained Pythia checkpoints, so we cannot inject canaries. (Pythia's released training
  data order does, however, let us do controlled *duplication-count* analysis instead.)

- **Guided prompting / "Time Travel" (`golchin2024timetravel`).** Deferred, not core: it is a
  black-box, text-only contamination test designed for closed models without logit access. Our
  setting *has* logit access and ground-truth membership, where likelihood-based detectors are
  stronger and cleaner. Retained only if we add a closed-model contrast section.

- **Neighborhood comparison (`mattern2023neighbourhood`).** Deferred to an ablation: it needs
  many extra forward passes per example (neighbor generation via a masked-LM) and, per
  `duan2024mia`, still underperforms in the low-memorization Pile regime. Good as a
  reference-free calibration ablation, not worth the compute as a headline detector.

- **Differential-privacy defenses (`abadi2016deep`, `li2022dpllm`, `yu2022dpfinetuning`).** Not
  a detection method — cited as the **defense/mitigation** direction in related work and the
  discussion, not implemented (we do not train models).

---

## 4. Access-tier coverage (why this set is defensible to a reviewer)

A reviewer will ask whether the method set spans realistic adversary capabilities. It does:

| Access tier | Adversary capability | Covered by |
|---|---|---|
| black-box (text only) | API completions, no logprobs | (deferred) guided prompting; Oren needs seq-logprob |
| gray-box (logprobs/loss) | top-k logprobs from an API | LOSS, Min-K%, zlib |
| white-box (full logits/weights) | open-weight model | Min-K%++ (primary), extraction |
| corpus-side | access to training corpus | n-gram overlap (ground-truth labels) |

The core security claim (contamination predicts leakage) is demonstrated in the white-box /
ground-truth regime where it can be measured cleanly, then its implications are argued down to
weaker access tiers.

---

## 5. Honest-scoping statement (carried into the paper)

We do **not** propose a novel detector or a novel metric. Every method above is from prior
work. The contribution is (a) the **security reframing + threat model** of contamination as a
privacy vulnerability, (b) a **systematic comparative evaluation** of existing detectors under
the S&P low-FPR protocol on ground-truth Pile membership, and (c) the **empirical
contamination→leakage link**. Per `duan2024mia`, membership signal on pretrained LLMs is weak;
we therefore frame results around *whether even weak contamination signal predicts concrete
leakage*, with confidence intervals and confound controls, rather than around beating an AUC
leaderboard.

---

## 6. Outstanding citation-verification debts (must clear before camera-ready)

From the subagents' "could not verify" flags:
- `duan2024mia` venue string (COLM 2024 vs NAACL Findings) — confirm against proceedings.
- `ippolito2023verbatim` venue (INLG 2023?) — currently cited as preprint to be safe.
- Page spans flagged `[VERIFY]` in `references.bib` (Yeom, Lukas, Huang, Carlini'21, Mattern, Cheng).
- ICLR-2024 acceptance pages for `shi2024detecting`, `golchin2024timetravel` (asserted via OpenReview ids).
- Full author lists truncated with `others` (OLMo, Dolma, BLOOM, RedPajama, HumanEval, GPT-3) — fill from camera-ready PDFs.
