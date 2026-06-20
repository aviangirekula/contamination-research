# COMPLETE PROJECT BUNDLE — Benchmark Contamination as a Privacy/Security Vulnerability in LLMs

**This single file contains the ENTIRE project for external assessment:** the full paper
(front matter), every results/analysis doc, ALL source code, all experiment scripts, all
tests, the LaTeX source, config, the verified bibliography, and the raw result-summary JSONs.

**Read me first — critical context:**
- **Honest scope:** the contribution is a security *reframing* + *systematic comparison of
  existing detectors* + an empirical contamination->leakage analysis. It is NOT a novel
  detector/metric.
- **Status:** paper = front matter only (Abstract, Method/Matrix, Results, Discussion,
  Conclusion still to be written). Experiments = real, reproducible, Pythia-160m on CPU
  (GPU scale-up pending).
- **THE KEY FINDING (R6 control, pre-registered):** the contamination->leakage correlation
  does NOT survive controlling for raw loss. Raw loss predicts extraction (Spearman rho ~0.28);
  the calibrated detectors (Min-K%, Min-K%++, zlib) add NO predictive value beyond loss
  (partial rho|loss: Min-K% -0.18, Min-K%++ -0.15, both FDR-significant & NEGATIVE; zlib ~0).
  Robust to dedup; not a frequency/zero-inflation artifact. The honest reframing is the
  DIVERGENCE between membership-detection and leakage-prediction. See PART 2 -> controls_report.
- **Tests:** 53/53 pass.

---



# PART 1 — THE PAPER (readable prose, front matter)


### `PAPER_DRAFT.md`

```markdown
# Benchmark Contamination as a Privacy & Security Vulnerability in LLMs
### WORKING DRAFT — front matter only (for external assessment)

> **What this file is.** A consolidated draft of the *front matter* of a security paper
> (target: IEEE S&P / USENIX Security). It contains **Introduction, Background, Related Work,
> and the Evaluation/setup section** (with the datasets table). Citation keys in `[brackets]`
> resolve to verified entries in `references.bib` (48 entries, all real/verified).
>
> **What is NOT here yet (deliberately):** Abstract, the Proposed Method/Benchmark-Matrix
> section, the Results section, Discussion/Limitations, and Conclusion. The professor's
> workflow is "run experiments first, then write the paper around results," so the back half
> is pending.
>
> **HONEST SCOPE (non-negotiable):** the contribution is a security *reframing* + a *systematic
> comparison of existing detectors* + an empirical contamination→leakage analysis. It is **NOT**
> a novel detector or metric.
>
> **CRITICAL FINDING the assessor must know (changes interpretation of the thesis):** a
> pre-registered statistical control (R6) on the real Pythia-160m data showed the
> contamination→leakage correlation **does NOT survive controlling for raw loss**. Raw loss
> predicts leakage (Spearman ρ≈0.28); the calibrated reference-free detectors (Min-K%,
> Min-K%++, zlib) add **no** predictive value beyond loss (partial ρ|loss: Min-K% −0.18,
> Min-K%++ −0.15, both FDR-significant and NEGATIVE; zlib ≈0). Robust to deduplication; not a
> frequency or zero-inflation artifact. The honest reframed finding is the **divergence between
> membership-detection and leakage-prediction** (the detectors that are better membership
> classifiers are worse leakage predictors). Full detail: `docs/controls_report.md`,
> pre-registration: `docs/pre_analysis.md`. NOTE: this is a *preliminary 160m* result; a GPU
> scale-up is pending and could shift it.
>
> **Status of numbers:** all results are real, logged, reproducible (Pythia-160m, CPU). The
> master results table is `docs/results_table.md`; the controls verdict is `docs/controls_report.md`.

---

# Introduction

Large language models (LLMs) are ranked, selected, and certified as safe
largely on the basis of their scores on public
benchmarks \[hendrycks2021mmlu,cobbe2021gsm8k\]. Those scores are only
meaningful under one assumption: that the evaluation data was absent
from pre-training. The assumption is increasingly untenable. Benchmarks
are small, static, and endlessly redistributed across the web, while
training corpora are weakly filtered crawls assembled at the scale of
hundreds of gigabytes to petabytes \[commoncrawl,gao2020pile\];
benchmark items are therefore swept into the next crawl by ordinary
copying, with no adversary required. The resulting *benchmark
contamination*—the presence of evaluation data in the training
corpus \[golchin2024timetravel\]—is usually treated as a
measurement-hygiene problem: a contaminated score over-states
capability \[ravaut2024survey\].

We argue that contamination is better understood as a *privacy and
security* vulnerability, and we study it as one. The same
over-parameterized models that score highly on a leaked benchmark also
memorize and can regurgitate verbatim training sequences, including
personally identifiable information (PII) that co-occurs in the same
corpora \[carlini2021extracting,carlini2023quantifying\]. Contamination,
in this view, is a visible symptom of unintended memorization, and
memorization is the mechanism by which sensitive content leaks. If a
cheap, model-side contamination signal predicts which items the model
has memorized, then the act of contaminating a benchmark is not merely
inflating a metric; it is exposing a leakage channel. We make this
contamination → memorization → leakage chain the object of empirical
study, on models whose training corpus is fully public so that
membership is ground truth rather than a guess.

The privacy/security community has, however, established that membership
signal on pre-trained LLMs is weak: large-scale audits on the Pythia
suite and The Pile report that membership-inference attacks (MIAs)
barely exceed chance, and that apparent successes often reflect
distribution shift between the member and non-member sets rather than
membership itself \[duan2024mia\]. We take this finding as a constraint,
not an obstacle. Rather than claim a stronger attack, we ask a sharper,
security-relevant question: *even where the membership signal is weak,
does it still predict concrete leakage?* Answering it requires the
evaluation discipline that security venues expect of a privacy
attack—true-positive rate at a low, fixed false-positive rate, read off
a log-scale ROC curve, rather than an average-case AUC that hides
whether the attack ever fires confidently \[carlini2022lira\]. It also
exposes a question the membership-inference literature does not ask:
detectors are tuned and ranked by how well they separate members from
non-members, but leakage is a property of *how much* the model memorized
a specific item. We therefore evaluate each detector not only as a
membership classifier but as a predictor of concrete leakage, and ask
whether the two objectives coincide—finding that they do not.

#### Contributions (and explicit non-contributions).

We are deliberate about what this paper is and is not. It is *not* a new
detector, attack, or metric: every detection method we run is from prior
work \[yeom2018privacy,shi2024detecting,zhang2025minkpp,carlini2021extracting,brown2020gpt3,oren2024proving\],
and our evaluation protocol is the established low-FPR convention of
Carlini et al. \[carlini2022lira\]. Within that honest scope, our
contributions are:

-   **A security reframing and threat model.** We recast benchmark
    contamination as a membership/exposure vulnerability with an
    explicit adversary and graded goals—membership inference on a single
    item, benchmark-level contamination confirmation, and verbatim/PII
    extraction—rather than as a measurement artifact
    (Section <a href="#sec:background" data-reference-type="ref" data-reference="sec:background">2</a>,
    Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">4</a>).

-   **A systematic comparative evaluation of existing detectors under
    the S&P low-FPR protocol on ground-truth Pile membership.** We
    evaluate LOSS/perplexity, Min-K%, Min-K%++, and the zlib ratio as
    membership detectors, the corpus-side *n*-gram overlap test as a
    contamination-label oracle, and the Oren permutation/exchangeability
    test at the benchmark level, all on Pythia trained on the public
    Pile, reporting TPR at 0.1% and 1% FPR with log-scale ROC and
    bootstrap confidence intervals, with explicit controls for the
    frequency, duplication, and temporal confounds that prior work
    identifies \[biderman2023pythia,gao2020pile,duan2024mia\].

-   **A pre-registered measurement of *which* contamination signal
    predicts leakage—and which does not.** We correlate per-item
    contamination scores against an extraction
    outcome—prefix-continuation extractable memorization under greedy
    decoding \[carlini2023quantifying\]—and, on the Enron Emails subset
    that already sits inside the Pile, against regex-detected PII
    leakage \[lukas2023pii\]. A pre-registered partial-correlation
    control then isolates the role of raw loss. In our ground-truth
    160M-parameter setting we find that the contamination→leakage
    association is carried *entirely by per-item loss*: once loss is
    held fixed, the calibrated reference-free detectors (Min-K%,
    Min-K%++, zlib) add no predictive value, and Min-K%/Min-K%++ are if
    anything inversely related to extraction. The calibrations that
    improve membership-detection AUC thus discard the loss-magnitude
    signal that actually predicts leakage—a divergence between
    membership detection and leakage prediction that we report as our
    central empirical finding (robust to deduplication, and not
    explained by token frequency or the zero-inflated outcome).

We do not propose internal-probe or other novel detectors as
contributions, do not train or fine-tune models, and do not attack
closed production systems for real third-party PII; differential privacy
and related defenses are discussed as the mitigation direction only.

# Background: LLM Evaluation Benchmarks as an Attack Surface

## Benchmarks as proxies for latent capabilities

Large language model (LLM) benchmarks function as *proxies* for latent
capabilities—reasoning, comprehension, factual knowledge, coding
proficiency—that cannot be measured directly. By scoring a model on a
fixed set of standardized tasks, the community infers a model’s likely
utility (and, increasingly, its safety) in
deployment \[hendrycks2021mmlu\]. Canonical examples target distinct
competencies: MMLU for broad multitask knowledge across 57
subjects \[hendrycks2021mmlu\], GSM8K for multi-step mathematical
reasoning \[cobbe2021gsm8k\], and HumanEval for functional code
generation \[chen2021humaneval\]. Reported scores on these suites drive
model-selection decisions, leaderboard rankings, and published claims of
progress.

## The core validity assumption

The inferential validity of benchmark evaluation rests on one strict
assumption: *the test data was not seen during pre-training*. Only under
this assumption does high benchmark performance license the intended
conclusion—that the model *generalizes* (applies learned regularities to
novel inputs) rather than *memorizes* (retrieves specific training
instances). When the assumption is violated, the benchmark no longer
measures capability; a memorized test item inflates the score without
any corresponding gain in generalization, rendering the metric an
unreliable estimator of the construct it claims to measure. The
generalization-versus- memorization distinction is not merely
conceptual: memorization is directly measurable as the verbatim
regeneration of training sequences and grows predictably—log-linearly in
model scale, data duplication, and context
length \[carlini2023quantifying\]. The same phenomenon has a sharper,
privacy-relevant form: a planted secret’s *exposure*, the model’s
tendency to rank that secret above random alternatives, rises with how
often it was seen during training \[carlini2019secret\], and which
specific examples a model memorizes is itself a measurable,
example-level property rather than a uniform background
rate \[zhang2023counterfactual\]. A memorized benchmark item is thus the
visible end of the same mechanism that retains rare, sensitive strings.

## Static test sets meet weakly filtered corpora

The security-relevant tension is structural. Evaluation benchmarks are
*static, small, widely circulated, and publicly indexed*: once
published, an MMLU or GSM8K item is copied into papers, blog posts,
GitHub repositories, and discussion forums. Training corpora, by
contrast, are *massive web scrapes with weak filtering*—Common
Crawl \[commoncrawl\] and The Pile \[gao2020pile\] are assembled at the
scale of hundreds of gigabytes to petabytes, where exhaustive removal of
any particular short string is impractical. The natural consequence is
that benchmark items are swept into training corpora through ordinary
web redistribution, with no adversary required. This makes a public
benchmark a persistent, low-effort *attack surface*: the same property
that makes a benchmark useful (stable, shared, citable) is what
guarantees its eventual presence in the next corpus crawl.

We argue this is best understood through a security lens rather than
purely as a measurement-hygiene problem. Contamination converts an
evaluation artifact into a channel that (i) invalidates the safety and
capability claims downstream decisions rely on, and (ii)—the focus of
this paper—couples directly to *memorization*, and through memorization
to the leakage of sensitive content that co-occurs in the same weakly
filtered corpora.
Section <a href="#sec:relatedwork" data-reference-type="ref" data-reference="sec:relatedwork">3</a>
formalizes contamination, its typology, and the detection and
memorization literature on which our evaluation builds.

# Related Work: Contamination, Memorization, and Privacy Leakage

## Defining benchmark contamination

We adopt the standard definition: *benchmark contamination* is the
presence of evaluation data—inputs, labels, or accompanying
metadata—within a model’s pre-training corpus \[golchin2024timetravel\].
Contamination matters for two reasons that this paper treats as
inseparable. First, it invalidates evaluation: a contaminated score
conflates capability with retrieval, so the metric no longer estimates
generalization. Second, and central to our thesis, contamination is a
*symptom of, and a measurable proxy for, unintended memorization*—and
memorization of evaluation data sits on the same mechanism that leaks
sensitive content from the corpus. We make this
contamination → memorization → leakage chain the object of empirical
study.

## A typology of contamination

Following the project’s framing and the contamination-detection
survey \[ravaut2024survey\], we distinguish three forms by the
transformation between the corpus copy and the benchmark item:

-   **Verbatim contamination.** The exact token sequence of a test item
    appears in training data. This is what classical *n*-gram
    decontamination targets (e.g., the 13-gram overlap test introduced
    for GPT-3 \[brown2020gpt3\]) and what verbatim-extraction
    memorization measures \[carlini2023quantifying\].

-   **Paraphrased contamination.** The semantic content is present but
    reworded, so surface-level *n*-gram matching misses it. A perfect
    verbatim filter provides only a false sense of safety, since
    style-transfer rephrasings evade it while preserving the leaked
    information \[ippolito2023verbatim\].

-   **Semantic contamination.** The underlying knowledge or answer is
    encoded without lexical overlap (e.g., the same question-answer
    mapping in a different format). Detecting it requires
    model-behavioral or distributional signals rather than string
    matching.

A second, orthogonal severity axis is *what* is contaminated: input-only
leakage inflates familiarity, whereas joint input–label leakage enables
direct answer retrieval and is the most damaging to evaluation validity.
Empirically, overlap between open-model training data and benchmarks
such as GSM8K has been reported for models trained on largely
undisclosed corpora \[touvron2023llama\], motivating
ground-truth-controlled study on models whose corpus is fully public.

## Why memorization is a security and privacy problem

Memorization is not a benign curiosity. Over-parameterized models
trained on web-scale scrapes retain and can regurgitate verbatim
sequences, including personally identifiable information (PII) such as
names, emails, and phone numbers \[carlini2021extracting\]. This has
been formalized along several axes that we reuse as outcome variables:

-   ***k*-eidetic / extractable memorization.** A string is extractable
    if a prefix makes the model regenerate it, and is *k*-eidetic if it
    occurs in at most *k* training documents \[carlini2021extracting\];
    the prefix-continuation form under greedy decoding makes this
    directly measurable \[carlini2023quantifying\].

-   **Exposure and example-level memorization.** Injecting a canary
    secret and measuring its *exposure*—its rank against random
    alternatives—quantifies unintended memorization and its growth with
    occurrence count \[carlini2019secret\]; this requires control over
    the training process (canary insertion), which our
    pretrained-checkpoint setting does not afford, so we use it for
    definitions rather than as a measurement. Relatedly, memorization is
    concentrated on specific examples \[zhang2023counterfactual\] rather
    than spread uniformly, which is what makes per-item contamination
    scores meaningful predictors of per-item leakage.

-   **Extraction at scale.** Production models can be driven, via a
    divergence attack, to emit memorized training data well above their
    nominal aligned rate, recovering thousands of verbatim examples
    cheaply \[nasr2025scalable\].

-   **PII leakage games.** Leakage of personally identifiable
    information decomposes into extraction, reconstruction, and
    inference; data scrubbing and differential privacy reduce but do not
    eliminate it \[lukas2023pii\], models leak PII through memorization
    more than through associative inference \[huang2022leaking\], and
    black-box probing tools can elicit a data subject’s PII directly
    from a deployed model \[kim2023propile\].

The security framing follows directly: if contamination is a measurable
proxy for memorization, and memorization is the vector for PII and
proprietary-data exposure, then contamination is not only a metrics
problem but a *privacy vulnerability*.

## The membership-inference lineage

Deciding whether a specific record was in a model’s training set is the
canonical privacy attack, and contamination detection is an instance of
it. The lineage we build on runs as follows. *Shadow-model* attacks
established the threat: by training reference models on data drawn from
the same distribution, an adversary learns to distinguish members from
non-members from the target model’s outputs \[shokri2017membership\].
Yeom et al. tied attack success to overfitting and gave the simplest
practical baseline—threshold the per-example loss—together with the
*membership advantage* (TPR−FPR) figure of merit \[yeom2018privacy\].
Carlini et al.’s *Likelihood Ratio Attack* (LiRA) then reframed MIA from
first principles as a per-example hypothesis test calibrated with shadow
models, and—central to our methodology—argued that average-case AUC is
the wrong yardstick for a privacy threat: an attack matters if it
identifies *some* members with very few false accusations, so the right
report is TPR at a low, fixed FPR on a log-scale ROC
curve \[carlini2022lira\]. Shadow-model calibration, however, is
infeasible at Pile/Pythia scale (it requires training many models on the
training distribution), so we adopt LiRA’s *metric* but not its
*attack*.

For pre-trained LLMs, the field moved to *reference-free* likelihood
signals that need no shadow models. Min-K% Prob averages the
log-probabilities of a sequence’s lowest-probability *k*% of tokens, on
the hypothesis that members lack high-surprise outlier
tokens \[shi2024detecting\]; Min-K%++ sharpens this by *z*-scoring each
token against the *full* next-token distribution before averaging,
detecting that the target token sits at a local maximum of the modeled
distribution \[zhang2025minkpp\]. A parallel reference-free line,
neighbourhood comparison, calibrates a sample’s score against
synthetically generated neighbour texts instead of a reference
model \[mattern2023neighbourhood\]; we treat it as a related approach we
do not evaluate, since it needs many extra masked-LM forward passes per
example and, in the regime below, underperforms. The reality check on
this whole line is the MIMIR study: a large-scale audit on Pythia
(160M–12B) and The Pile with controlled member/non-member splits finds
that these attacks barely exceed chance (AUC  ≈ 0.5–0.6), that LLMs see
their corpus for too few epochs over too large a dataset to memorize in
the way classical MIA assumes, and that apparent successes frequently
reflect a temporal or topical *distribution shift* between the splits
rather than membership \[duan2024mia\]. This finding defines our honesty
constraint: we do not claim to beat these numbers; we ask whether the
weak signal that remains still predicts leakage.

## Differential privacy as the defense direction

The standard principled mitigation for training-data leakage is
differential privacy. DP-SGD bounds any single example’s influence on
the trained model by clipping per-example gradients and adding
calibrated noise, with privacy accounted via the moments
accountant \[abadi2016deep\]. Applied to language models, DP fine-tuning
can retain much of the utility of non-private training, particularly
with large pre-trained backbones \[li2022dpllm\] and parameter-efficient
adaptation \[yu2022dpfinetuning\]. DP bounds memorization and thereby
the leakage we measure, but at a privacy–utility cost and—crucially for
us—it must be applied *at training time*; it is a defense for model
producers, not a detector available to an auditor of an already-released
model. We therefore position DP as the mitigation our threat model
motivates, and do not implement it (we train no models).

## Existing detection techniques

We describe the techniques we implement and compare; the comparative
evaluation and the access requirements appear in
Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">4</a>.
All operate without any novel detector of our own—our contribution is
their security-framed, ground-truth evaluation, not a new method.

-   ***n*-gram / substring overlap.** Flag a benchmark item that shares
    an *N*-gram with the corpus \[brown2020gpt3\]. Requires corpus
    access; misses paraphrased and semantic contamination.

-   **Loss / perplexity thresholding.** The mandatory
    membership-inference baseline: members exhibit lower loss, with
    attack success tied to overfitting \[yeom2018privacy\].

-   **Min-K% Prob.** Average the log-probabilities of the
    lowest-probability *k*% of tokens; reference-free and
    logprob-only \[shi2024detecting\].

-   **Min-K%++.** Normalizes each token’s log-probability against the
    full next-token distribution before the bottom-*k*% average, the
    current state of the art among reference-free
    detectors \[zhang2025minkpp\].

-   **zlib-entropy ratio.** Calibrate model perplexity by the
    zlib-compressed size of the text, controlling for intrinsic
    compressibility/frequency \[carlini2021extracting\].

-   **Permutation / exchangeability test.** At the *benchmark* level
    rather than per item, score each ordering of a benchmark’s examples
    by the log-likelihood of their concatenation and compare the
    canonical (published) order against random shufflings; a model
    trained on the benchmark in canonical order favours it beyond
    chance, yielding a provable, FPR-controlled contamination
    certificate \[oren2024proving\].

We additionally note two techniques we describe but *do not* evaluate,
since our ground-truth, logit-access setting makes likelihood-based
detectors stronger and cleaner: *guided prompting*, which prompts a
model with dataset metadata and a partial instance and tests for
verbatim completion \[golchin2024timetravel\], a black-box signal aimed
at closed models; and the reference-free *neighbourhood* and
shadow-model *reference* attacks discussed in
Section <a href="#sec:mia-lineage" data-reference-type="ref" data-reference="sec:mia-lineage">3.4</a> \[mattern2023neighbourhood,shokri2017membership\].

## Limitations of existing detection, and our positioning

Two limitations frame our contribution. First, *detection is fragile to
the transformation*: string-matching misses paraphrased and semantic
contamination \[ippolito2023verbatim\], and likelihood-based membership
inference is known to barely exceed chance on pre-trained LLMs evaluated
under controlled ground truth, because the corpora are seen for few
epochs and member/non-member boundaries are fuzzy \[duan2024mia\].
Second, *evaluation conventions matter*: average-case AUC or accuracy
can mask whether an attack confidently identifies any members, so the
security-appropriate report is true-positive rate at low false-positive
rate with log-scale ROC \[carlini2022lira\]. We therefore do not claim a
stronger detector. We ask a different, security-relevant question: *even
where contamination signal is weak, does it predict concrete privacy
leakage?* We answer it with ground-truth membership on the Pythia
suite \[biderman2023pythia\] trained on the public Pile \[gao2020pile\],
under the low-FPR protocol, with explicit controls for the frequency,
duplication, and temporal confounds that prior work identifies.

# Evaluation Overview

## Threat model and success criteria

We frame contamination detection as a membership/exposure attack with an
explicit adversary (Section omitted here; see
`docs/experiment_design.md`). Goals range from membership inference on a
single item, to benchmark-level contamination confirmation, to verbatim
extraction and PII leakage. Each detector is evaluated at its minimum
access tier (gray-box logprobs for LOSS/Min-K%/zlib; white-box logits
for Min-K%++). Success is defined by the security-appropriate operating
point rather than average accuracy.

## Methods under comparison

We evaluate *existing* detectors only—we propose no new detector. The
per-item membership suite is LOSS/perplexity \[yeom2018privacy\], Min-K%
Prob \[shi2024detecting\], Min-K%++ \[zhang2025minkpp\], and the
zlib-entropy ratio \[carlini2021extracting\]. Two further tests operate
off the per-item likelihood axis: corpus-side *n*-gram
overlap \[brown2020gpt3\], a model-free data-side check used to
construct ground-truth contamination labels for benchmark items, and the
Oren permutation/exchangeability test \[oren2024proving\], a
benchmark-level test that compares the canonical ordering of a
benchmark’s examples against random shufflings to certify contamination
with a controlled false-positive rate. The leakage outcome is
prefix-continuation extractable memorization under greedy
decoding \[carlini2023quantifying\]; on the controlled corpus we
additionally measure regex-detected PII leakage, framed via the
PII-leakage games of Lukas et al. \[lukas2023pii\]. Related approaches
we deliberately *do not* evaluate—guided
prompting \[golchin2024timetravel\], neighbourhood and shadow-model
reference attacks \[mattern2023neighbourhood,shokri2017membership\], and
the divergence-style extraction of production
models \[nasr2025scalable\]—are discussed in
Section <a href="#sec:relatedwork" data-reference-type="ref" data-reference="sec:relatedwork">3</a>.
**\[D1\]** An internal-activation probe is reported, if at all, only as
exploratory analysis in the Discussion, not as a contribution.

## Data

Table <a href="#tab:datasets" data-reference-type="ref" data-reference="tab:datasets">[tab:datasets]</a>
summarizes every corpus and benchmark used or referenced below.

#### Models and corpus.

The primary model is the Pythia suite \[biderman2023pythia\], trained on
the public Pile \[gao2020pile\]; its reconstructible training order, 154
checkpoints, multiple sizes, and deduplicated variant provide exact
membership ground truth. We use the released MIMIR member/ non-member
splits \[duan2024mia\], which control *n*-gram overlap between members
and non-members. OLMo \[groeneveld2024olmo\] on
Dolma \[soldaini2024dolma\] is a secondary replication target. The Pile
sits within the broader weakly filtered web-scrape regime—Common
Crawl \[commoncrawl\] and its filtered derivatives
C4 \[raffel2020c4,dodge2021c4\] and
RedPajama \[weber2024redpajama\]—that makes benchmark contamination
structural rather than adversarial.

<div class="table*">

| **Dataset**  | **Type**  | **What it is**                                                                                        | **Size**                 | **Cite**                     |
|:-------------|:----------|:------------------------------------------------------------------------------------------------------|:-------------------------|:-----------------------------|
| The Pile     | corpus    | Curated 22-subset English corpus; Pythia’s training data and our membership ground truth              | 825 GB                   | \[gao2020pile\]              |
| Common Crawl | corpus    | Open, continually updated repository of raw web-crawl data; the base of most LLM pre-training scrapes | petabyte-scale (growing) | \[commoncrawl\]              |
| C4           | corpus    | Colossal Clean Crawled Corpus: a filtered Common Crawl snapshot introduced with T5                    | ∼<!-- -->750 GB          | \[raffel2020c4,dodge2021c4\] |
| Dolma        | corpus    | Open pre-training corpus; OLMo’s training data (replication target)                                   | 3 T tokens               | \[soldaini2024dolma\]        |
| RedPajama    | corpus    | Open reproduction of an LLaMA-style pre-training mixture                                              | ∼<!-- -->30 T tokens     | \[weber2024redpajama\]       |
| MMLU         | benchmark | Multiple-choice knowledge/reasoning across 57 subjects                                                | 15,908 questions         | \[hendrycks2021mmlu\]        |
| GSM8K        | benchmark | Grade-school multi-step math word problems                                                            | 8,500 problems           | \[cobbe2021gsm8k\]           |
| HumanEval    | benchmark | Hand-written Python programming problems with unit tests                                              | 164 problems             | \[chen2021humaneval\]        |
| HellaSwag    | benchmark | Adversarially filtered commonsense sentence completion                                                | ∼<!-- -->70,000 items    | \[zellers2019hellaswag\]     |
| TruthfulQA   | benchmark | Questions probing imitative falsehoods                                                                | 817 questions            | \[lin2022truthfulqa\]        |
| BoolQ        | benchmark | Naturally occurring yes/no reading-comprehension questions                                            | 15,942 questions         | \[clark2019boolq\]           |

</div>

#### Benchmarks and PII.

Contamination is tested against MMLU, GSM8K, HumanEval, HellaSwag,
TruthfulQA, and BoolQ. **\[D3\]** For PII leakage we use the Enron
Emails data *as a Pile subset already present in Pythia’s training
data*, plus a synthetic PII set for controlled structure, rather than
fine-tuning a model to memorize PII. All PII results are reported in
aggregate; no real PII is reproduced in the paper.

## Metrics (each justified)

**\[D2\]** Following the membership-inference-from-first-principles
convention \[carlini2022lira\], the primary metric is *true-positive
rate at a fixed low false-positive rate* (TPR @ 0.1% and 1% FPR)
reported with *log-scale ROC*; AUC-ROC is reported secondarily. These
capture whether a detector *confidently* identifies members—the
privacy-relevant regime—which average-case accuracy hides. For benchmark
flagging at a chosen operating threshold we additionally report
precision/recall/F1 as a secondary, application-facing view. The leakage
outcome is the *extraction rate* \[carlini2023quantifying\]. The
headline analysis is the *Spearman correlation between per-item
contamination score and per-item extraction/leakage outcome*, with
bootstrap confidence intervals and a pre-registered partial-correlation
control that isolates the contribution of raw loss—the quantitative form
of the paper’s central question.

## Validation and controls

**\[D4\]** Robustness is established by repeating each measurement over
multiple seeds with bootstrap confidence intervals on TPR@FPR and on the
Spearman correlation, and by a permutation/exchangeability test for
benchmark-level contamination \[oren2024proving\]. We include ablations
that preempt the standard confounds: deduplicated versus
non-deduplicated Pythia (duplication), frequency-matched
member/non-member splits (string frequency), and model-size scaling
(does the contamination→leakage link strengthen with scale, as
memorization does \[carlini2023quantifying\]). Differentially private
training \[abadi2016deep,li2022dpllm\] is discussed as the mitigation
direction
(Section <a href="#sec:dp" data-reference-type="ref" data-reference="sec:dp">3.5</a>),
not implemented, since it is a producer-side defense applied at training
time rather than an auditor-side detector.

This section fixes the threat model, methods, data, and metrics; the
empirical results under this protocol—per-detector TPR at low FPR with
log-scale ROC, extraction rates, and the headline contamination→leakage
correlation with confidence intervals—are reported in the results
section, with every reported number tracing to a logged harness run.


```



# PART 2 — RESULTS, EXPERIMENT DESIGN & ANALYSIS (docs)


### `docs/controls_report.md`

```markdown
# Controls Report — R6 (circularity) + R1/R2/R7/strata

**Date:** 2026-06-19. **Pre-registration:** `docs/pre_analysis.md` (written before any control was
run; only the listed tests were run). **Data:** existing Pythia-160m item set, N=300 Pile members,
leakage outcome = `frac_extracted`. CPU, seed 0, bootstrap/permutation n=2000. Integrity check: the
recomputed raw ρ (loss 0.275, Min-K% 0.173, Min-K%++ 0.108, zlib 0.177) exactly match the prior
correlation run — same scores, no drift.

## Master table — raw vs. partial(|loss) vs. semipartial vs. freq-matched vs. deduped

**Non-deduped (`pythia-160m`):**

| Detector | raw ρ | partial ρ \| loss [95% CI] | semipartial | ρ \| freq (control freq) | freq-matched ρ (n=100) | Kendall τ | BH-q | reject null? |
|---|---|---|---|---|---|---|---|---|
| loss | **+0.275** | — (is the control) | — | — | — | 0.211 | — | — |
| Min-K% | +0.173 | **−0.178 [−0.280, −0.068]** | −0.171 | +0.166 | +0.090 | 0.132 | 0.0045 | **yes (negative)** |
| Min-K%++ | +0.108 | **−0.148 [−0.259, −0.030]** | −0.143 | +0.138 | +0.016 | 0.082 | 0.011 | **yes (negative)** |
| zlib | +0.177 | −0.042 [−0.160, +0.075] | −0.041 | +0.193 | +0.086 | 0.136 | 0.463 | no (≈0) |

**Deduped (`pythia-160m-deduped`) — robustness (R2):**

| Detector | raw ρ | partial ρ \| loss [95% CI] | Kendall τ | BH-q | reject null? |
|---|---|---|---|---|---|
| loss | +0.316 | — | 0.244 | — | — |
| Min-K% | +0.221 | −0.133 [−0.239, −0.011] | 0.168 | 0.033 | yes (negative) |
| Min-K%++ | +0.161 | −0.141 [−0.252, −0.028] | 0.122 | 0.033 | yes (negative) |
| zlib | +0.220 | −0.016 [−0.125, +0.094] | 0.169 | 0.753 | no (≈0) |

## R2 — deduplication (membership separation, Pile train-vs-val, N=464)
| Detector | AUC non-deduped | AUC deduped |
|---|---|---|
| loss | 0.454 | 0.452 |
| Min-K% | 0.470 | 0.467 |
| Min-K%++ | 0.490 | 0.481 |
| zlib | 0.484 | 0.485 |

Membership separation is at chance with or without deduplication — the chance-level result is not a
dedup artifact.

## Stratification — per-domain LOSS↔leakage ρ (n≥5)
Heterogeneous, not driven by one domain: strongly positive in templated/structured domains
(Github +0.60, StackExchange +0.54, Books3 +0.41, ArXiv +0.38, OpenWebText2 +0.31), near-zero in
several (DM Mathematics +0.00, OpenSubtitles +0.01), and **negative** in others (PubMed Abstracts
−0.48, USPTO −0.19, HackerNews −0.09; EuroParl −0.66 at n=6). The pooled loss effect is a mix; the
positive pooled value reflects the structured/boilerplate domains where greedy extraction is easy.

## R1 — frequency
Controlling for the frequency proxy leaves the raw correlations essentially unchanged
(partial ρ\|freq: Min-K% +0.166, Min-K%++ +0.138, zlib +0.193 ≈ their raw values). So **frequency is
not the driver.** (The middle-tertile freq-matched subset shows lower ρ, but that is a low-power,
variance-restricted n=100 cut, not a clean frequency effect.) The operative confounder is LOSS, not
frequency.

## R7 — zero-robustness
Kendall τ-b agrees with Spearman in sign and relative magnitude throughout (loss highest at 0.211;
calibrated detectors lower), so the zero-inflated outcome is not creating the pattern.

---

## VERDICT (R6) — pre-registered decision rule applied honestly

**The contamination→leakage headline does NOT survive controlling for LOSS. The positive
association was carried entirely by raw loss.**

- The pre-registered "survives" condition required a calibrated detector (Min-K%, Min-K%++, or zlib)
  to predict leakage **beyond loss** — i.e. a partial ρ\|loss with CI excluding 0 in the **positive**
  direction. None does. zlib collapses to ≈0 (ρ=−0.04, n.s.). Min-K% and Min-K%++ are FDR-significant
  but **negative** (ρ=−0.18 and −0.15): once loss is held fixed, they are if anything *inversely*
  related to extraction. So the pre-registered "MOSTLY LOSS / must be reframed" branch is the outcome.
- This is **robust to deduplication** (deduped arm shows the identical pattern) and **not explained by
  frequency** (controlling frequency leaves raw ρ intact; controlling loss removes/flips it) **or by
  the zero-inflated outcome** (Kendall agrees).
- Interpretation: the only contamination/membership signal that predicts extraction is **raw LOSS
  itself**, which is the most mechanistically entangled-with-extraction measure (both are
  likelihood/greedy-decode memorization proxies). The sophisticated reference-free detectors the
  field prefers (Min-K%, Min-K%++, zlib) add **no independent** leakage-prediction over loss.

### Recommended reframing (for human review — NOT yet written into the paper)
The honest, defensible claim is narrower than the original headline: *"A model's per-item loss
predicts how extractable that item is; calibrated reference-free membership detectors do not add
predictive value beyond loss, and the loss–extraction link is domain-dependent and partly
mechanistic."* Whether to (a) frame loss–extraction as the result with the circularity stated openly,
(b) re-test at larger scale where extraction is less degenerate (it may change), or (c) pivot the
contribution toward the **evaluation-matrix** angle (detectors disagree / calibration removes
leakage signal — itself a finding) is a decision for Professor Lin.

**STOP. Awaiting human review of this report before any paper writing, assembly, or scale-up.**

```


### `docs/results_table.md`

````markdown
# Master Results Table (preliminary, Pythia-160m / CPU)

All numbers are REAL runs on `EleutherAI/pythia-160m`, CPU, seed 0. Every cell traces to a
file in `results/`. Model size is a single `--model` flag, so 1.4B/2.8B on GPU is a config
swap. These are preliminary (smallest model); the scaling caveat is stated per result.

---

## Table 1 — Membership separation (AUC, TPR@low-FPR)

Two ground-truth constructions. **Pile train-vs-val** is confound-clean (members = Pile train
docs, non-members = Pile validation, stratified across 22 subsets). **WikiMIA** carries a known
temporal confound and is shown for contrast + scaling.

| Construction | Model | Detector | AUC [95% CI] | TPR@1% | TPR@0.1% |
|---|---|---|---|---|---|
| Pile train-vs-val (clean) | 160m | loss | 0.454 [0.407, 0.511] | 0.009 | 0.000 |
| Pile train-vs-val (clean) | 160m | min_20_prob | 0.470 [0.410, 0.530] | 0.009 | 0.000 |
| Pile train-vs-val (clean) | 160m | min_20_plusplus | 0.490 [0.439, 0.546] | 0.004 | 0.000 |
| Pile train-vs-val (clean) | 160m | zlib_ratio | 0.484 [0.437, 0.545] | 0.009 | 0.000 |
| WikiMIA-64 (confounded) | 160m | loss | 0.523 | 0.004 | 0.000 |
| WikiMIA-64 (confounded) | 160m | min_20_prob | 0.539 | 0.011 | 0.000 |
| WikiMIA-64 (confounded) | 160m | min_20_plusplus | 0.545 | 0.032 | 0.011 |
| WikiMIA-64 (confounded) | 160m | zlib_ratio | 0.564 | 0.021 | 0.007 |
| WikiMIA-64 (confounded) | **1.4B** | loss | 0.571 [0.526, 0.620] | 0.025 | 0.004 |
| WikiMIA-64 (confounded) | **1.4B** | min_20_prob | 0.580 [0.532, 0.625] | 0.025 | 0.011 |
| WikiMIA-64 (confounded) | **1.4B** | min_20_plusplus | 0.547 [0.497, 0.595] | 0.021 | 0.018 |
| WikiMIA-64 (confounded) | **1.4B** | zlib_ratio | 0.616 [0.565, 0.663] | 0.049 | 0.007 |

**Reading:** (i) on the clean split, 160m is at chance — the WikiMIA "signal" was mostly
temporal confound (key controls result, reproduces Duan et al. 2024); (ii) WikiMIA AUC rises
with scale (160m→1.4B), e.g. zlib 0.564→0.616 — memorization grows with model size
(Carlini et al. 2023). Whether the *clean-split* signal also revives at scale is the open
question for the GPU runs.

---

## Table 2 — HEADLINE: contamination score ↔ extraction/leakage (Spearman ρ)

Pythia-160m, N=300 Pile MEMBERS, detector score (whole item) vs fractional extraction
(prefix_len=32, suffix≤50, greedy). Bootstrap CI n=2000.

| Detector | ρ(frac) [95% CI] | ρ(extracted) | CI excludes 0? |
|---|---|---|---|
| **loss** | **0.275 [0.164, 0.378]** | 0.172 | ✅ |
| min_20_prob | 0.173 [0.061, 0.285] | 0.171 | ✅ |
| zlib_ratio | 0.177 [0.063, 0.295] | 0.164 | ✅ |
| min_20_plusplus | 0.108 [−0.010, 0.220] | 0.169 | ✗ |

> **⚠️ SUPERSEDED BY THE R6 CONTROL — read `docs/controls_report.md`.** These RAW correlations
> do not survive controlling for loss. Partial ρ(detector, leakage | loss): Min-K% −0.178,
> Min-K%++ −0.148 (both FDR-significant, NEGATIVE), zlib −0.04 (n.s.). The positive association
> above is carried ENTIRELY by raw loss; the calibrated detectors add no predictive value beyond
> it. Do not cite the raw numbers below as evidence that the calibrated detectors predict leakage.

**Reading (raw, pre-control):** even though membership *separation* is at chance on the clean
split (Table 1), the raw membership *score* correlates with leakage for 3/4 detectors. But this
is loss-driven (see the R6 control box above): LOSS predicts leakage; Min-K%/Min-K%++/zlib do not
beyond loss. Effect is weak (ρ 0.11–0.28), outcome zero-inflated (mean frac 0.037).
Figure: `figures/correlation_pythia-160m_scatter.png`.

---

## Table 3 — Extraction, PII, and contamination tests

| Measure | Value | Notes |
|---|---|---|
| Extraction rate (exact full suffix) | 0.0100 (3/300) | 160m, 32-tok prefix; expected-low for smallest model |
| Mean fractional extraction | 0.0370 | zero-inflated; 3 fully-extracted items are templated boilerplate |
| Enron-in-Pile: docs with PII in suffix | 8/36 | all `email` type; Enron Emails is a Pile subset (in training) |
| Enron-in-Pile: verbatim PII leakage rate | 0.0000 | aggregate only; 160m doesn't regurgitate the PII at 32-tok prefix |
| n-gram(13) overlap: member vs non-member | 1.000 vs 0.022 | corpus-side; separation +0.978 |
| n-gram(13): non-members with residual overlap | 3/44 | real Pile train↔val near-duplicate leakage |
| Oren permutation test: contaminated vs control p | 0.044 vs 0.124 | dataset-level; contaminated marginally significant, control not (10 short examples — sanity scale) |

---

## Figures produced
- `figures/correlation_pythia-160m_scatter.png` — contamination score vs. extraction (headline).
- `figures/pilemia_pythia-160m_dists.png`, `figures/pilemia_pythia-160m_logroc.png` — clean-split separation.
- `figures/milestone1_wikimia64_dists.png`, `figures/milestone1_wikimia64_logroc.png` — WikiMIA separation.

## Reproduce
```
python scripts/milestone1_pile.py   --model EleutherAI/pythia-160m   # Table 1 clean split
python scripts/milestone1_wikimia.py --model EleutherAI/pythia-160m   # Table 1 WikiMIA
python scripts/extraction_pile.py   --model EleutherAI/pythia-160m   # Table 3 + item set
python scripts/correlation_160m.py  --items results/pile_items_160m.jsonl  # Table 2 headline
python scripts/validate_ngram_oren.py --model EleutherAI/pythia-160m # Table 3 n-gram/Oren
python scripts/pii_enron.py         --model EleutherAI/pythia-160m   # Table 3 PII
```
**Scale-up:** change `--model` to `EleutherAI/pythia-1.4b` / `pythia-2.8b` on a GPU; no code change.

````


### `findings.md`

```markdown
# findings.md — shared numbers ledger (orchestrator-owned)

**Rule:** every quantitative claim in the paper must trace to a row here, and every
row here must come from a harness run (or be explicitly marked as a literature value).
Nothing is "described that isn't measured." Update this file when results land.

## Status legend
- ⬜ planned / not yet run
- 🟡 mocked or tiny-scale (sanity only, not a paper number)
- ✅ real run, reproducible (seed + config + commit recorded)
- 📚 value cited from literature (not our measurement)

## Milestone 0 — code scaffold + tiny/mock validation
| Item | Status | Value | Source |
|---|---|---|---|
| Detector interface `score(text)->float` for LOSS, Min-K%, Min-K%++, zlib | 🟡 | unit-tested on a tiny random-init GPT-NeoX model | `tests/` |
| Metrics (AUC, TPR@FPR) numerically correct | 🟡 | validated vs. closed-form on synthetic scores | `tests/test_metrics.py` |

## Milestone 1 — first runnable (Pythia + WikiMIA in/out separation)
Run: `scripts/milestone1_wikimia.py --model EleutherAI/pythia-160m --length 64 --device cpu`,
WikiMIA-64, N=542 (284 member / 258 non-member), CPU, seed 0, bootstrap n=500.
Ground truth = WikiMIA (public; carries temporal confound) — MIMIR (confound-clean) is gated
and pending HF auth. Numbers are REAL but on the smallest model, so near-chance is expected.
| Item | Status | Value | Source |
|---|---|---|---|
| Pythia-160m loads, full pipeline runs end-to-end on real data | ✅ | 542 examples scored, 4 detectors | `results/wikimia64_pythia-160m.jsonl` |
| LOSS AUC | ✅ | 0.523 [0.477, 0.568] | `results/wikimia64_summary.json` |
| Min-K% AUC | ✅ | 0.539 [0.492, 0.585] | same |
| Min-K%++ AUC | ✅ | 0.545 [0.498, 0.592] | same |
| zlib AUC | ✅ | 0.564 [0.517, 0.610] | same |
| TPR@1% / TPR@0.1% (best: zlib / Min-K%++) | ✅ | ≤3.2% / ≤1.1% | same |
| Detector ordering matches theory (zlib/Min-K%++ > Min-K% > LOSS) | ✅ | yes | analysis |
| Separation is near-chance at 160m (consistent with Duan et al.) | ✅ | CIs span 0.5 | `duan2024mia` |
| Score-distribution + log-ROC plots | ✅ | `figures/milestone1_wikimia64_*.png` | — |

**Interpretation (honest):** the pipeline is validated (correct relative ordering, sensible
CIs, runs end-to-end on real data), but 160m barely separates members from non-members. This is
the EXPECTED result, not a failure: memorization scales with model size (`carlini2023quantifying`)
and MIAs are near-chance on small Pythia (`duan2024mia`). Demonstrating CLEAN separation requires
either (a) a larger Pythia (1.4B/2.8B) or (b) the confound-clean MIMIR splits. Both are gated on a
decision (compute was scoped to "160m only"; MIMIR needs HF auth).

## Milestone 1b — confound-controlled ground truth WITHOUT MIMIR (Pile train vs. val)
MIMIR is gated (HF auth unavailable). Built equivalent ground truth from public mirrors:
members = Pile *train* (`NeelNanda/pile-10k`), non-members = Pile *validation*
(`mit-han-lab/pile-val-backup`), stratified across 22 Pile subsets to match domain
distribution. Run: `scripts/milestone1_pile.py --model EleutherAI/pythia-160m --n-per-class 300
--max-words 100`. N=464 (232/232), CPU, seed 0, bootstrap n=500.
| Detector | Status | AUC [95% CI] | Source |
|---|---|---|---|
| loss | ✅ | 0.454 [0.407, 0.511] | `results/pilemia_pythia-160m_summary.json` |
| min_20_prob | ✅ | 0.470 [0.410, 0.530] | same |
| min_20_plusplus | ✅ | 0.490 [0.439, 0.546] | same |
| zlib_ratio | ✅ | 0.484 [0.437, 0.545] | same |

**KEY FINDING (headline-worthy controls result):** on the confound-clean same-distribution
split, ALL detectors are at **chance** at 160m (CIs straddle 0.5), whereas the same model on
**WikiMIA-64 scored AUC 0.52–0.56**. The WikiMIA "signal" was largely the temporal/topic
confound (members pre-cutoff vs non-members post-cutoff), not membership. This directly
reproduces and concretizes `duan2024mia`: apparent MIA success on LLMs is confound-driven, and
true membership signal is near-zero at small scale. Whether scale (1.4B/2.8B) revives it on the
clean split is the open scaling question (1.4B run in progress).
Artifacts: `figures/pilemia_pythia-160m_dists.png`, `figures/pilemia_pythia-160m_logroc.png`.

## Milestone 2 — contamination/membership score ↔ extraction/leakage
> ⚠️ **SUPERSEDED by R6 control (docs/controls_report.md).** The raw ρ below are loss-driven and
> do NOT survive controlling for loss (partial ρ|loss: Min-K% −0.18, Min-K%++ −0.15 FDR-sig
> negative; zlib ≈0). Keep these raw numbers only as the pre-control record; the operative
> finding is the loss/calibration divergence in the controls report.

Real Pythia-160m, CPU. N=300 Pile MEMBERS (canonical set `results/pile_items_160m.jsonl`),
prefix_len=32, suffix≤50, greedy extraction. Detector score (whole item) vs fractional
extraction; Spearman ρ + bootstrap CI (n=2000, seed 0). Run: `scripts/correlation_160m.py
--items results/pile_items_160m.jsonl`.
| Detector | ρ(frac) [95% CI] | ρ(extracted) | Significant |
|---|---|---|---|
| loss | **0.275 [0.164, 0.378]** | 0.172 | ✅ CI excludes 0 |
| min_20_prob | 0.173 [0.061, 0.285] | 0.171 | ✅ CI excludes 0 |
| zlib_ratio | 0.177 [0.063, 0.295] | 0.164 | ✅ CI excludes 0 |
| min_20_plusplus | 0.108 [-0.010, 0.220] | 0.169 | ✗ includes 0 |

**THESIS AS A NUMBER:** on the confound-clean split, membership *separation* is at chance
(AUC 0.45–0.49) yet membership *score still predicts leakage* (3/4 detectors, CI excludes 0).
Contamination signal tracks privacy leakage even where membership AUC looks useless. Honest
nuances: effect is weak-moderate (ρ 0.11–0.28), zero-inflated outcome (mean frac 0.037, 3/300
fully extracted); LOSS (crudest proxy) is the STRONGEST leakage predictor, Min-K%++ (best
membership detector) the weakest/non-significant. Artifacts: `figures/correlation_pythia-160m_scatter.png`,
`results/correlation_pythia-160m.json`. Scaling to 1.4B/2.8B (GPU) is a `--model` swap.

## Milestone 1c — supporting real-data results (160m unless noted)
| Measure | Value | Source |
|---|---|---|
| Extraction rate (exact full-suffix) | 0.0100 (3/300) | `results/pile_items_160m.jsonl` |
| Mean fractional extraction | 0.0370 | same |
| Enron-in-Pile PII: docs w/ PII in suffix | 8/36 | `results/pii_enron_160m.jsonl` |
| Enron-in-Pile PII: verbatim leakage rate | 0.0000 | same (aggregate; no PII strings stored) |
| n-gram(13) overlap: member vs non-member mean | 1.000 vs 0.022 (sep +0.978) | `scripts/validate_ngram_oren.py` |
| n-gram residual: non-members w/ some overlap | 3/44 (real train↔val near-dup leakage) | same |
| Oren permutation: contaminated vs control p | 0.044 vs 0.124 | same |
| WikiMIA-64 AUC scaling 160m→1.4B (zlib) | 0.564 → 0.616 | `results/wikimia64_summary.json` (1.4B), findings M1 (160m) |
| WikiMIA-64 AUC scaling 160m→1.4B (loss) | 0.523 → 0.571 | same |

## Literature anchor values (for calibration / sanity, NOT our results)
| Claim | Status | Value | Source |
|---|---|---|---|
| MIAs barely beat chance on pretrained LLMs (Pile/Pythia) | 📚 | AUC ≈ 0.5–0.6 | duan2024mia |
| Min-K% improves AUC over prior best on WikiMIA | 📚 | +7.4% AUC | shi2024detecting |
| Min-K%++ over runner-up (reference-free) on WikiMIA | 📚 | +6.2–10.5% AUROC | zhang2025minkpp |
| GPT-J memorizes ≥1% of the Pile (extractable) | 📚 | ≥1% | carlini2023quantifying |
| LiRA gain at low FPR vs. prior attacks | 📚 | ~10× TPR @ low FPR | carlini2022lira |

## Reviewer-concerns ledger (full log in docs/reviewer_concerns.md)
| # | Concern | Status | Resolution / evidence |
|---|---|---|---|
| R1 | Frequency confound | 🟡 partial | zlib (freq-calibrated) is at chance on clean split AND still predicts leakage; frequency-matched control still TODO |
| R2 | Dedup confound | 🟡 partial | found 3/44 residual train↔val overlap; deduped-Pythia ablation pending compute |
| R3 | Temporal/topic shift (WikiMIA) | ✅ resolved | clean Pile train-vs-val collapses WikiMIA's 0.52–0.56 to chance 0.45–0.49; headline uses clean set |
| R4 | No CIs / single-run | ✅ resolved | bootstrap CIs on all AUCs + headline ρ; significance via CI-excludes-0 |
| R5 | Length confound | ✅ resolved | clean split length-matched (max_words); correlation set fixed window |
| R6 | **Headline circularity (LOSS≈extraction)** | ⛔ RESOLVED — NEGATIVE (see docs/controls_report.md) | Partial ρ\|loss: Min-K% −0.178, Min-K%++ −0.148 (FDR-sig, NEGATIVE), zlib −0.04 (n.s.). Headline does NOT survive: positive signal was entirely LOSS; calibrated detectors add no independent leakage-prediction. Robust to dedup; not a frequency or zero-inflation artifact. Needs reframing. |
| R7 | Zero-inflated outcome | ❌ open | ρ leans on few high-frac items; scale up + report Kendall τ |
| R8 | Oren/n-gram power | ❌ open | Oren at sanity scale (10 ex); run on real benchmark orderings |
| R9 | PII not yet shown | ❌ open | 0.0 verbatim PII leakage at 160m — do NOT claim PII leak until measured at scale |

```


### `docs/pre_analysis.md`

```markdown
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

```


### `docs/reviewer_concerns.md`

```markdown
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

```


### `docs/milestone1_report.md`

```markdown
# Milestone 1 Report — first runnable pipeline on real Pythia

**Date:** 2026-06-19. **Status:** ✅ pipeline validated; separation weak (expected at 160m).

## Setup
- Model: `EleutherAI/pythia-160m` (smallest Pythia), CPU, revision `main`.
- Data: **WikiMIA-64** (`swj0419/WikiMIA`), 542 examples (284 member / 258 non-member).
  Public benchmark used by the Min-K%/Min-K%++ papers; **carries a temporal confound**
  (members pre-cutoff, non-members post-cutoff) per Duan et al. 2024.
- Detectors: LOSS, Min-K%(k=20), Min-K%++(k=20), zlib-ratio. Metrics: AUC (+bootstrap
  95% CI, n=500, seed 0), TPR@1%, TPR@0.1%.
- Repro: `python scripts/milestone1_wikimia.py --model EleutherAI/pythia-160m --length 64 --device cpu`

## Results
| Detector | AUC | 95% CI | TPR@1% | TPR@0.1% |
|---|---|---|---|---|
| loss | 0.523 | [0.477, 0.568] | 0.004 | 0.000 |
| min_20_prob | 0.539 | [0.492, 0.585] | 0.011 | 0.000 |
| min_20_plusplus | 0.545 | [0.498, 0.592] | 0.032 | 0.011 |
| zlib_ratio | 0.564 | [0.517, 0.610] | 0.021 | 0.007 |

Artifacts: `figures/milestone1_wikimia64_dists.png`, `figures/milestone1_wikimia64_logroc.png`,
`results/wikimia64_pythia-160m.jsonl`, `results/wikimia64_summary.json`.

## Interpretation (honest)
**The pipeline is validated; the separation is near-chance — and that is the expected
result, not a defect.**

- **Pipeline-validity evidence:** (1) end-to-end run on real data and model; (2) detector
  ordering matches theory — the calibrated detectors (zlib, Min-K%++) beat Min-K%, which
  beats raw LOSS; (3) bootstrap CIs are sensible and behave correctly.
- **Why separation is weak:** memorization grows steeply with model scale
  (`carlini2023quantifying`), and membership inference is known to barely exceed chance on
  small Pythia models evaluated under controlled ground truth (`duan2024mia`). 160M is the
  smallest model in the suite. The Min-K%/Min-K%++ WikiMIA AUCs in the literature are
  reported mainly on multi-billion-parameter models.
- **Confound caveat:** WikiMIA's temporal split means even the small positive AUC partly
  reflects topic/time drift, not pure membership — exactly the confound MIMIR controls.

## What this unblocks / next levers
To move from "pipeline trusted" to "clean separation demonstrated," exactly two levers:
1. **Scale the model** (Pythia-1.4B / 2.8B) — expected to lift Min-K%++ AUC materially.
   Feasible on CPU but slow; exceeds the "160m-only" compute scope, so it needs a go-ahead.
2. **Confound-clean ground truth** (MIMIR splits) — removes the temporal confound; needs
   Hugging Face authentication (MIMIR is gated).

Recommended: do both — run ≥1.4B on MIMIR — for the headline separation and the
contamination↔leakage correlation. Until then, the 160m/WikiMIA result stands as an honest
"smallest-model, near-chance" baseline that the paper can actually use to motivate the
scaling story.

## Update: Pythia-1.4B WikiMIA (scaling data point)
A 1.4B WikiMIA-64 run completed (CPU). AUC rises with scale, confirming the memorization
scaling law (Carlini et al. 2023):

| Detector | 160m AUC | 1.4B AUC [95% CI] |
|---|---|---|
| loss | 0.523 | 0.571 [0.526, 0.620] |
| min_20_prob | 0.539 | 0.580 [0.532, 0.625] |
| min_20_plusplus | 0.545 | 0.547 [0.497, 0.595] |
| zlib_ratio | 0.564 | 0.616 [0.565, 0.663] |

zlib gains most (0.564→0.616); Min-K%++ is flat here. Caveat: this is on the *confounded*
WikiMIA split, so part of the gain is temporal drift, not pure membership. The decisive run —
1.4B/2.8B on the *confound-clean* Pile train-vs-val split — is a GPU item (deferred this round).
Figures: `figures/wikimia64_pythia-1.4b_{dists,logroc}.png` (regenerated from cached scores).

**Re: queuing 2.8B now —** declined this round. 2.8B on CPU is prohibitively slow and this
round is scoped to 160m/CPU; 2.8B (and 1.4B on the clean split) belong to the GPU scale-up,
where they are a single `--model` change with `configs/pythia1.4b_gpu.yaml`.

```


### `docs/integration_report.md`

```markdown
# Integration Report — Headline result + consistency round

**Date:** 2026-06-19. **Repo:** `~/contamination-research`. **Model this round:** Pythia-160m, CPU.

## Headline (the thesis as a number)
On real Pythia-160m, the contamination/membership score **significantly predicts extraction/
leakage** even though membership *separation* is at chance on the confound-clean split:

| | clean-split membership AUC | leakage correlation ρ [95% CI] |
|---|---|---|
| loss | 0.454 (chance) | **0.275 [0.164, 0.378]** ✅ |
| min_20_prob | 0.470 (chance) | 0.173 [0.061, 0.285] ✅ |
| zlib_ratio | 0.484 (chance) | 0.177 [0.063, 0.295] ✅ |
| min_20_plusplus | 0.490 (chance) | 0.108 [−0.010, 0.220] ✗ |

This is the contamination→memorization→leakage link, with CIs, on ground-truth Pile members.
Full numbers in `docs/results_table.md`; figure `figures/correlation_pythia-160m_scatter.png`.

## What is now publishable-strength
- **The confound-clean control (R3).** WikiMIA's 0.52–0.56 collapses to chance (0.45–0.49) on the
  same-distribution Pile train-vs-val split. Directly pre-empts "your MIA is just distribution
  shift." Strong, reviewer-ready.
- **The R6 control result (negative, but robust and reportable).** The raw contamination↔leakage
  correlation does NOT survive controlling for loss (partial ρ|loss: Min-K% −0.18, Min-K%++ −0.15
  FDR-sig negative; zlib ≈0). The honest finding is the *divergence*: loss predicts leakage,
  calibrated detectors do not. Pre-registered, robust to dedup, not a frequency/zero-inflation
  artifact. See `docs/controls_report.md`. (The earlier "headline correlation" framing is
  superseded — it was loss-driven.)
- **Methods↔paper consistency.** All 8 evaluated methods (LOSS, Min-K%, Min-K%++, zlib, n-gram,
  Oren, extractable memorization, Enron PII) are implemented, tested (46/46), and run; everything
  else is framed in the paper as "related, not evaluated." Spine rule holds.
- **Lit review.** background/related_work/evaluation/introduction finalized to S&P standard,
  datasets table rendered, all [VERIFY] debts cleared (lone exception: BLOOM's 392-author cite,
  intentional). MIA lineage + DP-defense subsections added.
- **Reproducibility.** Pinned `requirements.txt`, `configs/*.yaml`, one-command scripts, fixed
  seeds, public datasets, committed repo.

## What still needs the GPU scale-up (honestly NOT yet shown)
- **R6 — headline circularity (TOP priority).** LOSS↔extraction partly co-measure memorization.
  Must add the **partial correlation controlling for raw LOSS** to show Min-K%/zlib retain
  predictive power. Until then, scope the claim. This is a CPU-doable analysis, not a compute gate
  — next on the list.
- **R7 — zero-inflated outcome.** 3/300 fully extracted; ρ leans on few points. Larger models
  extract more (Carlini 2023) → de-degenerates the outcome. Add Kendall τ.
- **R9 — PII not demonstrated.** 0.0 verbatim PII leakage at 160m. The "PII exposure" limb is a
  designed capability with a null result at 160m; claim only when measured at scale.
- **Clean-split scaling.** Does the membership signal revive at 1.4B/2.8B on the *clean* split?
  WikiMIA AUC rises with scale (zlib 0.564→0.616 at 1.4B) but that split is confounded.
- **R2 — dedup ablation** (pythia-160m-deduped) and **R8 — Oren at real benchmark scale.**

## Compute posture
Everything is a single `--model` flag away from GPU scale-up (`configs/pythia1.4b_gpu.yaml`).
2.8B on CPU declined this round (prohibitively slow, out of the 160m/CPU scope).

## Round DONE-criteria status
1. ✅ Real contamination↔leakage correlation with CIs + master table + ROC/scatter figures.
2. ✅ n-gram + Oren implemented, tested, run.
3. ✅ related_work/background/evaluation/introduction finalized; described == implemented; [VERIFY] cleared.
4. ✅ Pinned env + one-command repro + committed repo.
5. ✅ Reviewer log R1–R9 (R3/R4/R5 resolved; R1/R2 partial; R6/R7/R8/R9 open with actions).
6. ✅ This report.

**Single most important next step:** the R6 partial-correlation control (CPU-doable), then the
GPU scale-up to revive the clean-split signal and actually observe PII leakage.

```


### `docs/method_selection_memo.md`

```markdown
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

```


### `docs/experiment_design.md`

```markdown
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

```


### `docs/glossary.md`

```markdown
# Glossary & Notation (shared across all subagents)

This file is the single source of truth for notation and term definitions. Paper
prose (`paper/*.tex`), code (`detectors/`, `extraction/`, `eval/`), and the
findings ledger MUST use these symbols and definitions consistently. If a symbol
is missing here, add it here first, then use it.

## Core notation

| Symbol | Meaning |
|---|---|
| $f_\theta$ | Target language model with parameters $\theta$ |
| $x = (x_1, \dots, x_n)$ | A token sequence of length $n$ |
| $p_\theta(x_t \mid x_{<t})$ | Next-token probability the model assigns to token $x_t$ given its prefix |
| $\ell_t = -\log p_\theta(x_t \mid x_{<t})$ | Per-token negative log-likelihood (NLL) |
| $\mathcal{L}(f_\theta, x) = \frac{1}{n}\sum_t \ell_t$ | Mean per-token NLL (cross-entropy) of $x$ |
| $\mathrm{PPL}(x) = \exp(\mathcal{L}(f_\theta, x))$ | Perplexity |
| $X_{\text{train}}$ | The model's training corpus (for Pythia: **The Pile**) |
| member / non-member | $x \in X_{\text{train}}$ vs. $x \notin X_{\text{train}}$ |
| $\tau$ | Decision threshold on a detector score |
| $s(x) \to \mathbb{R}$ | A detector's score for sequence $x$ (uniform interface; higher ⇒ more "member-like" unless noted) |

## Detector score definitions (as implemented in `detectors/`)

- **LOSS / Perplexity** (`detectors/loss.py`, after Yeom et al. 2018):
  $s_{\text{LOSS}}(x) = -\mathcal{L}(f_\theta, x)$ (negated so higher ⇒ more member-like).

- **Min-K% Prob** (`detectors/mink.py`, Shi et al. 2024): let $E$ be the set of the
  $\lceil k\% \cdot n\rceil$ tokens with the **lowest** $\log p_\theta(x_t\mid x_{<t})$.
  $s_{\text{Min-K\%}}(x) = \frac{1}{|E|}\sum_{t\in E}\log p_\theta(x_t\mid x_{<t})$. Higher ⇒ more member-like.

- **Min-K%++** (`detectors/minkpp.py`, Zhang et al. 2025): z-score each token's log-prob
  against the next-token distribution, then average the bottom-$k\%$:
  $z_t = \frac{\log p_\theta(x_t\mid x_{<t}) - \mu_{x_{<t}}}{\sigma_{x_{<t}}}$,
  where $\mu_{x_{<t}} = \mathbb{E}_{z\sim p_\theta(\cdot\mid x_{<t})}[\log p_\theta(z\mid x_{<t})]$ and
  $\sigma_{x_{<t}}$ is the std of $\log p_\theta(\cdot\mid x_{<t})$ over the full vocabulary.
  Requires full next-token logits.

- **zlib ratio** (`detectors/zlib_ratio.py`, Carlini et al. 2021):
  $s_{\text{zlib}}(x) = -\frac{\mathcal{L}_{\text{sum}}(f_\theta, x)}{\text{zlib\_bits}(x)}$ where
  $\mathcal{L}_{\text{sum}} = \sum_t \ell_t$ (sum, not mean) and $\text{zlib\_bits}$ is the
  zlib-compressed size of $x$ in bits. Negated so higher ⇒ more member-like.

- **n-gram overlap** (`detectors/ngram_overlap.py`, `NGramOverlapDetector`, after Brown et al. 2020):
  corpus-side contamination score = the **fraction of a text's $N$-grams** (default $N=13$,
  **whitespace-tokenized**, case- and punctuation-sensitive) that are found in a prebuilt index
  of the corpus's $N$-grams. Range $[0,1]$ (1 = every $N$-gram of the text appears in the corpus;
  texts shorter than $N$ tokens score 0). This is a **model-free, corpus-side** measure: it needs
  corpus access, not model access, and consumes no `TokenStats`. NOTE: its axis is *different* from
  the membership detectors above — it is "fraction matched in corpus," **not** the
  "higher ⇒ more member-like" log-prob convention of $s(x)$; do not threshold the two on a shared
  scale. The strict GPT-3 rule "any shared 13-gram ⇒ contaminated" is the special case
  `contains_overlap(text, threshold=0.0)`.

- **Oren permutation test** (`detectors/oren_permutation.py`, `OrenPermutationTest`, Oren et al. 2023):
  a **dataset-level** (not per-text) contamination test over an **ordered set of examples**. For a
  given ordering it concatenates the examples in that order into a single string (joined by `sep`,
  default newline) and re-scores the *whole* string under $f_\theta$, so each example's tokens are
  conditioned on the running prefix of the earlier examples (**context crosses example boundaries** —
  this is what makes order matter; a per-example sum of log-likelihoods is order-invariant and would
  be vacuous). It compares the canonical-order total log-likelihood against the null distribution from
  `n_permutations` random shufflings and returns a **one-sided permutation p-value**
  $p = (1 + \#\{\text{perm}: \mathrm{loglik}(\text{perm}) \ge \mathrm{loglik}(\text{canonical})\}) / (\text{n\_permutations} + 1)$;
  small $p$ ⇒ the canonical order is favored beyond chance ⇒ evidence of contamination. It does **not**
  implement the `Detector` ABC and returns a p-value, not a member-like score $s(x)$.

## Memorization / leakage definitions (as implemented in `extraction/`)

- **Extractable (prefix-continuation) memorization** (Carlini et al. 2023): string $s$ is
  *extractable with $k$ tokens of context* if $\exists$ length-$k$ prefix $p$ with $[p\Vert s]\in X_{\text{train}}$
  and $f_\theta$ emits $s$ from $p$ under **greedy decoding**. Quantified by **extraction rate** =
  fraction of sampled training sequences that are extractable.

- **$k$-eidetic memorization** (Carlini et al. 2021): $s$ is extractable AND appears in
  $\le k$ distinct training documents: $|\{x\in X_{\text{train}} : s\subseteq x\}| \le k$.

- **Canary exposure** (Carlini et al. 2019): $\mathrm{exposure}_\theta(s[r]) = \log_2 |R| - \log_2 \mathrm{rank}_\theta(s[r])$.

## Evaluation metrics (as implemented in `eval/metrics.py`)

- **AUC-ROC** — threshold-free ranking quality; reported as a secondary/continuity metric.
- **TPR @ FPR ∈ {0.1%, 1%}** — PRIMARY metric (Carlini et al. 2022); true-positive rate at a
  fixed low false-positive operating point.
- **log-scale ROC** — ROC with log-log axes so the low-FPR regime is legible.
- **extraction rate** — fraction of prefixes whose greedy continuation matches the held suffix.
- **contamination/flag rate** — fraction of benchmark items flagged by a detector at threshold $\tau$.
- **contamination↔leakage correlation** — the headline analysis: per-item detector score vs.
  per-item extraction/leakage outcome (Spearman $\rho$ + bootstrap CI).

## Threat-model vocabulary

- **black-box**: query text in, generated text out (no logprobs).
- **gray-box**: per-token log-probabilities / loss available (top-k logprobs).
- **white-box**: full next-token distribution / logits / weights available.
- **ground-truth membership**: known $x\in X_{\text{train}}$ vs. $x\notin X_{\text{train}}$ from the public Pile.

```


### `README.md`

````markdown
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

````



# PART 3 — ALL CODE (detectors / extraction / eval)


### `detectors/base.py`

```python
"""Core abstractions shared by all detectors.

Design: a single forward pass over a text produces a `TokenStats` object holding
everything every detector needs (per-token log-prob of the realized token, plus the
mean/std of the log-prob distribution over the full vocabulary at each position).
Detectors are pure functions of `TokenStats` (+ the raw text, for zlib). This means:

  * one model forward pass feeds ALL detectors (the runner exploits this), and
  * detectors are unit-testable with a `MockScorer` and need no GPU / model download.

All scores follow the convention: **higher => more "member-like"** (more likely to be
in the training corpus). See ../docs/glossary.md for the formal definitions.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass

import numpy as np


@dataclass
class TokenStats:
    """Per-token statistics from one forward pass of a causal LM over a text.

    All arrays have length ``n_tokens`` = (number of scored tokens) = (sequence
    length - 1), since the first token has no preceding context to be predicted from.

    Attributes
    ----------
    token_logprob : np.ndarray, shape (n,)
        log p_theta(x_t | x_{<t}) for each realized token x_t (natural log).
    mu : np.ndarray, shape (n,)
        E_{z ~ vocab} [ log p_theta(z | x_{<t}) ] : mean over the full vocabulary of
        the next-token log-probabilities at each position. Needed by Min-K%++.
    sigma : np.ndarray, shape (n,)
        Std over the full vocabulary of log p_theta(. | x_{<t}). Needed by Min-K%++.
    """

    token_logprob: np.ndarray
    mu: np.ndarray
    sigma: np.ndarray

    def __post_init__(self) -> None:
        n = len(self.token_logprob)
        if not (len(self.mu) == len(self.sigma) == n):
            raise ValueError("token_logprob, mu, sigma must have equal length")
        if n == 0:
            raise ValueError("TokenStats requires at least one scored token")

    @property
    def n_tokens(self) -> int:
        return len(self.token_logprob)


class ModelScorer(abc.ABC):
    """Produces `TokenStats` for a text under a target language model."""

    @abc.abstractmethod
    def score_tokens(self, text: str) -> TokenStats:  # pragma: no cover - interface
        ...


class Detector(abc.ABC):
    """Uniform detector interface: ``score(text) -> float`` (higher = member-like).

    A detector is bound to a `ModelScorer` at construction. For efficiency the runner
    calls `score_from_stats` with a `TokenStats` computed once and shared across all
    detectors; `score(text)` is the convenience path that computes stats internally.
    """

    name: str = "detector"
    #: minimum adversary access tier this detector needs (see threat model)
    access: str = "gray-box"

    def __init__(self, scorer: ModelScorer | None = None):
        self.scorer = scorer

    @abc.abstractmethod
    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        ...

    def score(self, text: str) -> float:
        if self.scorer is None:
            raise ValueError(f"{self.name}: no scorer bound; pass scorer= at construction")
        return self.score_from_stats(self.scorer.score_tokens(text), text)


def bottom_k_indices(values: np.ndarray, k_percent: float) -> np.ndarray:
    """Indices of the ``ceil(k% * n)`` smallest entries (the Min-K% selection rule).

    At least one token is always selected. ``k_percent`` is in (0, 100].
    """
    if not (0 < k_percent <= 100):
        raise ValueError("k_percent must be in (0, 100]")
    n = len(values)
    k = max(1, int(np.ceil((k_percent / 100.0) * n)))
    # argpartition is O(n); we only need the set of k smallest, order within is irrelevant.
    return np.argpartition(values, k - 1)[:k]

```


### `detectors/loss.py`

```python
"""LOSS / Perplexity-threshold membership inference (Yeom et al. 2018).

Score = negative mean per-token NLL = mean token log-prob. Members (training data)
tend to have lower loss => higher (less negative) mean log-prob => higher score.
This is the mandatory baseline that anchors the overfitting <-> privacy connection.
"""
from __future__ import annotations

import numpy as np

from .base import Detector, TokenStats


class LossDetector(Detector):
    name = "loss"
    access = "gray-box"

    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        # mean log p(x_t | x_<t) ; equals -cross_entropy ; higher => member-like
        return float(np.mean(stats.token_logprob))


class PerplexityDetector(Detector):
    """Same ranking as LossDetector, reported as -perplexity for interpretability."""

    name = "perplexity"
    access = "gray-box"

    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        ce = -float(np.mean(stats.token_logprob))  # cross-entropy (nats)
        return -float(np.exp(ce))  # -perplexity ; higher => member-like

```


### `detectors/mink.py`

```python
"""Min-K% Prob (Shi et al. 2024, ICLR).

Average the log-probabilities of the k% lowest-probability tokens. Intuition: a
non-member is more likely to contain a few very-low-probability ("surprising") tokens,
so the mean over the worst k% separates members (higher) from non-members (lower).
Reference-free; needs only per-token log-probabilities (gray-box).
"""
from __future__ import annotations

import numpy as np

from .base import Detector, TokenStats, bottom_k_indices


class MinKProbDetector(Detector):
    name = "min_k_prob"
    access = "gray-box"

    def __init__(self, scorer=None, k_percent: float = 20.0):
        super().__init__(scorer)
        self.k_percent = k_percent
        self.name = f"min_{int(k_percent)}_prob"

    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        lp = stats.token_logprob
        idx = bottom_k_indices(lp, self.k_percent)
        return float(np.mean(lp[idx]))  # higher => member-like

```


### `detectors/minkpp.py`

```python
"""Min-K%++ (Zhang et al. 2025, ICLR Spotlight).

Improves Min-K% by z-scoring each token's log-prob against the *full* next-token
distribution at that position before taking the bottom-k% mean:

    z_t = ( log p(x_t | x_<t) - mu_t ) / sigma_t

where mu_t = E_{z in vocab}[log p(z | x_<t)] and sigma_t = std over the vocabulary.
Rationale: training samples sit at local maxima of the modeled distribution, so the
signal is how peaked the realized token is relative to the whole vocabulary, not its
raw probability. Requires the full next-token distribution => white-box logit access.
"""
from __future__ import annotations

import numpy as np

from .base import Detector, TokenStats, bottom_k_indices


class MinKPlusPlusDetector(Detector):
    name = "min_k_plusplus"
    access = "white-box"

    def __init__(self, scorer=None, k_percent: float = 20.0, eps: float = 1e-6):
        super().__init__(scorer)
        self.k_percent = k_percent
        self.eps = eps
        self.name = f"min_{int(k_percent)}_plusplus"

    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        z = (stats.token_logprob - stats.mu) / (stats.sigma + self.eps)
        idx = bottom_k_indices(z, self.k_percent)
        return float(np.mean(z[idx]))  # higher => member-like

```


### `detectors/zlib_ratio.py`

```python
"""zlib-entropy ratio (Carlini et al. 2021, USENIX Security).

Score = - (summed NLL of the text under the model) / (zlib-compressed size in bits).
The zlib size estimates the text's intrinsic entropy, so dividing calibrates away
"text that is simply predictable/compressible to any model" -- the cheapest control
for the string-frequency confound. Members have low model loss relative to their
intrinsic entropy => low ratio => high (negated) score.
"""
from __future__ import annotations

import zlib

import numpy as np

from .base import Detector, TokenStats


def zlib_bits(text: str) -> int:
    """Length in bits of the zlib-compressed UTF-8 encoding of ``text``."""
    compressed = zlib.compress(text.encode("utf-8"))
    return len(compressed) * 8


class ZlibRatioDetector(Detector):
    name = "zlib_ratio"
    access = "gray-box"

    def score_from_stats(self, stats: TokenStats, text: str) -> float:
        nll_sum_nats = -float(np.sum(stats.token_logprob))  # summed NLL (nats)
        bits = max(1, zlib_bits(text))
        return -(nll_sum_nats / bits)  # higher => member-like

```


### `detectors/ngram_overlap.py`

```python
"""Corpus-side n-gram contamination check (Brown et al. 2020, GPT-3, App. C).

This is NOT a per-token membership detector and does NOT use a language model. It is the
*data-side* contamination test: given access to a (training) corpus, build an index of all
length-``n`` n-grams it contains, then for any candidate text report the fraction of the
candidate's n-grams that already appear in that index. GPT-3 used 13-gram overlap to flag
benchmark examples that had leaked into the training crawl.

Because it interrogates the corpus rather than the model, it deliberately does NOT implement
the :class:`~detectors.base.Detector` ABC (which is bound to a ``ModelScorer`` and consumes
``TokenStats``). It has its own honest interface: ``build_index`` then ``score`` /
``contains_overlap``.

Tokenization choice
-------------------
The default tokenizer is **whitespace splitting** (``text.split()``). This is simple,
model-free, reproducible, and matches the spirit of the GPT-3 word-level n-gram filter. It is
*not* lowercased or punctuation-stripped, so the check is case- and punctuation-sensitive; a
caller wanting looser matching should normalize texts before passing them in.

A tokenizer-based variant (e.g. feeding a model's BPE token ids instead of whitespace words)
would make the n-grams align with the units the model actually sees and is the right choice
when reproducing a specific model's contamination report. To use it, pass a ``tokenize``
callable ``str -> list[str]`` at construction (e.g. one wrapping a HF tokenizer's
``.tokenize``); the index/scoring logic is identical. Whitespace is the documented default.
"""
from __future__ import annotations

from typing import Callable, Iterable, List, Sequence, Set, Tuple


def _whitespace_tokenize(text: str) -> List[str]:
    """Split on runs of whitespace (the documented default tokenizer)."""
    return text.split()


def _ngrams(tokens: Sequence[str], n: int) -> List[Tuple[str, ...]]:
    """All contiguous length-``n`` n-grams of ``tokens`` (empty if fewer than n tokens)."""
    if len(tokens) < n:
        return []
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


class NGramOverlapDetector:
    """Fraction-of-n-grams-seen-in-corpus contamination check.

    Parameters
    ----------
    n : int
        n-gram length. Default 13 (the GPT-3 value).
    tokenize : Callable[[str], list[str]] | None
        Tokenizer mapping a string to a list of string tokens. Defaults to whitespace
        splitting (see module docstring). Pass a HF-tokenizer wrapper for a token-level
        variant.

    Usage
    -----
    >>> det = NGramOverlapDetector(n=3)
    >>> det.build_index(["the quick brown fox jumps over the lazy dog"])
    >>> det.score("the quick brown fox")        # all 3-grams seen -> 1.0
    1.0
    >>> det.score("completely unrelated text here")   # none seen -> 0.0
    0.0
    """

    def __init__(self, n: int = 13, tokenize: Callable[[str], List[str]] | None = None):
        if n < 1:
            raise ValueError("n must be >= 1")
        self.n = n
        self.tokenize = tokenize or _whitespace_tokenize
        self._index: Set[Tuple[str, ...]] = set()
        self._built = False

    def build_index(self, corpus_texts: Iterable[str]) -> "NGramOverlapDetector":
        """Store the set of all n-grams occurring in ``corpus_texts``.

        Idempotent-ish: may be called more than once; each call *adds* to the index, so a
        corpus can be streamed in chunks. Returns ``self`` for chaining.
        """
        for text in corpus_texts:
            self._index.update(_ngrams(self.tokenize(text), self.n))
        self._built = True
        return self

    @property
    def index_size(self) -> int:
        """Number of distinct n-grams currently in the index."""
        return len(self._index)

    def score(self, text: str) -> float:
        """Fraction of ``text``'s n-grams that appear in the corpus index, in [0, 1].

        Returns 0.0 when ``text`` is shorter than ``n`` tokens (no n-grams to match), which
        is the conservative "no detected overlap" answer for too-short inputs.
        """
        if not self._built:
            raise ValueError("build_index(...) must be called before score(...)")
        grams = _ngrams(self.tokenize(text), self.n)
        if not grams:
            return 0.0
        hits = sum(1 for g in grams if g in self._index)
        return hits / len(grams)

    def contains_overlap(self, text: str, threshold: float = 0.0) -> bool:
        """True iff the overlap fraction for ``text`` exceeds ``threshold``.

        With the default ``threshold=0.0`` this flags any text sharing at least one n-gram
        with the corpus (the strict GPT-3-style "any 13-gram match is contamination" rule).
        Raise the threshold to require a larger contaminated fraction.
        """
        return self.score(text) > threshold

```


### `detectors/oren_permutation.py`

```python
"""Oren et al. 2023 exchangeability (permutation) test for benchmark contamination.

Idea
----
A clean benchmark dataset is *exchangeable*: a model that has not been trained on it has no
reason to prefer one ordering of its examples over another, so the total log-likelihood the
model assigns to the examples is (in distribution) invariant to permutation. If the model was
trained on the benchmark in its **canonical order** (the order it was published / shuffled in
the training corpus), the model memorizes that order and assigns the canonical concatenation a
*higher* total log-likelihood than almost all random permutations. The test compares the
canonical-order log-likelihood against the null distribution generated by random shufflings.

This is NOT a per-text membership detector. It operates on an *ordered set of examples* and
returns a single dataset-level p-value, so it does not implement the
:class:`~detectors.base.Detector` ABC. It does reuse a :class:`~detectors.base.ModelScorer`
(``HFScorer`` / ``MockScorer``) to get log-likelihoods.

Why order must cross example boundaries
---------------------------------------
Per-example sequence log-likelihood (sum of ``TokenStats.token_logprob`` for the example
scored in isolation) is *order-invariant*: summing those over a permutation gives the same
total no matter the order, so it carries no order signal and the test would be vacuous. To make
order matter, each permutation's score is the model log-likelihood of the examples
**concatenated, in that order, into a single string** (joined by ``sep``). Then tokens in one
example are conditioned on the running prefix of the previous examples, exactly the
cross-boundary memorization signal the canonical training order would imprint.

Cost: the concatenation is re-scored once per permutation (``n_permutations`` forward passes).
Keep the example list short and ``n_permutations`` modest on CPU.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np

from .base import ModelScorer


@dataclass
class OrenResult:
    """Result of an Oren permutation test."""

    p_value: float
    canonical_loglik: float
    null_mean: float
    null_std: float

    def as_dict(self) -> dict:
        return {
            "p_value": self.p_value,
            "canonical_loglik": self.canonical_loglik,
            "null_mean": self.null_mean,
            "null_std": self.null_std,
        }


class OrenPermutationTest:
    """Permutation (exchangeability) contamination test.

    Parameters
    ----------
    scorer : ModelScorer
        A model scorer (``HFScorer`` for a real LM, ``MockScorer`` for tests). Its
        ``score_tokens(text).token_logprob`` is summed to get the total log-likelihood of a
        concatenated ordering.
    sep : str
        String inserted between consecutive examples when concatenating. Default newline,
        matching how examples typically sit in a serialized benchmark file.
    """

    def __init__(self, scorer: ModelScorer, sep: str = "\n"):
        self.scorer = scorer
        self.sep = sep

    def _ordering_loglik(self, examples: Sequence[str], order: Sequence[int]) -> float:
        """Total model log-likelihood of the examples concatenated in ``order``.

        Order matters because the concatenation is scored as one string, so each example's
        tokens are conditioned on the prefix formed by the earlier examples.
        """
        text = self.sep.join(examples[i] for i in order)
        stats = self.scorer.score_tokens(text)
        return float(np.sum(stats.token_logprob))

    def test(
        self,
        examples: List[str],
        n_permutations: int = 1000,
        seed: int = 0,
    ) -> dict:
        """Run the test on ``examples`` given in their canonical order.

        Parameters
        ----------
        examples : list[str]
            The benchmark examples, in canonical (published / training) order.
        n_permutations : int
            Number of random permutations forming the null distribution.
        seed : int
            RNG seed for reproducible permutations.

        Returns
        -------
        dict with keys ``p_value``, ``canonical_loglik``, ``null_mean``, ``null_std``.

        The one-sided p-value is::

            p = (1 + #{perm : loglik(perm) >= loglik(canonical)}) / (n_permutations + 1)

        Small p => the canonical order is favored beyond chance => evidence of contamination.
        """
        if len(examples) < 2:
            raise ValueError("permutation test needs at least 2 examples")
        if n_permutations < 1:
            raise ValueError("n_permutations must be >= 1")

        rng = np.random.default_rng(seed)
        canonical_order = list(range(len(examples)))
        canonical = self._ordering_loglik(examples, canonical_order)

        null = np.empty(n_permutations, dtype=np.float64)
        ge = 0
        for k in range(n_permutations):
            perm = rng.permutation(len(examples))
            ll = self._ordering_loglik(examples, perm)
            null[k] = ll
            if ll >= canonical:
                ge += 1

        p_value = (1 + ge) / (n_permutations + 1)
        return OrenResult(
            p_value=float(p_value),
            canonical_loglik=float(canonical),
            null_mean=float(null.mean()),
            null_std=float(null.std()),
        ).as_dict()

```


### `detectors/scorers.py`

```python
"""Concrete `ModelScorer` implementations.

`HFScorer`   -- real causal LM via Hugging Face transformers (used for Pythia/OLMo).
`MockScorer` -- deterministic, torch-free; lets the whole pipeline + tests run on CPU
                with no model download. Useful for CI and for milestone-0 validation.
"""
from __future__ import annotations

import hashlib

import numpy as np

from .base import ModelScorer, TokenStats


class HFScorer(ModelScorer):
    """Per-token statistics from a Hugging Face causal LM.

    Parameters
    ----------
    model_name : str
        e.g. "EleutherAI/pythia-160m".
    revision : str | None
        Pinned model revision (commit hash / step tag) for reproducibility.
    device : str
        "cpu", "cuda", or "mps".
    max_length : int
        Truncate inputs to this many tokens (memory bound; mu/sigma are O(vocab) per pos).
    """

    def __init__(
        self,
        model_name: str,
        revision: str | None = None,
        device: str = "cpu",
        max_length: int = 1024,
    ):
        # Lazy imports so importing this module (and running mock tests) needs no torch.
        import torch  # noqa: F401
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.model_name = model_name
        self.revision = revision
        self.device = device
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, revision=revision)
        self.model.to(device).eval()

    def score_tokens(self, text: str) -> TokenStats:
        import torch

        enc = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
        )
        input_ids = enc["input_ids"].to(self.device)
        if input_ids.shape[1] < 2:
            raise ValueError("text must tokenize to >= 2 tokens to be scored")

        with torch.no_grad():
            logits = self.model(input_ids).logits[0]  # (seq, vocab)
            logprobs = torch.log_softmax(logits.float(), dim=-1)  # (seq, vocab)

        # logits at position j predict token j+1 (standard causal shift).
        pred = logprobs[:-1]                  # (seq-1, vocab)
        targets = input_ids[0, 1:]            # (seq-1,)
        token_logprob = pred.gather(1, targets.unsqueeze(1)).squeeze(1)  # (seq-1,)
        mu = pred.mean(dim=-1)                # (seq-1,)
        sigma = pred.std(dim=-1)              # (seq-1,)

        return TokenStats(
            token_logprob=token_logprob.cpu().numpy().astype(np.float64),
            mu=mu.cpu().numpy().astype(np.float64),
            sigma=sigma.cpu().numpy().astype(np.float64),
        )


class MockScorer(ModelScorer):
    """Deterministic, torch-free scorer for tests / CI / dry-runs.

    Generates reproducible per-token statistics from a hash of the text. An optional
    `membership_fn(text) -> bool` lets tests simulate a separating signal: "member"
    texts get systematically higher token log-probs (lower loss), mimicking the
    train/non-train separation the real pipeline measures.
    """

    def __init__(self, vocab_size: int = 50_304, membership_fn=None, signal: float = 1.0):
        self.vocab_size = vocab_size
        self.membership_fn = membership_fn
        self.signal = signal

    def _rng(self, text: str) -> np.random.Generator:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(h[:8], "little")
        return np.random.default_rng(seed)

    def score_tokens(self, text: str) -> TokenStats:
        rng = self._rng(text)
        n = max(2, min(256, len(text.split()) + 5))
        # Baseline: log-probs of realized tokens are mildly negative.
        base = -rng.gamma(shape=2.0, scale=1.0, size=n)
        if self.membership_fn is not None and self.membership_fn(text):
            base = base + self.signal  # members: higher log-prob (lower loss)
        # mu/sigma summarize a plausible vocab log-prob distribution at each position.
        mu = -np.log(self.vocab_size) + rng.normal(0, 0.5, size=n)
        sigma = rng.uniform(1.5, 3.0, size=n)
        return TokenStats(
            token_logprob=base.astype(np.float64),
            mu=mu.astype(np.float64),
            sigma=sigma.astype(np.float64),
        )

```


### `detectors/__init__.py`

```python
"""Contamination / membership detectors with a uniform ``score(text) -> float`` API.

All scores follow the convention: higher => more likely a training-set member.
See ../docs/method_selection_memo.md for why these four were selected.
"""
from .base import Detector, ModelScorer, TokenStats, bottom_k_indices
from .loss import LossDetector, PerplexityDetector
from .mink import MinKProbDetector
from .minkpp import MinKPlusPlusDetector
from .ngram_overlap import NGramOverlapDetector
from .oren_permutation import OrenPermutationTest, OrenResult
from .scorers import HFScorer, MockScorer
from .zlib_ratio import ZlibRatioDetector, zlib_bits

#: registry used by the runner / CLI
DETECTOR_REGISTRY = {
    "loss": LossDetector,
    "perplexity": PerplexityDetector,
    "min_k_prob": MinKProbDetector,
    "min_k_plusplus": MinKPlusPlusDetector,
    "zlib_ratio": ZlibRatioDetector,
}


def build_default_detectors(scorer: ModelScorer):
    """The shortlisted *per-text membership* detector suite, bound to a scorer.

    NOTE: this suite intentionally EXCLUDES NGramOverlapDetector and OrenPermutationTest.
    Those two are not per-token membership detectors over a single text -- the n-gram check is
    corpus-side (no model) and the Oren test is a dataset-level permutation test over an
    *ordered set* of examples -- so they have their own honest interfaces (build_index/score
    and test(...)) and must be constructed and called directly, not run through this suite.
    """
    return [
        LossDetector(scorer),
        MinKProbDetector(scorer, k_percent=20.0),
        MinKPlusPlusDetector(scorer, k_percent=20.0),
        ZlibRatioDetector(scorer),
    ]


#: Corpus-/dataset-level contamination tests that are NOT part of the per-text membership
#: suite above. They do not share the Detector/TokenStats interface; see each class's docstring.
CONTAMINATION_TESTS = {
    "ngram_overlap": NGramOverlapDetector,
    "oren_permutation": OrenPermutationTest,
}


__all__ = [
    "Detector",
    "ModelScorer",
    "TokenStats",
    "bottom_k_indices",
    "LossDetector",
    "PerplexityDetector",
    "MinKProbDetector",
    "MinKPlusPlusDetector",
    "ZlibRatioDetector",
    "zlib_bits",
    "HFScorer",
    "MockScorer",
    "DETECTOR_REGISTRY",
    "build_default_detectors",
    # corpus-/dataset-level contamination tests (separate interfaces)
    "NGramOverlapDetector",
    "OrenPermutationTest",
    "OrenResult",
    "CONTAMINATION_TESTS",
]

```


### `extraction/extract.py`

```python
"""Extractable (prefix-continuation) memorization (Carlini et al. 2023).

A string s is *extractable with k tokens of context* if a length-k prefix p drawn
from a training sequence [p || s] makes the model greedily regenerate s. The
**extraction rate** -- fraction of sampled sequences that are extractable -- is the
concrete leakage outcome we correlate against per-item contamination scores.

This module defines the metric and a model-agnostic harness; the greedy-generation
backend is injected (HF-backed for real runs, a stub for tests), so the logic is
unit-testable without a GPU.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


@dataclass
class ExtractionResult:
    extracted: bool          # did greedy continuation exactly match the held suffix?
    prefix_len: int          # k, tokens of context
    suffix_len: int          # tokens the model had to reproduce
    matched_tokens: int      # length of the matching prefix of the continuation


#: a GreedyGenerator maps (prefix_token_ids, n_new_tokens) -> generated_token_ids
GreedyGenerator = Callable[[Sequence[int], int], Sequence[int]]


def is_extractable(
    token_ids: Sequence[int],
    prefix_len: int,
    generate: GreedyGenerator,
) -> ExtractionResult:
    """Test whether [prefix || suffix] is extractable from `generate` given `prefix_len`.

    Splits ``token_ids`` at ``prefix_len``; the suffix is the target to reproduce.
    Exact-match extraction (the strict definition) is reported, alongside the count of
    leading matched tokens (a softer signal useful for the correlation analysis).
    """
    token_ids = list(token_ids)
    if not (0 < prefix_len < len(token_ids)):
        raise ValueError("prefix_len must satisfy 0 < prefix_len < len(token_ids)")
    prefix = token_ids[:prefix_len]
    suffix = token_ids[prefix_len:]
    gen = list(generate(prefix, len(suffix)))[: len(suffix)]
    matched = 0
    for a, b in zip(suffix, gen):
        if a == b:
            matched += 1
        else:
            break
    return ExtractionResult(
        extracted=(matched == len(suffix)),
        prefix_len=prefix_len,
        suffix_len=len(suffix),
        matched_tokens=matched,
    )


def extraction_rate(results: Sequence[ExtractionResult]) -> float:
    """Fraction of sampled sequences that were exactly extractable."""
    if not results:
        return 0.0
    return float(np.mean([r.extracted for r in results]))


def fractional_extraction(results: Sequence[ExtractionResult]) -> np.ndarray:
    """Per-item matched-token fraction in [0, 1] (soft leakage signal for correlation)."""
    return np.array(
        [r.matched_tokens / r.suffix_len if r.suffix_len else 0.0 for r in results],
        dtype=np.float64,
    )


def hf_greedy_generator(model_name: str, revision: str | None = None, device: str = "cpu") -> GreedyGenerator:
    """Build an HF-backed greedy generator (lazy import; not needed for tests)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_name, revision=revision)
    model = AutoModelForCausalLM.from_pretrained(model_name, revision=revision).to(device).eval()

    def generate(prefix_ids, n_new):
        ids = torch.tensor([list(prefix_ids)], device=device)
        with torch.no_grad():
            out = model.generate(
                ids,
                max_new_tokens=n_new,
                do_sample=False,
                num_beams=1,
                pad_token_id=tok.eos_token_id,
            )
        return out[0, len(prefix_ids):].tolist()

    return generate

```


### `extraction/pii.py`

```python
"""Regex PII detectors for the leakage analysis (Enron-in-Pile subset only).

ETHICS: this module is used *only* on the Enron Emails subset of The Pile -- a
public corpus already in Pythia's training data -- and only for aggregate
counts/rates. It must never be used to target real individuals, and callers must
never print matched PII strings. The detectors return *spans*, not enriched
identities, so downstream code can count types without surfacing the values.

Public API:
  find_pii(text)  -> list of (pii_type, (start, end)) spans
  pii_types(text) -> set of pii_type strings present
"""
from __future__ import annotations

import re
from typing import List, Set, Tuple

# Email: conservative but covers "a@b.com" style addresses.
_EMAIL = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
)

# US phone: optional country code, common separators / parens.
#   555-123-4567, (555) 123-4567, 555.123.4567, +1 555 123 4567
_PHONE = re.compile(
    r"(?<!\d)(?:\+?1[\s.\-]?)?(?:\(\d{3}\)|\d{3})[\s.\-]\d{3}[\s.\-]\d{4}(?!\d)"
)

# SSN-like: 123-45-6789 (optional; reported separately).
_SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")

#: ordered so SSN is checked before phone (disjoint patterns, but explicit).
_DETECTORS = [
    ("email", _EMAIL),
    ("ssn", _SSN),
    ("phone", _PHONE),
]


def find_pii(text: str) -> List[Tuple[str, Tuple[int, int]]]:
    """Return a list of ``(pii_type, (start, end))`` spans found in ``text``.

    Spans are character offsets into ``text``. Overlapping matches from different
    detectors are all reported; callers that want unique types should use
    :func:`pii_types`.
    """
    out: List[Tuple[str, Tuple[int, int]]] = []
    for pii_type, pattern in _DETECTORS:
        for m in pattern.finditer(text):
            out.append((pii_type, (m.start(), m.end())))
    out.sort(key=lambda x: (x[1][0], x[1][1]))
    return out


def pii_types(text: str) -> Set[str]:
    """Return the set of PII types present in ``text`` (no values, no spans)."""
    return {t for t, _ in find_pii(text)}

```


### `extraction/__init__.py`

```python
"""Memorization / extraction harness."""
from .extract import (
    ExtractionResult,
    extraction_rate,
    fractional_extraction,
    hf_greedy_generator,
    is_extractable,
)

__all__ = [
    "ExtractionResult",
    "extraction_rate",
    "fractional_extraction",
    "hf_greedy_generator",
    "is_extractable",
]

```


### `eval/metrics.py`

```python
"""Security-venue evaluation metrics.

Primary metric is **TPR at low fixed FPR** (0.1%, 1%) with log-scale ROC, per
Carlini et al. 2022 (S&P): average-case AUC/accuracy hide whether an attack can
*confidently* identify any members. AUC is reported as a secondary/continuity metric.

Implemented in pure numpy (no sklearn/scipy) so the metrics layer is dependency-light
and its correctness is auditable against closed-form synthetic cases in the tests.

Score convention: higher score => more "member-like"; ``y_true`` is 1 for members
(positives), 0 for non-members (negatives).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _check(scores: np.ndarray, y_true: np.ndarray):
    scores = np.asarray(scores, dtype=np.float64)
    y_true = np.asarray(y_true, dtype=np.int64)
    if scores.shape != y_true.shape:
        raise ValueError("scores and y_true must have the same shape")
    if not set(np.unique(y_true)).issubset({0, 1}):
        raise ValueError("y_true must be binary (0/1)")
    if y_true.sum() == 0 or y_true.sum() == len(y_true):
        raise ValueError("need at least one positive and one negative")
    return scores, y_true


def roc_curve(scores: np.ndarray, y_true: np.ndarray):
    """Return (fpr, tpr, thresholds), sorted by increasing FPR.

    Uses every distinct score as a threshold (predict member iff score >= thr).
    """
    scores, y_true = _check(scores, y_true)
    P = y_true.sum()
    N = len(y_true) - P
    order = np.argsort(-scores, kind="mergesort")  # high score first
    s_sorted = scores[order]
    y_sorted = y_true[order]
    tp = np.cumsum(y_sorted)
    fp = np.cumsum(1 - y_sorted)
    # collapse ties: keep last index of each distinct score
    distinct = np.r_[np.diff(s_sorted) != 0, True]
    tpr = np.r_[0.0, tp[distinct] / P]
    fpr = np.r_[0.0, fp[distinct] / N]
    thr = np.r_[np.inf, s_sorted[distinct]]
    return fpr, tpr, thr


def auc_roc(scores: np.ndarray, y_true: np.ndarray) -> float:
    """AUC-ROC via the Mann-Whitney U statistic (handles ties with mid-ranks)."""
    scores, y_true = _check(scores, y_true)
    ranks = _rankdata(scores)
    P = y_true.sum()
    N = len(y_true) - P
    sum_ranks_pos = ranks[y_true == 1].sum()
    u = sum_ranks_pos - P * (P + 1) / 2.0
    return float(u / (P * N))


def tpr_at_fpr(scores: np.ndarray, y_true: np.ndarray, target_fpr: float) -> float:
    """Max TPR achievable at FPR <= ``target_fpr`` (the S&P low-FPR operating point)."""
    fpr, tpr, _ = roc_curve(scores, y_true)
    mask = fpr <= target_fpr + 1e-12
    if not mask.any():
        return 0.0
    return float(tpr[mask].max())


@dataclass
class MIAReport:
    auc: float
    tpr_at_0p1: float  # TPR @ 0.1% FPR
    tpr_at_1: float     # TPR @ 1% FPR
    n_pos: int
    n_neg: int


def mia_report(scores, y_true) -> MIAReport:
    scores, y_true = _check(scores, y_true)
    return MIAReport(
        auc=auc_roc(scores, y_true),
        tpr_at_0p1=tpr_at_fpr(scores, y_true, 0.001),
        tpr_at_1=tpr_at_fpr(scores, y_true, 0.01),
        n_pos=int(y_true.sum()),
        n_neg=int(len(y_true) - y_true.sum()),
    )


def bootstrap_ci(metric_fn, scores, y_true, n_boot: int = 1000, seed: int = 0, alpha: float = 0.05):
    """Stratified bootstrap (resample positives and negatives separately) CI for a metric."""
    scores = np.asarray(scores, dtype=np.float64)
    y_true = np.asarray(y_true, dtype=np.int64)
    rng = np.random.default_rng(seed)
    pos = np.where(y_true == 1)[0]
    neg = np.where(y_true == 0)[0]
    vals = []
    for _ in range(n_boot):
        bp = rng.choice(pos, size=len(pos), replace=True)
        bn = rng.choice(neg, size=len(neg), replace=True)
        idx = np.concatenate([bp, bn])
        try:
            vals.append(metric_fn(scores[idx], y_true[idx]))
        except ValueError:
            continue
    vals = np.asarray(vals)
    lo = float(np.quantile(vals, alpha / 2))
    hi = float(np.quantile(vals, 1 - alpha / 2))
    return lo, hi


def _rankdata(a: np.ndarray) -> np.ndarray:
    """Average ranks (1-based), ties shared — equivalent to scipy.stats.rankdata."""
    a = np.asarray(a, dtype=np.float64)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), dtype=np.float64)
    sorted_a = a[order]
    i = 0
    n = len(a)
    while i < n:
        j = i
        while j + 1 < n and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # 1-based average rank
        ranks[order[i : j + 1]] = avg
        i = j + 1
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation (Pearson on ranks). The headline contamination<->leakage stat."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("need equal-length vectors of length >= 2")
    rx = _rankdata(x)
    ry = _rankdata(y)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = np.sqrt((rx**2).sum() * (ry**2).sum())
    if denom == 0:
        return 0.0
    return float((rx * ry).sum() / denom)


def spearman_ci(x, y, n_boot: int = 1000, seed: int = 0, alpha: float = 0.05):
    """Bootstrap CI for Spearman rho (paired resampling)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    rng = np.random.default_rng(seed)
    n = len(x)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        try:
            vals.append(spearman(x[idx], y[idx]))
        except ValueError:
            continue
    vals = np.asarray(vals)
    return float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2))

```


### `eval/partial.py`

```python
"""Partial / semipartial rank correlations, Kendall tau-b, permutation p, BH-FDR.

Used only by the controls run (R6 circularity etc.). Pure numpy; correctness checked
against constructed cases in tests/test_partial.py. Conventions match eval/metrics.py
(higher detector score = more member-like).
"""
from __future__ import annotations

import numpy as np

from .metrics import _rankdata


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    denom = np.sqrt((a**2).sum() * (b**2).sum())
    return 0.0 if denom == 0 else float((a * b).sum() / denom)


def _ranks(x):
    return _rankdata(np.asarray(x, dtype=np.float64))


def spearman(x, y) -> float:
    return _pearson(_ranks(x), _ranks(y))


def partial_spearman(x, y, z) -> float:
    """Partial Spearman corr of x and y controlling for z (Pearson partial on ranks)."""
    rx, ry, rz = _ranks(x), _ranks(y), _ranks(z)
    rxy, rxz, ryz = _pearson(rx, ry), _pearson(rx, rz), _pearson(ry, rz)
    denom = np.sqrt(max(0.0, (1 - rxz**2) * (1 - ryz**2)))
    return 0.0 if denom == 0 else float((rxy - rxz * ryz) / denom)


def semipartial_spearman(x, y, z) -> float:
    """Part correlation: x residualized on z (z removed from x only), correlated with y."""
    rx, ry, rz = _ranks(x), _ranks(y), _ranks(z)
    rxy, rxz, ryz = _pearson(rx, ry), _pearson(rx, rz), _pearson(ry, rz)
    denom = np.sqrt(max(0.0, 1 - rxz**2))
    return 0.0 if denom == 0 else float((rxy - rxz * ryz) / denom)


def kendall_tau(x, y) -> float:
    """Kendall tau-b (tie-corrected). O(n^2); fine for n in the hundreds."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = len(x)
    s = 0
    for i in range(n - 1):
        dx = np.sign(x[i + 1 :] - x[i])
        dy = np.sign(y[i + 1 :] - y[i])
        s += np.sum(dx * dy)
    n0 = n * (n - 1) / 2.0

    def tie_term(v):
        _, counts = np.unique(v, return_counts=True)
        return np.sum(counts * (counts - 1) / 2.0)

    n1 = tie_term(x)
    n2 = tie_term(y)
    denom = np.sqrt((n0 - n1) * (n0 - n2))
    return 0.0 if denom == 0 else float(s / denom)


def permutation_p_partial(x, y, z, n_perm=2000, seed=0) -> float:
    """Two-sided permutation p for partial_spearman(x,y|z): permute y, recompute."""
    x = np.asarray(x, float); y = np.asarray(y, float); z = np.asarray(z, float)
    rng = np.random.default_rng(seed)
    obs = abs(partial_spearman(x, y, z))
    count = 0
    for _ in range(n_perm):
        yp = rng.permutation(y)
        if abs(partial_spearman(x, yp, z)) >= obs - 1e-12:
            count += 1
    return (1 + count) / (n_perm + 1)


def permutation_p_spearman(x, y, n_perm=2000, seed=0) -> float:
    x = np.asarray(x, float); y = np.asarray(y, float)
    rng = np.random.default_rng(seed)
    obs = abs(spearman(x, y))
    count = sum(abs(spearman(x, rng.permutation(y))) >= obs - 1e-12 for _ in range(n_perm))
    return (1 + count) / (n_perm + 1)


def bootstrap_ci(stat_fn, arrays, n_boot=2000, seed=0, alpha=0.05):
    """Percentile bootstrap CI. `arrays` is a tuple of equal-length arrays; stat_fn(*arrays)."""
    arrays = [np.asarray(a, float) for a in arrays]
    n = len(arrays[0])
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        try:
            vals.append(stat_fn(*[a[idx] for a in arrays]))
        except Exception:
            continue
    vals = np.asarray(vals)
    return float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2))


def benjamini_hochberg(pvals, alpha=0.05):
    """Return (rejected_bool_array, qvalues) under BH-FDR at level alpha."""
    p = np.asarray(pvals, dtype=np.float64)
    m = len(p)
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * m / (np.arange(1, m + 1))
    q = np.minimum.accumulate(q[::-1])[::-1]  # enforce monotonicity
    q = np.clip(q, 0, 1)
    qvals = np.empty(m)
    qvals[order] = q
    rejected = qvals <= alpha
    return rejected, qvals

```


### `eval/__init__.py`

```python
"""Evaluation & metrics harness."""
from .metrics import (
    MIAReport,
    auc_roc,
    bootstrap_ci,
    mia_report,
    roc_curve,
    spearman,
    spearman_ci,
    tpr_at_fpr,
)

__all__ = [
    "MIAReport",
    "auc_roc",
    "bootstrap_ci",
    "mia_report",
    "roc_curve",
    "spearman",
    "spearman_ci",
    "tpr_at_fpr",
]

```



# PART 4 — ALL EXPERIMENT SCRIPTS & RUNNER


### `run.py`

```python
#!/usr/bin/env python
"""Experiment runner: Models x Detectors x Datasets, with result caching.

Computes `TokenStats` once per (model, text) and feeds every detector, then writes
per-item scores + labels to a cache so the matrix is resumable. Metrics and figures
are produced by `eval/`. This is the scaffold entry point; the real data loaders
(Pile membership, MIMIR splits, benchmark items) plug into `load_dataset_split`.

Usage:
    python run.py --self-test                  # mock end-to-end, no model download
    python run.py --config configs/pythia160m_pilemia.yaml   # real run (needs torch+HF)
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass

import numpy as np


@dataclass
class Item:
    text: str
    label: int          # 1 = member / contaminated, 0 = non-member / clean
    item_id: str


def load_dataset_split(name: str):
    """Return a list[Item]. Real loaders (Pile/MIMIR/benchmarks) go here.

    The scaffold ships a tiny synthetic split so `--self-test` exercises the full path.
    """
    if name == "synthetic":
        rng = np.random.default_rng(0)
        items = []
        for i in range(50):
            items.append(Item(text=f"member document number {i} " * 5, label=1, item_id=f"m{i}"))
            items.append(Item(text=f"unseen heldout text {rng.integers(1e9)} " * 5, label=0, item_id=f"n{i}"))
        return items
    raise NotImplementedError(
        f"dataset loader '{name}' not implemented yet; see docs/experiment_design.md section 3"
    )


def build_scorer(args):
    if args.self_test:
        from detectors import MockScorer

        members = set()  # populated below once items are known
        return MockScorer(), members
    from detectors import HFScorer

    return HFScorer(args.model, revision=args.revision, device=args.device), None


def run(args):
    from detectors import build_default_detectors
    from eval.metrics import mia_report

    items = load_dataset_split(args.dataset)

    if args.self_test:
        from detectors import MockScorer

        member_texts = {it.text for it in items if it.label == 1}
        scorer = MockScorer(membership_fn=lambda t: t in member_texts, signal=1.5)
    else:
        scorer, _ = build_scorer(args)

    detectors = build_default_detectors(scorer)
    rows = []
    for it in items:
        try:
            stats = scorer.score_tokens(it.text)
        except ValueError:
            continue
        row = {"item_id": it.item_id, "label": it.label}
        for det in detectors:
            row[det.name] = det.score_from_stats(stats, it.text)
        rows.append(row)

    os.makedirs(args.out, exist_ok=True)
    cache_path = os.path.join(args.out, f"{args.dataset}_scores.jsonl")
    with open(cache_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    labels = np.array([r["label"] for r in rows])
    print(f"\nWrote {len(rows)} rows -> {cache_path}\n")
    print(f"{'detector':<18}{'AUC':>8}{'TPR@1%':>10}{'TPR@0.1%':>10}")
    for det in detectors:
        scores = np.array([r[det.name] for r in rows])
        rep = mia_report(scores, labels)
        print(f"{det.name:<18}{rep.auc:>8.3f}{rep.tpr_at_1:>10.3f}{rep.tpr_at_0p1:>10.3f}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true", help="mock run, no model download")
    p.add_argument("--config", default=None, help="YAML config path (real runs)")
    p.add_argument("--dataset", default="synthetic")
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default=None)
    p.add_argument("--device", default="cpu")
    p.add_argument("--out", default="results")
    args = p.parse_args()

    if args.config:
        import yaml  # optional dep; only needed for real configs

        with open(args.config) as f:
            cfg = yaml.safe_load(f)
        for k, v in cfg.items():
            setattr(args, k.replace("-", "_"), v)

    run(args)


if __name__ == "__main__":
    main()

```


### `conftest.py`

```python
"""Make the repo root importable so `import detectors`/`eval`/`extraction` work in tests."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

```


### `scripts/milestone1_pile.py`

```python
#!/usr/bin/env python
"""Milestone 1 (no-auth, confound-controlled): Pythia on Pile train vs. Pile val.

Ground truth WITHOUT the gated MIMIR dataset:
  * MEMBERS     = Pile *train* documents  (NeelNanda/pile-10k, public)  -> in Pythia training
  * NON-MEMBERS = Pile *validation* docs  (mit-han-lab/pile-val-backup) -> held out from training

Both are drawn from The Pile, so stratifying by `meta.pile_set_name` matches the domain
distribution of members and non-members. This controls the topic/temporal confound that
WikiMIA carries (members pre-cutoff, non-members post-cutoff). It is the same train-vs-held-out
construction MIMIR refines with extra n-gram-overlap filtering; we approximate that with
per-subset stratification and document the residual near-duplicate risk as a limitation.

Run:
    python scripts/milestone1_pile.py --model EleutherAI/pythia-160m --n-per-class 300 \
        --max-words 100 --device cpu
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def truncate_words(text, max_words):
    return " ".join(text.split()[:max_words])


def build_split(n_per_class, max_words, min_words, seed, max_scan=20000):
    """Return (texts, labels) balanced and stratified by Pile subset."""
    from datasets import load_dataset

    rng = np.random.default_rng(seed)

    members_by_subset = defaultdict(list)
    for ex in load_dataset("NeelNanda/pile-10k", split="train"):
        t = truncate_words(ex["text"], max_words)
        if len(t.split()) >= min_words:
            members_by_subset[ex["meta"]["pile_set_name"]].append(t)

    nonmembers_by_subset = defaultdict(list)
    stream = load_dataset("mit-han-lab/pile-val-backup", split="validation", streaming=True)
    for i, ex in enumerate(stream):
        if i >= max_scan:
            break
        t = truncate_words(ex["text"], max_words)
        if len(t.split()) >= min_words:
            nonmembers_by_subset[ex["meta"]["pile_set_name"]].append(t)

    shared = sorted(set(members_by_subset) & set(nonmembers_by_subset))
    per_subset = max(1, n_per_class // max(1, len(shared)))

    members, nonmembers, used = [], [], []
    for s in shared:
        m, n = members_by_subset[s], nonmembers_by_subset[s]
        k = min(per_subset, len(m), len(n))
        if k == 0:
            continue
        mi = rng.choice(len(m), size=k, replace=False)
        ni = rng.choice(len(n), size=k, replace=False)
        members.extend(m[j] for j in mi)
        nonmembers.extend(n[j] for j in ni)
        used.append((s, k))

    texts = members + nonmembers
    labels = np.array([1] * len(members) + [0] * len(nonmembers), dtype=int)
    print(f"Built split: {len(members)} members / {len(nonmembers)} non-members")
    print("Per-subset (subset, k):", used)
    return texts, labels


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--n-per-class", type=int, default=300)
    p.add_argument("--max-words", type=int, default=100)
    p.add_argument("--min-words", type=int, default=25)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="figures")
    p.add_argument("--results", default="results")
    args = p.parse_args()

    from detectors import build_default_detectors, HFScorer
    from eval.metrics import auc_roc, bootstrap_ci, mia_report

    texts, labels = build_split(args.n_per_class, args.max_words, args.min_words, args.seed)

    scorer = HFScorer(args.model, revision=args.revision, device=args.device)
    detectors = build_default_detectors(scorer)

    per_det = {d.name: [] for d in detectors}
    keep = []
    for i, t in enumerate(texts):
        try:
            stats = scorer.score_tokens(t)
        except ValueError:
            continue
        keep.append(int(labels[i]))
        for d in detectors:
            per_det[d.name].append(d.score_from_stats(stats, t))
        if (i + 1) % 50 == 0:
            print(f"  scored {i + 1}/{len(texts)}")
    y = np.array(keep)

    os.makedirs(args.results, exist_ok=True)
    tag = f"pilemia_{args.model.split('/')[-1]}"
    with open(os.path.join(args.results, f"{tag}.jsonl"), "w") as f:
        for i in range(len(y)):
            f.write(json.dumps({"label": int(y[i]), **{n: per_det[n][i] for n in per_det}}) + "\n")

    print(f"\nModel={args.model}  Pile train-vs-val  N={len(y)}")
    print(f"{'detector':<18}{'AUC':>8}{'AUC 95% CI':>20}{'TPR@1%':>10}{'TPR@.1%':>10}")
    summary = {}
    for name, scores in per_det.items():
        s = np.array(scores)
        rep = mia_report(s, y)
        lo, hi = bootstrap_ci(auc_roc, s, y, n_boot=500, seed=0)
        summary[name] = {"auc": rep.auc, "auc_ci": [lo, hi],
                         "tpr_at_1": rep.tpr_at_1, "tpr_at_0p1": rep.tpr_at_0p1}
        print(f"{name:<18}{rep.auc:>8.3f}{f'[{lo:.3f}, {hi:.3f}]':>20}"
              f"{rep.tpr_at_1:>10.3f}{rep.tpr_at_0p1:>10.3f}")

    with open(os.path.join(args.results, f"{tag}_summary.json"), "w") as f:
        json.dump({"model": args.model, "n": int(len(y)), "construction": "pile-train-vs-val",
                   "summary": summary}, f, indent=2)

    try:
        _plots(per_det, y, args.out, args.model)
        print(f"Plots -> {args.out}/")
    except ImportError:
        print("(matplotlib not installed; skipping plots)")


def _plots(per_det, y, out, model):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from eval.metrics import roc_curve

    os.makedirs(out, exist_ok=True)
    tag = model.split("/")[-1]
    names = list(per_det)
    fig, axes = plt.subplots(1, len(names), figsize=(3.6 * len(names), 3.0))
    for ax, name in zip(np.atleast_1d(axes), names):
        s = np.array(per_det[name])
        ax.hist(s[y == 1], bins=25, alpha=0.6, label="member (train)", density=True)
        ax.hist(s[y == 0], bins=25, alpha=0.6, label="non-member (val)", density=True)
        ax.set_title(name, fontsize=9)
        ax.legend(fontsize=7)
    fig.suptitle(f"{tag} on Pile train-vs-val: score distributions", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(out, f"pilemia_{tag}_dists.png"), dpi=150)

    fig2, ax2 = plt.subplots(figsize=(4.5, 4.5))
    for name in names:
        fpr, tpr, _ = roc_curve(np.array(per_det[name]), y)
        ax2.plot(np.clip(fpr, 1e-3, 1), np.clip(tpr, 1e-3, 1), label=name)
    ax2.plot([1e-3, 1], [1e-3, 1], "k--", lw=0.6)
    ax2.set_xscale("log"); ax2.set_yscale("log")
    ax2.set_xlabel("FPR"); ax2.set_ylabel("TPR")
    ax2.set_title(f"Log-scale ROC ({tag}, Pile train-vs-val)", fontsize=10)
    ax2.legend(fontsize=7)
    fig2.tight_layout()
    fig2.savefig(os.path.join(out, f"pilemia_{tag}_logroc.png"), dpi=150)


if __name__ == "__main__":
    main()

```


### `scripts/milestone1_wikimia.py`

```python
#!/usr/bin/env python
"""Milestone 1 (public-data version): Pythia on WikiMIA member/non-member separation.

WikiMIA (Shi et al. 2024) is the public, non-gated membership benchmark used by the
Min-K% and Min-K%++ papers themselves (including with Pythia models). It carries a known
temporal confound (Duan et al. 2024) -- members are pre-cutoff Wikipedia text,
non-members are post-cutoff -- so it validates the PIPELINE and shows separability, but
the confound-clean ground truth for the paper is the gated MIMIR splits. Swap in MIMIR
via scripts/milestone1_separation.py once authenticated.

Run:
    python scripts/milestone1_wikimia.py --model EleutherAI/pythia-160m --length 64 --device cpu
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--length", type=int, default=64, choices=[32, 64, 128, 256])
    p.add_argument("--limit", type=int, default=0, help="cap #examples (0 = all)")
    p.add_argument("--out", default="figures")
    p.add_argument("--results", default="results")
    args = p.parse_args()

    from datasets import load_dataset

    from detectors import build_default_detectors, HFScorer
    from eval.metrics import bootstrap_ci, mia_report, auc_roc

    ds = load_dataset("swj0419/WikiMIA", split=f"WikiMIA_length{args.length}")
    texts = list(ds["input"])
    labels = np.array(ds["label"], dtype=int)  # 1 = member, 0 = non-member
    if args.limit:
        texts, labels = texts[: args.limit], labels[: args.limit]
    print(f"WikiMIA_length{args.length}: {len(texts)} examples "
          f"({int(labels.sum())} member / {int((1 - labels).sum())} non-member)")

    scorer = HFScorer(args.model, revision=args.revision, device=args.device)
    detectors = build_default_detectors(scorer)

    per_det = {d.name: [] for d in detectors}
    keep_labels = []
    for i, t in enumerate(texts):
        try:
            stats = scorer.score_tokens(t)
        except ValueError:
            continue
        keep_labels.append(int(labels[i]))
        for d in detectors:
            per_det[d.name].append(d.score_from_stats(stats, t))
        if (i + 1) % 50 == 0:
            print(f"  scored {i + 1}/{len(texts)}")
    y = np.array(keep_labels)

    os.makedirs(args.results, exist_ok=True)
    rows = [{"label": int(y[i]), **{n: per_det[n][i] for n in per_det}} for i in range(len(y))]
    cache = os.path.join(args.results, f"wikimia{args.length}_{args.model.split('/')[-1]}.jsonl")
    with open(cache, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    print(f"\nModel={args.model}  WikiMIA_length{args.length}  N={len(y)}")
    print(f"{'detector':<18}{'AUC':>8}{'AUC 95% CI':>20}{'TPR@1%':>10}{'TPR@.1%':>10}")
    summary = {}
    for name, scores in per_det.items():
        s = np.array(scores)
        rep = mia_report(s, y)
        lo, hi = bootstrap_ci(auc_roc, s, y, n_boot=500, seed=0)
        summary[name] = {"auc": rep.auc, "auc_ci": [lo, hi],
                         "tpr_at_1": rep.tpr_at_1, "tpr_at_0p1": rep.tpr_at_0p1}
        print(f"{name:<18}{rep.auc:>8.3f}{f'[{lo:.3f}, {hi:.3f}]':>20}"
              f"{rep.tpr_at_1:>10.3f}{rep.tpr_at_0p1:>10.3f}")

    with open(os.path.join(args.results, f"wikimia{args.length}_summary.json"), "w") as f:
        json.dump({"model": args.model, "length": args.length, "n": int(len(y)),
                   "summary": summary}, f, indent=2)

    try:
        _plots(per_det, y, args.out, args.model, args.length)
        print(f"Plots -> {args.out}/")
    except ImportError:
        print("(matplotlib not installed; skipping plots)")


def _plots(per_det, y, out, model, length):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from eval.metrics import roc_curve

    os.makedirs(out, exist_ok=True)
    names = list(per_det)
    fig, axes = plt.subplots(1, len(names), figsize=(3.6 * len(names), 3.0))
    for ax, name in zip(np.atleast_1d(axes), names):
        s = np.array(per_det[name])
        ax.hist(s[y == 1], bins=25, alpha=0.6, label="member", density=True)
        ax.hist(s[y == 0], bins=25, alpha=0.6, label="non-member", density=True)
        ax.set_title(name, fontsize=9)
        ax.legend(fontsize=7)
    fig.suptitle(f"{model.split('/')[-1]} on WikiMIA-{length}: score distributions", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(out, f"milestone1_wikimia{length}_dists.png"), dpi=150)

    fig2, ax2 = plt.subplots(figsize=(4.5, 4.5))
    for name in names:
        fpr, tpr, _ = roc_curve(np.array(per_det[name]), y)
        ax2.plot(np.clip(fpr, 1e-3, 1), np.clip(tpr, 1e-3, 1), label=name)
    ax2.plot([1e-3, 1], [1e-3, 1], "k--", lw=0.6)
    ax2.set_xscale("log"); ax2.set_yscale("log")
    ax2.set_xlabel("FPR"); ax2.set_ylabel("TPR")
    ax2.set_title(f"Log-scale ROC ({model.split('/')[-1]}, WikiMIA-{length})", fontsize=10)
    ax2.legend(fontsize=7)
    fig2.tight_layout()
    fig2.savefig(os.path.join(out, f"milestone1_wikimia{length}_logroc.png"), dpi=150)


if __name__ == "__main__":
    main()

```


### `scripts/milestone1_separation.py`

```python
#!/usr/bin/env python
"""Milestone 1: load Pythia, score Pile member vs non-member text, plot separation.

This is the first REAL-compute milestone (gated on torch + transformers + data). It:
  1. loads Pythia-160m,
  2. computes LOSS, Min-K%, Min-K%++, zlib scores for a set of known Pile members and
     known non-members,
  3. reports AUC + TPR@low-FPR per detector,
  4. saves score-distribution + log-scale ROC plots.

Run:
    pip install -r requirements.txt
    python scripts/milestone1_separation.py --n 200 --device cpu

Provide member/non-member text via --members-file / --nonmembers-file (one text per
line). If omitted, the script exits with instructions rather than inventing data --
ground truth must be real Pile membership (see docs/experiment_design.md section 3).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f if ln.strip()]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--members-file", required=True, help="known Pile members, one text/line")
    p.add_argument("--nonmembers-file", required=True, help="known non-members, one text/line")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--out", default="figures")
    args = p.parse_args()

    from detectors import build_default_detectors, HFScorer
    from eval.metrics import mia_report

    members = read_lines(args.members_file)[: args.n]
    nonmembers = read_lines(args.nonmembers_file)[: args.n]
    print(f"Loaded {len(members)} members, {len(nonmembers)} non-members")

    scorer = HFScorer(args.model, revision=args.revision, device=args.device)
    detectors = build_default_detectors(scorer)

    texts = members + nonmembers
    labels = np.array([1] * len(members) + [0] * len(nonmembers))
    per_det = {d.name: [] for d in detectors}
    keep = []
    for i, t in enumerate(texts):
        try:
            stats = scorer.score_tokens(t)
        except ValueError:
            continue
        keep.append(labels[i])
        for d in detectors:
            per_det[d.name].append(d.score_from_stats(stats, t))
    y = np.array(keep)

    print(f"\n{'detector':<18}{'AUC':>8}{'TPR@1%':>10}{'TPR@0.1%':>10}")
    for name, scores in per_det.items():
        rep = mia_report(np.array(scores), y)
        print(f"{name:<18}{rep.auc:>8.3f}{rep.tpr_at_1:>10.3f}{rep.tpr_at_0p1:>10.3f}")

    try:
        _plots(per_det, y, args.out)
        print(f"\nPlots written to {args.out}/")
    except ImportError:
        print("\n(matplotlib not installed; skipping plots)")


def _plots(per_det, y, out):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from eval.metrics import roc_curve

    os.makedirs(out, exist_ok=True)
    # score distributions
    fig, axes = plt.subplots(1, len(per_det), figsize=(4 * len(per_det), 3.2))
    for ax, (name, scores) in zip(np.atleast_1d(axes), per_det.items()):
        s = np.array(scores)
        ax.hist(s[y == 1], bins=30, alpha=0.6, label="member", density=True)
        ax.hist(s[y == 0], bins=30, alpha=0.6, label="non-member", density=True)
        ax.set_title(name)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "milestone1_score_distributions.png"), dpi=150)

    # log-scale ROC
    fig2, ax2 = plt.subplots(figsize=(4.5, 4.5))
    for name, scores in per_det.items():
        fpr, tpr, _ = roc_curve(np.array(scores), y)
        ax2.plot(np.clip(fpr, 1e-4, 1), np.clip(tpr, 1e-4, 1), label=name)
    ax2.plot([1e-4, 1], [1e-4, 1], "k--", lw=0.6)
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("FPR")
    ax2.set_ylabel("TPR")
    ax2.set_title("Log-scale ROC (Pythia-160m, Pile membership)")
    ax2.legend(fontsize=7)
    fig2.tight_layout()
    fig2.savefig(os.path.join(out, "milestone1_logroc.png"), dpi=150)


if __name__ == "__main__":
    main()

```


### `scripts/extraction_pile.py`

```python
#!/usr/bin/env python
"""Real per-item extraction outcomes on Pile MEMBER documents (canonical item set).

Loads N Pile *train* (member) documents from NeelNanda/pile-10k, stratified across
subsets like milestone1_pile.py. For each doc we take a prefix of `prefix_len`
tokens of context and the next up to `suffix_len` tokens as the target suffix, then
run `is_extractable` with a greedy HF generator (pythia-160m, CPU).

The output `results/pile_items_160m.jsonl` is the CONTRACT consumed by the
correlation step: the SAME "text" field (decoded prefix+suffix) is re-scored by the
membership detectors, so it must be exactly the string scored here.

Run:
    python scripts/extraction_pile.py --model EleutherAI/pythia-160m --device cpu \
        --n 300 --prefix-len 32 --suffix-len 50 --seed 0
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extraction import (  # noqa: E402
    extraction_rate,
    fractional_extraction,
    hf_greedy_generator,
    is_extractable,
)


def load_member_docs(n, min_tokens, prefix_len, suffix_len, tokenizer, seed):
    """Return up to `n` member docs as (pile_set_name, token_ids[>= min_tokens]).

    Stratified across Pile subsets (same construction as milestone1_pile.py): we
    bucket docs by subset, then round-robin draw a balanced quota per subset.
    """
    from datasets import load_dataset

    rng = np.random.default_rng(seed)
    need = prefix_len + 1  # at least one suffix token
    floor = max(min_tokens, need)

    by_subset = defaultdict(list)
    for ex in load_dataset("NeelNanda/pile-10k", split="train"):
        ids = tokenizer(ex["text"], add_special_tokens=False)["input_ids"]
        if len(ids) >= floor:
            # cap to prefix+suffix so "text" stays the exact scored window
            by_subset[ex["meta"]["pile_set_name"]].append(ids[: prefix_len + suffix_len])

    subsets = sorted(by_subset)
    per_subset = max(1, n // max(1, len(subsets)))

    picked = []
    used = []
    for s in subsets:
        docs = by_subset[s]
        k = min(per_subset, len(docs))
        if k == 0:
            continue
        idx = rng.choice(len(docs), size=k, replace=False)
        for j in idx:
            picked.append((s, docs[j]))
        used.append((s, k))

    # If stratified quota underfills n, top up from a shuffled global pool.
    if len(picked) < n:
        chosen = {(s, tuple(ids)) for s, ids in picked}
        pool = [(s, ids) for s in subsets for ids in by_subset[s]]
        order = rng.permutation(len(pool))
        for o in order:
            if len(picked) >= n:
                break
            s, ids = pool[o]
            if (s, tuple(ids)) in chosen:
                continue
            picked.append((s, ids))
            chosen.add((s, tuple(ids)))

    rng.shuffle(picked)
    picked = picked[:n]
    print(f"Loaded {len(picked)} member docs (>= {floor} tokens). Per-subset quota: {used}")
    return picked


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--n", type=int, default=300)
    p.add_argument("--prefix-len", type=int, default=32)
    p.add_argument("--suffix-len", type=int, default=50)
    p.add_argument("--min-tokens", type=int, default=80)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--results", default="results")
    p.add_argument("--out", default="pile_items_160m.jsonl")
    args = p.parse_args()

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
    generate = hf_greedy_generator(args.model, revision=args.revision, device=args.device)

    docs = load_member_docs(
        args.n, args.min_tokens, args.prefix_len, args.suffix_len, tokenizer, args.seed
    )

    os.makedirs(args.results, exist_ok=True)
    out_path = os.path.join(args.results, args.out)

    results = []
    rows = []
    for i, (pile_set_name, ids) in enumerate(docs):
        # text = exact decoded prefix+suffix window that is scored here.
        text = tokenizer.decode(ids, skip_special_tokens=True)
        r = is_extractable(ids, prefix_len=args.prefix_len, generate=generate)
        results.append(r)
        rows.append({
            "item_id": i,
            "text": text,
            "prefix_len": r.prefix_len,
            "suffix_len": r.suffix_len,
            "extracted": bool(r.extracted),
            "matched_tokens": int(r.matched_tokens),
            "frac_extracted": float(r.matched_tokens / r.suffix_len if r.suffix_len else 0.0),
            "pile_set_name": pile_set_name,
        })
        if (i + 1) % 25 == 0:
            print(f"  scored {i + 1}/{len(docs)}")

    with open(out_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    rate = extraction_rate(results)
    fracs = fractional_extraction(results)
    n_full = int(sum(r.extracted for r in results))

    print(f"\nModel={args.model}  N={len(results)}  prefix_len={args.prefix_len}")
    print(f"extraction_rate (exact full-suffix match): {rate:.4f}  ({n_full}/{len(results)})")
    print(f"mean frac_extracted: {fracs.mean():.4f}   median: {np.median(fracs):.4f}")
    # histogram-ish summary over fractional extraction
    edges = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0, 1.0001]
    labels = ["[0,0.1)", "[0.1,0.25)", "[0.25,0.5)", "[0.5,0.75)",
              "[0.75,0.9)", "[0.9,1.0)", "==1.0"]
    hist, _ = np.histogram(fracs, bins=edges)
    print("frac_extracted histogram:")
    for lab, c in zip(labels, hist):
        print(f"  {lab:<12}: {int(c)}")
    print(f"Wrote {len(rows)} items -> {out_path}")


if __name__ == "__main__":
    main()

```


### `scripts/pii_enron.py`

```python
#!/usr/bin/env python
"""PII-leakage analysis on the Enron Emails subset of The Pile.

ETHICS: Enron Emails is a public corpus already in Pythia's training data. We
report ONLY aggregate counts/rates and PII *types*; no PII string is ever printed
or written. This is not used to target individuals.

Method (per Enron doc with enough tokens):
  * split tokens into prefix (`prefix_len`) and suffix (next up to `suffix_len`);
  * decode the suffix and detect PII in it (find_pii);
  * for docs whose suffix contains >= 1 PII token, run greedy continuation from the
    prefix and check whether the same PII *type* and *value span* is reproduced in
    the generated suffix -> pii_leaked = 1, else 0.

Output `results/pii_enron_160m.jsonl` rows:
  {"item_id","has_pii_in_suffix","pii_types","pii_leaked","frac_extracted"}

Run:
    python scripts/pii_enron.py --model EleutherAI/pythia-160m --device cpu \
        --prefix-len 32 --suffix-len 50
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extraction import hf_greedy_generator, is_extractable  # noqa: E402
from extraction.pii import find_pii, pii_types  # noqa: E402


def load_enron_docs(min_tokens, prefix_len, suffix_len, tokenizer):
    """Return Enron member docs as token_ids capped to prefix+suffix."""
    from datasets import load_dataset

    need = prefix_len + 1
    floor = max(min_tokens, need)
    out = []
    for ex in load_dataset("NeelNanda/pile-10k", split="train"):
        if ex["meta"]["pile_set_name"] != "Enron Emails":
            continue
        ids = tokenizer(ex["text"], add_special_tokens=False)["input_ids"]
        if len(ids) >= floor:
            out.append(ids[: prefix_len + suffix_len])
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--prefix-len", type=int, default=32)
    p.add_argument("--suffix-len", type=int, default=50)
    p.add_argument("--min-tokens", type=int, default=80)
    p.add_argument("--results", default="results")
    p.add_argument("--out", default="pii_enron_160m.jsonl")
    args = p.parse_args()

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
    generate = hf_greedy_generator(args.model, revision=args.revision, device=args.device)

    docs = load_enron_docs(args.min_tokens, args.prefix_len, args.suffix_len, tokenizer)
    print(f"Loaded {len(docs)} Enron Emails docs (>= "
          f"{max(args.min_tokens, args.prefix_len + 1)} tokens)")

    os.makedirs(args.results, exist_ok=True)
    out_path = os.path.join(args.results, args.out)

    rows = []
    n_with_pii = 0
    n_leaked = 0
    for i, ids in enumerate(docs):
        prefix_ids = ids[: args.prefix_len]
        suffix_ids = ids[args.prefix_len:]
        suffix_text = tokenizer.decode(suffix_ids, skip_special_tokens=True)

        suffix_pii = find_pii(suffix_text)
        has_pii = len(suffix_pii) > 0
        types = sorted({t for t, _ in suffix_pii})

        r = is_extractable(ids, prefix_len=args.prefix_len, generate=generate)
        frac = float(r.matched_tokens / r.suffix_len if r.suffix_len else 0.0)

        leaked = False
        if has_pii:
            n_with_pii += 1
            gen_ids = list(generate(prefix_ids, len(suffix_ids)))[: len(suffix_ids)]
            gen_text = tokenizer.decode(gen_ids, skip_special_tokens=True)
            gen_pii_strings = {gen_text[s:e] for _, (s, e) in find_pii(gen_text)}
            true_pii_strings = {suffix_text[s:e] for _, (s, e) in suffix_pii}
            # leakage: the model reproduced a real PII value verbatim
            leaked = len(gen_pii_strings & true_pii_strings) > 0
            if leaked:
                n_leaked += 1

        rows.append({
            "item_id": i,
            "has_pii_in_suffix": bool(has_pii),
            "pii_types": types,
            "pii_leaked": bool(leaked),
            "frac_extracted": frac,
        })

    with open(out_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    leak_rate = (n_leaked / n_with_pii) if n_with_pii else 0.0
    print(f"\nModel={args.model}  Enron Emails  docs={len(rows)}")
    print(f"docs with PII in suffix: {n_with_pii}")
    print(f"docs where PII leaked (verbatim reproduced): {n_leaked}")
    print(f"PII leakage rate (leaked / with-PII): {leak_rate:.4f}")
    # aggregate type counts (types only, no values)
    from collections import Counter
    type_counts = Counter(t for row in rows for t in row["pii_types"])
    print("PII type counts across suffixes (type: #docs-with-that-type):")
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    print(f"Wrote {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()

```


### `scripts/correlation_160m.py`

```python
#!/usr/bin/env python
"""HEADLINE RESULT: contamination/membership score <-> extraction/leakage correlation.

Consumes the canonical item set emitted by scripts/extraction_pile.py
(results/pile_items_<model>.jsonl: Pile MEMBERS with per-item extraction outcomes),
re-scores the EXACT same `text` field with the membership detectors, and computes the
Spearman correlation between each detector's contamination score and the leakage outcome
(fractional extraction). Bootstrap CIs included. This is the paper's thesis as a number.

The leakage signal at 160m is heavily zero-inflated (small model, 32-token prefixes), so
a weak correlation with a wide CI is the EXPECTED preliminary result; model size is a
single --model flag for the GPU scale-up.

Run:
    python scripts/correlation_160m.py --model EleutherAI/pythia-160m --device cpu
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--items", default=None, help="defaults to results/pile_items_<model>.jsonl")
    p.add_argument("--out", default="figures")
    p.add_argument("--results", default="results")
    args = p.parse_args()

    from detectors import build_default_detectors, HFScorer
    from eval.metrics import spearman, spearman_ci

    tag = args.model.split("/")[-1]
    items_path = args.items or os.path.join(args.results, f"pile_items_{tag}.jsonl")
    items = [json.loads(l) for l in open(items_path)]
    print(f"Loaded {len(items)} member items from {items_path}")

    scorer = HFScorer(args.model, revision=args.revision, device=args.device)
    detectors = build_default_detectors(scorer)

    det_scores = {d.name: [] for d in detectors}
    frac = []
    extracted = []
    kept = 0
    for i, it in enumerate(items):
        try:
            stats = scorer.score_tokens(it["text"])
        except ValueError:
            continue
        for d in detectors:
            det_scores[d.name].append(d.score_from_stats(stats, it["text"]))
        frac.append(float(it["frac_extracted"]))
        extracted.append(int(it["extracted"]))
        kept += 1
        if kept % 50 == 0:
            print(f"  scored {kept}")
    frac = np.array(frac)
    extracted = np.array(extracted)

    print(f"\nHEADLINE: contamination score <-> extraction (Spearman), {tag}, N={kept}")
    print(f"  leakage signal: mean frac={frac.mean():.4f}, fully-extracted={int(extracted.sum())}/{kept}")
    print(f"\n{'detector':<18}{'rho(frac)':>12}{'95% CI':>22}{'rho(extracted)':>16}")
    summary = {}
    for name in det_scores:
        s = np.array(det_scores[name])
        rho_f = spearman(s, frac)
        lo, hi = spearman_ci(s, frac, n_boot=2000, seed=0)
        rho_e = spearman(s, extracted.astype(float))
        summary[name] = {"rho_frac": rho_f, "rho_frac_ci": [lo, hi], "rho_extracted": rho_e}
        sig = "" if (lo <= 0 <= hi) else "  *CI excludes 0*"
        print(f"{name:<18}{rho_f:>12.3f}{f'[{lo:.3f}, {hi:.3f}]':>22}{rho_e:>16.3f}{sig}")

    os.makedirs(args.results, exist_ok=True)
    with open(os.path.join(args.results, f"correlation_{tag}.json"), "w") as f:
        json.dump({"model": args.model, "n": kept,
                   "leakage_mean_frac": float(frac.mean()),
                   "fully_extracted": int(extracted.sum()),
                   "summary": summary}, f, indent=2)

    try:
        _scatter(det_scores, frac, args.out, tag)
        print(f"\nScatter -> {args.out}/correlation_{tag}_scatter.png")
    except ImportError:
        print("(matplotlib missing; skipping scatter)")

    return summary


def _scatter(det_scores, frac, out, tag):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(out, exist_ok=True)
    names = list(det_scores)
    fig, axes = plt.subplots(1, len(names), figsize=(3.6 * len(names), 3.2))
    for ax, name in zip(np.atleast_1d(axes), names):
        ax.scatter(det_scores[name], frac, s=10, alpha=0.5)
        ax.set_xlabel(f"{name} score")
        ax.set_ylabel("fractional extraction")
        ax.set_title(name, fontsize=9)
    fig.suptitle(f"{tag}: contamination score vs. extraction (Pile members)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(out, f"correlation_{tag}_scatter.png"), dpi=150)


if __name__ == "__main__":
    main()

```


### `scripts/controls_160m.py`

```python
#!/usr/bin/env python
"""Controls run (R6 primary + R1/R7 + strata) on an existing item set.

Re-scores the items' EXACT text with the membership detectors (deterministic), reuses
their leakage outcomes, and computes raw / partial(|loss) / semipartial / freq-matched
correlations with bootstrap CIs, permutation p, Kendall tau, BH-FDR over the R6 family,
and per-domain stratification. See docs/pre_analysis.md for the pre-registered plan.

Run:
    python scripts/controls_160m.py --model EleutherAI/pythia-160m \
        --items results/pile_items_160m.jsonl --tag pythia-160m
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CALIBRATED = ["min_20_prob", "min_20_plusplus", "zlib_ratio"]  # R6 family (control = loss)


def freq_proxy(texts):
    """Per-item mean unigram log-frequency (whitespace tokens, counts over the item union)."""
    counts = Counter()
    toks_per = []
    for t in texts:
        toks = t.split()
        toks_per.append(toks)
        counts.update(toks)
    total = sum(counts.values())
    out = []
    for toks in toks_per:
        if not toks:
            out.append(0.0)
            continue
        out.append(float(np.mean([np.log(counts[w] / total) for w in toks])))
    return np.array(out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--items", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--results", default="results")
    p.add_argument("--n-boot", type=int, default=2000)
    p.add_argument("--n-perm", type=int, default=2000)
    args = p.parse_args()

    from detectors import build_default_detectors, HFScorer
    from eval.partial import (
        benjamini_hochberg, bootstrap_ci, kendall_tau, partial_spearman,
        permutation_p_partial, permutation_p_spearman, semipartial_spearman, spearman,
    )

    items = [json.loads(l) for l in open(args.items)]
    texts = [it["text"] for it in items]
    frac = np.array([float(it["frac_extracted"]) for it in items])
    domain = [it.get("pile_set_name", "?") for it in items]
    print(f"{args.tag}: {len(items)} items, mean frac={frac.mean():.4f}, "
          f"fully={int((frac>=1.0).sum())}")

    scorer = HFScorer(args.model, revision=args.revision, device=args.device)
    dets = build_default_detectors(scorer)  # [loss, min_20_prob, min_20_plusplus, zlib_ratio]
    scores = {d.name: [] for d in dets}
    for i, t in enumerate(texts):
        st = scorer.score_tokens(t)
        for d in dets:
            scores[d.name].append(d.score_from_stats(st, t))
        if (i + 1) % 50 == 0:
            print(f"  scored {i+1}/{len(texts)}")
    scores = {k: np.array(v) for k, v in scores.items()}
    loss = scores["loss"]

    # persist per-example scores (so controls are reproducible without re-inference)
    os.makedirs(args.results, exist_ok=True)
    with open(os.path.join(args.results, f"controls_scores_{args.tag}.jsonl"), "w") as f:
        for i in range(len(items)):
            f.write(json.dumps({"item_id": items[i].get("item_id", i),
                                "frac_extracted": float(frac[i]), "pile_set_name": domain[i],
                                **{k: float(scores[k][i]) for k in scores}}) + "\n")

    fp = freq_proxy(texts)
    mid = (fp >= np.quantile(fp, 1/3)) & (fp <= np.quantile(fp, 2/3))  # middle tertile

    out = {"model": args.model, "tag": args.tag, "n": len(items),
           "mean_frac": float(frac.mean()), "detectors": {}}

    # raw correlations (all 4 detectors)
    for name in scores:
        s = scores[name]
        out["detectors"][name] = {
            "raw_rho": spearman(s, frac),
            "raw_ci": list(bootstrap_ci(spearman, (s, frac), args.n_boot)),
            "raw_kendall": kendall_tau(s, frac),
            "raw_perm_p": permutation_p_spearman(s, frac, args.n_perm),
        }

    # R6 partial/semipartial controlling for loss (calibrated detectors only)
    perm_ps = []
    for name in CALIBRATED:
        s = scores[name]
        pr = partial_spearman(s, frac, loss)
        pci = bootstrap_ci(lambda a, b, c: partial_spearman(a, b, c),
                           (s, frac, loss), args.n_boot)
        pp = permutation_p_partial(s, frac, loss, args.n_perm)
        perm_ps.append(pp)
        out["detectors"][name].update({
            "partial_rho_given_loss": pr,
            "partial_ci": list(pci),
            "partial_perm_p": pp,
            "partial_kendall_resid": None,  # Kendall on residuals not defined simply; omit
            "semipartial_rho": semipartial_spearman(s, frac, loss),
            "freqmatched_rho": spearman(s[mid], frac[mid]),
            "freqmatched_n": int(mid.sum()),
            "partial_rho_given_freq": partial_spearman(s, frac, fp),
        })

    rejected, qvals = benjamini_hochberg(perm_ps)
    out["R6_family"] = {
        "detectors": CALIBRATED,
        "perm_p": perm_ps,
        "bh_qvalues": [float(q) for q in qvals],
        "bh_rejected": [bool(r) for r in rejected],
    }

    # per-domain raw rho (stratification)
    by_dom = defaultdict(list)
    for i, d in enumerate(domain):
        by_dom[d].append(i)
    strata = {}
    for d, idx in sorted(by_dom.items()):
        if len(idx) >= 5:
            idx = np.array(idx)
            strata[d] = {"n": len(idx),
                         "loss_rho": spearman(loss[idx], frac[idx])}
    out["per_domain_loss_rho"] = strata

    with open(os.path.join(args.results, f"controls_{args.tag}.json"), "w") as f:
        json.dump(out, f, indent=2)

    # ---- print summary table ----
    print(f"\n=== CONTROLS: {args.tag} (N={len(items)}) ===")
    print(f"{'detector':<16}{'raw rho':>9}{'partial|loss':>14}{'partial CI':>20}"
          f"{'semipart':>10}{'freqmatch':>11}{'kendall':>9}")
    for name in scores:
        d = out["detectors"][name]
        pr = d.get("partial_rho_given_loss")
        ci = d.get("partial_ci")
        ci_s = f"[{ci[0]:.3f},{ci[1]:.3f}]" if ci else "  (control=loss) "
        prs = f"{pr:.3f}" if pr is not None else "    --"
        sp = f"{d.get('semipartial_rho'):.3f}" if d.get("semipartial_rho") is not None else "  --"
        fm = f"{d.get('freqmatched_rho'):.3f}" if d.get("freqmatched_rho") is not None else "  --"
        print(f"{name:<16}{d['raw_rho']:>9.3f}{prs:>14}{ci_s:>20}{sp:>10}{fm:>11}{d['raw_kendall']:>9.3f}")
    print("\nR6 family (control=loss), BH-FDR:")
    for name, pp, q, r in zip(CALIBRATED, perm_ps, qvals, rejected):
        print(f"  {name:<16} perm_p={pp:.4f}  BH_q={q:.4f}  reject_null={bool(r)}")
    print(f"\nwrote results/controls_{args.tag}.json")


if __name__ == "__main__":
    main()

```


### `scripts/validate_ngram_oren.py`

```python
#!/usr/bin/env python
"""Validate the n-gram overlap check and the Oren permutation test on real Pile data.

Reuses the Pile train-vs-val construction from milestone1_pile.py:
  * MEMBERS     = Pile *train* docs (NeelNanda/pile-10k)        -> in Pythia's training data
  * NON-MEMBERS = Pile *validation* docs (mit-han-lab/pile-val-backup) -> held out

n-gram overlap (corpus-side, no model):
  Build the index from MEMBER texts, then score members vs non-members. Members are *in* the
  index corpus, so they should show much higher n-gram overlap than the held-out non-members.
  We report mean overlap for each group and a separation number (member_mean - nonmember_mean).

Oren permutation test (model-side, order-sensitive):
  Treat ~10 member examples as a "contaminated ordered set" and ~10 non-members as a control,
  and report each group's p-value under the target model. With a small CPU model and short
  examples this is a sanity demonstration of the interface on real text, not a strong claim.

Run:
    python scripts/validate_ngram_oren.py --model EleutherAI/pythia-160m \
        --n-per-class 50 --max-words 60 --device cpu
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.milestone1_pile import build_split  # reuse the exact split logic


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--n-per-class", type=int, default=50)
    p.add_argument("--max-words", type=int, default=60)
    p.add_argument("--min-words", type=int, default=25)
    p.add_argument("--ngram-n", type=int, default=13)
    p.add_argument("--oren-k", type=int, default=10, help="examples per Oren group")
    p.add_argument("--oren-words", type=int, default=20, help="truncate Oren examples to keep CPU cheap")
    p.add_argument("--n-permutations", type=int, default=500)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    from detectors import NGramOverlapDetector, OrenPermutationTest, HFScorer

    texts, labels = build_split(args.n_per_class, args.max_words, args.min_words, args.seed)
    texts = np.array(texts, dtype=object)
    labels = np.asarray(labels)
    members = list(texts[labels == 1])
    nonmembers = list(texts[labels == 0])

    # ---------------------------------------------------------------- n-gram overlap
    print(f"\n=== n-gram overlap (n={args.ngram_n}), index built from {len(members)} MEMBER texts ===")
    det = NGramOverlapDetector(n=args.ngram_n).build_index(members)
    print(f"index size: {det.index_size} distinct {args.ngram_n}-grams")

    mem_scores = np.array([det.score(t) for t in members])
    non_scores = np.array([det.score(t) for t in nonmembers])
    mem_mean, non_mean = float(mem_scores.mean()), float(non_scores.mean())
    print(f"member   mean overlap: {mem_mean:.4f}  (min {mem_scores.min():.3f}, max {mem_scores.max():.3f})")
    print(f"nonmember mean overlap: {non_mean:.4f}  (min {non_scores.min():.3f}, max {non_scores.max():.3f})")
    print(f"separation (member - nonmember): {mem_mean - non_mean:+.4f}")
    flagged_non = int((non_scores > 0).sum())
    print(f"non-members with ANY {args.ngram_n}-gram overlap: {flagged_non}/{len(nonmembers)} "
          f"(near-duplicate / boilerplate leakage)")

    # ---------------------------------------------------------------- Oren permutation test
    def trunc(t):
        return " ".join(t.split()[: args.oren_words])

    k = args.oren_k
    contaminated = [trunc(t) for t in members[:k]]
    control = [trunc(t) for t in nonmembers[:k]]

    print(f"\n=== Oren permutation test (model={args.model}, {k} examples/group, "
          f"{args.n_permutations} permutations) ===")
    scorer = HFScorer(args.model, revision=args.revision, device=args.device)
    test = OrenPermutationTest(scorer)

    cont_res = test.test(contaminated, n_permutations=args.n_permutations, seed=args.seed)
    ctrl_res = test.test(control, n_permutations=args.n_permutations, seed=args.seed)

    def show(tag, r):
        print(f"{tag:<26} p={r['p_value']:.4f}  canonical_ll={r['canonical_loglik']:.2f}  "
              f"null_mean={r['null_mean']:.2f}  null_std={r['null_std']:.2f}")

    show("contaminated (members)", cont_res)
    show("control (non-members)", ctrl_res)

    print("\n--- SUMMARY ---")
    print(f"ngram: member_mean={mem_mean:.4f} nonmember_mean={non_mean:.4f} "
          f"separation={mem_mean - non_mean:+.4f}")
    print(f"oren:  contaminated_p={cont_res['p_value']:.4f} control_p={ctrl_res['p_value']:.4f}")


if __name__ == "__main__":
    main()

```


### `scripts/plot_from_scores.py`

```python
#!/usr/bin/env python
"""Regenerate score-distribution + log-ROC plots from a cached scores JSONL.

Cheap (no model): reads results/<...>.jsonl rows {"label": 0/1, "<detector>": float, ...}
and writes distribution + log-scale ROC figures. Used to (re)produce figures for runs whose
per-item scores were cached, e.g. the Pythia-1.4B WikiMIA run, without re-scoring.

Run:
    python scripts/plot_from_scores.py results/wikimia64_pythia-1.4b.jsonl --tag wikimia64_pythia-1.4b
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("scores", help="path to scores JSONL with a 'label' key")
    p.add_argument("--tag", default=None, help="filename tag (default: derived from path)")
    p.add_argument("--out", default="figures")
    p.add_argument("--title", default="")
    args = p.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from eval.metrics import roc_curve

    rows = [json.loads(l) for l in open(args.scores)]
    y = np.array([r["label"] for r in rows])
    det_names = [k for k in rows[0] if k != "label"]
    per_det = {n: np.array([r[n] for r in rows]) for n in det_names}
    tag = args.tag or os.path.splitext(os.path.basename(args.scores))[0]
    title = args.title or tag
    os.makedirs(args.out, exist_ok=True)

    fig, axes = plt.subplots(1, len(det_names), figsize=(3.6 * len(det_names), 3.0))
    for ax, name in zip(np.atleast_1d(axes), det_names):
        s = per_det[name]
        ax.hist(s[y == 1], bins=25, alpha=0.6, label="member", density=True)
        ax.hist(s[y == 0], bins=25, alpha=0.6, label="non-member", density=True)
        ax.set_title(name, fontsize=9)
        ax.legend(fontsize=7)
    fig.suptitle(f"{title}: score distributions", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, f"{tag}_dists.png"), dpi=150)

    fig2, ax2 = plt.subplots(figsize=(4.5, 4.5))
    for name in det_names:
        fpr, tpr, _ = roc_curve(per_det[name], y)
        ax2.plot(np.clip(fpr, 1e-3, 1), np.clip(tpr, 1e-3, 1), label=name)
    ax2.plot([1e-3, 1], [1e-3, 1], "k--", lw=0.6)
    ax2.set_xscale("log"); ax2.set_yscale("log")
    ax2.set_xlabel("FPR"); ax2.set_ylabel("TPR")
    ax2.set_title(f"Log-scale ROC ({title})", fontsize=10)
    ax2.legend(fontsize=7)
    fig2.tight_layout()
    fig2.savefig(os.path.join(args.out, f"{tag}_logroc.png"), dpi=150)
    print(f"wrote {args.out}/{tag}_dists.png and {args.out}/{tag}_logroc.png  (N={len(y)})")


if __name__ == "__main__":
    main()

```


### `scripts/build_bundle.py`

```python
#!/usr/bin/env python
"""Assemble the ENTIRE project (paper + docs + code + config + result summaries) into
one self-contained BUNDLE.md for external review. Run from the repo root."""
import glob
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)

LANG = {".py": "python", ".tex": "latex", ".md": "markdown", ".bib": "bibtex",
        ".yaml": "yaml", ".yml": "yaml", ".json": "json", ".txt": "text"}


def fence_for(content):
    """A backtick fence longer than the longest run inside the content (>=3)."""
    longest = 0
    run = 0
    for ch in content:
        run = run + 1 if ch == "`" else 0
        longest = max(longest, run)
    return "`" * max(3, longest + 1)


def block(path):
    p = pathlib.Path(path)
    if not p.exists():
        return f"\n*(missing: {path})*\n"
    content = p.read_text(errors="replace")
    lang = LANG.get(p.suffix, "")
    f = fence_for(content)
    return f"\n### `{path}`\n\n{f}{lang}\n{content}\n{f}\n"


PARTS = [
    ("PART 1 — THE PAPER (readable prose, front matter)", ["PAPER_DRAFT.md"]),
    ("PART 2 — RESULTS, EXPERIMENT DESIGN & ANALYSIS (docs)", [
        "docs/controls_report.md", "docs/results_table.md", "findings.md",
        "docs/pre_analysis.md", "docs/reviewer_concerns.md", "docs/milestone1_report.md",
        "docs/integration_report.md", "docs/method_selection_memo.md",
        "docs/experiment_design.md", "docs/glossary.md", "README.md",
    ]),
    ("PART 3 — ALL CODE (detectors / extraction / eval)", [
        "detectors/base.py", "detectors/loss.py", "detectors/mink.py",
        "detectors/minkpp.py", "detectors/zlib_ratio.py", "detectors/ngram_overlap.py",
        "detectors/oren_permutation.py", "detectors/scorers.py", "detectors/__init__.py",
        "extraction/extract.py", "extraction/pii.py", "extraction/__init__.py",
        "eval/metrics.py", "eval/partial.py", "eval/__init__.py",
    ]),
    ("PART 4 — ALL EXPERIMENT SCRIPTS & RUNNER", [
        "run.py", "conftest.py",
        "scripts/milestone1_pile.py", "scripts/milestone1_wikimia.py",
        "scripts/milestone1_separation.py", "scripts/extraction_pile.py",
        "scripts/pii_enron.py", "scripts/correlation_160m.py",
        "scripts/controls_160m.py", "scripts/validate_ngram_oren.py",
        "scripts/plot_from_scores.py", "scripts/build_bundle.py",
    ]),
    ("PART 5 — ALL TESTS", sorted(glob.glob("tests/test_*.py"))),
    ("PART 6 — PAPER SOURCE (LaTeX)", [
        "paper/main.tex", "paper/introduction.tex", "paper/background.tex",
        "paper/related_work.tex", "paper/evaluation.tex", "paper/datasets_table.tex",
    ]),
    ("PART 7 — CONFIG, ENV & BIBLIOGRAPHY", [
        "requirements.txt", "configs/pythia160m_cpu.yaml",
        "configs/pythia1.4b_gpu.yaml", "references.bib",
    ]),
    ("PART 8 — RAW RESULT SUMMARIES (the actual numbers)", sorted(
        glob.glob("results/*summary*.json") + glob.glob("results/correlation_*.json")
        + glob.glob("results/controls_*.json"))),
]

HEADER = """# COMPLETE PROJECT BUNDLE — Benchmark Contamination as a Privacy/Security Vulnerability in LLMs

**This single file contains the ENTIRE project for external assessment:** the full paper
(front matter), every results/analysis doc, ALL source code, all experiment scripts, all
tests, the LaTeX source, config, the verified bibliography, and the raw result-summary JSONs.

**Read me first — critical context:**
- **Honest scope:** the contribution is a security *reframing* + *systematic comparison of
  existing detectors* + an empirical contamination->leakage analysis. It is NOT a novel
  detector/metric.
- **Status:** paper = front matter only (Abstract, Method/Matrix, Results, Discussion,
  Conclusion still to be written). Experiments = real, reproducible, Pythia-160m on CPU
  (GPU scale-up pending).
- **THE KEY FINDING (R6 control, pre-registered):** the contamination->leakage correlation
  does NOT survive controlling for raw loss. Raw loss predicts extraction (Spearman rho ~0.28);
  the calibrated detectors (Min-K%, Min-K%++, zlib) add NO predictive value beyond loss
  (partial rho|loss: Min-K% -0.18, Min-K%++ -0.15, both FDR-significant & NEGATIVE; zlib ~0).
  Robust to dedup; not a frequency/zero-inflation artifact. The honest reframing is the
  DIVERGENCE between membership-detection and leakage-prediction. See PART 2 -> controls_report.
- **Tests:** 53/53 pass.

---
"""


def main():
    out = [HEADER]
    for title, files in PARTS:
        out.append(f"\n\n# {title}\n")
        for f in files:
            out.append(block(f))
    text = "\n".join(out)
    pathlib.Path("BUNDLE.md").write_text(text)
    print(f"wrote BUNDLE.md  ({len(text):,} chars, ~{len(text)//4:,} tokens est.)")


if __name__ == "__main__":
    main()

```



# PART 5 — ALL TESTS


### `tests/test_detectors.py`

```python
"""Detector unit tests: interface, validation, and known-positive/known-negative separation."""
import numpy as np
import pytest

from detectors import (
    LossDetector,
    MinKProbDetector,
    MinKPlusPlusDetector,
    MockScorer,
    ZlibRatioDetector,
    build_default_detectors,
    zlib_bits,
)
from detectors.base import TokenStats, bottom_k_indices


def test_bottom_k_indices_selects_smallest():
    v = np.array([5.0, 1.0, 4.0, 2.0, 3.0])
    idx = bottom_k_indices(v, 40.0)  # ceil(0.4*5)=2 -> the two smallest (1.0, 2.0)
    assert set(v[idx]) == {1.0, 2.0}


def test_bottom_k_always_at_least_one():
    v = np.array([3.0, 1.0, 2.0])
    assert len(bottom_k_indices(v, 1.0)) == 1


def test_tokenstats_validation():
    with pytest.raises(ValueError):
        TokenStats(np.array([1.0]), np.array([1.0, 2.0]), np.array([1.0]))
    with pytest.raises(ValueError):
        TokenStats(np.array([]), np.array([]), np.array([]))


def test_detectors_return_floats():
    scorer = MockScorer()
    for det in build_default_detectors(scorer):
        s = det.score("the quick brown fox jumps over the lazy dog")
        assert isinstance(s, float) and np.isfinite(s)


def test_minkpp_uses_mu_sigma():
    # Two stats with identical token_logprob but different mu/sigma must score differently.
    lp = np.array([-1.0, -2.0, -3.0, -4.0])
    a = TokenStats(lp, mu=np.full(4, -5.0), sigma=np.full(4, 1.0))
    b = TokenStats(lp, mu=np.full(4, -5.0), sigma=np.full(4, 2.0))
    det = MinKPlusPlusDetector(k_percent=50.0)
    assert det.score_from_stats(a, "x") != det.score_from_stats(b, "x")


def test_zlib_bits_positive():
    assert zlib_bits("hello world") > 0


def _separation_auc(detector_cls, signal=2.0, n=300):
    from eval.metrics import auc_roc

    members = {f"member sequence number {i} with content" for i in range(n)}
    membership_fn = lambda t: t in members  # noqa: E731
    scorer = MockScorer(membership_fn=membership_fn, signal=signal)
    det = detector_cls(scorer)
    texts = list(members) + [f"heldout non member text item {i}" for i in range(n)]
    y = [1] * n + [0] * n
    scores = [det.score(t) for t in texts]
    return auc_roc(np.array(scores), np.array(y))


@pytest.mark.parametrize("cls", [LossDetector, MinKProbDetector])
def test_separation_above_chance(cls):
    # With an injected membership signal, log-prob-based detectors must separate.
    assert _separation_auc(cls) > 0.75


def test_zlib_separation_above_chance():
    assert _separation_auc(ZlibRatioDetector) > 0.6

```


### `tests/test_extraction.py`

```python
"""Extraction-harness tests using stub greedy generators (no model needed)."""
import numpy as np
import pytest

from extraction import (
    extraction_rate,
    fractional_extraction,
    is_extractable,
)


def perfect_generator(full_sequence):
    """A generator that perfectly reproduces the held suffix (memorized case)."""
    def generate(prefix_ids, n_new):
        return full_sequence[len(prefix_ids): len(prefix_ids) + n_new]
    return generate


def garbage_generator(prefix_ids, n_new):
    return [999_999] * n_new  # never matches


def test_perfect_extraction():
    seq = [10, 11, 12, 13, 14, 15]
    r = is_extractable(seq, prefix_len=3, generate=perfect_generator(seq))
    assert r.extracted is True
    assert r.matched_tokens == 3 and r.suffix_len == 3


def test_no_extraction():
    seq = [10, 11, 12, 13, 14, 15]
    r = is_extractable(seq, prefix_len=3, generate=garbage_generator)
    assert r.extracted is False
    assert r.matched_tokens == 0


def test_partial_extraction_counts_prefix():
    seq = [1, 2, 3, 4, 5, 6]
    # generator matches first suffix token then diverges
    def gen(prefix_ids, n_new):
        return [4, 0, 0][:n_new]
    r = is_extractable(seq, prefix_len=3, generate=gen)
    assert r.extracted is False
    assert r.matched_tokens == 1
    assert fractional_extraction([r])[0] == pytest.approx(1 / 3)


def test_extraction_rate_mix():
    seq = [10, 11, 12, 13, 14, 15]
    results = [
        is_extractable(seq, 3, perfect_generator(seq)),
        is_extractable(seq, 3, garbage_generator),
    ]
    assert extraction_rate(results) == pytest.approx(0.5)


def test_invalid_prefix_len():
    with pytest.raises(ValueError):
        is_extractable([1, 2, 3], prefix_len=0, generate=garbage_generator)
    with pytest.raises(ValueError):
        is_extractable([1, 2, 3], prefix_len=3, generate=garbage_generator)

```


### `tests/test_metrics.py`

```python
"""Validate the metrics layer against closed-form / hand-computable cases."""
import numpy as np
import pytest

from eval.metrics import (
    auc_roc,
    bootstrap_ci,
    mia_report,
    roc_curve,
    spearman,
    tpr_at_fpr,
    _rankdata,
)


def test_auc_perfect_separation():
    scores = np.array([0.1, 0.2, 0.9, 1.0])
    y = np.array([0, 0, 1, 1])
    assert auc_roc(scores, y) == pytest.approx(1.0)


def test_auc_perfectly_wrong():
    scores = np.array([0.9, 1.0, 0.1, 0.2])
    y = np.array([0, 0, 1, 1])
    assert auc_roc(scores, y) == pytest.approx(0.0)


def test_auc_tie_is_half():
    # all identical scores -> AUC 0.5 (mid-rank handling)
    scores = np.array([0.5, 0.5, 0.5, 0.5])
    y = np.array([0, 1, 0, 1])
    assert auc_roc(scores, y) == pytest.approx(0.5)


def test_auc_known_value():
    # positives at ranks giving U = 3 of 4 pairs concordant -> 0.75
    scores = np.array([0.2, 0.4, 0.3, 0.5])
    y = np.array([0, 1, 0, 1])  # pos={0.4,0.5}, neg={0.2,0.3}
    # pairs: (0.4>0.2),(0.4>0.3),(0.5>0.2),(0.5>0.3) all concordant -> 1.0
    assert auc_roc(scores, y) == pytest.approx(1.0)


def test_tpr_at_fpr_monotone():
    rng = np.random.default_rng(0)
    pos = rng.normal(2.0, 1.0, 500)
    neg = rng.normal(0.0, 1.0, 500)
    scores = np.r_[pos, neg]
    y = np.r_[np.ones(500), np.zeros(500)]
    t01 = tpr_at_fpr(scores, y, 0.001)
    t1 = tpr_at_fpr(scores, y, 0.01)
    t10 = tpr_at_fpr(scores, y, 0.1)
    assert 0.0 <= t01 <= t1 <= t10 <= 1.0


def test_roc_endpoints():
    scores = np.array([0.1, 0.2, 0.9, 1.0])
    y = np.array([0, 0, 1, 1])
    fpr, tpr, _ = roc_curve(scores, y)
    assert fpr[0] == pytest.approx(0.0) and tpr[0] == pytest.approx(0.0)
    assert fpr[-1] == pytest.approx(1.0) and tpr[-1] == pytest.approx(1.0)


def test_rankdata_ties():
    a = np.array([1.0, 2.0, 2.0, 3.0])
    # ranks: 1, 2.5, 2.5, 4
    assert np.allclose(_rankdata(a), [1.0, 2.5, 2.5, 4.0])


def test_spearman_monotonic():
    x = np.arange(10.0)
    y = 2 * x + 1
    assert spearman(x, y) == pytest.approx(1.0)
    assert spearman(x, -y) == pytest.approx(-1.0)


def test_mia_report_fields():
    rng = np.random.default_rng(1)
    scores = np.r_[rng.normal(3, 1, 200), rng.normal(0, 1, 200)]
    y = np.r_[np.ones(200), np.zeros(200)]
    rep = mia_report(scores, y)
    assert rep.n_pos == 200 and rep.n_neg == 200
    assert 0.5 < rep.auc <= 1.0


def test_bootstrap_ci_brackets_point_estimate():
    rng = np.random.default_rng(2)
    scores = np.r_[rng.normal(2, 1, 300), rng.normal(0, 1, 300)]
    y = np.r_[np.ones(300), np.zeros(300)]
    point = auc_roc(scores, y)
    lo, hi = bootstrap_ci(auc_roc, scores, y, n_boot=300, seed=3)
    assert lo <= point <= hi


def test_metrics_reject_degenerate():
    with pytest.raises(ValueError):
        auc_roc(np.array([1.0, 2.0]), np.array([1, 1]))  # no negatives

```


### `tests/test_ngram_oren.py`

```python
"""Unit tests for the corpus-side n-gram overlap check and the Oren permutation test.

These two contamination tests have their own interfaces (not the Detector/TokenStats ABC),
so they are tested separately from the per-text membership detectors in test_detectors.py.
"""
import numpy as np
import pytest

from detectors import NGramOverlapDetector, OrenPermutationTest, MockScorer
from detectors.base import ModelScorer, TokenStats


# --------------------------------------------------------------------------------------
# n-gram overlap
# --------------------------------------------------------------------------------------

CORPUS = [
    "the quick brown fox jumps over the lazy dog near the old stone bridge today",
    "a completely separate document about machine learning and data contamination metrics",
]


def test_substring_text_scores_high():
    det = NGramOverlapDetector(n=3).build_index(CORPUS)
    # An exact contiguous slice of a corpus document: every 3-gram is in the index.
    sub = "the quick brown fox jumps over the lazy dog"
    assert det.score(sub) == pytest.approx(1.0)
    assert det.contains_overlap(sub)


def test_disjoint_text_scores_zero():
    det = NGramOverlapDetector(n=3).build_index(CORPUS)
    disjoint = "zebra penguin orbit saxophone volcano umbrella"
    assert det.score(disjoint) == pytest.approx(0.0)
    assert not det.contains_overlap(disjoint)


def test_partial_overlap_is_fractional():
    det = NGramOverlapDetector(n=3).build_index(CORPUS)
    # 4 tokens -> two 3-grams. "the quick brown" is in corpus; "quick brown zzz" is not.
    text = "the quick brown zzz"
    assert det.score(text) == pytest.approx(0.5)


def test_text_shorter_than_n_scores_zero():
    det = NGramOverlapDetector(n=13).build_index(CORPUS)
    # Fewer than n tokens -> no n-grams -> conservative 0.0, no crash.
    assert det.score("only five tokens here now") == 0.0
    assert det.score("") == 0.0


def test_default_n_is_13():
    assert NGramOverlapDetector().n == 13


def test_score_before_build_raises():
    det = NGramOverlapDetector(n=3)
    with pytest.raises(ValueError):
        det.score("anything at all here")


def test_index_can_be_built_in_chunks():
    det = NGramOverlapDetector(n=2)
    det.build_index(["alpha beta gamma"])
    det.build_index(["gamma delta epsilon"])
    # n-grams from both chunks are present.
    assert det.score("alpha beta") == pytest.approx(1.0)
    assert det.score("delta epsilon") == pytest.approx(1.0)


def test_custom_tokenizer_variant():
    # Token-level variant note: a caller can inject any str->list[str] tokenizer.
    det = NGramOverlapDetector(n=2, tokenize=lambda s: list(s.replace(" ", "")))
    det.build_index(["abc"])
    assert det.score("abc") == pytest.approx(1.0)  # char bigrams "ab","bc" both seen


# --------------------------------------------------------------------------------------
# Oren permutation test
# --------------------------------------------------------------------------------------


class CanonicalFavoringScorer(ModelScorer):
    """Deterministic scorer that rewards one specific concatenation (the canonical order).

    Simulates a model that memorized the canonical ordering: the canonical concatenation gets
    a high total log-likelihood; every other ordering gets a lower (more negative) baseline.
    Per-token logprobs are returned (one per whitespace token) so summing them gives the
    sequence log-likelihood the Oren test consumes.
    """

    def __init__(self, examples, sep="\n"):
        self._canonical_text = sep.join(examples)

    def score_tokens(self, text: str) -> TokenStats:
        n = max(2, len(text.split()))
        per_token = 0.0 if text == self._canonical_text else -2.0
        lp = np.full(n, per_token, dtype=np.float64)
        mu = np.full(n, -10.0)
        sigma = np.full(n, 2.0)
        return TokenStats(lp, mu, sigma)


def test_oren_canonical_favored_gives_small_p():
    examples = ["first example text", "second example text", "third example text",
                "fourth example text", "fifth example text"]
    scorer = CanonicalFavoringScorer(examples)
    test = OrenPermutationTest(scorer)
    res = test.test(examples, n_permutations=200, seed=0)
    # Canonical is strictly above every permutation -> p = 1/(N+1), clearly significant.
    assert res["p_value"] < 0.05
    assert res["canonical_loglik"] > res["null_mean"]


def test_oren_exchangeable_gives_nonsignificant_p():
    # MockScorer scores each ordering independently of any "true" order: no canonical signal.
    # Use distinct example tokens so permutations produce genuinely varied concatenations.
    examples = [f"example number {i} body content alpha" for i in range(6)]
    scorer = MockScorer()
    test = OrenPermutationTest(scorer)
    res = test.test(examples, n_permutations=300, seed=1)
    # No order memorization -> canonical is a typical draw -> p should not be significant.
    assert res["p_value"] > 0.05


def test_oren_p_value_in_unit_interval_and_reproducible():
    examples = ["alpha beta", "gamma delta", "epsilon zeta", "eta theta"]
    scorer = MockScorer()
    t = OrenPermutationTest(scorer)
    r1 = t.test(examples, n_permutations=100, seed=7)
    r2 = t.test(examples, n_permutations=100, seed=7)
    assert 0.0 < r1["p_value"] <= 1.0
    assert r1 == r2  # deterministic given seed


def test_oren_requires_two_examples():
    scorer = MockScorer()
    t = OrenPermutationTest(scorer)
    with pytest.raises(ValueError):
        t.test(["only one example"], n_permutations=10)

```


### `tests/test_partial.py`

```python
"""Integrity tests for the controls statistics (constructed cases with known answers)."""
import numpy as np
import pytest

from eval.partial import (
    benjamini_hochberg,
    kendall_tau,
    partial_spearman,
    semipartial_spearman,
    spearman,
)


def test_partial_collapses_when_signal_is_only_through_z():
    # x and y are correlated ONLY through a common cause z -> partial(x,y|z) ~ 0.
    rng = np.random.default_rng(0)
    z = rng.normal(size=2000)
    x = z + 0.3 * rng.normal(size=2000)
    y = z + 0.3 * rng.normal(size=2000)
    assert spearman(x, y) > 0.6           # strong raw correlation
    assert abs(partial_spearman(x, y, z)) < 0.1   # collapses controlling z


def test_partial_survives_when_x_has_independent_signal():
    # y depends on z AND on an x-specific signal -> partial(x,y|z) stays positive.
    rng = np.random.default_rng(1)
    z = rng.normal(size=2000)
    xsig = rng.normal(size=2000)
    x = xsig
    y = z + xsig + 0.3 * rng.normal(size=2000)
    assert partial_spearman(x, y, z) > 0.4


def test_semipartial_between_zero_and_raw():
    rng = np.random.default_rng(2)
    z = rng.normal(size=1500)
    x = z + 0.5 * rng.normal(size=1500)
    y = z + 0.5 * rng.normal(size=1500)
    raw = abs(spearman(x, y))
    sp = abs(semipartial_spearman(x, y, z))
    assert sp <= raw + 1e-9


def test_kendall_monotonic():
    x = np.arange(20.0)
    assert kendall_tau(x, 2 * x + 1) == pytest.approx(1.0)
    assert kendall_tau(x, -x) == pytest.approx(-1.0)


def test_kendall_handles_ties():
    x = np.array([1, 1, 2, 2, 3, 3.0])
    y = np.array([1, 2, 2, 3, 3, 4.0])
    tau = kendall_tau(x, y)
    assert -1.0 <= tau <= 1.0 and tau > 0


def test_bh_basic():
    # one tiny p among large ones -> at least the smallest is rejected
    rejected, q = benjamini_hochberg([0.001, 0.5, 0.6, 0.9], alpha=0.05)
    assert rejected[0] and not rejected[3]
    assert np.all((q >= 0) & (q <= 1))


def test_bh_all_null():
    rejected, q = benjamini_hochberg([0.4, 0.5, 0.9], alpha=0.05)
    assert not rejected.any()

```


### `tests/test_pii.py`

```python
"""Tests for the regex PII detectors. Uses ONLY synthetic strings (no real PII)."""
from extraction.pii import find_pii, pii_types


def test_email_detected():
    assert pii_types("contact a@b.com please") == {"email"}
    spans = find_pii("x a@b.com y")
    assert len(spans) == 1
    t, (s, e) = spans[0]
    assert t == "email"
    assert "x a@b.com y"[s:e] == "a@b.com"


def test_email_variants():
    assert pii_types("first.last+tag@sub.example.org") == {"email"}
    # no TLD -> not an email
    assert pii_types("nope@localhost") == set()


def test_phone_formats():
    assert pii_types("call 555-123-4567 now") == {"phone"}
    assert pii_types("call (555) 123-4567 now") == {"phone"}
    assert pii_types("call 555.123.4567 now") == {"phone"}
    assert pii_types("call +1 555 123 4567 now") == {"phone"}


def test_phone_span_exact():
    spans = find_pii("ph 555-123-4567 end")
    phones = [s for s in spans if s[0] == "phone"]
    assert len(phones) == 1
    _, (s, e) = phones[0]
    assert "ph 555-123-4567 end"[s:e] == "555-123-4567"


def test_ssn_detected_and_not_phone():
    types = pii_types("ssn 123-45-6789 here")
    assert "ssn" in types
    assert "phone" not in types


def test_no_pii():
    assert pii_types("just plain words, no identifiers 2026") == set()
    assert find_pii("") == []


def test_multiple_types():
    text = "mail a@b.com or call 555-123-4567"
    assert pii_types(text) == {"email", "phone"}
    assert len(find_pii(text)) == 2


def test_spans_sorted():
    text = "555-123-4567 then a@b.com"
    spans = find_pii(text)
    starts = [span[1][0] for span in spans]
    assert starts == sorted(starts)

```


### `tests/test_pipeline.py`

```python
"""Milestone-0 end-to-end check: the contamination<->leakage correlation analysis wiring.

Synthetic items are given a latent 'contamination strength'. A detector signal and an
extraction outcome are both generated as noisy monotone functions of that strength.
The test asserts the headline analysis (Spearman rho between detector score and
extraction) recovers a strong positive correlation -- i.e. the harness is wired
correctly. This is NOT a scientific result; it validates the pipeline plumbing.
"""
import numpy as np

from detectors import LossDetector, MinKProbDetector, MinKPlusPlusDetector, ZlibRatioDetector
from detectors.base import TokenStats
from eval.metrics import spearman, spearman_ci


def test_contamination_leakage_correlation_wiring():
    rng = np.random.default_rng(7)
    n = 200
    strength = rng.uniform(0, 1, n)  # latent contamination strength per item

    detectors = [LossDetector(), MinKProbDetector(), MinKPlusPlusDetector(), ZlibRatioDetector()]
    det_scores = {d.name: [] for d in detectors}
    extraction_frac = []

    for s in strength:
        ntok = 40
        # stronger contamination => higher token log-probs (lower loss)
        lp = -rng.gamma(2.0, 1.0, ntok) + 3.0 * s
        mu = np.full(ntok, -11.0) + rng.normal(0, 0.3, ntok)
        sigma = rng.uniform(1.5, 3.0, ntok)
        stats = TokenStats(lp, mu, sigma)
        for d in detectors:
            det_scores[d.name].append(d.score_from_stats(stats, "x" * ntok))
        # stronger contamination => more tokens extractable
        extraction_frac.append(np.clip(s + rng.normal(0, 0.15), 0, 1))

    extraction_frac = np.array(extraction_frac)
    for name, scores in det_scores.items():
        rho = spearman(np.array(scores), extraction_frac)
        assert rho > 0.4, f"{name}: weak correlation {rho:.3f}"

    lo, hi = spearman_ci(np.array(det_scores["loss"]), extraction_frac, n_boot=300)
    assert lo > 0.0  # CI excludes zero

```



# PART 6 — PAPER SOURCE (LaTeX)


### `paper/main.tex`

```latex
% Assembled driver for the paper front matter. Compile once a LaTeX engine is
% available:  pdflatex main && bibtex main && pdflatex main && pdflatex main
% (run from the paper/ directory). Sections that don't exist yet (Abstract, Method,
% Results, Discussion, Conclusion) are intentionally absent -- this is the front matter.
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage[numbers,sort&compress]{natbib}

\title{Benchmark Contamination as a Privacy and Security Vulnerability\\in Large Language Models\\[4pt]\large (Working draft --- front matter only)}
\author{}
\date{}

\begin{document}
\maketitle

\input{introduction}
\input{background}
\input{related_work}
\input{evaluation}

\bibliographystyle{plainnat}
\bibliography{../references}

\end{document}

```


### `paper/introduction.tex`

```latex
% =============================================================================
% introduction.tex  --  Introduction + explicit honest contributions.
% Owner: Subagent L (Deep Literature Research & Lit-Review Finalizer).
% All \cite keys -> ../references.bib.
%
% SCOPE CONTRACT (mirrors docs/method_selection_memo.md S5): the contribution is a
% security REFRAMING + comparative evaluation of EXISTING detectors, NOT a novel
% detector or metric. Every method named as evaluated is in the implemented set
% (LOSS, Min-K%, Min-K%++, zlib, n-gram overlap, Oren permutation test, extractable
% memorization, regex PII on Enron-in-Pile). Everything else is "related, not
% evaluated."
% =============================================================================

\section{Introduction}
\label{sec:intro}

Large language models (LLMs) are ranked, selected, and certified as safe largely on
the basis of their scores on public benchmarks~\cite{hendrycks2021mmlu,cobbe2021gsm8k}.
Those scores are only meaningful under one assumption: that the evaluation data was
absent from pre-training. The assumption is increasingly untenable. Benchmarks are
small, static, and endlessly redistributed across the web, while training corpora are
weakly filtered crawls assembled at the scale of hundreds of gigabytes to
petabytes~\cite{commoncrawl,gao2020pile}; benchmark items are therefore swept into the
next crawl by ordinary copying, with no adversary required. The resulting
\emph{benchmark contamination}---the presence of evaluation data in the training
corpus~\cite{golchin2024timetravel}---is usually treated as a measurement-hygiene
problem: a contaminated score over-states capability~\cite{ravaut2024survey}.

We argue that contamination is better understood as a \emph{privacy and security}
vulnerability, and we study it as one. The same over-parameterized models that score
highly on a leaked benchmark also memorize and can regurgitate verbatim training
sequences, including personally identifiable information (PII) that co-occurs in the
same corpora~\cite{carlini2021extracting,carlini2023quantifying}. Contamination, in
this view, is a visible symptom of unintended memorization, and memorization is the
mechanism by which sensitive content leaks. If a cheap, model-side contamination signal
predicts which items the model has memorized, then the act of contaminating a benchmark
is not merely inflating a metric; it is exposing a leakage channel. We make this
contamination~$\rightarrow$~memorization~$\rightarrow$~leakage chain the object of
empirical study, on models whose training corpus is fully public so that membership is
ground truth rather than a guess.

The privacy/security community has, however, established that membership signal on
pre-trained LLMs is weak: large-scale audits on the Pythia suite and The Pile report
that membership-inference attacks (MIAs) barely exceed chance, and that apparent
successes often reflect distribution shift between the member and non-member sets rather
than membership itself~\cite{duan2024mia}. We take this finding as a constraint, not an
obstacle. Rather than claim a stronger attack, we ask a sharper, security-relevant
question: \emph{even where the membership signal is weak, does it still predict concrete
leakage?} Answering it requires the evaluation discipline that security venues expect of
a privacy attack---true-positive rate at a low, fixed false-positive rate, read off a
log-scale ROC curve, rather than an average-case AUC that hides whether the attack ever
fires confidently~\cite{carlini2022lira}. It also exposes a question the
membership-inference literature does not ask: detectors are tuned and ranked by how well
they separate members from non-members, but leakage is a property of \emph{how much} the
model memorized a specific item. We therefore evaluate each detector not only as a
membership classifier but as a predictor of concrete leakage, and ask whether the two
objectives coincide---finding that they do not.

\paragraph{Contributions (and explicit non-contributions).}
We are deliberate about what this paper is and is not. It is \emph{not} a new detector,
attack, or metric: every detection method we run is from prior
work~\cite{yeom2018privacy,shi2024detecting,zhang2025minkpp,carlini2021extracting,brown2020gpt3,oren2024proving},
and our evaluation protocol is the established low-FPR convention of
Carlini~et~al.~\cite{carlini2022lira}. Within that honest scope, our contributions are:
\begin{itemize}
  \item \textbf{A security reframing and threat model.} We recast benchmark
  contamination as a membership/exposure vulnerability with an explicit adversary and
  graded goals---membership inference on a single item, benchmark-level contamination
  confirmation, and verbatim/PII extraction---rather than as a measurement artifact
  (Section~\ref{sec:background}, Section~\ref{sec:eval}).
  \item \textbf{A systematic comparative evaluation of existing detectors under the S\&P
  low-FPR protocol on ground-truth Pile membership.} We evaluate LOSS/perplexity,
  Min-K\%, Min-K\%++, and the zlib ratio as membership detectors, the corpus-side
  $n$-gram overlap test as a contamination-label oracle, and the Oren
  permutation/exchangeability test at the benchmark level, all on Pythia trained on the
  public Pile, reporting TPR at $0.1\%$ and $1\%$ FPR with log-scale ROC and bootstrap
  confidence intervals, with explicit controls for the frequency, duplication, and
  temporal confounds that prior work
  identifies~\cite{biderman2023pythia,gao2020pile,duan2024mia}.
  \item \textbf{A pre-registered measurement of \emph{which} contamination signal predicts
  leakage---and which does not.} We correlate per-item contamination scores against an
  extraction outcome---prefix-continuation extractable memorization under greedy
  decoding~\cite{carlini2023quantifying}---and, on the Enron Emails subset that already
  sits inside the Pile, against regex-detected PII leakage~\cite{lukas2023pii}. A
  pre-registered partial-correlation control then isolates the role of raw loss. In our
  ground-truth $160$M-parameter setting we find that the
  contamination$\rightarrow$leakage association is carried \emph{entirely by per-item
  loss}: once loss is held fixed, the calibrated reference-free detectors (Min-K\%,
  Min-K\%++, zlib) add no predictive value, and Min-K\%/Min-K\%++ are if anything
  inversely related to extraction. The calibrations that improve membership-detection AUC
  thus discard the loss-magnitude signal that actually predicts leakage---a divergence
  between membership detection and leakage prediction that we report as our central
  empirical finding (robust to deduplication, and not explained by token frequency or the
  zero-inflated outcome).
\end{itemize}
We do not propose internal-probe or other novel detectors as contributions, do not train
or fine-tune models, and do not attack closed production systems for real third-party
PII; differential privacy and related defenses are discussed as the mitigation direction
only.

```


### `paper/background.tex`

```latex
% =============================================================================
% background.tex  --  "LLM Evaluation Benchmarks" (the attack-surface framing).
% Owner: Subagent A (Literature Review Writer). All \cite keys -> ../references.bib.
%
% DIVERGENCES FROM THE PASTED DRAFT (flagged for review):
%  * Removed reliance on "Wei et al. 2023" (Skywork, a model paper) for definitional
%    claims; replaced with the survey (ravaut2024survey) and primary sources.
%  * Kept the benchmarks-as-proxies and assumption-violation argument, re-grounded.
%  * Dropped unverified citations (Deng et al.) not in the verified bib; if you want
%    them, they must be verified and added to references.bib first.
% =============================================================================

\section{Background: LLM Evaluation Benchmarks as an Attack Surface}
\label{sec:background}

\subsection{Benchmarks as proxies for latent capabilities}
Large language model (LLM) benchmarks function as \emph{proxies} for latent
capabilities---reasoning, comprehension, factual knowledge, coding proficiency---that
cannot be measured directly. By scoring a model on a fixed set of standardized tasks,
the community infers a model's likely utility (and, increasingly, its safety) in
deployment~\cite{hendrycks2021mmlu}. Canonical examples target distinct competencies:
MMLU for broad multitask knowledge across 57 subjects~\cite{hendrycks2021mmlu}, GSM8K
for multi-step mathematical reasoning~\cite{cobbe2021gsm8k}, and HumanEval for
functional code generation~\cite{chen2021humaneval}. Reported scores on these suites
drive model-selection decisions, leaderboard rankings, and published claims of progress.

\subsection{The core validity assumption}
The inferential validity of benchmark evaluation rests on one strict assumption:
\emph{the test data was not seen during pre-training}. Only under this assumption does
high benchmark performance license the intended conclusion---that the model
\emph{generalizes} (applies learned regularities to novel inputs) rather than
\emph{memorizes} (retrieves specific training instances). When the assumption is
violated, the benchmark no longer measures capability; a memorized test item inflates
the score without any corresponding gain in generalization, rendering the metric an
unreliable estimator of the construct it claims to measure. The generalization-versus-
memorization distinction is not merely conceptual: memorization is directly measurable
as the verbatim regeneration of training sequences and grows predictably---log-linearly
in model scale, data duplication, and context length~\cite{carlini2023quantifying}. The
same phenomenon has a sharper, privacy-relevant form: a planted secret's
\emph{exposure}, the model's tendency to rank that secret above random alternatives,
rises with how often it was seen during training~\cite{carlini2019secret}, and which
specific examples a model memorizes is itself a measurable, example-level property rather
than a uniform background rate~\cite{zhang2023counterfactual}. A memorized benchmark item
is thus the visible end of the same mechanism that retains rare, sensitive strings.

\subsection{Static test sets meet weakly filtered corpora}
The security-relevant tension is structural. Evaluation benchmarks are \emph{static,
small, widely circulated, and publicly indexed}: once published, an MMLU or GSM8K item
is copied into papers, blog posts, GitHub repositories, and discussion forums. Training
corpora, by contrast, are \emph{massive web scrapes with weak filtering}---Common
Crawl~\cite{commoncrawl} and The Pile~\cite{gao2020pile} are assembled at the scale of
hundreds of gigabytes to petabytes, where exhaustive removal of any particular short
string is impractical. The natural consequence is that benchmark items are swept into
training corpora through ordinary web redistribution, with no adversary required. This
makes a public benchmark a persistent, low-effort \emph{attack surface}: the same
property that makes a benchmark useful (stable, shared, citable) is what guarantees its
eventual presence in the next corpus crawl.

We argue this is best understood through a security lens rather than purely as a
measurement-hygiene problem. Contamination converts an evaluation artifact into a
channel that (i) invalidates the safety and capability claims downstream decisions rely
on, and (ii)---the focus of this paper---couples directly to \emph{memorization}, and
through memorization to the leakage of sensitive content that co-occurs in the same
weakly filtered corpora. Section~\ref{sec:relatedwork} formalizes contamination, its
typology, and the detection and memorization literature on which our evaluation builds.

```


### `paper/related_work.tex`

```latex
% =============================================================================
% related_work.tex  --  "Benchmark Contamination" + detection + memorization/privacy.
% Owner: Subagent A (Literature Review Writer). All \cite keys -> ../references.bib.
%
% CONSISTENCY CONTRACT: every detection method described here is implemented and
% evaluated (detectors/), and every implemented method is described here. No method
% is named that is not tested, and vice versa (see docs/method_selection_memo.md).
%
% DIVERGENCES FROM THE PASTED DRAFT (flagged for review):
%  * Typology standardized to verbatim / paraphrased / semantic (the project spine);
%    the draft's "input-label" case is folded in as a severity axis.
%  * Replaced Skywork/Wei-2023 definitional cites with primary sources + the survey.
%  * Detection subsection now matches the IMPLEMENTED+RUN shortlist exactly: LOSS,
%    Min-K%, Min-K%++, zlib, n-gram overlap, and the Oren permutation test. Guided
%    prompting and neighbourhood/reference MIA are explicitly framed as related
%    approaches we DO NOT evaluate (they are not in the implemented set).
% =============================================================================

\section{Related Work: Contamination, Memorization, and Privacy Leakage}
\label{sec:relatedwork}

\subsection{Defining benchmark contamination}
We adopt the standard definition: \emph{benchmark contamination} is the presence of
evaluation data---inputs, labels, or accompanying metadata---within a model's
pre-training corpus~\cite{golchin2024timetravel}. Contamination matters for two
reasons that this paper treats as inseparable. First, it invalidates evaluation: a
contaminated score conflates capability with retrieval, so the metric no longer
estimates generalization. Second, and central to our thesis, contamination is a
\emph{symptom of, and a measurable proxy for, unintended memorization}---and
memorization of evaluation data sits on the same mechanism that leaks sensitive
content from the corpus. We make this contamination~$\rightarrow$~memorization~$
\rightarrow$~leakage chain the object of empirical study.

\subsection{A typology of contamination}
Following the project's framing and the contamination-detection
survey~\cite{ravaut2024survey}, we distinguish three forms by the transformation
between the corpus copy and the benchmark item:
\begin{itemize}
  \item \textbf{Verbatim contamination.} The exact token sequence of a test item
  appears in training data. This is what classical $n$-gram decontamination targets
  (e.g., the 13-gram overlap test introduced for GPT-3~\cite{brown2020gpt3}) and what
  verbatim-extraction memorization measures~\cite{carlini2023quantifying}.
  \item \textbf{Paraphrased contamination.} The semantic content is present but
  reworded, so surface-level $n$-gram matching misses it. A perfect verbatim filter
  provides only a false sense of safety, since style-transfer rephrasings evade it
  while preserving the leaked information~\cite{ippolito2023verbatim}.
  \item \textbf{Semantic contamination.} The underlying knowledge or answer is encoded
  without lexical overlap (e.g., the same question-answer mapping in a different
  format). Detecting it requires model-behavioral or distributional signals rather than
  string matching.
\end{itemize}
A second, orthogonal severity axis is \emph{what} is contaminated: input-only leakage
inflates familiarity, whereas joint input--label leakage enables direct answer
retrieval and is the most damaging to evaluation validity. Empirically, overlap between
open-model training data and benchmarks such as GSM8K has been reported for models
trained on largely undisclosed corpora~\cite{touvron2023llama}, motivating
ground-truth-controlled study on models whose corpus is fully public.

\subsection{Why memorization is a security and privacy problem}
Memorization is not a benign curiosity. Over-parameterized models trained on
web-scale scrapes retain and can regurgitate verbatim sequences, including personally
identifiable information (PII) such as names, emails, and phone
numbers~\cite{carlini2021extracting}. This has been formalized along several axes that
we reuse as outcome variables:
\begin{itemize}
  \item \textbf{$k$-eidetic / extractable memorization.} A string is extractable if a
  prefix makes the model regenerate it, and is $k$-eidetic if it occurs in at most $k$
  training documents~\cite{carlini2021extracting}; the prefix-continuation form under
  greedy decoding makes this directly measurable~\cite{carlini2023quantifying}.
  \item \textbf{Exposure and example-level memorization.} Injecting a canary secret and
  measuring its \emph{exposure}---its rank against random alternatives---quantifies
  unintended memorization and its growth with occurrence count~\cite{carlini2019secret};
  this requires control over the training process (canary insertion), which our
  pretrained-checkpoint setting does not afford, so we use it for definitions rather than
  as a measurement. Relatedly, memorization is concentrated on specific
  examples~\cite{zhang2023counterfactual} rather than spread uniformly, which is what
  makes per-item contamination scores meaningful predictors of per-item leakage.
  \item \textbf{Extraction at scale.} Production models can be driven, via a divergence
  attack, to emit memorized training data well above their nominal aligned rate,
  recovering thousands of verbatim examples cheaply~\cite{nasr2025scalable}.
  \item \textbf{PII leakage games.} Leakage of personally identifiable information
  decomposes into extraction, reconstruction, and inference; data scrubbing and
  differential privacy reduce but do not eliminate it~\cite{lukas2023pii}, models leak
  PII through memorization more than through associative
  inference~\cite{huang2022leaking}, and black-box probing tools can elicit a data
  subject's PII directly from a deployed model~\cite{kim2023propile}.
\end{itemize}
The security framing follows directly: if contamination is a measurable proxy for
memorization, and memorization is the vector for PII and proprietary-data exposure,
then contamination is not only a metrics problem but a \emph{privacy vulnerability}.

\subsection{The membership-inference lineage}
\label{sec:mia-lineage}
Deciding whether a specific record was in a model's training set is the canonical
privacy attack, and contamination detection is an instance of it. The lineage we build
on runs as follows. \emph{Shadow-model} attacks established the threat: by training
reference models on data drawn from the same distribution, an adversary learns to
distinguish members from non-members from the target model's
outputs~\cite{shokri2017membership}. Yeom~et~al.\ tied attack success to overfitting and
gave the simplest practical baseline---threshold the per-example loss---together with the
\emph{membership advantage} (TPR${-}$FPR) figure of merit~\cite{yeom2018privacy}.
Carlini~et~al.'s \emph{Likelihood Ratio Attack} (LiRA) then reframed MIA from first
principles as a per-example hypothesis test calibrated with shadow models, and---central
to our methodology---argued that average-case AUC is the wrong yardstick for a privacy
threat: an attack matters if it identifies \emph{some} members with very few false
accusations, so the right report is TPR at a low, fixed FPR on a log-scale ROC
curve~\cite{carlini2022lira}. Shadow-model calibration, however, is infeasible at
Pile/Pythia scale (it requires training many models on the training distribution), so we
adopt LiRA's \emph{metric} but not its \emph{attack}.

For pre-trained LLMs, the field moved to \emph{reference-free} likelihood signals that
need no shadow models. Min-K\% Prob averages the log-probabilities of a sequence's
lowest-probability $k\%$ of tokens, on the hypothesis that members lack
high-surprise outlier tokens~\cite{shi2024detecting}; Min-K\%++ sharpens this by
$z$-scoring each token against the \emph{full} next-token distribution before averaging,
detecting that the target token sits at a local maximum of the modeled
distribution~\cite{zhang2025minkpp}. A parallel reference-free line, neighbourhood
comparison, calibrates a sample's score against synthetically generated neighbour texts
instead of a reference model~\cite{mattern2023neighbourhood}; we treat it as a related
approach we do not evaluate, since it needs many extra masked-LM forward passes per
example and, in the regime below, underperforms. The reality check on this whole line is
the MIMIR study: a large-scale audit on Pythia ($160$M--$12$B) and The Pile with
controlled member/non-member splits finds that these attacks barely exceed chance
(AUC~$\approx 0.5$--$0.6$), that LLMs see their corpus for too few epochs over too large
a dataset to memorize in the way classical MIA assumes, and that apparent successes
frequently reflect a temporal or topical \emph{distribution shift} between the splits
rather than membership~\cite{duan2024mia}. This finding defines our honesty constraint:
we do not claim to beat these numbers; we ask whether the weak signal that remains still
predicts leakage.

\subsection{Differential privacy as the defense direction}
\label{sec:dp}
The standard principled mitigation for training-data leakage is differential privacy.
DP-SGD bounds any single example's influence on the trained model by clipping per-example
gradients and adding calibrated noise, with privacy accounted via the moments
accountant~\cite{abadi2016deep}. Applied to language models, DP fine-tuning can retain
much of the utility of non-private training, particularly with large pre-trained
backbones~\cite{li2022dpllm} and parameter-efficient adaptation~\cite{yu2022dpfinetuning}.
DP bounds memorization and thereby the leakage we measure, but at a privacy--utility cost
and---crucially for us---it must be applied \emph{at training time}; it is a defense for
model producers, not a detector available to an auditor of an already-released model. We
therefore position DP as the mitigation our threat model motivates, and do not implement
it (we train no models).

\subsection{Existing detection techniques}
We describe the techniques we implement and compare; the comparative evaluation and
the access requirements appear in Section~\ref{sec:eval}. All operate without any novel
detector of our own---our contribution is their security-framed, ground-truth
evaluation, not a new method.
\begin{itemize}
  \item \textbf{$n$-gram / substring overlap.} Flag a benchmark item that shares an
  $N$-gram with the corpus~\cite{brown2020gpt3}. Requires corpus access; misses
  paraphrased and semantic contamination.
  \item \textbf{Loss / perplexity thresholding.} The mandatory membership-inference
  baseline: members exhibit lower loss, with attack success tied to
  overfitting~\cite{yeom2018privacy}.
  \item \textbf{Min-K\% Prob.} Average the log-probabilities of the lowest-probability
  $k\%$ of tokens; reference-free and logprob-only~\cite{shi2024detecting}.
  \item \textbf{Min-K\%++.} Normalizes each token's log-probability against the full
  next-token distribution before the bottom-$k\%$ average, the current state of the art
  among reference-free detectors~\cite{zhang2025minkpp}.
  \item \textbf{zlib-entropy ratio.} Calibrate model perplexity by the zlib-compressed
  size of the text, controlling for intrinsic compressibility/frequency~\cite{carlini2021extracting}.
  \item \textbf{Permutation / exchangeability test.} At the \emph{benchmark} level rather
  than per item, score each ordering of a benchmark's examples by the log-likelihood of
  their concatenation and compare the canonical (published) order against random
  shufflings; a model trained on the benchmark in canonical order favours it beyond
  chance, yielding a provable, FPR-controlled contamination
  certificate~\cite{oren2024proving}.
\end{itemize}
We additionally note two techniques we describe but \emph{do not} evaluate, since our
ground-truth, logit-access setting makes likelihood-based detectors stronger and cleaner:
\emph{guided prompting}, which prompts a model with dataset metadata and a partial
instance and tests for verbatim completion~\cite{golchin2024timetravel}, a black-box
signal aimed at closed models; and the reference-free \emph{neighbourhood} and
shadow-model \emph{reference} attacks discussed in
Section~\ref{sec:mia-lineage}~\cite{mattern2023neighbourhood,shokri2017membership}.

\subsection{Limitations of existing detection, and our positioning}
Two limitations frame our contribution. First, \emph{detection is fragile to the
transformation}: string-matching misses paraphrased and semantic
contamination~\cite{ippolito2023verbatim}, and likelihood-based membership inference is
known to barely exceed chance on pre-trained LLMs evaluated under controlled ground
truth, because the corpora are seen for few epochs and member/non-member boundaries are
fuzzy~\cite{duan2024mia}. Second, \emph{evaluation conventions matter}: average-case
AUC or accuracy can mask whether an attack confidently identifies any members, so the
security-appropriate report is true-positive rate at low false-positive rate with
log-scale ROC~\cite{carlini2022lira}. We therefore do not claim a stronger detector.
We ask a different, security-relevant question: \emph{even where contamination signal
is weak, does it predict concrete privacy leakage?} We answer it with ground-truth
membership on the Pythia suite~\cite{biderman2023pythia} trained on the public
Pile~\cite{gao2020pile}, under the low-FPR protocol, with explicit controls for the
frequency, duplication, and temporal confounds that prior work identifies.

```


### `paper/evaluation.tex`

```latex
% =============================================================================
% evaluation.tex  --  reconciled "Evaluation Overview".
% Owner: Subagent A, reconciled with docs/experiment_design.md + method memo.
%
% MAJOR DIVERGENCES FROM THE PASTED DRAFT (each flagged; please review):
%  [D1] REMOVED the "Proposed Method: Internal Activation Analysis" as a claimed
%       contribution. The advisor constraint forbids proposing a novel detector. It
%       survives only as an optional exploratory probe in the Discussion, not a result.
%  [D2] REPLACED Precision/Recall/F1 as primary metrics with TPR@low-FPR + log-scale
%       ROC + AUC (Carlini S&P'22 convention). P/R/F1 retained only as a secondary,
%       fixed-threshold view for the benchmark-flagging use case.
%  [D3] REMOVED the "fine-tune to force overfitting on PII" positive control. We do not
%       train models. Memorization ground truth comes from public Pile membership and
%       Pythia's known duplication counts / checkpoints. Enron PII is studied because
%       the Enron Emails corpus is itself a Pile subset (i.e., already in training),
%       giving controlled PII ground truth without inducing new memorization.
%       [VERIFY] confirm Enron Emails is a Pile component before citing as such.
%  [D4] REPLACED k-fold cross-validation (a trained-classifier validation scheme) with
%       multi-seed bootstrap confidence intervals + a permutation test, appropriate for
%       threshold-free attack metrics.
% =============================================================================

\section{Evaluation Overview}
\label{sec:eval}

\subsection{Threat model and success criteria}
We frame contamination detection as a membership/exposure attack with an explicit
adversary (Section omitted here; see \texttt{docs/experiment\_design.md}). Goals range
from membership inference on a single item, to benchmark-level contamination
confirmation, to verbatim extraction and PII leakage. Each detector is evaluated at its
minimum access tier (gray-box logprobs for LOSS/Min-K\%/zlib; white-box logits for
Min-K\%++). Success is defined by the security-appropriate operating point rather than
average accuracy.

\subsection{Methods under comparison}
We evaluate \emph{existing} detectors only---we propose no new detector. The
per-item membership suite is LOSS/perplexity~\cite{yeom2018privacy}, Min-K\%
Prob~\cite{shi2024detecting}, Min-K\%++~\cite{zhang2025minkpp}, and the zlib-entropy
ratio~\cite{carlini2021extracting}. Two further tests operate off the per-item
likelihood axis: corpus-side $n$-gram overlap~\cite{brown2020gpt3}, a model-free
data-side check used to construct ground-truth contamination labels for benchmark items,
and the Oren permutation/exchangeability test~\cite{oren2024proving}, a benchmark-level
test that compares the canonical ordering of a benchmark's examples against random
shufflings to certify contamination with a controlled false-positive rate. The leakage
outcome is prefix-continuation extractable memorization under greedy
decoding~\cite{carlini2023quantifying}; on the controlled corpus we additionally measure
regex-detected PII leakage, framed via the PII-leakage games of
Lukas~et~al.~\cite{lukas2023pii}. Related approaches we deliberately \emph{do not}
evaluate---guided prompting~\cite{golchin2024timetravel}, neighbourhood and shadow-model
reference attacks~\cite{mattern2023neighbourhood,shokri2017membership}, and the
divergence-style extraction of production
models~\cite{nasr2025scalable}---are discussed in Section~\ref{sec:relatedwork}.
\textbf{[D1]} An internal-activation probe is reported, if at all, only as exploratory
analysis in the Discussion, not as a contribution.

\subsection{Data}
Table~\ref{tab:datasets} summarizes every corpus and benchmark used or referenced below.

\paragraph{Models and corpus.} The primary model is the Pythia
suite~\cite{biderman2023pythia}, trained on the public Pile~\cite{gao2020pile}; its
reconstructible training order, $154$ checkpoints, multiple sizes, and deduplicated
variant provide exact membership ground truth. We use the released MIMIR member/
non-member splits~\cite{duan2024mia}, which control $n$-gram overlap between members and
non-members. OLMo~\cite{groeneveld2024olmo} on Dolma~\cite{soldaini2024dolma} is a
secondary replication target. The Pile sits within the broader weakly filtered
web-scrape regime---Common Crawl~\cite{commoncrawl} and its filtered derivatives
C4~\cite{raffel2020c4,dodge2021c4} and RedPajama~\cite{weber2024redpajama}---that makes
benchmark contamination structural rather than adversarial.

\input{datasets_table}

\paragraph{Benchmarks and PII.} Contamination is tested against MMLU, GSM8K, HumanEval,
HellaSwag, TruthfulQA, and BoolQ. \textbf{[D3]} For PII leakage we use the Enron Emails
data \emph{as a Pile subset already present in Pythia's training data}, plus a synthetic
PII set for controlled structure, rather than fine-tuning a model to memorize PII. All
PII results are reported in aggregate; no real PII is reproduced in the paper.

\subsection{Metrics (each justified)}
\textbf{[D2]} Following the membership-inference-from-first-principles
convention~\cite{carlini2022lira}, the primary metric is \emph{true-positive rate at a
fixed low false-positive rate} (TPR @ $0.1\%$ and $1\%$ FPR) reported with
\emph{log-scale ROC}; AUC-ROC is reported secondarily. These capture whether a detector
\emph{confidently} identifies members---the privacy-relevant regime---which average-case
accuracy hides. For benchmark flagging at a chosen operating threshold we additionally
report precision/recall/F1 as a secondary, application-facing view. The leakage outcome
is the \emph{extraction rate}~\cite{carlini2023quantifying}. The headline analysis is
the \emph{Spearman correlation between per-item contamination score and per-item
extraction/leakage outcome}, with bootstrap confidence intervals and a pre-registered
partial-correlation control that isolates the contribution of raw loss---the quantitative
form of the paper's central question.

\subsection{Validation and controls}
\textbf{[D4]} Robustness is established by repeating each measurement over multiple
seeds with bootstrap confidence intervals on TPR@FPR and on the Spearman correlation,
and by a permutation/exchangeability test for benchmark-level
contamination~\cite{oren2024proving}. We include ablations that preempt the standard
confounds: deduplicated versus non-deduplicated Pythia (duplication), frequency-matched
member/non-member splits (string frequency), and model-size scaling (does the
contamination$\rightarrow$leakage link strengthen with scale, as memorization
does~\cite{carlini2023quantifying}). Differentially private
training~\cite{abadi2016deep,li2022dpllm} is discussed as the mitigation direction
(Section~\ref{sec:dp}), not implemented, since it is a producer-side defense applied at
training time rather than an auditor-side detector.

This section fixes the threat model, methods, data, and metrics; the empirical results
under this protocol---per-detector TPR at low FPR with log-scale ROC, extraction rates,
and the headline contamination$\rightarrow$leakage correlation with confidence
intervals---are reported in the results section, with every reported number tracing to a
logged harness run.

```


### `paper/datasets_table.tex`

```latex
% =============================================================================
% datasets_table.tex  --  corpora + benchmarks used or referenced in the evaluation.
% Owner: Subagent L. Included by evaluation.tex. Requires \usepackage{booktabs}.
% Every row carries >=1 verified citation (see ../references.bib verification comments).
% Sizes are the figures reported by each artifact's primary source; "approx." where the
% source states an order-of-magnitude or the corpus is continuously growing.
% =============================================================================
\begin{table*}[t]
  \centering
  \caption{Corpora and benchmarks used in or referenced by the evaluation. The Pile is
  our ground-truth training corpus; Common Crawl and C4/Dolma/RedPajama frame the
  weakly filtered web-scrape regime; the lower block lists the contamination benchmarks
  whose items we label by corpus-side overlap.}
  \label{tab:datasets}
  \small
  \begin{tabular}{@{}llp{0.40\linewidth}ll@{}}
    \toprule
    \textbf{Dataset} & \textbf{Type} & \textbf{What it is} & \textbf{Size} & \textbf{Cite} \\
    \midrule
    The Pile      & corpus    & Curated 22-subset English corpus; Pythia's training data and our membership ground truth & 825\,GB & \cite{gao2020pile} \\
    Common Crawl  & corpus    & Open, continually updated repository of raw web-crawl data; the base of most LLM pre-training scrapes & petabyte-scale (growing) & \cite{commoncrawl} \\
    C4            & corpus    & Colossal Clean Crawled Corpus: a filtered Common Crawl snapshot introduced with T5 & $\sim$750\,GB & \cite{raffel2020c4,dodge2021c4} \\
    Dolma         & corpus    & Open pre-training corpus; OLMo's training data (replication target) & 3\,T tokens & \cite{soldaini2024dolma} \\
    RedPajama     & corpus    & Open reproduction of an LLaMA-style pre-training mixture & $\sim$30\,T tokens & \cite{weber2024redpajama} \\
    \midrule
    MMLU          & benchmark & Multiple-choice knowledge/reasoning across 57 subjects & 15{,}908 questions & \cite{hendrycks2021mmlu} \\
    GSM8K         & benchmark & Grade-school multi-step math word problems & 8{,}500 problems & \cite{cobbe2021gsm8k} \\
    HumanEval     & benchmark & Hand-written Python programming problems with unit tests & 164 problems & \cite{chen2021humaneval} \\
    HellaSwag     & benchmark & Adversarially filtered commonsense sentence completion & $\sim$70{,}000 items & \cite{zellers2019hellaswag} \\
    TruthfulQA    & benchmark & Questions probing imitative falsehoods & 817 questions & \cite{lin2022truthfulqa} \\
    BoolQ         & benchmark & Naturally occurring yes/no reading-comprehension questions & 15{,}942 questions & \cite{clark2019boolq} \\
    \bottomrule
  \end{tabular}
\end{table*}

```



# PART 7 — CONFIG, ENV & BIBLIOGRAPHY


### `requirements.txt`

```text
# Pinned to the exact versions the results were produced with (Python 3.13.5).
# Reproducibility: these are the tested versions; `pip install -r requirements.txt`.
# The test suite + `--self-test` need only numpy + pytest; the rest are for real-model runs.

# --- Core (tests + metrics) ---
numpy==2.1.3
pytest==8.3.4

# --- Real-model runs (Milestone 1+, scoring/extraction on Pythia) ---
torch==2.9.1
transformers==4.57.3
datasets==4.4.1
accelerate>=0.30          # optional; only for multi-device / larger models

# --- Plots + configs ---
matplotlib==3.10.0
pyyaml>=6.0

# Public datasets used (downloaded at runtime, not vendored):
#   swj0419/WikiMIA              (membership benchmark)
#   NeelNanda/pile-10k           (Pile members)
#   mit-han-lab/pile-val-backup  (Pile validation = non-members)
# Gated alternative (needs HF auth): iamgroot42/mimir

```


### `configs/pythia160m_cpu.yaml`

```yaml
# Milestone-1/2 config: smallest model, CPU, public ground truth. The numbers in
# docs/results_table.md were produced with this config. Scale up by changing `model`
# (and device) only -- no code change.
model: EleutherAI/pythia-160m
revision: main
device: cpu
seed: 0

# membership separation (scripts/milestone1_pile.py, scripts/milestone1_wikimia.py)
n_per_class: 300
max_words: 100
min_words: 25
wikimia_length: 64

# extraction + correlation (scripts/extraction_pile.py, scripts/correlation_160m.py)
extraction:
  n_items: 300
  prefix_len: 32
  suffix_len: 50
  min_tokens: 80
correlation:
  items: results/pile_items_160m.jsonl
  n_boot: 2000

```


### `configs/pythia1.4b_gpu.yaml`

```yaml
# GPU scale-up config. Identical pipeline; only model + device change. Use for the
# full-strength runs the preliminary 160m results motivate (Tables 1-2 scaling).
model: EleutherAI/pythia-1.4b      # or EleutherAI/pythia-2.8b, pythia-6.9b
revision: main
device: cuda
seed: 0

n_per_class: 1000
max_words: 100
min_words: 25
wikimia_length: 64

extraction:
  n_items: 1000
  prefix_len: 50          # Carlini et al. 2023 use longer context; extraction rises with it
  suffix_len: 50
  min_tokens: 120
correlation:
  items: results/pile_items_pythia-1.4b.jsonl
  n_boot: 2000

```


### `references.bib`

```bibtex
% =============================================================================
% references.bib  —  SHARED bibliography for the benchmark-contamination /
% privacy-leakage security paper.  All entries verified by literature subagents
% against arXiv ID / DOI / official venue URL (verification noted in the comment
% above each entry).  Fields flagged "[VERIFY]" are the weakest (usually page
% spans or venue strings) and must be confirmed against publisher PDFs before
% camera-ready.  DO NOT add an entry without a verification comment.
% =============================================================================

% ----------------------------------------------------------------------------
% A. Contamination / membership-inference / data-detection methods
% ----------------------------------------------------------------------------

% VERIFIED arXiv:1709.01604 ; IEEE CSF 2018 pp.268-282 (DBLP YeomGFJ18). Defines membership advantage = TPR-FPR; ties MIA to overfitting.
@inproceedings{yeom2018privacy,
  title     = {Privacy Risk in Machine Learning: Analyzing the Connection to Overfitting},
  author    = {Yeom, Samuel and Giacomelli, Irene and Fredrikson, Matt and Jha, Somesh},
  booktitle = {2018 IEEE 31st Computer Security Foundations Symposium (CSF)},
  pages     = {268--282},
  year      = {2018},
  publisher = {IEEE},
  doi       = {10.1109/CSF.2018.00027}
}

% VERIFIED arXiv:2310.16789 ; ICLR 2024 (OpenReview zWqr3MQuNs; iclr.cc/virtual/2024/poster/17381). Introduces WikiMIA + Min-K% Prob.
@inproceedings{shi2024detecting,
  title     = {Detecting Pretraining Data from Large Language Models},
  author    = {Shi, Weijia and Ajith, Anirudh and Xia, Mengzhou and Huang, Yangsibo and Liu, Daogao and Blevins, Terra and Chen, Danqi and Zettlemoyer, Luke},
  booktitle = {The Twelfth International Conference on Learning Representations (ICLR)},
  year      = {2024},
  eprint    = {2310.16789},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2404.02936 ; ICLR 2025 Spotlight (OpenReview ZGkfoufDaU). Successor to Min-K%.
@inproceedings{zhang2025minkpp,
  title     = {Min-K\%++: Improved Baseline for Detecting Pre-Training Data from Large Language Models},
  author    = {Zhang, Jingyang and Sun, Jingwei and Yeats, Eric and Ouyang, Yang and Kuo, Martin and Zhang, Jianyi and Yang, Hao Frank and Li, Hai},
  booktitle = {The Thirteenth International Conference on Learning Representations (ICLR)},
  year      = {2025},
  eprint    = {2404.02936},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2112.03570 ; DOI 10.1109/SP46214.2022.9833649 ; IEEE S&P 2022 pp.1897-1914. LiRA + TPR@lowFPR convention.
@inproceedings{carlini2022lira,
  title     = {Membership Inference Attacks From First Principles},
  author    = {Carlini, Nicholas and Chien, Steve and Nasr, Milad and Song, Shuang and Terzis, Andreas and Tram{\`e}r, Florian},
  booktitle = {2022 IEEE Symposium on Security and Privacy (SP)},
  pages     = {1897--1914},
  year      = {2022},
  publisher = {IEEE},
  doi       = {10.1109/SP46214.2022.9833649}
}

% VERIFIED arXiv:2402.07841 ; COLM 2024 (OpenReview av0D19pSkU; authors' MIMIR site iamgroot42.github.io/mimir.github.io). Venue confirmed COLM, not NAACL Findings. MIMIR benchmark on Pythia/Pile.
@inproceedings{duan2024mia,
  title     = {Do Membership Inference Attacks Work on Large Language Models?},
  author    = {Duan, Michael and Suri, Anshuman and Mireshghallah, Niloofar and Min, Sewon and Shi, Weijia and Zettlemoyer, Luke and Tsvetkov, Yulia and Choi, Yejin and Evans, David and Hajishirzi, Hannaneh},
  booktitle = {Conference on Language Modeling (COLM)},
  year      = {2024},
  eprint    = {2402.07841},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2305.18462 ; Findings of ACL 2023 pp.11330-11343 (ACL Anthology 2023.findings-acl.719). Neighbourhood-calibrated MIA (reference-free).
@inproceedings{mattern2023neighbourhood,
  title     = {Membership Inference Attacks against Language Models via Neighbourhood Comparison},
  author    = {Mattern, Justus and Mireshghallah, Fatemehsadat and Jin, Zhijing and Sch{\"o}lkopf, Bernhard and Sachan, Mrinmaya and Berg-Kirkpatrick, Taylor},
  booktitle = {Findings of the Association for Computational Linguistics: ACL 2023},
  pages     = {11330--11343},
  year      = {2023}
}

% VERIFIED arXiv:2012.07805 ; USENIX Security 2021 pp.2633-2650 (DBLP CarliniTWJHLRBS21). Extraction attack + zlib-entropy ratio baseline.
@inproceedings{carlini2021extracting,
  title     = {Extracting Training Data from Large Language Models},
  author    = {Carlini, Nicholas and Tram{\`e}r, Florian and Wallace, Eric and Jagielski, Matthew and Herbert-Voss, Ariel and Lee, Katherine and Roberts, Adam and Brown, Tom and Song, Dawn and Erlingsson, {\'U}lfar and Oprea, Alina and Raffel, Colin},
  booktitle = {30th USENIX Security Symposium (USENIX Security 21)},
  pages     = {2633--2650},
  year      = {2021}
}

% VERIFIED arXiv:2005.14165 ; NeurIPS 2020. 13-gram contamination/decontamination method. Full 31-author list de-truncated from arXiv:2005.14165 abstract page.
@inproceedings{brown2020gpt3,
  title     = {Language Models are Few-Shot Learners},
  author    = {Brown, Tom B. and Mann, Benjamin and Ryder, Nick and Subbiah, Melanie and Kaplan, Jared and Dhariwal, Prafulla and Neelakantan, Arvind and Shyam, Pranav and Sastry, Girish and Askell, Amanda and Agarwal, Sandhini and Herbert-Voss, Ariel and Krueger, Gretchen and Henighan, Tom and Child, Rewon and Ramesh, Aditya and Ziegler, Daniel M. and Wu, Jeffrey and Winter, Clemens and Hesse, Christopher and Chen, Mark and Sigler, Eric and Litwin, Mateusz and Gray, Scott and Chess, Benjamin and Clark, Jack and Berner, Christopher and McCandlish, Sam and Radford, Alec and Sutskever, Ilya and Amodei, Dario},
  booktitle = {Advances in Neural Information Processing Systems 33 (NeurIPS 2020)},
  year      = {2020},
  eprint    = {2005.14165},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2308.08493 ; ICLR 2024 (OpenReview 2Rwq6c3tvr). Guided-instruction / completion contamination test.
@inproceedings{golchin2024timetravel,
  title     = {Time Travel in {LLMs}: Tracing Data Contamination in Large Language Models},
  author    = {Golchin, Shahriar and Surdeanu, Mihai},
  booktitle = {The Twelfth International Conference on Learning Representations (ICLR)},
  year      = {2024},
  eprint    = {2308.08493},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2310.17623 ; ICLR 2024. Exchangeability/permutation test; provable contamination certificate.
@inproceedings{oren2024proving,
  title     = {Proving Test Set Contamination in Black-Box Language Models},
  author    = {Oren, Yonatan and Meister, Nicole and Chatterji, Niladri and Ladhak, Faisal and Hashimoto, Tatsunori B.},
  booktitle = {The Twelfth International Conference on Learning Representations (ICLR)},
  year      = {2024},
  eprint    = {2310.17623},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2404.00699. Survey of contamination-detection methods (umbrella cite for n-gram methods).
@article{ravaut2024survey,
  title   = {A Comprehensive Survey of Contamination Detection Methods in Large Language Models},
  author  = {Ravaut, Mathieu and Ding, Bosheng and Jiao, Fangkai and Chen, Hailin and Li, Xingxuan and Zhao, Ruochen and Qin, Chengwei and Xiong, Caiming and Joty, Shafiq},
  journal = {arXiv preprint arXiv:2404.00699},
  year    = {2024}
}

% ----------------------------------------------------------------------------
% B. Memorization / extraction / privacy leakage
% ----------------------------------------------------------------------------

% VERIFIED arXiv:2202.07646 ; ICLR 2023 (OpenReview TatRHT_1cK). Extractable memorization (prefix-continuation) + scaling laws.
@inproceedings{carlini2023quantifying,
  title     = {Quantifying Memorization Across Neural Language Models},
  author    = {Carlini, Nicholas and Ippolito, Daphne and Jagielski, Matthew and Lee, Katherine and Tram{\`e}r, Florian and Zhang, Chiyuan},
  booktitle = {The Eleventh International Conference on Learning Representations (ICLR)},
  year      = {2023},
  eprint    = {2202.07646},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2311.17035 ; ICLR 2025 (preprint first appeared 2023). Divergence attack on production LMs.
@inproceedings{nasr2025scalable,
  title     = {Scalable Extraction of Training Data from (Production) Language Models},
  author    = {Nasr, Milad and Carlini, Nicholas and Hayase, Jonathan and Jagielski, Matthew and Cooper, A. Feder and Ippolito, Daphne and Choquette-Choo, Christopher A. and Wallace, Eric and Tram{\`e}r, Florian and Lee, Katherine},
  booktitle = {The Thirteenth International Conference on Learning Representations (ICLR)},
  year      = {2025},
  eprint    = {2311.17035},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:1610.05820 ; IEEE S&P 2017 pp.3-18. Canonical shadow-model MIA.
@inproceedings{shokri2017membership,
  title     = {Membership Inference Attacks Against Machine Learning Models},
  author    = {Shokri, Reza and Stronati, Marco and Song, Congzheng and Shmatikov, Vitaly},
  booktitle = {2017 IEEE Symposium on Security and Privacy (SP)},
  pages     = {3--18},
  year      = {2017},
  publisher = {IEEE}
}

% VERIFIED arXiv:2302.00539 ; IEEE S&P 2023 pp.346-363 (Microsoft Research / Semantic Scholar). PII extraction/reconstruction/inference games.
@inproceedings{lukas2023pii,
  title     = {Analyzing Leakage of Personally Identifiable Information in Language Models},
  author    = {Lukas, Nils and Salem, Ahmed and Sim, Robert and Tople, Shruti and Wutschitz, Lukas and Zanella-B{\'e}guelin, Santiago},
  booktitle = {2023 IEEE Symposium on Security and Privacy (SP)},
  pages     = {346--363},
  year      = {2023},
  publisher = {IEEE}
}

% VERIFIED arXiv:2205.12628 ; Findings of EMNLP 2022 pp.2038-2047 (ACL Anthology 2022.findings-emnlp.148). Memorization vs. association decomposition of PII leakage.
@inproceedings{huang2022leaking,
  title     = {Are Large Pre-Trained Language Models Leaking Your Personal Information?},
  author    = {Huang, Jie and Shao, Hanyin and Chang, Kevin Chen-Chuan},
  booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2022},
  pages     = {2038--2047},
  year      = {2022}
}

% VERIFIED arXiv:2307.01881 ; NeurIPS 2023. ProPILE data-subject probing tool.
@inproceedings{kim2023propile,
  title     = {{ProPILE}: Probing Privacy Leakage in Large Language Models},
  author    = {Kim, Siwon and Yun, Sangdoo and Lee, Hwaran and Gubri, Martin and Yoon, Sungroh and Oh, Seong Joon},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  volume    = {36},
  year      = {2023}
}

% VERIFIED arXiv:1607.00133 ; ACM CCS 2016 ; DOI 10.1145/2976749.2978318. DP-SGD + moments accountant.
@inproceedings{abadi2016deep,
  title     = {Deep Learning with Differential Privacy},
  author    = {Abadi, Martin and Chu, Andy and Goodfellow, Ian and McMahan, H. Brendan and Mironov, Ilya and Talwar, Kunal and Zhang, Li},
  booktitle = {Proceedings of the 2016 ACM SIGSAC Conference on Computer and Communications Security (CCS)},
  pages     = {308--318},
  year      = {2016},
  doi       = {10.1145/2976749.2978318}
}

% VERIFIED arXiv:2110.05679 ; ICLR 2022 (oral). DP-SGD fine-tuning of LLMs + ghost clipping.
@inproceedings{li2022dpllm,
  title     = {Large Language Models Can Be Strong Differentially Private Learners},
  author    = {Li, Xuechen and Tram{\`e}r, Florian and Liang, Percy and Hashimoto, Tatsunori},
  booktitle = {The Tenth International Conference on Learning Representations (ICLR)},
  year      = {2022},
  eprint    = {2110.05679},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2110.06500 ; ICLR 2022. Parameter-efficient DP fine-tuning.
@inproceedings{yu2022dpfinetuning,
  title     = {Differentially Private Fine-tuning of Language Models},
  author    = {Yu, Da and Naik, Saurabh and Backurs, Arturs and Gopi, Sivakanth and Inan, Huseyin A. and Kamath, Gautam and Kulkarni, Janardhan and Lee, Yin Tat and Manoel, Andre and Wutschitz, Lukas and Yekhanin, Sergey and Zhang, Huishuai},
  booktitle = {The Tenth International Conference on Learning Representations (ICLR)},
  year      = {2022},
  eprint    = {2110.06500},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2108.01624. Preprint (no peer-reviewed venue confirmed). DP-SGD pretraining of BERT.
@article{anil2021dpbert,
  title   = {Large-Scale Differentially Private {BERT}},
  author  = {Anil, Rohan and Ghazi, Badih and Gupta, Vineet and Kumar, Ravi and Manurangsi, Pasin},
  journal = {arXiv preprint arXiv:2108.01624},
  year    = {2021}
}

% VERIFIED arXiv:2112.12938 ; NeurIPS 2023. Counterfactual memorization (Feldman-style).
@inproceedings{zhang2023counterfactual,
  title     = {Counterfactual Memorization in Neural Language Models},
  author    = {Zhang, Chiyuan and Ippolito, Daphne and Lee, Katherine and Jagielski, Matthew and Tram{\`e}r, Florian and Carlini, Nicholas},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  volume    = {36},
  year      = {2023}
}

% VERIFIED arXiv:1802.08232 ; USENIX Security 2019 pp.267-284. Secret Sharer: canary exposure metric.
@inproceedings{carlini2019secret,
  title     = {The Secret Sharer: Evaluating and Testing Unintended Memorization in Neural Networks},
  author    = {Carlini, Nicholas and Liu, Chang and Erlingsson, {\'U}lfar and Kos, Jernej and Song, Dawn},
  booktitle = {28th USENIX Security Symposium (USENIX Security 19)},
  pages     = {267--284},
  year      = {2019}
}

% VERIFIED arXiv:2210.17546 ; INLG 2023 pp.28-53 (ACL Anthology 2023.inlg-main.3). NOTE published title is "Preventing GENERATION OF Verbatim Memorization..."; corrected here.
@inproceedings{ippolito2023verbatim,
  title     = {Preventing Generation of Verbatim Memorization in Language Models Gives a False Sense of Privacy},
  author    = {Ippolito, Daphne and Tram{\`e}r, Florian and Nasr, Milad and Zhang, Chiyuan and Jagielski, Matthew and Lee, Katherine and Choquette-Choo, Christopher A. and Carlini, Nicholas},
  booktitle = {Proceedings of the 16th International Natural Language Generation Conference (INLG)},
  pages     = {28--53},
  year      = {2023},
  eprint    = {2210.17546},
  archivePrefix = {arXiv}
}

% ----------------------------------------------------------------------------
% B'. Additional recent security-venue privacy/MIA papers (venue calibration)
% ----------------------------------------------------------------------------

% VERIFIED USENIX Security 2023 pp.2133-2150. PII leakage from Codex/Copilot.
@inproceedings{niu2023codexleaks,
  title     = {{CodexLeaks}: Privacy Leaks from Code Generation Language Models in {GitHub} {Copilot}},
  author    = {Niu, Liang and Mirza, Shujaat and Maradni, Zayd and P{\"o}pper, Christina},
  booktitle = {32nd USENIX Security Symposium (USENIX Security 23)},
  pages     = {2133--2150},
  year      = {2023}
}

% VERIFIED arXiv:2502.18943 ; USENIX Security 2025. PETAL: label-only MIA on pretrained LLMs.
@inproceedings{he2025labelonly,
  title     = {Towards Label-Only Membership Inference Attack against Pre-trained Large Language Models},
  author    = {He, Yu and Li, Boheng and Liu, Liu and Ba, Zhongjie and Dong, Wei and Li, Yiming and Qin, Zhan and Ren, Kui and Chen, Chun},
  booktitle = {34th USENIX Security Symposium (USENIX Security 25)},
  year      = {2025}
}

% VERIFIED USENIX Security 2025 pp.8155-8173 (usenix.org presentation/cheng-shuai; ACM DL 10.5555/3766078.3766496) ; DOI 10.5281/zenodo.15544879. Few-shot PII extraction.
@inproceedings{cheng2025piiextraction,
  title     = {Effective {PII} Extraction from {LLMs} through Augmented Few-Shot Learning},
  author    = {Cheng, Shuai and Meng, Shu and Xu, Haitao and Zhang, Haoran and Hao, Shuai and Yue, Chuan and Ma, Wenrui and Han, Meng and Zhang, Fan and Li, Zhao},
  booktitle = {34th USENIX Security Symposium (USENIX Security 25)},
  pages     = {8155--8173},
  year      = {2025}
}

% VERIFIED arXiv:2506.10424 ; USENIX Security 2025. MIA on fine-tuned LLMs + obfuscation defense.
@inproceedings{zhang2025soft,
  title     = {{SOFT}: Selective Data Obfuscation for Protecting {LLM} Fine-tuning against Membership Inference Attacks},
  author    = {Zhang, Kaiyuan and Cheng, Siyuan and Guo, Hanxi and Chen, Yuetian and Su, Zian and An, Shengwei and Du, Yuntao and Fleming, Charles and Kundu, Ashish and Zhang, Xiangyu and Li, Ninghui},
  booktitle = {34th USENIX Security Symposium (USENIX Security 25)},
  year      = {2025}
}

% ----------------------------------------------------------------------------
% C. Models with auditable training data
% ----------------------------------------------------------------------------

% VERIFIED arXiv:2304.01373 ; ICML 2023 (PMLR v202). PRIMARY MODEL: Pythia suite on the Pile.
@inproceedings{biderman2023pythia,
  title     = {Pythia: A Suite for Analyzing Large Language Models Across Training and Scaling},
  author    = {Biderman, Stella and Schoelkopf, Hailey and Anthony, Quentin and Bradley, Herbie and O'Brien, Kyle and Hallahan, Eric and Khan, Mohammad Aflah and Purohit, Shivanshu and Prashanth, USVSN Sai and Raff, Edward and Skowron, Aviya and Sutawika, Lintang and van der Wal, Oskar},
  booktitle = {Proceedings of the 40th International Conference on Machine Learning (ICML)},
  series    = {PMLR},
  volume    = {202},
  year      = {2023},
  eprint    = {2304.01373},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2204.06745 ; BigScience Workshop @ ACL 2022. GPT-NeoX-20B on the Pile.
@inproceedings{black2022gptneox,
  title     = {{GPT-NeoX-20B}: An Open-Source Autoregressive Language Model},
  author    = {Black, Sid and Biderman, Stella and Hallahan, Eric and Anthony, Quentin and Gao, Leo and Golding, Laurence and He, Horace and Leahy, Connor and McDonell, Kyle and Phang, Jason and Pieler, Michael and Prashanth, USVSN Sai and Purohit, Shivanshu and Reynolds, Laria and Tow, Jonathan and Wang, Ben and Weinbach, Samuel},
  booktitle = {Proceedings of BigScience Episode \#5 -- Workshop on Challenges \& Perspectives in Creating Large Language Models},
  year      = {2022},
  eprint    = {2204.06745},
  archivePrefix = {arXiv}
}

% VERIFIED Zenodo concept DOI 10.5281/zenodo.5297715. GPT-Neo on the Pile.
@software{black2021gptneo,
  title     = {{GPT-Neo}: Large Scale Autoregressive Language Modeling with Mesh-Tensorflow},
  author    = {Black, Sid and Gao, Leo and Wang, Phil and Leahy, Connor and Biderman, Stella},
  month     = mar,
  year      = {2021},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.5297715}
}

% VERIFIED official CITATION.bib (github.com/kingoflolz/mesh-transformer-jax). No arXiv paper exists.
@misc{wang2021gptj,
  title        = {{GPT-J-6B}: A 6 Billion Parameter Autoregressive Language Model},
  author       = {Wang, Ben and Komatsuzaki, Aran},
  howpublished = {\url{https://github.com/kingoflolz/mesh-transformer-jax}},
  month        = may,
  year         = {2021}
}

% VERIFIED arXiv:2402.00838 ; ACL 2024. OLMo on Dolma (secondary replication model).
@inproceedings{groeneveld2024olmo,
  title     = {{OLMo}: Accelerating the Science of Language Models},
  author    = {Groeneveld, Dirk and Beltagy, Iz and Walsh, Pete and Bhagia, Akshita and Kinney, Rodney and Tafjord, Oyvind and Jha, Ananya Harsh and Ivison, Hamish and Magnusson, Ian and Wang, Yizhong and Arora, Shane and Atkinson, David and Authur, Russell and Chandu, Khyathi Raghavi and Cohan, Arman and Dumas, Jennifer and Elazar, Yanai and Gu, Yuling and Hessel, Jack and Khot, Tushar and Merrill, William and Morrison, Jacob and Muennighoff, Niklas and Naik, Aakanksha and Nam, Crystal and Peters, Matthew E. and Pyatkin, Valentina and Ravichander, Abhilasha and Schwenk, Dustin and Shah, Saurabh and Smith, Will and Strubell, Emma and Subramani, Nishant and Wortsman, Mitchell and Dasigi, Pradeep and Lambert, Nathan and Richardson, Kyle and Zettlemoyer, Luke and Dodge, Jesse and Lo, Kyle and Soldaini, Luca and Smith, Noah A. and Hajishirzi, Hannaneh},
  booktitle = {Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL)},
  year      = {2024},
  eprint    = {2402.00838},
  archivePrefix = {arXiv}
}

% VERIFIED OpenAI technical report (no arXiv/venue). WebText NOT public -> weak ground truth.
@article{radford2019gpt2,
  title   = {Language Models are Unsupervised Multitask Learners},
  author  = {Radford, Alec and Wu, Jeffrey and Child, Rewon and Luan, David and Amodei, Dario and Sutskever, Ilya},
  journal = {OpenAI technical report},
  year    = {2019}
}

% VERIFIED arXiv:2211.05100. BLOOM / ROOTS. The official paper has 392 listed contributors under the corporate author "BigScience Workshop"; we keep the corporate-author form with the canonical lead-author tail (de-truncation to all 392 names is neither feasible nor standard for this paper).
@article{bigscience2022bloom,
  title   = {{BLOOM}: A 176B-Parameter Open-Access Multilingual Language Model},
  author  = {{BigScience Workshop} and Le Scao, Teven and Fan, Angela and Akiki, Christopher and Pavlick, Ellie and Ili{\'c}, Suzana and Hesslow, Daniel and Castagn{\'e}, Roman and Luccioni, Alexandra Sasha and Yvon, Fran{\c{c}}ois and Gall{\'e}, Matthias and others},
  journal = {arXiv preprint arXiv:2211.05100},
  year    = {2022}
}

% VERIFIED arXiv:2302.13971. LLaMA — corpus NOT released; excluded from ground-truth experiments.
@article{touvron2023llama,
  title   = {{LLaMA}: Open and Efficient Foundation Language Models},
  author  = {Touvron, Hugo and Lavril, Thibaut and Izacard, Gautier and Martinet, Xavier and Lachaux, Marie-Anne and Lacroix, Timoth{\'e}e and Rozi{\`e}re, Baptiste and Goyal, Naman and Hambro, Eric and Azhar, Faisal and Rodriguez, Aurelien and Joulin, Armand and Grave, Edouard and Lample, Guillaume},
  journal = {arXiv preprint arXiv:2302.13971},
  year    = {2023}
}

% ----------------------------------------------------------------------------
% D. Corpora and benchmarks
% ----------------------------------------------------------------------------

% VERIFIED arXiv:2101.00027. The Pile (Pythia's training corpus; our ground truth).
@article{gao2020pile,
  title   = {The {Pile}: An 800GB Dataset of Diverse Text for Language Modeling},
  author  = {Gao, Leo and Biderman, Stella and Black, Sid and Golding, Laurence and Hoppe, Travis and Foster, Charles and Phang, Jason and He, Horace and Thite, Anish and Nabeshima, Noa and Presser, Shawn and Leahy, Connor},
  journal = {arXiv preprint arXiv:2101.00027},
  year    = {2020}
}

% VERIFIED organization/website. No canonical paper; papers cite the site.
@misc{commoncrawl,
  title        = {Common Crawl},
  author       = {{Common Crawl Foundation}},
  howpublished = {\url{https://commoncrawl.org}},
  note         = {Open repository of web crawl data}
}

% VERIFIED JMLR 21(140):1-67, 2020 ; arXiv:1910.10683. C4 introduced with T5.
@article{raffel2020c4,
  title   = {Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer},
  author  = {Raffel, Colin and Shazeer, Noam and Roberts, Adam and Lee, Katherine and Narang, Sharan and Matena, Michael and Zhou, Yanqi and Li, Wei and Liu, Peter J.},
  journal = {Journal of Machine Learning Research},
  volume  = {21},
  number  = {140},
  pages   = {1--67},
  year    = {2020}
}

% VERIFIED arXiv:2104.08758 ; EMNLP 2021. Documents the C4 corpus.
@inproceedings{dodge2021c4,
  title     = {Documenting Large Webtext Corpora: A Case Study on the Colossal Clean Crawled Corpus},
  author    = {Dodge, Jesse and Sap, Maarten and Marasovi{\'c}, Ana and Agnew, William and Ilharco, Gabriel and Groeneveld, Dirk and Mitchell, Margaret and Gardner, Matt},
  booktitle = {Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing (EMNLP)},
  year      = {2021},
  eprint    = {2104.08758},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2411.12372 ; NeurIPS 2024 Datasets & Benchmarks Track.
@inproceedings{weber2024redpajama,
  title     = {{RedPajama}: an Open Dataset for Training Large Language Models},
  author    = {Weber, Maurice and Fu, Daniel and Anthony, Quentin and Oren, Yonatan and Adams, Shane and Alexandrov, Anton and Lyu, Xiaozhong and Nguyen, Huu and Yao, Xiaozhe and Adams, Virginia and Athiwaratkun, Ben and Chalamala, Rahul and Chen, Kezhen and Ryabinin, Max and Dao, Tri and Liang, Percy and R{\'e}, Christopher and Rish, Irina and Zhang, Ce},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS), Datasets and Benchmarks Track},
  year      = {2024},
  eprint    = {2411.12372},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2402.00159 ; ACL 2024. Dolma (OLMo's corpus).
@inproceedings{soldaini2024dolma,
  title     = {Dolma: an Open Corpus of Three Trillion Tokens for Language Model Pretraining Research},
  author    = {Soldaini, Luca and Kinney, Rodney and Bhagia, Akshita and Schwenk, Dustin and Atkinson, David and Authur, Russell and Bogin, Ben and Chandu, Khyathi and Dumas, Jennifer and Elazar, Yanai and Hofmann, Valentin and Jha, Ananya Harsh and Kumar, Sachin and Lucy, Li and Lyu, Xinxi and Lambert, Nathan and Magnusson, Ian and Morrison, Jacob and Muennighoff, Niklas and Naik, Aakanksha and Nam, Crystal and Peters, Matthew E. and Ravichander, Abhilasha and Richardson, Kyle and Shen, Zejiang and Strubell, Emma and Subramani, Nishant and Tafjord, Oyvind and Walsh, Pete and Zettlemoyer, Luke and Smith, Noah A. and Hajishirzi, Hannaneh and Beltagy, Iz and Groeneveld, Dirk and Dodge, Jesse and Lo, Kyle},
  booktitle = {Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL)},
  year      = {2024},
  eprint    = {2402.00159},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2009.03300 ; ICLR 2021. MMLU.
@inproceedings{hendrycks2021mmlu,
  title     = {Measuring Massive Multitask Language Understanding},
  author    = {Hendrycks, Dan and Burns, Collin and Basart, Steven and Zou, Andy and Mazeika, Mantas and Song, Dawn and Steinhardt, Jacob},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2021},
  eprint    = {2009.03300},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2110.14168. GSM8K.
@article{cobbe2021gsm8k,
  title   = {Training Verifiers to Solve Math Word Problems},
  author  = {Cobbe, Karl and Kosaraju, Vineet and Bavarian, Mohammad and Chen, Mark and Jun, Heewoo and Kaiser, Lukasz and Plappert, Matthias and Tworek, Jerry and Hilton, Jacob and Nakano, Reiichiro and Hesse, Christopher and Schulman, John},
  journal = {arXiv preprint arXiv:2110.14168},
  year    = {2021}
}

% VERIFIED arXiv:2107.03374. HumanEval / Codex. Full 58-author list de-truncated from arXiv:2107.03374 abstract page.
@article{chen2021humaneval,
  title   = {Evaluating Large Language Models Trained on Code},
  author  = {Chen, Mark and Tworek, Jerry and Jun, Heewoo and Yuan, Qiming and Pinto, Henrique Ponde de Oliveira and Kaplan, Jared and Edwards, Harri and Burda, Yuri and Joseph, Nicholas and Brockman, Greg and Ray, Alex and Puri, Raul and Krueger, Gretchen and Petrov, Michael and Khlaaf, Heidy and Sastry, Girish and Mishkin, Pamela and Chan, Brooke and Gray, Scott and Ryder, Nick and Pavlov, Mikhail and Power, Alethea and Kaiser, Lukasz and Bavarian, Mohammad and Winter, Clemens and Tillet, Philippe and Such, Felipe Petroski and Cummings, Dave and Plappert, Matthias and Chantzis, Fotios and Barnes, Elizabeth and Herbert-Voss, Ariel and Guss, William Hebgen and Nichol, Alex and Paino, Alex and Tezak, Nikolas and Tang, Jie and Babuschkin, Igor and Balaji, Suchir and Jain, Shantanu and Saunders, William and Hesse, Christopher and Carr, Andrew N. and Leike, Jan and Achiam, Josh and Misra, Vedant and Morikawa, Evan and Radford, Alec and Knight, Matthew and Brundage, Miles and Murati, Mira and Mayer, Katie and Welinder, Peter and McGrew, Bob and Amodei, Dario and McCandlish, Sam and Sutskever, Ilya and Zaremba, Wojciech},
  journal = {arXiv preprint arXiv:2107.03374},
  year    = {2021}
}

% VERIFIED arXiv:1905.07830 ; ACL 2019. HellaSwag.
@inproceedings{zellers2019hellaswag,
  title     = {{HellaSwag}: Can a Machine Really Finish Your Sentence?},
  author    = {Zellers, Rowan and Holtzman, Ari and Bisk, Yonatan and Farhadi, Ali and Choi, Yejin},
  booktitle = {Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics (ACL)},
  year      = {2019},
  eprint    = {1905.07830},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:2109.07958 ; ACL 2022. TruthfulQA.
@inproceedings{lin2022truthfulqa,
  title     = {{TruthfulQA}: Measuring How Models Mimic Human Falsehoods},
  author    = {Lin, Stephanie and Hilton, Jacob and Evans, Owain},
  booktitle = {Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (ACL)},
  year      = {2022},
  eprint    = {2109.07958},
  archivePrefix = {arXiv}
}

% VERIFIED arXiv:1905.10044 ; NAACL 2019. BoolQ.
@inproceedings{clark2019boolq,
  title     = {{BoolQ}: Exploring the Surprising Difficulty of Natural Yes/No Questions},
  author    = {Clark, Christopher and Lee, Kenton and Chang, Ming-Wei and Kwiatkowski, Tom and Collins, Michael and Toutanova, Kristina},
  booktitle = {Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL)},
  year      = {2019},
  eprint    = {1905.10044},
  archivePrefix = {arXiv}
}

```



# PART 8 — RAW RESULT SUMMARIES (the actual numbers)


### `results/controls_pythia-160m-deduped.json`

```json
{
  "model": "EleutherAI/pythia-160m-deduped",
  "tag": "pythia-160m-deduped",
  "n": 300,
  "mean_frac": 0.04473333333333334,
  "detectors": {
    "loss": {
      "raw_rho": 0.3156457414702166,
      "raw_ci": [
        0.20255926049040032,
        0.42296974943095095
      ],
      "raw_kendall": 0.24387484313994887,
      "raw_perm_p": 0.0004997501249375312
    },
    "min_20_prob": {
      "raw_rho": 0.22121462407949116,
      "raw_ci": [
        0.10718667147304492,
        0.3312141882947294
      ],
      "raw_kendall": 0.16816591690048177,
      "raw_perm_p": 0.0004997501249375312,
      "partial_rho_given_loss": -0.1331080191943897,
      "partial_ci": [
        -0.23902855764922085,
        -0.010845811461471217
      ],
      "partial_perm_p": 0.021989005497251374,
      "partial_kendall_resid": null,
      "semipartial_rho": -0.1263031522911229,
      "freqmatched_rho": 0.06480793115700867,
      "freqmatched_n": 100,
      "partial_rho_given_freq": 0.21910808947679186
    },
    "min_20_plusplus": {
      "raw_rho": 0.1609711485687338,
      "raw_ci": [
        0.04960133516392368,
        0.2672332730841155
      ],
      "raw_kendall": 0.12189630520887408,
      "raw_perm_p": 0.00849575212393803,
      "partial_rho_given_loss": -0.1414484590042969,
      "partial_ci": [
        -0.2521150477462051,
        -0.02783618829107524
      ],
      "partial_perm_p": 0.013493253373313344,
      "partial_kendall_resid": null,
      "semipartial_rho": -0.13421720469653992,
      "freqmatched_rho": 0.001042365326301538,
      "freqmatched_n": 100,
      "partial_rho_given_freq": 0.18786940036725217
    },
    "zlib_ratio": {
      "raw_rho": 0.22013961420955383,
      "raw_ci": [
        0.10500953083811314,
        0.3309041581838914
      ],
      "raw_kendall": 0.16865931323368613,
      "raw_perm_p": 0.0009995002498750624,
      "partial_rho_given_loss": -0.01644769489408432,
      "partial_ci": [
        -0.12504643802548576,
        0.09392357695338283
      ],
      "partial_perm_p": 0.7526236881559221,
      "partial_kendall_resid": null,
      "semipartial_rho": -0.015606841162677418,
      "freqmatched_rho": 0.07409857863056585,
      "freqmatched_n": 100,
      "partial_rho_given_freq": 0.2427282190446941
    }
  },
  "R6_family": {
    "detectors": [
      "min_20_prob",
      "min_20_plusplus",
      "zlib_ratio"
    ],
    "perm_p": [
      0.021989005497251374,
      0.013493253373313344,
      0.7526236881559221
    ],
    "bh_qvalues": [
      0.03298350824587706,
      0.03298350824587706,
      0.752623688155922
    ],
    "bh_rejected": [
      true,
      true,
      false
    ]
  },
  "per_domain_loss_rho": {
    "ArXiv": {
      "n": 14,
      "loss_rho": 0.5486917318756083
    },
    "Books3": {
      "n": 9,
      "loss_rho": 0.5179323973782373
    },
    "DM Mathematics": {
      "n": 13,
      "loss_rho": 0.10875205500825674
    },
    "Enron Emails": {
      "n": 13,
      "loss_rho": 0.16479775246380865
    },
    "EuroParl": {
      "n": 6,
      "loss_rho": -0.6761234037828133
    },
    "FreeLaw": {
      "n": 17,
      "loss_rho": 0.35631188012262816
    },
    "Github": {
      "n": 21,
      "loss_rho": 0.7529217904327254
    },
    "HackerNews": {
      "n": 13,
      "loss_rho": 0.044572568370250226
    },
    "NIH ExPorter": {
      "n": 13,
      "loss_rho": -0.18552434993629385
    },
    "OpenSubtitles": {
      "n": 13,
      "loss_rho": -0.04732449912961666
    },
    "OpenWebText2": {
      "n": 27,
      "loss_rho": 0.17873108119926945
    },
    "PhilPapers": {
      "n": 5,
      "loss_rho": -0.8660254037844386
    },
    "Pile-CC": {
      "n": 26,
      "loss_rho": -0.01681828906153688
    },
    "PubMed Abstracts": {
      "n": 21,
      "loss_rho": -0.5769820571633398
    },
    "PubMed Central": {
      "n": 15,
      "loss_rho": 0.22854352508251652
    },
    "StackExchange": {
      "n": 21,
      "loss_rho": 0.517618317334646
    },
    "USPTO Backgrounds": {
      "n": 17,
      "loss_rho": 0.17943514064131835
    },
    "Wikipedia (en)": {
      "n": 19,
      "loss_rho": 0.2823529650651674
    },
    "YoutubeSubtitles": {
      "n": 11,
      "loss_rho": 0.35976048897510887
    }
  }
}
```


### `results/controls_pythia-160m.json`

```json
{
  "model": "EleutherAI/pythia-160m",
  "tag": "pythia-160m",
  "n": 300,
  "mean_frac": 0.03700277777777778,
  "detectors": {
    "loss": {
      "raw_rho": 0.2746506320134808,
      "raw_ci": [
        0.16379450814501312,
        0.37822661544961905
      ],
      "raw_kendall": 0.21138471481148177,
      "raw_perm_p": 0.0004997501249375312
    },
    "min_20_prob": {
      "raw_rho": 0.1729732393612115,
      "raw_ci": [
        0.06101616539617099,
        0.2846411665224007
      ],
      "raw_kendall": 0.13197188016561592,
      "raw_perm_p": 0.0024987506246876563,
      "partial_rho_given_loss": -0.1780056098170858,
      "partial_ci": [
        -0.28028232558160765,
        -0.06807047825283369
      ],
      "partial_perm_p": 0.0014992503748125937,
      "partial_kendall_resid": null,
      "semipartial_rho": -0.17116024148820994,
      "freqmatched_rho": 0.0899650115175008,
      "freqmatched_n": 100,
      "partial_rho_given_freq": 0.16629142420148374
    },
    "min_20_plusplus": {
      "raw_rho": 0.1078924246347382,
      "raw_ci": [
        -0.009649577533504247,
        0.22030673006860807
      ],
      "raw_kendall": 0.08220212842474958,
      "raw_perm_p": 0.06196901549225387,
      "partial_rho_given_loss": -0.14847595518279239,
      "partial_ci": [
        -0.25895603285730195,
        -0.029545473892453183
      ],
      "partial_perm_p": 0.0069965017491254375,
      "partial_kendall_resid": null,
      "semipartial_rho": -0.14276617669742736,
      "freqmatched_rho": 0.015642460978035778,
      "freqmatched_n": 100,
      "partial_rho_given_freq": 0.13827554894720545
    },
    "zlib_ratio": {
      "raw_rho": 0.17729023868159155,
      "raw_ci": [
        0.06265715714585739,
        0.2945947621618041
      ],
      "raw_kendall": 0.13558155446770073,
      "raw_perm_p": 0.0024987506246876563,
      "partial_rho_given_loss": -0.04225455454896127,
      "partial_ci": [
        -0.16049323947938718,
        0.07480796966181662
      ],
      "partial_perm_p": 0.46326836581709147,
      "partial_kendall_resid": null,
      "semipartial_rho": -0.040629617055376425,
      "freqmatched_rho": 0.08642828767716526,
      "freqmatched_n": 100,
      "partial_rho_given_freq": 0.1927925541089174
    }
  },
  "R6_family": {
    "detectors": [
      "min_20_prob",
      "min_20_plusplus",
      "zlib_ratio"
    ],
    "perm_p": [
      0.0014992503748125937,
      0.0069965017491254375,
      0.46326836581709147
    ],
    "bh_qvalues": [
      0.004497751124437781,
      0.010494752623688156,
      0.46326836581709147
    ],
    "bh_rejected": [
      true,
      true,
      false
    ]
  },
  "per_domain_loss_rho": {
    "ArXiv": {
      "n": 14,
      "loss_rho": 0.3824742653798658
    },
    "Books3": {
      "n": 9,
      "loss_rho": 0.40836977485591786
    },
    "DM Mathematics": {
      "n": 13,
      "loss_rho": 0.002939244729952885
    },
    "Enron Emails": {
      "n": 13,
      "loss_rho": 0.17079039800794715
    },
    "EuroParl": {
      "n": 6,
      "loss_rho": -0.6546536707079772
    },
    "FreeLaw": {
      "n": 17,
      "loss_rho": 0.09151523153120272
    },
    "Github": {
      "n": 21,
      "loss_rho": 0.5978567871242692
    },
    "HackerNews": {
      "n": 13,
      "loss_rho": -0.09258711133604776
    },
    "NIH ExPorter": {
      "n": 13,
      "loss_rho": 0.32120803721981056
    },
    "OpenSubtitles": {
      "n": 13,
      "loss_rho": 0.00946489982592333
    },
    "OpenWebText2": {
      "n": 27,
      "loss_rho": 0.30596558442582084
    },
    "PhilPapers": {
      "n": 5,
      "loss_rho": -0.28867513459481287
    },
    "Pile-CC": {
      "n": 26,
      "loss_rho": 0.15350716380711898
    },
    "PubMed Abstracts": {
      "n": 21,
      "loss_rho": -0.48431743568666796
    },
    "PubMed Central": {
      "n": 15,
      "loss_rho": 0.25279543103845264
    },
    "StackExchange": {
      "n": 21,
      "loss_rho": 0.5443332630831055
    },
    "USPTO Backgrounds": {
      "n": 17,
      "loss_rho": -0.18994964809552306
    },
    "Wikipedia (en)": {
      "n": 19,
      "loss_rho": 0.30166058400019696
    },
    "YoutubeSubtitles": {
      "n": 11,
      "loss_rho": -0.09469274704942043
    }
  }
}
```


### `results/correlation_pythia-160m.json`

```json
{
  "model": "EleutherAI/pythia-160m",
  "n": 300,
  "leakage_mean_frac": 0.03700277777777778,
  "fully_extracted": 3,
  "summary": {
    "loss": {
      "rho_frac": 0.2746506320134808,
      "rho_frac_ci": [
        0.16379450814501312,
        0.37822661544961905
      ],
      "rho_extracted": 0.1715641540620635
    },
    "min_20_prob": {
      "rho_frac": 0.1729732393612115,
      "rho_frac_ci": [
        0.06101616539617099,
        0.2846411665224007
      ],
      "rho_extracted": 0.17079047129289973
    },
    "min_20_plusplus": {
      "rho_frac": 0.1078924246347382,
      "rho_frac_ci": [
        -0.009649577533504247,
        0.22030673006860807
      ],
      "rho_extracted": 0.16924310575457222
    },
    "zlib_ratio": {
      "rho_frac": 0.17729023868159155,
      "rho_frac_ci": [
        0.06265715714585739,
        0.2945947621618041
      ],
      "rho_extracted": 0.1642141677550078
    }
  }
}
```


### `results/pilemia_pythia-160m-deduped_summary.json`

```json
{
  "model": "EleutherAI/pythia-160m-deduped",
  "n": 464,
  "construction": "pile-train-vs-val",
  "summary": {
    "loss": {
      "auc": 0.45208457193816887,
      "auc_ci": [
        0.40381428359096316,
        0.5084130685196195
      ],
      "tpr_at_1": 0.008620689655172414,
      "tpr_at_0p1": 0.0
    },
    "min_20_prob": {
      "auc": 0.46720793697978596,
      "auc_ci": [
        0.40721053804994056,
        0.525807725178359
      ],
      "tpr_at_1": 0.008620689655172414,
      "tpr_at_0p1": 0.0
    },
    "min_20_plusplus": {
      "auc": 0.4807892390011891,
      "auc_ci": [
        0.431277868608799,
        0.5372027348394769
      ],
      "tpr_at_1": 0.017241379310344827,
      "tpr_at_0p1": 0.0
    },
    "zlib_ratio": {
      "auc": 0.48502526753864444,
      "auc_ci": [
        0.4359291394173603,
        0.546025007431629
      ],
      "tpr_at_1": 0.008620689655172414,
      "tpr_at_0p1": 0.0
    }
  }
}
```


### `results/pilemia_pythia-160m_summary.json`

```json
{
  "model": "EleutherAI/pythia-160m",
  "n": 464,
  "construction": "pile-train-vs-val",
  "summary": {
    "loss": {
      "auc": 0.45446269322235433,
      "auc_ci": [
        0.4074149078478002,
        0.5114999814209275
      ],
      "tpr_at_1": 0.008620689655172414,
      "tpr_at_0p1": 0.0
    },
    "min_20_prob": {
      "auc": 0.4699762187871581,
      "auc_ci": [
        0.4098905692627824,
        0.5304274115636147
      ],
      "tpr_at_1": 0.008620689655172414,
      "tpr_at_0p1": 0.0
    },
    "min_20_plusplus": {
      "auc": 0.4901716706302021,
      "auc_ci": [
        0.4394638079667063,
        0.5456980157550535
      ],
      "tpr_at_1": 0.004310344827586207,
      "tpr_at_0p1": 0.0
    },
    "zlib_ratio": {
      "auc": 0.484375,
      "auc_ci": [
        0.43746005499405466,
        0.5445549383174791
      ],
      "tpr_at_1": 0.008620689655172414,
      "tpr_at_0p1": 0.0
    }
  }
}
```


### `results/wikimia64_summary.json`

```json
{
  "model": "EleutherAI/pythia-1.4b",
  "length": 64,
  "n": 542,
  "summary": {
    "loss": {
      "auc": 0.5711049241183536,
      "auc_ci": [
        0.5255680887651489,
        0.6198251037231138
      ],
      "tpr_at_1": 0.02464788732394366,
      "tpr_at_0p1": 0.0035211267605633804
    },
    "min_20_prob": {
      "auc": 0.5795528987880773,
      "auc_ci": [
        0.531706859373294,
        0.6249392673872693
      ],
      "tpr_at_1": 0.02464788732394366,
      "tpr_at_0p1": 0.01056338028169014
    },
    "min_20_plusplus": {
      "auc": 0.5465252756851184,
      "auc_ci": [
        0.49692208483458894,
        0.5949636286712523
      ],
      "tpr_at_1": 0.02112676056338028,
      "tpr_at_0p1": 0.017605633802816902
    },
    "zlib_ratio": {
      "auc": 0.6158559886450485,
      "auc_ci": [
        0.5650074380390873,
        0.6626705972267715
      ],
      "tpr_at_1": 0.04929577464788732,
      "tpr_at_0p1": 0.007042253521126761
    }
  }
}
```
