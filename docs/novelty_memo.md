# Novelty Memo — Membership/Contamination Detection vs. Leakage Prediction

Prepared by Subagent N (novelty verification + citations). Every claim below was
checked against the actual paper (arXiv abstract page + arXiv HTML full text +,
where relevant, ACL Anthology). Verbatim quotes are marked with quotation marks.
Items that could not be fully verified are flagged `[VERIFY]`.

## Our contribution, restated (for novelty calibration)

On Pythia-160m with ground-truth Pile membership, we correlate per-item
membership/contamination detector scores (LOSS, Min-K%, Min-K%++, zlib) against a
per-item **extraction/leakage** outcome (prefix-continuation extractable
memorization). Our distinctive method is a **pre-registered partial correlation /
mediation controlling for raw LOSS**: the contamination->leakage association is
carried entirely by per-item loss; the calibrated reference-free detectors add no
independent predictive value beyond loss (partial rho|loss: Min-K% -0.178,
Min-K%++ -0.148, both FDR-significant and negative; zlib ~0). We frame this as a
membership-detection-vs-leakage-prediction **divergence**. Honest scope: this is
*not* a novel detector/metric; the contribution is the security reframing + a
systematic comparison + a controlled mediation result.

---

## Per-paper verified summaries

### 1. Al Sahili, Chehab & Tajeddine — CLOSEST PRIOR WORK
- **arXiv:2512.13352** (submitted 15 Dec 2025). arXiv preprint; no peer venue at read time.
- Title (verified): "On the Effectiveness of Membership Inference in Targeted Data
  Extraction from Large Language Models." Authors verified: Ali Al Sahili, Ali
  Chehab, Razane Tajeddine.
- Summary: integrates many MIA scores (LOSS, Min-K%, Min-K%++, zlib, S-ReCaLL,
  lowercase, ...) into a *targeted extraction* pipeline and asks whether they beat
  plain likelihood ranking. Evaluation = **ranking precision** (proportion of
  correctly extracted suffixes among top-ranked outputs) plus an **AdaBoost
  ensemble** over all MIA features.
- Verified quotes: "complex MIA techniques yield only marginal improvements over
  simple likelihood-based ranking"; "while certain methods (e.g., S-ReCaLL,
  Min K%) achieve consistent but marginal gains over the baseline ranking, most
  approaches perform comparably to the baseline"; "methods such as lowercase and
  Min-K%++ systematically underperform."
- Partial correlation / residualization / mediation: **verified NOT FOUND.**
- Relation to us: same *qualitative bottom line* (detectors barely beat
  likelihood for extraction) but different *epistemics*. They show **marginal
  aggregate gains** via ranking precision + a predictive ensemble; we show, via a
  pre-registered **partial correlation controlling for loss**, that the residual
  signal is **zero or negative** — a formal "no independent contribution"
  statement they do not make. Brief's characterization **CONFIRMED**.

### 2. Hayes et al.
- **arXiv:2505.18773**; **NeurIPS 2025** (comment field states NeurIPS 2025;
  versions v1 24 May 2025, v2 2 Nov 2025, v3 8 Jan 2026).
- **TITLE CORRECTION:** the brief's title "Strong Membership Inference Attacks on
  Massive Datasets and (Moderately) Large LLMs" is the **arXiv v1 header**; the
  current/published title is **"Exploring the Limits of Strong Membership
  Inference Attacks on Large Language Models."** The bib uses the published title
  and records the old v1 title in the comment.
- Summary: scales LiRA to GPT-2-style LMs (10M-1B params); strong MIAs succeed but
  remain limited (AUC < 0.7) with unstable per-sample decisions.
- Verified quotes: "We also study if there is any relationship between training
  data extraction and MIA, and observe no correlation with MIA success"; "This
  suggests that the two privacy attacks may capture different signals related to
  memorization"; "we observe no correlation between MIA and standard extraction
  methodology."
- Relation to us: closest on the **conceptual claim** (MIA != extraction). But
  their evidence is a **direct (zero-order) correlation** between a strong
  reference-model attack (LiRA) and extraction; they do **not** partial out raw
  per-item loss, and they study a *reference-model* attack, not the
  reference-free calibrated detectors (Min-K%, Min-K%++, zlib) that our security
  framing targets. We add the mechanism: the divergence survives *after*
  controlling for loss, and the calibrated detectors add nothing beyond it. Brief
  **CONFIRMED** (with the title caveat).

### 3. Chen, Han & Miyao
- **arXiv:2412.13475** (submitted 18 Dec 2024); **ACL 2025**, Proc. 63rd ACL,
  Vol. 1: Long Papers (Vienna), **pp. 22854-22874** [VERIFY exact Anthology ID].
- Title (verified): "A Statistical and Multi-Perspective Revisiting of the
  Membership Inference Attack in Large Language Models." Authors verified.
- Summary: large-scale statistical re-analysis of MIA on LLMs; overall MIA
  performance is low and detector advantages are often within seed variance.
- Verified quotes: "Loss baseline is only outperformed by Min-k% ++, Min-k%, and
  ReCaLL" **but** "their performance gap is within the variance from random
  seeds"; per-domain: "Wikipedia (en) and FreeLaw show statistically better
  performance compared to other domains"; "GitHub and StackExchange are related to
  codes that have less token diversity compared to FreeLaw and Wikipedia."
- **Honest nuance:** the brief said "most detectors do not statistically beat the
  loss baseline." More precisely, Chen et al. find a *few* (Min-K%++, Min-K%,
  ReCaLL) numerically beat loss, but the gaps are **within seed variance** — i.e.,
  not robustly significant. Statement is **CONFIRMED in spirit**; phrase it as
  "do not robustly/statistically beat loss once seed variance is accounted for,"
  not "no method ever beats loss."
- Relation to us: independently corroborates (a) loss-baseline parity for these
  detectors and (b) our **per-domain strata** (code-like, low-token-diversity
  domains are harder). They do this for the *membership* task; we extend to the
  *extraction* outcome with a controlled mediation.

### 4. Das, Zhang & Tramèr
- **arXiv:2406.16201** (submitted 23 Jun 2024; rev 30 Mar 2025); **DATA-FM @
  ICLR 2025** / IEEE DLSP Workshop 2025 [VERIFY exact proceedings string].
- Title/authors verified: "Blind Baselines Beat Membership Inference Attacks for
  Foundation Models," Debeshee Das, Jie Zhang, Florian Tramèr.
- Verified claim: "blind attacks -- that distinguish the member and non-member
  distributions without looking at any trained model -- outperform
  state-of-the-art MI attacks," across 8 published datasets; the flaw is sampling
  member/non-member from different distributions.
- Relation to us: a *methodological-validity* warning about MIA evaluation. We
  sidestep it by using **ground-truth Pile membership** (no post-hoc split), so
  the blind-baseline confound does not apply to our design. Supports our framing
  that detector "success" can be an artifact rather than memorization signal.

### 5. Meeus et al.
- **arXiv:2406.17975** (submitted 25 Jun 2024; rev 7 Mar 2025); **IEEE SaTML
  2025** (Secure and Trustworthy ML).
- Title/authors verified: "SoK: Membership Inference Attacks on LLMs are Rushing
  Nowhere (and How to Fix It)," Meeus, Shilov, Jain, Faysse, Rei, de Montjoye.
- Verified quote: post-hoc dataset construction induces member/non-member shift,
  and these shifts "invalidate the claims of LLMs memorizing strongly in
  real-world scenarios and, potentially, also the methodological contributions of
  the recent papers based on these datasets."
- Relation to us: SoK that motivates rigorous, ground-truth evaluation — exactly
  the discipline our pre-registered, true-membership Pythia/Pile design adopts.

### Spot-verification of already-cited entries
- **duan2024mia** — arXiv:2402.07841; venue **COLM 2024** (existing comment
  confirmed; MIMIR on Pythia/Pile). OK.
- **carlini2023quantifying** — arXiv:2202.07646; **ICLR 2023** (existing comment
  cites OpenReview TatRHT_1cK). Title/authors confirmed; defines extractable
  memorization (prefix-continuation). The abstract page alone does not restate the
  prefix-continuation definition verbatim, but the OpenReview ID + established
  usage support it. OK; `[VERIFY]` only the verbatim definition string if a
  reviewer demands it.
- **zhang2025minkpp** — arXiv:2404.02936; **ICLR 2025** (existing comment cites
  OpenReview ZGkfoufDaU, Spotlight). Title/authors confirmed. OK.

---

## Targeted search for pre-empting work

I actively searched (multiple queries) for any paper that performs
loss-residualization / partial correlation / formal mediation of a
membership-or-contamination detector against an **extraction or memorization**
outcome. **None found.** The closest are:
- Al Sahili (#1): ranking-precision + ensemble, "marginal gains" — not a
  residualized/partial-correlation argument.
- Hayes (#2): direct zero-order correlation MIA-vs-extraction — does not partial
  out loss, and uses LiRA rather than reference-free calibrated detectors.
- Chen (#3): seed-variance significance testing of detectors vs. loss for the
  *membership* task — not the extraction outcome, not a mediation.
No paper pre-empts the specific contribution (controlled mediation of calibrated
reference-free detectors against per-item extraction, showing zero/negative
residual beyond loss).

---

## VERDICT: adjacent-but-distinct (novel framing + method, not a reproduction)

The *direction* of our finding (detectors barely help beyond likelihood for
extraction) is consistent with #1 and #2, so we cannot claim the bottom line is
surprising. But the **method** (pre-registered partial correlation / mediation
controlling for raw loss) and the **specific object** (reference-free *calibrated*
contamination detectors -> per-item *extraction* outcome, with a quantified
zero/negative residual) are not done by any prior work we could verify. This is a
defensible "adjacent-but-distinct" contribution, **not** a reproduction. We must
cite #1 and #2 prominently and frame ourselves as the controlled/mechanistic
complement.

## One-sentence "to our knowledge" contribution statement

> To our knowledge, this is the first work to use a pre-registered partial
> correlation / mediation analysis — controlling for raw per-item loss — to show
> that calibrated reference-free contamination detectors (Min-K%, Min-K%++, zlib)
> add no independent signal beyond loss for predicting per-item extractable
> memorization, reframing the gap between membership detection and leakage
> prediction as a security-relevant divergence.

## Drop-in related-work text (distinguishing us from #1 and #2)

> Al Sahili et al. (arXiv:2512.13352) reach a compatible conclusion for targeted
> extraction — that "complex MIA techniques yield only marginal improvements over
> simple likelihood-based ranking" — but they establish it through aggregate
> *ranking-precision* comparisons and an AdaBoost ensemble over MIA features,
> reporting *marginal gains* rather than testing for independent signal. In
> contrast, we run a pre-registered *partial correlation controlling for raw
> per-item loss*, which lets us state the stronger, calibrated claim that the
> reference-free detectors contribute *zero or negative* residual predictive value
> once loss is partialled out.
>
> Hayes et al. (NeurIPS 2025) likewise "observe no correlation with MIA success"
> for extraction and conclude the "two privacy attacks may capture different
> signals," but their evidence is a *direct, zero-order* correlation between a
> reference-model attack (LiRA) and extraction. We differ on both method and
> object: we *partial out per-item loss* rather than correlating directly, and we
> target the reference-free *calibrated* detectors (Min-K%, Min-K%++, zlib) that
> the contamination-detection literature actually deploys, showing the divergence
> persists as a controlled mediation result.

---

## Could-not-verify / contradicts-brief list

- **Hayes title [CONTRADICTS BRIEF]:** brief title "Strong Membership Inference
  Attacks on Massive Datasets and (Moderately) Large LLMs" is the **arXiv v1**
  title; the published NeurIPS 2025 title is "Exploring the Limits of Strong
  Membership Inference Attacks on Large Language Models." Bib uses the published
  title; old title recorded in comment.
- **Chen "most detectors do not beat loss" [PARTIAL CONTRADICTION / nuance]:**
  Min-K%++, Min-K%, and ReCaLL *do* numerically beat the loss baseline in their
  experiments, but the gap is "within the variance from random seeds." Reframe as
  "not robustly/statistically beyond seed variance," not "no method beats loss."
- **Chen venue [VERIFY]:** confirmed ACL 2025 Vol. 1 Long Papers (Vienna),
  pp. 22854-22874 via search; the exact ACL Anthology ID string was not pulled
  from the canonical Anthology page — confirm `2025.acl-long.<NNNN>` before
  camera-ready.
- **Das venue [VERIFY]:** "DATA-FM @ ICLR 2025 / IEEE DLSP Workshop 2025" per
  arXiv metadata; entered as `@misc` (arXiv) to be safe — confirm the precise
  workshop proceedings string before camera-ready.
- **Al Sahili venue:** arXiv-only preprint at read time (Dec 2025); entered as
  `@misc`. No peer venue to verify.
- **carlini2023quantifying definition [VERIFY]:** ICLR 2023 venue and
  title/authors confirmed; the verbatim prefix-continuation definition string was
  not re-extracted from the abstract page (well-established in the literature).
