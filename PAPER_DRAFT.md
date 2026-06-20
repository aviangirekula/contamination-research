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

