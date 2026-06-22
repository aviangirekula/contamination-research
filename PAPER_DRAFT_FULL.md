Large language models are ranked and certified as safe on public
benchmarks whose validity rests on the benchmark not appearing in
pre-training. We study *benchmark contamination* not as a
measurement-hygiene problem but as a privacy/security vulnerability:
contamination is a visible symptom of memorization, and memorization is
the mechanism by which sensitive content leaks. Using the Pythia suite
trained on the public Pile—so that membership is ground truth rather
than an inferred label—we run a systematic, pre-registered comparison of
existing contamination/membership detectors (LOSS, Min-K%, Min-K%++,
zlib) against a per-item *extraction* outcome. We make no claim to a new
detector or metric. Our contribution is a *controlled* result: a
pre-registered partial-correlation and mediation analysis that isolates
the role of raw per-item loss. We find that the apparent
contamination→leakage association is *loss-mediated to the resolution of
this experiment*: the calibrated reference-free detectors—which are
themselves strongly-to-moderately collinear with loss (Spearman
0.74–0.90)—add no positive predictive value beyond it, and their
residual partials are null or, for the most loss-collinear detector
(Min-K%), weakly negative in a manner consistent with a suppression
artifact rather than substantive inverse prediction. This absence of
positive residual survives a non-linear (cubic-residual and
decile-stratified) loss control and deduplication, and is not explained
by token frequency or the zero-inflated outcome. We frame this as a
*membership-detection-versus-leakage-prediction divergence*: the
detectors the field optimizes for membership are not the right
instrument for the privacy question. **These results are preliminary,
obtained on the smallest (160M) Pythia model on CPU; the pipeline is
built so that the GPU-scale replication is a single configuration
change.** All analyses are pre-registered and every number is
reproducible from a seeded script.

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
    Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">5</a>).

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
    leakage \[lukas2023pii\]. A pre-registered partial-correlation and
    mediation control then isolates the role of raw loss. In our
    ground-truth 160M-parameter setting we find that the
    contamination→leakage association is *loss-mediated to the
    resolution of this experiment*: once loss is held fixed, the
    calibrated reference-free detectors (Min-K%, Min-K%++, zlib) add no
    positive predictive value. These detectors are themselves
    near-collinear transforms of loss (Spearman 0.74–0.90), so we read a
    negative residual for the most collinear of them (Min-K%) as a
    likely suppression artifact rather than substantive inverse
    prediction, and claim only the conservative result: no positive
    signal beyond loss. The calibrations that improve
    membership-detection AUC thus do not retain the loss-magnitude
    signal that predicts leakage—a divergence between membership
    detection and leakage prediction that we report as our central
    empirical finding (robust to deduplication and a non-linear loss
    control, and not explained by token frequency or the zero-inflated
    outcome).

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
Section <a href="#sec:relatedwork" data-reference-type="ref" data-reference="sec:relatedwork">4</a>
formalizes contamination, its typology, and the detection and
memorization literature on which our evaluation builds.

# Threat Model

We frame contamination detection as a membership/exposure attack and
state the adversary explicitly, following the convention that a privacy
attack must be evaluated by its behaviour at a low false-positive
operating point rather than on average \[carlini2022lira\].

#### Adversary goals (graded).

-   **G1 — Membership inference.** Decide whether a specific sequence (a
    benchmark item, document, or record) was in the training corpus.

-   **G2 — Benchmark-level contamination confirmation.** Decide, with a
    controlled false-positive rate, whether an entire benchmark was
    trained on.

-   **G3 — Extraction / leakage.** Recover verbatim content—and, on a
    controlled corpus, PII—that was in training. This is the concrete
    harm; G1–G2 are of interest largely insofar as they predict G3.

#### Adversary knowledge and access.

We grade detectors by the minimum access each requires: *black-box*
(text in, text out; e.g. guided prompting, which we do not evaluate),
*gray-box* (per-token log-probabilities / loss; LOSS, Min-K%, zlib), and
*white-box* (the full next-token distribution; Min-K%++). The
corpus-side *n*-gram test instead assumes access to the training corpus
(available here because the Pile is public) and is used to construct
ground-truth contamination labels, not as a model-access attack. For our
ground-truth experiments the *auditor* additionally knows the public
training corpus; the modelled attacker does not need corpus access for
G1/G3.

#### Success criteria.

G1: true-positive rate at 0.1% and 1% false-positive rate (log-scale
ROC), with AUC secondary and bootstrap confidence intervals. G2: a
permutation-test *p*-value below threshold with a controlled
false-positive rate \[oren2024proving\]. G3: a non-zero extraction rate,
and—our headline analysis—a positive association between a per-item
contamination score and the per-item extraction outcome that *survives
controlling for raw loss*. The last criterion is what distinguishes a
contamination signal that genuinely predicts leakage from one that
merely restates the model’s loss.

#### Out of scope.

We do not attack closed production models for real third-party PII, do
not train or fine-tune models, and propose no new detector. Differential
privacy is discussed as the producer-side mitigation our threat model
motivates
(Section <a href="#sec:dp" data-reference-type="ref" data-reference="sec:dp">4.5</a>),
not implemented.

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
Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">5</a>.
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
Section <a href="#sec:mia-lineage" data-reference-type="ref" data-reference="sec:mia-lineage">4.4</a> \[mattern2023neighbourhood,shokri2017membership\].

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

## Closest prior work, and how we differ

Three recent works reach conclusions adjacent to ours, and we are
careful to position against them rather than overclaim. Al Sahili et
al. \[alsahili2025effectiveness\] reach a compatible conclusion for
targeted extraction—that “complex MIA techniques yield only marginal
improvements over simple likelihood-based ranking”—but they establish it
through aggregate *ranking-precision* comparisons and an AdaBoost
ensemble over MIA features, reporting *marginal gains* rather than
testing for independent signal. In contrast, we run a pre-registered
*partial correlation controlling for raw per-item loss*, which lets us
state the stronger, calibrated claim that the reference-free detectors
contribute *zero or negative* residual predictive value once loss is
partialled out. Hayes et al. \[hayes2025strong\] likewise “observe no
correlation with MIA success” for extraction and conclude the “two
privacy attacks may capture different signals,” but their evidence is a
*direct, zero-order* correlation between a reference-model attack (LiRA)
and extraction. We differ on both method and object: we *partial out
per-item loss* rather than correlating directly, and we target the
reference-free *calibrated* detectors (Min-K%, Min-K%++, zlib) that the
contamination-detection literature actually deploys, showing the
divergence persists as a controlled mediation result. Independently,
Chen et al. \[chen2025statistical\] find for the *membership* task that
the few detectors numerically above the loss baseline (Min-K%, Min-K%++,
ReCaLL) do not beat it robustly once random-seed variance is accounted
for, and that performance is domain-dependent (code-like,
low-token-diversity domains such as GitHub and StackExchange behave
differently from Wikipedia and FreeLaw); we revisit this domain
dependence for the *extraction* outcome in our per-domain analysis
(Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">5</a>),
noting it is a distinct axis from their membership-AUC result. Finally,
blind-baseline and SoK critiques \[das2024blind,meeus2025sok\] show that
post-hoc member/non-member splits can make detector “success” an
artifact of distribution shift; our use of ground-truth Pile membership
(no post-hoc split) is precisely the design discipline they call for.

<div class="tabular">

@p2.1cmp1.6cmp1.9cmp2.0cmp2.4cm@ **Study** & **Outcome** & **Detectors**
& **Statistical method** & **Conclusion**  
Shi’24; Zhang’25 \[shi2024detecting,zhang2025minkpp\] & membership &
reference-free (Min-K%/++) & AUC / TPR@FPR & detector raises membership
AUC  
Duan’24 (MIMIR) \[duan2024mia\] & membership & ref-free + reference &
AUC on ground truth & MIAs ≈ chance on LLMs  
Carlini’22 (LiRA) \[carlini2022lira\] & membership & shadow/reference &
TPR at low FPR & strong only with shadow models  
Chen’25 \[chen2025statistical\] & membership & reference-free &
seed-variance testing vs loss & not robustly beyond loss  
Hayes’25 \[hayes2025strong\] & membership & extraction & LiRA
(reference) & direct (zero-order) correlation & MIA ≠ extraction  
Al Sahili’25 \[alsahili2025effectiveness\] & extraction (targeted) &
ref-free + AdaBoost & ranking precision; ensemble & marginal gains over
likelihood  
**This work** & **extraction** & **ref-free calibrated** & **partial
corr. + mediation (control loss)** & **zero/negative residual beyond
loss**  

</div>

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
Section <a href="#sec:relatedwork" data-reference-type="ref" data-reference="sec:relatedwork">4</a>.
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
(Section <a href="#sec:dp" data-reference-type="ref" data-reference="sec:dp">4.5</a>),
not implemented, since it is a producer-side defense applied at training
time rather than an auditor-side detector.

This section fixes the threat model, methods, data, and metrics; the
empirical results under this protocol—per-detector TPR at low FPR with
log-scale ROC, extraction rates, and the headline contamination→leakage
correlation with confidence intervals—are reported in the results
section, with every reported number tracing to a logged harness run.

# Results

**All results in this section are preliminary, obtained on Pythia-160M
on CPU with *N* = 300 ground-truth Pile members (seed 0); larger-model
rows are left for the GPU replication.** Every number is reproducible
from a seeded script and recorded in our results ledger.

## Membership separation is at chance on a confound-clean split

We first reproduce, as a control, the known weakness of membership
inference on pre-trained LLMs \[duan2024mia\]. On a confound-clean split
(members = Pile train, non-members = Pile validation, stratified across
22 Pile subsets to match domain), all four detectors sit at chance at
160M
(Table <a href="#tab:membership" data-reference-type="ref" data-reference="tab:membership">1</a>);
on the temporally-confounded WikiMIA split the same model shows a
spurious 0.52–0.56, and a 1.4B model rises further—evidence that the
WikiMIA signal is substantially distribution shift, not membership.

<div id="tab:membership">

| Construction (model)            | LOSS  | Min-K% | Min-K%++ | zlib  |
|:--------------------------------|:-----:|:------:|:--------:|:-----:|
| Pile train-vs-val, clean (160M) | 0.454 | 0.470  |  0.490   | 0.484 |
| WikiMIA-64, confounded (160M)   | 0.523 | 0.539  |  0.545   | 0.564 |
| WikiMIA-64, confounded (1.4B)   | 0.571 | 0.580  |  0.547   | 0.616 |

Membership AUC. Chance ( ≈ 0.5) on the confound-clean split at 160M; the
WikiMIA “signal” is largely temporal/topical distribution shift. CIs in
the ledger; deduplicated Pythia gives the same chance-level result.

</div>

## Contamination predicts leakage — but only through loss

Our headline analysis correlates each per-item detector score with the
per-item extraction outcome (prefix-continuation extractable
memorization under greedy decoding \[carlini2023quantifying\]), then
controls for raw loss.
Table <a href="#tab:headline" data-reference-type="ref" data-reference="tab:headline">2</a>
reports, for each calibrated detector, the zero-order Spearman *ρ*, the
linear partial *ρ* given loss, the non-linear (cubic-residual) partial
*ρ* with bootstrap CI, the FDR-corrected permutation *q*, and the
mediation decomposition.

<div id="tab:headline">

| Detector | zero-order | partial∣loss |     cubic-resid. \[95% CI\]     |  BH-*q*   | mediation: direct ∣ indirect |
|:---------|:----------:|:------------:|:-------------------------------:|:---------:|:----------------------------:|
| LOSS     |   + 0.275  |      —       |                —                |     —     |          (mediator)          |
| Min-K%   |   + 0.173  |    − 0.178   |  − 0.110 \[ − 0.234,  − 0.002\] |   0.058   |      − 0.394 ∣  + 0.567      |
| Min-K%++ |   + 0.108  |    − 0.148   |  − 0.160 \[ − 0.287,  − 0.041\] | **0.015** |      − 0.213 ∣  + 0.321      |
| zlib     |   + 0.177  |    − 0.042   |  − 0.052 \[ − 0.165,  + 0.068\] |   0.331   |      − 0.061 ∣  + 0.238      |

Headline: per-item contamination score vs. extraction (Spearman *ρ*),
Pythia-160M, *N* = 300 members. The positive zero-order correlations
collapse to  ≈ 0 or significantly *negative* once loss is
controlled—linearly, and under the non-linear cubic-residual control (no
positive signal revives; deciles and the deduplicated arm agree).
Mediation: the loss-mediated *indirect* effect is significantly positive
for all three detectors while the *direct* effect is null (zlib) or
negative (Min-K%, Min-K%++). We read this as a *descriptive*
decomposition, not a causal mediation claim (see below): no calibrated
detector adds positive signal beyond loss.

</div>

#### Collinearity caveat (why we do not over-read the negative partials).

The calibrated detectors are deterministic transforms of the same
per-token log-probabilities as loss, and are empirically collinear with
it: Spearman *ρ*(loss,  ⋅ ) = 0.90 (Min-K%), 0.74 (Min-K%++), 0.74
(zlib), with variance-inflation factors 6.2, 2.6, 2.4. The strongest
negative partial (Min-K%, the most loss-collinear detector at VIF 6.2)
is therefore consistent with a *suppression artifact* of
near-collinearity rather than substantive inverse prediction; we do not
claim the calibrated detectors *negatively* predict leakage. The
defensible, conservative statement is that they carry *no positive*
leakage signal independent of loss. Min-K%++ and zlib have only moderate
collinearity (VIF  &lt; 3), so their null/near-null residuals are less
attributable to collinearity.

The pre-registered decision rule asked whether any calibrated detector
predicts leakage *beyond* loss (a positive partial *ρ*, CI excluding
zero, FDR-significant). None does, under the linear or the non-linear
control. **Power note:** with *N* = 300 and a near-degenerate outcome
(3/300 fully extracted), this is evidence of *no positive independent
signal of appreciable size*, not proof of an exact null; the analysis is
well-powered only for moderate-to-large positive residuals, and a small
positive effect at scale is not excluded (hence the GPU replication).
The per-domain breakdown (ledger) shows the loss↔extraction link is
heterogeneous and sign-flipping across domains—strongest in
templated/structured domains (GitHub, StackExchange), reversed in some
prose domains (PubMed Abstracts)—so the pooled *ρ* is a domain-mixture,
not a uniform effect.

## Extraction and PII at this scale

Extractable memorization is rare at 160M: 3/300 members are fully
extractable (exact-match extraction rate 0.010; mean fractional
extraction 0.037), the fully-extracted items being templated
boilerplate. On the Enron-Emails-in-Pile subset we measured *zero*
verbatim PII leakage (8/36 documents contained PII in the held suffix;
none were regurgitated). We report the PII result as a null at this
scale and make no PII-exposure claim; both quantities are expected to
grow with model scale.

## Benchmark contamination (model-free *n*-gram + permutation test)

We complement the per-item analysis with two benchmark-level
contamination tests
(Table <a href="#tab:matrix" data-reference-type="ref" data-reference="tab:matrix">3</a>).
The model-free *n*-gram overlap against a public *sample* of the Pile
(10k documents) is a scale-invariant method but, with a sampled
reference, yields only a loose *lower bound*: overlap is near-zero for
MMLU (0.2% at 13-grams), GSM8K (0%), and HumanEval (0% at 13-grams),
which certifies overlap is *at least* this small and is uninformative
about true contamination—a full-Pile index (infrastructure-, not GPU-,
gated) is required for a real rate. The Oren permutation/exchangeability
test \[oren2024proving\] at 160M finds the canonical ordering favoured
beyond chance for MMLU (*p* = 0.001) and GSM8K (*p* = 0.013) but not
HumanEval (*p* = 0.875); we draw *no* contamination conclusion from
this, as the test is membership-based, run at sanity scale (small *k*,
smallest model), and subject to a fluency/orientation artifact—it is
flagged GPU-gated and requires a fluency-control baseline before any
claim.

<div id="tab:matrix">

| Benchmark | 13-gram overlap (lower bound) | 8-gram overlap | Oren *p* (160M, sanity) |
|:----------|:-----------------------------:|:--------------:|:-----------------------:|
| MMLU      |             0.2%              |      0.8%      |          0.001          |
| GSM8K     |             0.0%              |      0.0%      |          0.013          |
| HumanEval |             0.0%              |      1.8%      |          0.875          |

Benchmark-level contamination at small scale. *n*-gram cells are a
*lower bound* against a 10k Pile sample (method scale-invariant,
reference under-powered); Oren *p*-values are sanity-scale at 160M and
GPU-gated (no contamination conclusion drawn). See
`docs/contamination_matrix.md`.

</div>

# Discussion

#### Membership detection and leakage prediction diverge.

The central empirical observation is that the contamination/membership
signal which predicts *extraction* is, to the resolution of our
experiment, *just raw loss*. The reference-free detectors that the
contamination-detection literature has invested in—Min-K%, Min-K%++,
zlib—improve membership ranking by re-calibrating the per-token
likelihood (z-scoring against the vocabulary, compressing, or trimming
to the lowest-probability tokens), but in doing so they discard
precisely the loss-magnitude information that tracks how extractable an
item is. A descriptive mediation decomposition is consistent with
this—the loss-mediated (indirect) path is positive for all three
detectors while the direct paths are null or negative—but we read it
descriptively, not causally: the detectors are near-collinear transforms
of loss (Spearman up to 0.90; VIF up to 6.2), so a negative
direct/partial term is consistent with statistical suppression rather
than genuine inverse prediction. We therefore claim only the
conservative version: the calibrated detectors add *no positive* leakage
signal beyond loss. A practitioner who wants to know *which contaminated
items the model will actually leak* is, on this evidence, no better
served by a state-of-the-art membership detector than by raw loss. This
is the sense in which membership detection and leakage prediction are
different tasks.

#### Why this is a security result, not a leaderboard result.

Our finding is deliberately *not* “we built a better detector.” It is
that the privacy question—will contamination of a benchmark expose a
leakage channel?—is mis-served by importing the membership-inference
toolkit wholesale. For an auditor of a released model, the actionable
implication is to measure loss/extractability directly and to treat a
high Min-K%/Min-K%++ score as evidence about membership, not about
leakage risk. This reframing is the contribution; the detectors
themselves are prior work.

#### Relation to concurrent work.

Our direction agrees with two recent results and we do not claim the
bottom line is surprising: Al Sahili et
al. \[alsahili2025effectiveness\] report only “marginal” gains of MIA
scores over likelihood ranking for targeted extraction, and Hayes et
al. \[hayes2025strong\] find no correlation between (LiRA) membership
success and extraction. We add the controlled, mechanistic form of the
claim—a pre-registered partial-correlation/mediation that quantifies a
*zero-to-negative* residual for the calibrated reference-free detectors
after loss is removed—and we target the reference-free detectors the
contamination literature actually deploys rather than a shadow-model
attack. Chen et al. \[chen2025statistical\] independently find these
detectors do not robustly beat the loss baseline for *membership* once
seed variance is accounted for; our result is the extraction-outcome
analogue.

#### Defenses.

Because the leakage we measure is downstream of memorization, the
principled mitigation is differential privacy applied at training
time \[abadi2016deep,li2022dpllm\]; it is a producer-side control, not
an auditor-side detector, and bounds the very quantity (loss-magnitude /
memorization) our analysis identifies as the operative one.

# Limitations

We state the limitations plainly; several bound the strength of the
present claims and motivate the GPU-scale replication the pipeline is
built for.

-   **Single, smallest model.** All results are on Pythia-160M (CPU).
    Memorization grows log-linearly with model
    scale \[carlini2023quantifying\], so both the membership signal and
    the extraction outcome are expected to be stronger at 1.4B–12B. The
    present numbers are *preliminary*; we have built every analysis so
    the larger-model run is a one-line configuration change.

-   **Chance-level membership separation.** On the confound-clean Pile
    train-vs-val split, membership AUC is at chance (0.45–0.49) at 160M,
    consistent with \[duan2024mia\]. The divergence result is therefore
    established in a regime where the membership signal is itself weak;
    whether the calibrated detectors gain *independent*
    leakage-predictive value once membership separation becomes
    non-trivial at scale is an open question our design is poised to
    answer.

-   **Near-degenerate extraction outcome.** Extractable memorization at
    160M is rare (3/300 items fully extracted; mean fractional
    extraction 0.037), so the correlation analysis leans on a small
    high-extraction tail. We mitigate with rank statistics, bootstrap
    CIs, and a zero-robust Kendall check, but a less zero-inflated
    outcome at scale would sharpen all estimates.

-   **PII not yet demonstrated.** On the Enron-in-Pile subset we
    observed *zero* verbatim PII leakage at 160M (8/36 documents
    contained PII in the held suffix; none were regurgitated). The PII
    limb of the threat model is thus a designed capability with a null
    result at this scale, not a demonstrated leak; we report it as such
    and do not claim PII exposure.

-   **Benchmark-level test underpowered.** The Oren
    permutation/exchangeability test is run only at sanity scale on
    160M; membership-based, it is underpowered here and is flagged as
    GPU-gated rather than used to draw contamination conclusions.

-   ***n*-gram contamination is a lower bound.** Our model-free *n*-gram
    overlap uses a public *sample* of the Pile as the reference index,
    so measured benchmark↔Pile overlap underestimates the true overlap
    against the full corpus.

-   **Observational, members-only correlation.** The headline analysis
    correlates detector scores with extraction across known members; it
    is observational, not interventional. We address the most important
    confound (loss) by pre-registered partial correlation and mediation,
    and the obvious alternatives (frequency, duplication, non-linearity,
    distribution shift) by explicit controls, but residual confounding
    cannot be excluded.

-   **Collinearity of detectors with loss.** The calibrated detectors
    are deterministic transforms of the same per-token log-probabilities
    as loss and are empirically collinear with it (Spearman 0.74–0.90;
    VIF up to 6.2 for Min-K%). Consequently we interpret the negative
    partial/direct terms as possible *suppression artifacts* of
    near-collinearity and claim only the conservative “no positive
    residual” result; we do not assert the detectors inversely predict
    leakage.

-   **Construct validity of the leakage proxy.** The outcome (greedy
    prefix-continuation extraction over the held suffix) is itself
    likelihood-related, so part of the loss↔ extraction association is
    mechanical/definitional. Our control removes the loss component, but
    a decisive separation would compute prefix-only loss against
    extraction; we flag this as a known construct-validity limitation
    rather than claiming the two are independent by construction.

-   **Selection and aggregation.** Members are drawn from a non-uniform
    public Pile sample (`pile-10k`), so member-selection bias is
    possible; and the pooled correlation aggregates domains whose
    effects flip sign
    (Section <a href="#sec:res-headline" data-reference-type="ref" data-reference="sec:res-headline">6.2</a>),
    so the pooled *ρ* should be read as a domain-mixture, not a
    homogeneous effect.

-   **Linearity (now addressed).** An earlier version controlled for
    loss only linearly; we added a cubic-residual and decile-stratified
    non-linear control, under which no positive independent signal
    revives. We note it here because it was a live threat to the claim
    until tested.

# Conclusion

We argued that benchmark contamination is best understood as a
privacy/security vulnerability and asked, on models with ground-truth
public training data, whether the contamination/membership signal that a
benchmark leaks actually predicts concrete extraction. Using a
pre-registered partial-correlation and mediation analysis that controls
for raw per-item loss, we found that it does—but only through loss: the
calibrated reference-free detectors (Min-K%, Min-K%++, zlib) add no
independent predictive value beyond loss, and two are negatively
associated with extraction once loss is held fixed. The result is robust
to a non-linear loss control and to deduplication, and is not a
frequency or zero-inflation artifact. The practical message is a
divergence: the detectors optimized for membership inference are not the
right instrument for the leakage question, and an auditor should measure
loss/extractability directly. We claim no new detector or metric; the
contribution is the security reframing and the controlled,
pre-registered measurement. These findings are preliminary, on the
smallest Pythia model; the immediate next step—and the design target of
our released pipeline—is the GPU-scale replication across model sizes,
where memorization, extraction, and any PII leakage are expected to
strengthen, and where the question of whether calibrated detectors gain
independent leakage-predictive value at scale can be settled.
