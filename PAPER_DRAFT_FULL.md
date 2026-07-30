Large language models are ranked and certified as safe using public
benchmarks, and that practice is only valid if the benchmark was absent
from pre-training. When a benchmark does appear in the training corpus,
a condition known as *benchmark contamination*, the usual concern is
that scores overstate capability. A growing line of argument treats
contamination instead as a privacy warning sign, on the reasoning that
contamination reveals *memorization*, and that memorization is the
mechanism by which sensitive training content escapes. That reasoning is
rarely stated precisely, and contamination and sensitive-data leakage
are distinct phenomena, so we begin by decomposing it into four explicit
assumptions and identifying which are empirically testable. Our
experiments target the first and most basic of them: that a
contamination score reflects retention of a *specific* item rather than
how intrinsically predictable that item is. We test it on Pythia models
trained on the public Pile, so that training-set membership is ground
truth rather than an inferred label, and we compare four existing
reference-free detectors (LOSS, Min-K%, Min-K%++, and a compression
ratio) against a per-item extraction outcome. We propose no new
detector, attack, or metric. Our contribution is a controlled
measurement of *incremental* value: a pre-registered partial-correlation
and mediation analysis that asks what each detector predicts once the
model’s per-item loss is held fixed. The three adjusted detectors add no
positive predictive value beyond loss. They are near-collinear with it
(Spearman 0.74 to 0.90), and their residual associations are null or,
for the most loss-collinear detector, weakly negative in a manner
consistent with a statistical suppression artifact rather than genuine
inverse prediction. The absence of positive residual survives non-linear
controls for loss and survives deduplication, and is not explained by
token frequency or by the mostly-zero outcome. We read this as a
measurement-validity result: the detectors an auditor can afford carry
little information about *which* items leak that loss does not already
carry, which bounds what detector-based contamination auditing can
support. We do not demonstrate leakage of sensitive information. A PII
measurement on the Enron Emails subset of the Pile returned no detected
leakage at our scale, and we report that null rather than treating the
sensitive-data link as established. **These results are preliminary,
obtained on the smallest (160M) Pythia model on CPU, which is the regime
least likely to exhibit memorization. The pipeline is built so that
replication at larger scale is a single configuration change.** All
analyses are pre-registered and every number is reproducible from a
seeded script.

# Introduction

## Benchmarks, and the assumption they depend on

Large language models (LLMs) are compared, selected, and increasingly
certified as safe on the basis of their scores on public test sets
called *benchmarks* (Cobbe et al., 2021; Hendrycks et al., 2021). A
benchmark is a fixed collection of questions with known answers. A model
that answers more of them is taken to be more capable.

That inference depends on one assumption: the model must not have seen
the benchmark during training. If it has, a high score may reflect
recall of the answer rather than the ability the benchmark was built to
measure. The presence of evaluation data inside a model’s training
corpus is called *benchmark contamination* (Golchin & Surdeanu, 2024).

Contamination is now difficult to avoid. Benchmarks are small, fixed,
and copied widely across the web once published. Training corpora are
enormous and lightly filtered, assembled at the scale of hundreds of
gigabytes to petabytes (Common Crawl Foundation, n.d.; Gao et al.,
2020). Benchmark items are therefore drawn into the next crawl through
ordinary redistribution, with no adversary and no misconduct required.
The research community treats this primarily as a measurement-hygiene
problem, on the grounds that a contaminated score overstates
capability (Ravaut et al., 2024).

## Why this is also a privacy and security question

There is a second consequence that the hygiene framing sets aside. The
mechanism that makes a contaminated benchmark score untrustworthy is
*memorization*: the model has retained information specific to
individual training examples rather than only the general patterns
across them. Memorization is also the mechanism behind a known privacy
failure. Models trained on web-scale corpora can reproduce training text
word for word, including personal information such as names, addresses,
and contact details (Carlini et al., 2021; Carlini et al., 2023).

This suggests an appealing argument: because contamination is easy to
look for and sensitive-data leakage is not, perhaps a cheap
contamination signal can act as an early warning for leakage risk. If
so, contaminating a benchmark would not merely distort a leaderboard. It
would expose a measurable channel into the training data.

We want to be careful here, because this argument is not automatic, and
stating it loosely has consequences for what the resulting measurements
mean. Contamination and sensitive-data leakage are related but genuinely
distinct phenomena. Contamination concerns *evaluation* data appearing
in a training corpus. Leakage concerns a model *emitting* sensitive
content. One does not imply the other. Benchmark items are in fact
usually public and non-sensitive by construction, so a contaminated
benchmark is not itself a privacy harm. Any bridge between the two must
be built from explicit premises about a shared underlying mechanism.

Section <a href="#sec:chain" data-reference-type="ref" data-reference="sec:chain">2.5</a>
therefore sets out that bridge as four named assumptions (A1 through A4)
rather than as a claim, and states plainly which of them this paper
tests, which it inherits from prior work, and which remain untested. The
short version is that our experiments bear on the first link, whether a
contamination score reflects item-specific retention at all, and that
the link from retention to *sensitive* content remains an assumption of
the framing rather than a finding of this paper.

## The practical problem: which instrument should an auditor trust?

Suppose you want to know whether a model has memorized a particular
document. The direct test is to try to make the model reproduce it,
which requires generating text and comparing it against the original.
That is expensive at corpus scale and requires possessing the document
already.

The cheaper alternative, and the one widely used in practice, is a
*detector*: a score computed from the model’s own reported probabilities
for the text, with no retraining and no reference models. Several such
detectors exist, and Section
<a href="#sec:concepts" data-reference-type="ref" data-reference="sec:concepts">2.4</a>
defines each one before we use it. The simplest is the model’s *loss* on
the text, which measures how unsurprised the model is by it. Others
(Min-K%, Min-K%++, and a compression-based ratio) are transformations of
the same per-token probabilities, designed to separate training members
from non-members more sharply than loss alone.

These detectors are developed and ranked by how well they answer a
membership question: was this text in the training data? But an auditor
concerned with privacy wants the answer to a different question: how
much of this specific item has the model retained, and would it come
back out? Those two questions need not have the same answer, and the
distinction has been noted before. Hayes et al. (2025) report no
correlation between a strong membership attack’s success and extraction
on the models they study, and suggest the two capture different signals.

Our question is the one that follows from theirs, and it is a question
about measurement validity rather than about attack strength. If the
detectors an auditor would actually reach for are all computed from the
same per-token probabilities as loss, do they carry any information
about leakage that loss does not already carry? This matters because it
determines whether detector-based auditing can be trusted to tell you
*which* items are at risk, or only whether contamination happened at
all.

## Research questions

-   **RQ1 (conceptual validity).** Under what assumptions can a
    contamination score serve as an indicator of memorization, and
    further as an indicator of sensitive-information leakage? Which of
    those assumptions are empirically testable in a setting where
    training-set membership is known with certainty?

-   **RQ2 (incremental predictive value).** Do the widely used detectors
    provide information about which individual items a model has
    memorized, over and above what the model’s per-item loss already
    provides?

-   **RQ3 (choice of instrument).** Do the adjustments that make a
    detector better at membership discrimination also make it better at
    predicting leakage, or do the two objectives come apart?

## Approach in brief

We study Pythia models (Biderman et al., 2023), which were trained on
The Pile (Gao et al., 2020), a corpus that is public. This is the
central design choice of the paper and
Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">5</a>
defends it in detail. Because the corpus is published, we can look up
whether a document was genuinely in the training data instead of
inferring it. Membership is therefore ground truth, which removes the
largest source of error in this literature, namely that a detector can
appear to succeed because the member and non-member texts differ in
topic or era rather than in membership (Duan et al., 2024).

For each document we compute the detector scores, and separately measure
a concrete leakage outcome: given the first part of the document, does
the model reproduce the rest (Carlini et al., 2023)? We then ask whether
the detector scores predict that outcome once the model’s loss is held
fixed.
Section <a href="#sec:concepts" data-reference-type="ref" data-reference="sec:concepts">2.4</a>
explains what "holding loss fixed" means and why it is the right
comparison, and
Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">5</a>
explains why we pre-committed to the analysis in writing before running
it.

## Contributions, and explicit non-contributions

We are deliberate about what this paper is not. It introduces no new
detector, no new attack, and no new metric. Every detection method we
run is from prior work (Brown et al., 2020; Carlini et al., 2021; Oren
et al., 2024; Shi et al., 2024; Yeom et al., 2018; J. Zhang et al.,
2025). We do not train or fine-tune models, and we do not attack
deployed systems for real third-party personal data. Within that scope:

-   **An explicit conceptual bridge, stated as assumptions.** We replace
    the usual one-line assertion that contamination indicates leakage
    risk with four named assumptions, and we identify which are
    testable, which we test, and which the field currently takes on
    faith
    (Section <a href="#sec:chain" data-reference-type="ref" data-reference="sec:chain">2.5</a>).
    This makes the framing falsifiable and bounds what any
    contamination-based privacy claim can support.

-   **A ground-truth comparison of existing detectors as leakage
    predictors.** On Pythia and The Pile, where membership is known, we
    evaluate the detectors both as membership classifiers and as
    predictors of a per-item extraction outcome, using the
    low-false-positive reporting convention that privacy work
    expects (Carlini et al., 2022) and controlling for the frequency,
    duplication, and distribution-shift confounds that prior work
    identifies (Biderman et al., 2023; Duan et al., 2024).

-   **A controlled measurement of incremental value, which is the
    paper’s core result.** Using an analysis fixed in advance, we ask
    whether each detector predicts leakage after the model’s per-item
    loss is accounted for. In our setting the detectors add no positive
    predictive value beyond loss. They are close to being mathematical
    restatements of loss, which we quantify directly, and we therefore
    read the result as a measurement-validity finding: these instruments
    carry little information about *which* items leak that loss does not
    already carry.

#### What we do not claim.

We do not claim to demonstrate leakage of sensitive or personal
information. We attempted such a measurement on the Enron Emails subset
that sits inside The Pile, and it returned no detected leakage at the
scale we could run
(Section <a href="#sec:results" data-reference-type="ref" data-reference="sec:results">6</a>).
We report that null honestly and treat the step from memorization to
*sensitive* content as an untested assumption (A3 and A4 in
Section <a href="#sec:chain" data-reference-type="ref" data-reference="sec:chain">2.5</a>)
rather than as a result. We also do not claim a stronger attack than
prior work, and we do not claim that the detectors are *worse* than
loss, only that we find no evidence they are better.

#### Preliminary scope.

The results reported here come from the smallest Pythia model, at 160
million parameters, run on a CPU. Memorization increases with model
scale (Carlini et al., 2023), so this is the regime least likely to show
leakage, and we flag every affected conclusion as preliminary. The
pipeline was built so that repeating everything on larger models is a
change of one configuration value.

## Roadmap

Section <a href="#sec:background" data-reference-type="ref" data-reference="sec:background">2</a>
explains benchmarks, memorization, and every technical term and
statistical tool this paper uses, and then states the assumption chain
that connects contamination to leakage.
Section <a href="#sec:threat" data-reference-type="ref" data-reference="sec:threat">3</a>
defines the threat model.
Section <a href="#sec:relatedwork" data-reference-type="ref" data-reference="sec:relatedwork">4</a>
positions the work against prior contamination, memorization, and
membership-inference research.
Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">5</a>
gives the experimental design and the reasoning behind each
methodological choice.
Section <a href="#sec:results" data-reference-type="ref" data-reference="sec:results">6</a>
reports results,
Section <a href="#sec:discussion" data-reference-type="ref" data-reference="sec:discussion">7</a>
interprets them, and
Section <a href="#sec:limitations" data-reference-type="ref" data-reference="sec:limitations">8</a>
states the limitations.

# Background and Key Concepts

## Benchmarks as proxies for capability

LLM benchmarks act as *proxies* for abilities that cannot be measured
directly, such as reasoning, comprehension, factual recall, and
programming skill. By scoring a model on a fixed set of standardized
tasks, the community infers how useful, and increasingly how safe, that
model is likely to be in deployment (Hendrycks et al., 2021). Familiar
examples target distinct competencies: MMLU covers multitask knowledge
across 57 subjects (Hendrycks et al., 2021), GSM8K covers multi-step
arithmetic word problems (Cobbe et al., 2021), and HumanEval covers
functional code generation (M. Chen et al., 2021). Scores on these
suites drive model selection, leaderboard position, and public claims of
progress.

## The validity assumption, and what breaks when it fails

The inference from benchmark score to capability rests on one strict
assumption: *the test data was not seen during training*. Only then does
a high score support the intended conclusion, that the model
*generalizes*, meaning it applies learned regularities to inputs it has
not encountered, rather than *memorizes*, meaning it reproduces specific
training instances.

When the assumption fails, the benchmark stops measuring what it claims
to measure. A memorized test item raises the score with no corresponding
gain in ability, so the metric becomes an unreliable estimate of the
underlying construct. This distinction is not only conceptual.
Memorization is directly measurable as verbatim regeneration of training
text, and it grows predictably with model size, with how often a
sequence was duplicated in training, and with how much context the model
is given (Carlini et al., 2023). A closely related privacy-facing
measurement plants a secret in the training data and records how
strongly the model prefers it over random alternatives, which rises with
the number of times the secret was seen (Carlini et al., 2019).
Memorization is also highly uneven across examples rather than a uniform
background rate, so which particular items a model memorizes is itself a
measurable per-example property (C. Zhang et al., 2023).

## Static test sets meet weakly filtered corpora

The structural tension is that benchmarks and training corpora have
opposite properties. Benchmarks are static, small, widely circulated,
and publicly indexed. Once an MMLU or GSM8K item is published it is
copied into papers, blog posts, code repositories, and forum
discussions. Training corpora are the reverse: very large web scrapes
with light filtering. Common Crawl (Common Crawl Foundation, n.d.) and
The Pile (Gao et al., 2020) are assembled at the scale of hundreds of
gigabytes to petabytes, where reliably removing any particular short
string is impractical.

The consequence is that benchmark items enter training corpora through
ordinary redistribution, with no adversary required. A public benchmark
is therefore a persistent and low-effort exposure surface, because the
very properties that make a benchmark useful (stable, shared, citable)
are what make its eventual presence in a future crawl likely.

## Key concepts and methodological tools

This subsection defines every technical idea used later in the paper.
Each entry states what the concept is, why the study needs it, and how
it bears on the research questions of
Section <a href="#sec:intro" data-reference-type="ref" data-reference="sec:intro">1</a>.

### Token probabilities, loss, and perplexity

A language model reads text as a sequence of *tokens*, which are words
or word fragments. At each position it produces a probability
distribution over which token comes next. Given a real text, we can
therefore ask what probability the model assigned to each token that
actually occurred.

The *loss* of a text is the average negative logarithm of those
probabilities. Low loss means the model found the text unsurprising.
*Perplexity* is the exponential of the loss and carries the same
information in a different scale, so we use loss throughout. Every
detector in this paper is computed from these same per-token
probabilities, which is the fact that ultimately drives our result.

*Why this is needed.* Loss is the oldest and simplest membership signal,
on the reasoning that a model tends to find its own training data less
surprising than new text (Yeom et al., 2018). It is also the natural
baseline against which any more elaborate detector must prove its worth,
which makes it the control variable in RQ2.

### Memorization and how leakage is measured

We use the standard operational definition of *extractable
memorization* (Carlini et al., 2023). Take a document from the training
data, split it into a *prefix* and a *suffix*, and give the model only
the prefix. Then let the model continue the text by repeatedly choosing
its single most probable next token, a procedure called *greedy
decoding*. If the continuation reproduces the suffix, the suffix is
*extractable*: the model has retained enough about this specific
document to regenerate it.

We report two versions of this outcome. *Exact extraction* is whether
the whole suffix was reproduced. *Fractional extraction* is the
proportion of leading suffix tokens reproduced before the first
mismatch, which is a softer measure and is much less prone to being zero
for every item.

*Why this is needed.* This is our concrete leakage outcome, and the
quantity detectors must predict if they are to be useful for privacy
auditing. It is a lower bound on leakage rather than a complete account,
because a determined adversary may use richer prompting than a single
prefix (Nasr et al., 2025), and because rewording can preserve leaked
content while defeating exact matching (Ippolito et al., 2023).

### Personally identifiable information

*Personally identifiable information* (PII) is content that identifies a
specific person, such as a name paired with an email address, a phone
number, or a postal address. Leakage of PII from training data is the
canonical privacy harm in this literature (Carlini et al., 2021), it
decomposes into distinct extraction, reconstruction, and inference
threats (Lukas et al., 2023), and models leak it more through
memorization than through inference about individuals (Huang et al.,
2022).

*Why this is needed.* PII is the harm that motivates the security
framing. It is also the point where we must be most careful about scope,
because benchmark items are generally not PII-bearing.
Section <a href="#sec:chain" data-reference-type="ref" data-reference="sec:chain">2.5</a>
makes this gap explicit.

### Membership inference, and the detectors we evaluate

*Membership inference* asks whether a particular piece of text was part
of a model’s training data (Shokri et al., 2017). A *detector* assigns
each text a score intended to be higher for training members.

Detectors divide by what they require. *Reference-based* methods compare
the target model against other models trained on similar data, which is
accurate but requires training those extra models and is therefore
infeasible at the scale of a corpus like The Pile (Carlini et al.,
2022). *Reference-free* methods need only the target model’s own token
probabilities. Reference-free methods are what a real auditor can
afford, so they are the family we study. We evaluate four:

-   **LOSS.** The average per-token loss described above, used directly
    as the score (Yeom et al., 2018). This is the baseline.

-   **Min-K%.** Rather than averaging over all tokens, average only over
    the *k*% of tokens the model found *least* likely. The motivation is
    that a text the model has seen should lack highly surprising outlier
    tokens, so focusing on the worst tokens should sharpen the
    distinction (Shi et al., 2024). We use *k* = 20.

-   **Min-K%++.** A refinement that, before selecting the least likely
    tokens, rescales each token’s log-probability by the mean and
    standard deviation of the model’s full distribution at that
    position. This asks whether a token was unlikely *relative to the
    alternatives the model considered there*, rather than in absolute
    terms (J. Zhang et al., 2025). It needs the full next-token
    distribution and therefore assumes deeper access than the others.

-   **zlib ratio.** Divide the model’s loss by the length of the text
    after generic compression with the zlib algorithm. Compressed length
    is a model-independent estimate of how repetitive or formulaic a
    text is, so the ratio is intended to discount texts that are
    unsurprising merely because they are boilerplate (Carlini et
    al., 2021).

Throughout, we call the last three *calibrated* detectors, meaning only
that each adjusts raw loss by some additional quantity in an attempt to
improve separation. The word carries no claim that the adjustment is
probabilistically well calibrated.

*Why this is needed.* These four are the instruments an auditor would
actually use, and RQ2 asks whether the three adjusted ones add anything
to the plain baseline.

### Corpus-side and benchmark-level contamination tests

Two further tests operate on the corpus or the whole benchmark rather
than on the model’s probabilities for a single item.

**n*-gram overlap* searches the training corpus for exact matches of
contiguous *n*-token spans from a benchmark item, the convention
introduced with GPT-3 (Brown et al., 2020). Because it needs the corpus
rather than the model, we use it to build contamination labels rather
than as an attack. It provides a lower bound only, since reworded copies
do not match.

The *permutation*, or *exchangeability*, test asks whether a model
prefers a benchmark’s items in their original published order over
randomly shuffled orderings. A model trained on the benchmark file tends
to favour the canonical order, which yields a statistically calibrated
benchmark-level test (Oren et al., 2024).

*Why this is needed.* These give benchmark-level and corpus-level
evidence to complement the per-item model-side detectors, and they let
us report contamination status for real benchmarks independent of any
detector’s reliability.

### How privacy attacks should be evaluated

A detector produces a score, and turning it into a decision requires a
threshold. Varying the threshold traces a *receiver operating
characteristic* (ROC) curve, plotting the *true-positive rate* (the
fraction of real members flagged) against the *false-positive rate* (the
fraction of non-members wrongly flagged). The *area under the curve*
(AUC) summarizes the whole curve in one number, where 0.5 means no
better than chance.

Average-case AUC is a poor summary for a privacy threat, because an
attack matters if it identifies *some* members with very few false
accusations. The accepted convention is therefore to report the
true-positive rate at a low fixed false-positive rate, such as 0.1% or
1%, and to plot the ROC curve on logarithmic axes so that the
low-false-positive region is visible (Carlini et al., 2022). We follow
that convention and treat AUC as secondary.

*Why this is needed.* It is the reporting standard that privacy and
security venues expect, and it prevents a detector that never fires
confidently from looking successful.

### Statistical tools for isolating incremental value

RQ2 asks whether a detector adds predictive value *beyond* loss, which
is a question about incremental contribution rather than about raw
association. The following tools answer it, and each is used exactly as
defined here.

-   **Spearman rank correlation (*ρ*).** A measure between  − 1 and  + 1
    of how well two quantities increase together after each is replaced
    by its rank. Ranks make it insensitive to outliers and to any
    monotone rescaling, which matters because the detectors are on
    different and arbitrary scales.

-   **Partial correlation.** The correlation between a detector score
    and the leakage outcome *after statistically removing* the part of
    each that is predictable from loss. This is the precise meaning of
    "holding loss fixed". If a detector’s partial correlation is zero,
    it tells us nothing about leakage that loss had not already told us.
    This single quantity is the paper’s primary outcome measure.

-   **Collinearity.** Two variables are collinear when one is close to a
    rescaling of the other. We measure it with the correlation between
    loss and each detector, and with the *variance inflation factor*, a
    standard index of how much collinearity destabilizes a regression
    coefficient. Collinearity matters because it limits how confidently
    any residual effect can be interpreted.

-   **Suppression.** When two predictors are strongly collinear, the
    estimated coefficient of one can flip sign for purely algebraic
    reasons rather than because the relationship truly reverses. This is
    a known artifact, and it is why we interpret a negative partial
    correlation cautiously and claim only the absence of positive value.

-   **Mediation.** A descriptive decomposition of an association into
    the part that travels through an intermediate variable (here loss)
    and the part that does not. We use it only as description, not as a
    causal claim, because our design is observational.

-   **Non-linear controls.** Partial correlation removes only a linear
    relationship with loss. To check that nothing survives merely
    because the true relationship is curved, we repeat the analysis
    after removing a cubic function of loss, and again within narrow
    bands of similar loss values.

-   **Bootstrap confidence interval.** Repeatedly resample the items
    with replacement, recompute the statistic, and report the middle 95%
    of the results. This conveys how much the estimate would move with a
    different sample of the same size.

-   **Permutation test.** Randomly shuffle one variable many times to
    build the distribution of the statistic under no association, then
    locate the observed value in it. This yields a *p*-value without
    assuming the data are normally distributed.

-   **Multiple-comparison correction.** Testing several detectors at
    once inflates the chance of at least one false positive. We apply
    the Benjamini-Hochberg procedure, which controls the expected
    proportion of false discoveries among the findings declared
    significant.

-   **Zero inflation.** An outcome is zero-inflated when most
    observations are exactly zero, which weakens any correlation and
    widens its confidence interval. Our exact-extraction outcome is
    severely zero-inflated at small model scale, which is why we also
    report the fractional outcome.

-   **Pre-registration.** Writing the analysis plan down, in the
    repository, before running it. This prevents the outcome from being
    chosen after seeing the data, which is the main way a null result
    can be quietly converted into a positive one.

## From contamination to leakage: the assumption chain

The security framing of
Section <a href="#sec:intro" data-reference-type="ref" data-reference="sec:intro">1</a>
rests on a chain of reasoning from contamination to
sensitive-information leakage. Contamination and leakage are distinct
phenomena, and the chain is not automatic, so we state it as four
assumptions and then say which the paper tests. Writing them out serves
two purposes: it makes the framing falsifiable, and it bounds what any
contamination-based privacy claim is entitled to conclude.

The chain has the form
contamination → memorization → extractable output → sensitive leakage,
and each arrow needs a premise.

-   **A1 (signal validity).** A detector’s contamination score reflects
    *item-specific retention*, and not merely how intrinsically
    predictable the text is.  
    *Why it is needed.* If a score rises only because a text is generic
    or formulaic, it cannot separate "the model saw this item" from
    "this item is easy for any model", and it cannot indicate which
    items carry risk.  
    *Status.* Testable wherever membership is ground truth. **This is
    the assumption our experiments examine**, and RQ2 is its operational
    form. We test it in the strongest available way, by asking whether
    each detector predicts leakage after the text’s intrinsic
    predictability, as captured by loss, is held fixed.

-   **A2 (retention implies emission).** Content the model has retained
    can be elicited by a procedure an adversary could actually run.  
    *Why it is needed.* Retained but unreachable content is not a leak.
    A privacy claim requires that something come out.  
    *Status.* Partially supported by prior work and partially tested
    here. We use prefix-continuation with greedy decoding, which is one
    realizable procedure (Carlini et al., 2023) and a lower bound, since
    stronger prompting extracts more (Nasr et al., 2025).

-   **A3 (sensitivity co-occurrence).** The content a model memorizes
    includes sensitive information.  
    *Why it is needed.* This is the assumption that turns an evaluation
    problem into a privacy problem, and it is the weakest link.
    Memorizing a public MMLU question damages measurement validity but
    harms nobody’s privacy. Benchmark items are generally public and
    non-sensitive by construction.  
    *Status.* Testable in principle on a corpus with known sensitive
    content. We attempted it on the Enron Emails subset of The Pile and
    detected no leakage at our scale
    (Section <a href="#sec:results" data-reference-type="ref" data-reference="sec:results">6</a>),
    so for practical purposes it remains **untested here**. Prior work
    establishes that models can emit PII from web-scale corpora (Carlini
    et al., 2021; Lukas et al., 2023), which is why we regard the
    assumption as plausible rather than established.

-   **A4 (mechanism transfer).** The relationship measured on
    benchmark-like documents also holds for sensitive records.  
    *Why it is needed.* We measure on Pile documents, whereas the
    privacy claim concerns sensitive content. If memorization behaves
    differently for rare, unusually formatted, or seldom-duplicated
    strings, then a result about benchmark-like text does not
    automatically transfer.  
    *Status.* **Untested here**, and non-trivial. Memorization is known
    to be strongly example-dependent (C. Zhang et al., 2023) and to
    scale with duplication (Carlini et al., 2023), both of which argue
    against assuming free transfer.

#### What this means for the paper’s claims.

Our empirical work bears on A1, and secondarily on A2. We do not
establish A3 or A4, so we make no claim to have demonstrated
sensitive-data leakage, and we present the privacy framing as the
motivation for studying A1 rather than as a validated end-to-end result.
This matters for interpretation in a specific way. A1 is the chain’s
first plank, so evidence that it fails for the calibrated detectors
constrains every downstream privacy claim built on those detectors,
regardless of whether A3 and A4 hold. Conversely, and we state this
plainly, a positive result on A1 alone would not have demonstrated a
privacy harm either.
Section <a href="#sec:limitations" data-reference-type="ref" data-reference="sec:limitations">8</a>
returns to what would be required to test A3 and A4 directly.

# Threat Model

This section states who is acting, what they know, what they are trying
to achieve, and what counts as success. All technical terms used here
are defined in
Section <a href="#sec:concepts" data-reference-type="ref" data-reference="sec:concepts">2.4</a>.

## Two parties with different problems

Discussions of contamination often blur two roles that need separating,
because they have different access and different objectives.

The **auditor** is a defender. This is a model developer, an evaluation
organization, or an external reviewer who wants to know whether a
benchmark leaked into training and, more usefully, *which* specific
items a model has retained. The auditor is willing to run cheap tests
over many items and cannot afford to train reference models. The auditor
is the party this paper is really about, because the question of whether
a detector is a valid instrument is the auditor’s question.

The **adversary** is an attacker who wants to recover content from the
training data. The adversary needs only the deployed model and does not
need the training corpus.

A key asymmetry is that the auditor is trying to *predict* what the
adversary could extract, without performing the extraction on every
item. That is precisely why detector validity matters, and it is the
practical stake behind assumption A1 in
Section <a href="#sec:chain" data-reference-type="ref" data-reference="sec:chain">2.5</a>.

## Goals, in increasing order of harm

-   **G1: membership inference.** Decide whether one specific sequence,
    such as a benchmark item, document, or record, was in the training
    corpus.

-   **G2: benchmark-level contamination confirmation.** Decide, with a
    controlled false-positive rate, whether an entire benchmark was
    trained on.

-   **G3: extraction.** Cause the model to reproduce content that was in
    the training data. On a corpus with known sensitive content this is
    where privacy harm would occur.

G3 is the outcome that matters. G1 and G2 are of interest mainly insofar
as they predict G3, and whether they do is exactly what this paper
measures. Under the terminology of
Section <a href="#sec:chain" data-reference-type="ref" data-reference="sec:chain">2.5</a>,
a detector that achieves G1 but fails to predict G3 is a detector for
which A1 does not hold in the sense the privacy framing requires.

## Knowledge and access

We grade the detectors by the least access each one needs, using the
definitions from
Section <a href="#sec:concepts" data-reference-type="ref" data-reference="sec:concepts">2.4</a>:

-   **Black-box.** Text in, text out, with no probabilities. Guided
    prompting falls here. We do not evaluate black-box detectors.

-   **Gray-box.** The model’s per-token log-probabilities for a supplied
    text. LOSS, Min-K%, and the zlib ratio need only this.

-   **White-box.** The full next-token probability distribution at each
    position. Min-K%++ requires this, because it rescales each token
    against the alternatives the model considered.

The *n*-gram overlap test is different in kind, because it inspects the
training corpus rather than the model. We can run it only because The
Pile is public, and we use it to construct contamination labels rather
than as an attack an adversary could mount. Extraction (G3) requires
only the ability to prompt the model and read its output.

For our experiments the auditor additionally knows the training corpus,
which is what makes membership ground truth rather than an inference. We
treat this as a deliberate methodological advantage rather than a
realistic assumption, and
Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">5</a>
explains why studying a model whose corpus is public is the only way to
test A1 without confounding.

## Success criteria

-   **G1.** True-positive rate at 0.1% and at 1% false-positive rate,
    read from a logarithmic-axis ROC curve, with AUC reported as
    secondary and with bootstrap confidence intervals.
    Section <a href="#sec:concepts" data-reference-type="ref" data-reference="sec:concepts">2.4</a>
    explains why the low-false-positive operating point is the
    meaningful one for a privacy attack.

-   **G2.** A permutation-test *p*-value below a pre-specified
    threshold, with a controlled false-positive rate (Oren et
    al., 2024).

-   **G3.** A non-zero extraction rate, and then the paper’s central
    criterion: a *positive* association between a per-item detector
    score and the per-item extraction outcome that *survives holding the
    model’s loss fixed*, in the partial-correlation sense of
    Section <a href="#sec:concepts" data-reference-type="ref" data-reference="sec:concepts">2.4</a>.

The last criterion is the one that distinguishes a detector that
genuinely identifies which items are at risk from one that merely
restates the model’s loss in different units. We fixed this criterion in
advance of running the analysis, for the reason given under
pre-registration in
Section <a href="#sec:concepts" data-reference-type="ref" data-reference="sec:concepts">2.4</a>.

## Out of scope

We do not attack deployed production models for real third-party
personal data. We do not train or fine-tune models, and we propose no
new detector. We do not claim to demonstrate leakage of sensitive
information, since assumptions A3 and A4 of
Section <a href="#sec:chain" data-reference-type="ref" data-reference="sec:chain">2.5</a>
are untested here. Differential privacy is discussed as the
producer-side mitigation this threat model motivates
(Section <a href="#sec:dp" data-reference-type="ref" data-reference="sec:dp">4.5</a>)
and is not implemented or evaluated.

# Related Work: Contamination, Memorization, and Privacy Leakage

## Defining benchmark contamination

We adopt the standard definition: *benchmark contamination* is the
presence of evaluation data, inputs, labels, or accompanying metadata,
within a model’s pre-training corpus (Golchin & Surdeanu, 2024).
Contamination matters for two reasons that this paper treats as
inseparable. First, it invalidates evaluation: a contaminated score
conflates capability with retrieval, so the metric no longer estimates
generalization. Second, and central to our thesis, contamination is a
*symptom of, and a measurable proxy for, unintended memorization*, and
memorization of evaluation data sits on the same mechanism that leaks
sensitive content from the corpus. We make this
contamination → memorization → leakage chain the object of empirical
study.

## A typology of contamination

Following the project’s framing and the contamination-detection
survey (Ravaut et al., 2024), we distinguish three forms by the
transformation between the corpus copy and the benchmark item:

-   **Verbatim contamination.** The exact token sequence of a test item
    appears in training data. This is what classical *n*-gram
    decontamination targets (e.g., the 13-gram overlap test introduced
    for GPT-3 (Brown et al., 2020)) and what verbatim-extraction
    memorization measures (Carlini et al., 2023).

-   **Paraphrased contamination.** The semantic content is present but
    reworded, so surface-level *n*-gram matching misses it. A perfect
    verbatim filter provides only a false sense of safety, since
    style-transfer rephrasings evade it while preserving the leaked
    information (Ippolito et al., 2023).

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
undisclosed corpora (Touvron et al., 2023), motivating
ground-truth-controlled study on models whose corpus is fully public.

## Why memorization is a security and privacy problem

Memorization is not a benign curiosity. Over-parameterized models
trained on web-scale scrapes retain and can regurgitate verbatim
sequences, including personally identifiable information (PII) such as
names, emails, and phone numbers (Carlini et al., 2021). This has been
formalized along several axes that we reuse as outcome variables:

-   ***k*-eidetic / extractable memorization.** A string is extractable
    if a prefix makes the model regenerate it, and is *k*-eidetic if it
    occurs in at most *k* training documents (Carlini et al., 2021). The
    prefix-continuation form under greedy decoding makes this directly
    measurable (Carlini et al., 2023).

-   **Exposure and example-level memorization.** Injecting a canary
    secret and measuring its *exposure*, its rank against random
    alternatives, quantifies unintended memorization and its growth with
    occurrence count (Carlini et al., 2019). This requires control over
    the training process (canary insertion), which our
    pretrained-checkpoint setting does not afford, so we use it for
    definitions rather than as a measurement. Relatedly, memorization is
    concentrated on specific examples (C. Zhang et al., 2023) rather
    than spread uniformly, which is what makes per-item contamination
    scores meaningful predictors of per-item leakage.

-   **Extraction at scale.** Production models can be driven, via a
    divergence attack, to emit memorized training data well above their
    nominal aligned rate, recovering thousands of verbatim examples
    cheaply (Nasr et al., 2025).

-   **PII leakage games.** Leakage of personally identifiable
    information decomposes into extraction, reconstruction, and
    inference. Data scrubbing and differential privacy reduce but do not
    eliminate it (Lukas et al., 2023), models leak PII through
    memorization more than through associative inference (Huang et
    al., 2022), and black-box probing tools can elicit a data subject’s
    PII directly from a deployed model (Kim et al., 2023).

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
non-members from the target model’s outputs (Shokri et al., 2017). Yeom
et al. (2018) tied attack success to overfitting and gave the simplest
practical baseline (thresholding the per-example loss) together with the
*membership advantage* (TPR−FPR) figure of merit. Carlini et al.
(2022)’s *Likelihood Ratio Attack* (LiRA) then reframed MIA from first
principles as a per-example hypothesis test calibrated with shadow
models, and, central to our methodology, argued that average-case AUC is
the wrong yardstick for a privacy threat: an attack matters if it
identifies *some* members with very few false accusations, so the right
report is TPR at a low, fixed FPR on a log-scale ROC curve. Shadow-model
calibration, however, is infeasible at Pile/Pythia scale (it requires
training many models on the training distribution), so we adopt LiRA’s
*metric* but not its *attack*.

For pre-trained LLMs, the field moved to *reference-free* likelihood
signals that need no shadow models. Min-K% Prob averages the
log-probabilities of a sequence’s lowest-probability *k*% of tokens, on
the hypothesis that members lack high-surprise outlier tokens (Shi et
al., 2024). Min-K%++ sharpens this by *z*-scoring each token against the
*full* next-token distribution before averaging, detecting that the
target token sits at a local maximum of the modeled distribution (J.
Zhang et al., 2025). A parallel reference-free line, neighbourhood
comparison, calibrates a sample’s score against synthetically generated
neighbour texts instead of a reference model (Mattern et al., 2023). We
treat it as a related approach we do not evaluate, since it needs many
extra masked-LM forward passes per example and, in the regime below,
underperforms. The reality check on this whole line is the MIMIR study:
a large-scale audit on Pythia (160M–12B) and The Pile with controlled
member/non-member splits finds that these attacks barely exceed chance
(AUC  ≈ 0.5–0.6), that LLMs see their corpus for too few epochs over too
large a dataset to memorize in the way classical MIA assumes, and that
apparent successes frequently reflect a temporal or topical
*distribution shift* between the splits rather than membership (Duan et
al., 2024). This finding defines our honesty constraint: we do not claim
to beat these numbers. We ask whether the weak signal that remains still
predicts leakage.

## Differential privacy as the defense direction

The standard principled mitigation for training-data leakage is
differential privacy. DP-SGD bounds any single example’s influence on
the trained model by clipping per-example gradients and adding
calibrated noise, with privacy accounted via the moments
accountant (Abadi et al., 2016). Applied to language models, DP
fine-tuning can retain much of the utility of non-private training,
particularly with large pre-trained backbones (Li et al., 2022) and
parameter-efficient adaptation (Yu et al., 2022). DP bounds memorization
and thereby the leakage we measure, but at a privacy–utility cost and,
crucially for us, it must be applied *at training time*. It is a defense
for model producers, not a detector available to an auditor of an
already-released model. We therefore position DP as the mitigation our
threat model motivates, and do not implement it (we train no models).

## Existing detection techniques

We describe the techniques we implement and compare. The comparative
evaluation and the access requirements appear in
Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">5</a>.
All operate without any novel detector of our own, our contribution is
their security-framed, ground-truth evaluation, not a new method.

-   ***n*-gram / substring overlap.** Flag a benchmark item that shares
    an *N*-gram with the corpus (Brown et al., 2020). Requires corpus
    access, and misses paraphrased and semantic contamination.

-   **Loss / perplexity thresholding.** The mandatory
    membership-inference baseline: members exhibit lower loss, with
    attack success tied to overfitting (Yeom et al., 2018).

-   **Min-K% Prob.** Average the log-probabilities of the
    lowest-probability *k*% of tokens, reference-free and
    logprob-only (Shi et al., 2024).

-   **Min-K%++.** Normalizes each token’s log-probability against the
    full next-token distribution before the bottom-*k*% average, the
    current state of the art among reference-free detectors (J. Zhang et
    al., 2025).

-   **zlib-entropy ratio.** Calibrate model perplexity by the
    zlib-compressed size of the text, controlling for intrinsic
    compressibility/frequency (Carlini et al., 2021).

-   **Permutation / exchangeability test.** At the *benchmark* level
    rather than per item, score each ordering of a benchmark’s examples
    by the log-likelihood of their concatenation and compare the
    canonical (published) order against random shufflings. A model
    trained on the benchmark in canonical order favours it beyond
    chance, yielding a provable, FPR-controlled contamination
    certificate (Oren et al., 2024).

We additionally note two techniques we describe but *do not* evaluate,
since our ground-truth, logit-access setting makes likelihood-based
detectors stronger and cleaner: *guided prompting*, which prompts a
model with dataset metadata and a partial instance and tests for
verbatim completion (Golchin & Surdeanu, 2024), a black-box signal aimed
at closed models, and the reference-free *neighbourhood* and
shadow-model *reference* attacks discussed in
Section <a href="#sec:mia-lineage" data-reference-type="ref" data-reference="sec:mia-lineage">4.4</a> (Mattern
et al., 2023; Shokri et al., 2017).

## Limitations of existing detection, and our positioning

Two limitations frame our contribution. First, *detection is fragile to
the transformation*: string-matching misses paraphrased and semantic
contamination (Ippolito et al., 2023), and likelihood-based membership
inference is known to barely exceed chance on pre-trained LLMs evaluated
under controlled ground truth, because the corpora are seen for few
epochs and member/non-member boundaries are fuzzy (Duan et al., 2024).
Second, *evaluation conventions matter*: average-case AUC or accuracy
can mask whether an attack confidently identifies any members, so the
security-appropriate report is true-positive rate at low false-positive
rate with log-scale ROC (Carlini et al., 2022). We therefore do not
claim a stronger detector. We ask a different, security-relevant
question: *even where contamination signal is weak, does it predict
concrete privacy leakage?* We answer it with ground-truth membership on
the Pythia suite (Biderman et al., 2023) trained on the public Pile (Gao
et al., 2020), under the low-FPR protocol, with explicit controls for
the frequency, duplication, and temporal confounds that prior work
identifies.

## Closest prior work, and how we differ

Three recent works reach conclusions adjacent to ours, and we are
careful to position against them rather than overclaim. Al Sahili et al.
(2025) reach a compatible conclusion for targeted extraction, that
“complex MIA techniques yield only marginal improvements over simple
likelihood-based ranking,” but they establish it through aggregate
*ranking-precision* comparisons and an AdaBoost ensemble over MIA
features, reporting *marginal gains* rather than testing for independent
signal. In contrast, we run a pre-registered *partial correlation
controlling for raw per-item loss*, which lets us state the stronger,
calibrated claim that the reference-free detectors contribute *zero or
negative* residual predictive value once loss is partialled out. Hayes
et al. (2025) likewise “observe no correlation with MIA success” for
extraction and conclude the “two privacy attacks may capture different
signals,” but their evidence is a *direct, zero-order* correlation
between a reference-model attack (LiRA) and extraction. We differ on
both method and object: we *partial out per-item loss* rather than
correlating directly, and we target the reference-free *calibrated*
detectors (Min-K%, Min-K%++, zlib) that the contamination-detection
literature actually deploys, showing the divergence persists as a
controlled mediation result. Independently, B. Chen et al. (2025) find
for the *membership* task that the few detectors numerically above the
loss baseline (Min-K%, Min-K%++, ReCaLL) do not beat it robustly once
random-seed variance is accounted for, and that performance is
domain-dependent (code-like, low-token-diversity domains such as GitHub
and StackExchange behave differently from Wikipedia and FreeLaw). We
revisit this domain dependence for the *extraction* outcome in our
per-domain analysis
(Section <a href="#sec:eval" data-reference-type="ref" data-reference="sec:eval">5</a>),
noting it is a distinct axis from their membership-AUC result. Finally,
blind-baseline and SoK critiques (Das et al., 2024; Meeus et al., 2025)
show that post-hoc member/non-member splits can make detector “success”
an artifact of distribution shift. Our use of ground-truth Pile
membership (no post-hoc split) is precisely the design discipline they
call for.

| **Study**                                | **Outcome**             | **Detectors**              | **Statistical method**                       | **Conclusion**                         |
|:-----------------------------------------|:------------------------|:---------------------------|:---------------------------------------------|:---------------------------------------|
| Shi et al. (2024; J. Zhang et al., 2025) | membership              | reference-free (Min-K%/++) | AUC / TPR@FPR                                | detector raises membership AUC         |
| Duan et al. (2024) (MIMIR)               | membership              | ref-free + reference       | AUC on ground truth                          | MIAs ≈ chance on LLMs                  |
| Carlini et al. (2022) (LiRA)             | membership              | shadow/reference           | TPR at low FPR                               | strong only with shadow models         |
| B. Chen et al. (2025)                    | membership              | reference-free             | seed-variance testing vs loss                | not robustly beyond loss               |
| Hayes et al. (2025)                      | membership & extraction | LiRA (reference)           | direct (zero-order) correlation              | MIA does not imply extraction          |
| Al Sahili et al. (2025)                  | extraction (targeted)   | ref-free + AdaBoost        | ranking precision, ensemble                  | marginal gains over likelihood         |
| **This work**                            | **extraction**          | **ref-free calibrated**    | **partial corr. + mediation (control loss)** | **zero/negative residual beyond loss** |

Where this work sits. To our knowledge it is the only study that pairs a
per-item *extraction* outcome with a *partial-correlation/mediation*
control for raw loss on *calibrated reference-free* detectors, yielding
a quantified zero/negative marginal.

# Evaluation Overview

## Threat model and success criteria

We frame contamination detection as a membership/exposure attack with an
explicit adversary (Section omitted here, see
`docs/experiment_design.md`). Goals range from membership inference on a
single item, to benchmark-level contamination confirmation, to verbatim
extraction and PII leakage. Each detector is evaluated at its minimum
access tier (gray-box logprobs for LOSS/Min-K%/zlib, white-box logits
for Min-K%++). Success is defined by the security-appropriate operating
point rather than average accuracy.

## Methods under comparison

We evaluate *existing* detectors only. We propose no new detector. The
per-item membership suite is LOSS/perplexity (Yeom et al., 2018), Min-K%
Prob (Shi et al., 2024), Min-K%++ (J. Zhang et al., 2025), and the
zlib-entropy ratio (Carlini et al., 2021). Two further tests operate off
the per-item likelihood axis: corpus-side *n*-gram overlap (Brown et
al., 2020), a model-free data-side check used to construct ground-truth
contamination labels for benchmark items, and the Oren
permutation/exchangeability test (Oren et al., 2024), a benchmark-level
test that compares the canonical ordering of a benchmark’s examples
against random shufflings to certify contamination with a controlled
false-positive rate. The leakage outcome is prefix-continuation
extractable memorization under greedy decoding (Carlini et al., 2023).
On the controlled corpus we additionally measure regex-detected PII
leakage, framed via the PII-leakage games of Lukas et al. (2023).
Related approaches we deliberately *do not* evaluate, guided
prompting (Golchin & Surdeanu, 2024), neighbourhood and shadow-model
reference attacks (Mattern et al., 2023; Shokri et al., 2017), and the
divergence-style extraction of production models (Nasr et al., 2025),
are discussed in
Section <a href="#sec:relatedwork" data-reference-type="ref" data-reference="sec:relatedwork">4</a>.
**\[D1\]** An internal-activation probe is reported, if at all, only as
exploratory analysis in the Discussion, not as a contribution.

## Data

Table <a href="#tab:datasets" data-reference-type="ref" data-reference="tab:datasets">2</a>
summarizes every corpus and benchmark used or referenced below.

#### Models and corpus.

The primary model is the Pythia suite (Biderman et al., 2023), trained
on the public Pile (Gao et al., 2020). Its reconstructible training
order, 154 checkpoints, multiple sizes, and deduplicated variant provide
exact membership ground truth. We use the released MIMIR member/
non-member splits (Duan et al., 2024), which control *n*-gram overlap
between members and non-members. OLMo (Groeneveld et al., 2024) on
Dolma (Soldaini et al., 2024) is a secondary replication target. The
Pile sits within the broader weakly filtered web-scrape regime, Common
Crawl (Common Crawl Foundation, n.d.) and its filtered derivatives
C4 (Dodge et al., 2021; Raffel et al., 2020) and RedPajama (Weber et
al., 2024), that makes benchmark contamination structural rather than
adversarial.

| **Dataset**  | **Type**  | **What it is**                                                                                        | **Size**                 | **Cite**                                  |
|:-------------|:----------|:------------------------------------------------------------------------------------------------------|:-------------------------|:------------------------------------------|
| The Pile     | corpus    | Curated 22-subset English corpus. Pythia’s training data and our membership ground truth              | 825 GB                   | (Gao et al., 2020)                        |
| Common Crawl | corpus    | Open, continually updated repository of raw web-crawl data, the base of most LLM pre-training scrapes | petabyte-scale (growing) | (Common Crawl Foundation, n.d.)           |
| C4           | corpus    | Colossal Clean Crawled Corpus: a filtered Common Crawl snapshot introduced with T5                    | ∼<!-- -->750 GB          | (Dodge et al., 2021; Raffel et al., 2020) |
| Dolma        | corpus    | Open pre-training corpus, OLMo’s training data (replication target)                                   | 3 T tokens               | (Soldaini et al., 2024)                   |
| RedPajama    | corpus    | Open reproduction of an LLaMA-style pre-training mixture                                              | ∼<!-- -->30 T tokens     | (Weber et al., 2024)                      |
| MMLU         | benchmark | Multiple-choice knowledge/reasoning across 57 subjects                                                | 15,908 questions         | (Hendrycks et al., 2021)                  |
| GSM8K        | benchmark | Grade-school multi-step math word problems                                                            | 8,500 problems           | (Cobbe et al., 2021)                      |
| HumanEval    | benchmark | Hand-written Python programming problems with unit tests                                              | 164 problems             | (M. Chen et al., 2021)                    |
| HellaSwag    | benchmark | Adversarially filtered commonsense sentence completion                                                | ∼<!-- -->70,000 items    | (Zellers et al., 2019)                    |
| TruthfulQA   | benchmark | Questions probing imitative falsehoods                                                                | 817 questions            | (Lin et al., 2022)                        |
| BoolQ        | benchmark | Naturally occurring yes/no reading-comprehension questions                                            | 15,942 questions         | (Clark et al., 2019)                      |

Corpora and benchmarks used in or referenced by the evaluation. The Pile
is our ground-truth training corpus. Common Crawl and C4/Dolma/RedPajama
frame the weakly filtered web-scrape regime. The lower block lists the
contamination benchmarks whose items we label by corpus-side overlap.

#### Benchmarks and PII.

Contamination is tested against MMLU, GSM8K, HumanEval, HellaSwag,
TruthfulQA, and BoolQ. **\[D3\]** For PII leakage we use the Enron
Emails data *as a Pile subset already present in Pythia’s training
data*, plus a synthetic PII set for controlled structure, rather than
fine-tuning a model to memorize PII. All PII results are reported in
aggregate. No real PII is reproduced in the paper.

## Metrics (each justified)

**\[D2\]** Following the membership-inference-from-first-principles
convention (Carlini et al., 2022), the primary metric is *true-positive
rate at a fixed low false-positive rate* (TPR @ 0.1% and 1% FPR)
reported with *log-scale ROC*. AUC-ROC is reported secondarily. These
capture whether a detector *confidently* identifies members, the
privacy-relevant regime, which average-case accuracy hides. For
benchmark flagging at a chosen operating threshold we additionally
report precision/recall/F1 as a secondary, application-facing view. The
leakage outcome is the *extraction rate* (Carlini et al., 2023). The
headline analysis is the *Spearman correlation between per-item
contamination score and per-item extraction/leakage outcome*, with
bootstrap confidence intervals and a pre-registered partial-correlation
control that isolates the contribution of raw loss, the quantitative
form of the paper’s central question.

## Validation and controls

**\[D4\]** Robustness is established by repeating each measurement over
multiple seeds with bootstrap confidence intervals on TPR@FPR and on the
Spearman correlation, and by a permutation/exchangeability test for
benchmark-level contamination (Oren et al., 2024). We include ablations
that preempt the standard confounds: deduplicated versus
non-deduplicated Pythia (duplication), frequency-matched
member/non-member splits (string frequency), and model-size scaling
(does the contamination→leakage link strengthen with scale, as
memorization does (Carlini et al., 2023)). Differentially private
training (Abadi et al., 2016; Li et al., 2022) is discussed as the
mitigation direction
(Section <a href="#sec:dp" data-reference-type="ref" data-reference="sec:dp">4.5</a>),
not implemented, since it is a producer-side defense applied at training
time rather than an auditor-side detector.

This section fixes the threat model, methods, data, and metrics. The
empirical results under this protocol, per-detector TPR at low FPR with
log-scale ROC, extraction rates, and the headline contamination→leakage
correlation with confidence intervals, are reported in the results
section, with every reported number tracing to a logged harness run.

# Results

**All results in this section are preliminary, obtained on Pythia-160M
on CPU with *N* = 300 ground-truth Pile members (seed 0), and
larger-model rows are left for the GPU replication.** Every number is
reproducible from a seeded script and recorded in our results ledger.

## Membership separation is at chance on a confound-clean split

We first reproduce, as a control, the known weakness of membership
inference on pre-trained LLMs (Duan et al., 2024). On a confound-clean
split (members = Pile train, non-members = Pile validation, stratified
across 22 Pile subsets to match domain), all four detectors sit at
chance at 160M
(Table <a href="#tab:membership" data-reference-type="ref" data-reference="tab:membership">3</a>).
On the temporally-confounded WikiMIA split the same model shows a
spurious 0.52–0.56, and a 1.4B model rises further, evidence that the
WikiMIA signal is substantially distribution shift, not membership.

| Construction (model)            | LOSS  | Min-K% | Min-K%++ | zlib  |
|:--------------------------------|:-----:|:------:|:--------:|:-----:|
| Pile train-vs-val, clean (160M) | 0.454 | 0.470  |  0.490   | 0.484 |
| WikiMIA-64, confounded (160M)   | 0.523 | 0.539  |  0.545   | 0.564 |
| WikiMIA-64, confounded (1.4B)   | 0.571 | 0.580  |  0.547   | 0.616 |

Membership AUC. Chance ( ≈ 0.5) on the confound-clean split at 160M. The
WikiMIA “signal” is largely temporal/topical distribution shift. CIs in
the ledger. Deduplicated Pythia gives the same chance-level result.

## Contamination predicts leakage, but only through loss

Our headline analysis correlates each per-item detector score with the
per-item extraction outcome (prefix-continuation extractable
memorization under greedy decoding (Carlini et al., 2023)), then
controls for raw loss.
Table <a href="#tab:headline" data-reference-type="ref" data-reference="tab:headline">4</a>
reports, for each calibrated detector, the zero-order Spearman *ρ*, the
linear partial *ρ* given loss, the non-linear (cubic-residual) partial
*ρ* with bootstrap CI, the FDR-corrected permutation *q*, and the
mediation decomposition.

| Detector | zero-order | partial∣loss |     cubic-resid. \[95% CI\]     |  BH-*q*   | mediation: direct ∣ indirect |
|:---------|:----------:|:------------:|:-------------------------------:|:---------:|:----------------------------:|
| LOSS     |   + 0.275  |     n/a      |               n/a               |    n/a    |          (mediator)          |
| Min-K%   |   + 0.173  |    − 0.178   |  − 0.110 \[ − 0.234,  − 0.002\] |   0.058   |      − 0.394 ∣  + 0.567      |
| Min-K%++ |   + 0.108  |    − 0.148   |  − 0.160 \[ − 0.287,  − 0.041\] | **0.015** |      − 0.213 ∣  + 0.321      |
| zlib     |   + 0.177  |    − 0.042   |  − 0.052 \[ − 0.165,  + 0.068\] |   0.331   |      − 0.061 ∣  + 0.238      |

Headline: per-item contamination score vs. extraction (Spearman *ρ*),
Pythia-160M, *N* = 300 members. The positive zero-order correlations
collapse to  ≈ 0 or significantly *negative* once loss is controlled,
linearly, and under the non-linear cubic-residual control (no positive
signal revives, and deciles and the deduplicated arm agree). Mediation:
the loss-mediated *indirect* effect is significantly positive for all
three detectors while the *direct* effect is null (zlib) or negative
(Min-K%, Min-K%++). We read this as a *descriptive* decomposition, not a
causal mediation claim (see below): no calibrated detector adds positive
signal beyond loss.

#### Collinearity caveat (why we do not over-read the negative partials).

The calibrated detectors are deterministic transforms of the same
per-token log-probabilities as loss, and are empirically collinear with
it: Spearman *ρ*(loss,  ⋅ ) = 0.90 (Min-K%), 0.74 (Min-K%++), 0.74
(zlib), with variance-inflation factors 6.2, 2.6, 2.4. The strongest
negative partial (Min-K%, the most loss-collinear detector at VIF 6.2)
is therefore consistent with a *suppression artifact* of
near-collinearity rather than substantive inverse prediction. We do not
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
signal of appreciable size*, not proof of an exact null. The analysis is
well-powered only for moderate-to-large positive residuals, and a small
positive effect at scale is not excluded (hence the GPU replication).
The per-domain breakdown (ledger) shows the loss↔extraction link is
heterogeneous and sign-flipping across domains, strongest in
templated/structured domains (GitHub, StackExchange), reversed in some
prose domains (PubMed Abstracts), so the pooled *ρ* is a domain-mixture,
not a uniform effect.

## Extraction and PII at this scale

Extractable memorization is rare at 160M: 3/300 members are fully
extractable (exact-match extraction rate 0.010, mean fractional
extraction 0.037), the fully-extracted items being templated
boilerplate. On the Enron-Emails-in-Pile subset we measured *zero*
verbatim PII leakage (8/36 documents contained PII in the held suffix,
none were regurgitated). We report the PII result as a null at this
scale and make no PII-exposure claim. Both quantities are expected to
grow with model scale.

## Benchmark contamination (model-free *n*-gram + permutation test)

We complement the per-item analysis with two benchmark-level
contamination tests
(Table <a href="#tab:matrix" data-reference-type="ref" data-reference="tab:matrix">5</a>).
The model-free *n*-gram overlap against a public *sample* of the Pile
(10k documents) is a scale-invariant method but, with a sampled
reference, yields only a loose *lower bound*: overlap is near-zero for
MMLU (0.2% at 13-grams), GSM8K (0%), and HumanEval (0% at 13-grams),
which certifies overlap is *at least* this small and is uninformative
about true contamination, a full-Pile index (infrastructure-, not GPU-,
gated) is required for a real rate. The Oren permutation/exchangeability
test (Oren et al., 2024) at 160M finds the canonical ordering favoured
beyond chance for MMLU (*p* = 0.001) and GSM8K (*p* = 0.013) but not
HumanEval (*p* = 0.875). We draw *no* contamination conclusion from
this, as the test is membership-based, run at sanity scale (small *k*,
smallest model), and subject to a fluency/orientation artifact, it is
flagged GPU-gated and requires a fluency-control baseline before any
claim.

| Benchmark | 13-gram overlap (lower bound) | 8-gram overlap | Oren *p* (160M, sanity) |
|:----------|:-----------------------------:|:--------------:|:-----------------------:|
| MMLU      |             0.2%              |      0.8%      |          0.001          |
| GSM8K     |             0.0%              |      0.0%      |          0.013          |
| HumanEval |             0.0%              |      1.8%      |          0.875          |

Benchmark-level contamination at small scale. *n*-gram cells are a
*lower bound* against a 10k Pile sample (method scale-invariant,
reference under-powered). Oren *p*-values are sanity-scale at 160M and
GPU-gated (no contamination conclusion drawn). See
`docs/contamination_matrix.md`.

# Discussion

#### Membership detection and leakage prediction diverge.

The central empirical observation is that the contamination/membership
signal which predicts *extraction* is, to the resolution of our
experiment, *just raw loss*. The reference-free detectors that the
contamination-detection literature has invested in, Min-K%, Min-K%++,
zlib, improve membership ranking by re-calibrating the per-token
likelihood (z-scoring against the vocabulary, compressing, or trimming
to the lowest-probability tokens), but in doing so they discard
precisely the loss-magnitude information that tracks how extractable an
item is. A descriptive mediation decomposition is consistent with this,
the loss-mediated (indirect) path is positive for all three detectors
while the direct paths are null or negative, but we read it
descriptively, not causally: the detectors are near-collinear transforms
of loss (Spearman up to 0.90, VIF up to 6.2), so a negative
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
that the privacy question, will contamination of a benchmark expose a
leakage channel? is mis-served by importing the membership-inference
toolkit wholesale. For an auditor of a released model, the actionable
implication is to measure loss/extractability directly and to treat a
high Min-K%/Min-K%++ score as evidence about membership, not about
leakage risk. This reframing is the contribution. The detectors
themselves are prior work.

#### Relation to concurrent work.

Our direction agrees with two recent results and we do not claim the
bottom line is surprising: Al Sahili et al. (2025) report only
“marginal” gains of MIA scores over likelihood ranking for targeted
extraction, and Hayes et al. (2025) find no correlation between (LiRA)
membership success and extraction. We add the controlled, mechanistic
form of the claim, a pre-registered partial-correlation/mediation that
quantifies a *zero-to-negative* residual for the calibrated
reference-free detectors after loss is removed, and we target the
reference-free detectors the contamination literature actually deploys
rather than a shadow-model attack. B. Chen et al. (2025) independently
find these detectors do not robustly beat the loss baseline for
*membership* once seed variance is accounted for. Our result is the
extraction-outcome analogue.

#### Defenses.

Because the leakage we measure is downstream of memorization, the
principled mitigation is differential privacy applied at training
time (Abadi et al., 2016; Li et al., 2022). It is a producer-side
control, not an auditor-side detector, and bounds the very quantity
(loss-magnitude / memorization) our analysis identifies as the operative
one.

# Limitations

We state the limitations plainly. Several bound the strength of the
present claims and motivate the GPU-scale replication the pipeline is
built for.

-   **Single, smallest model.** All results are on Pythia-160M (CPU).
    Memorization grows log-linearly with model scale (Carlini et
    al., 2023), so both the membership signal and the extraction outcome
    are expected to be stronger at 1.4B–12B. The present numbers are
    *preliminary*. We have built every analysis so the larger-model run
    is a one-line configuration change.

-   **Chance-level membership separation.** On the confound-clean Pile
    train-vs-val split, membership AUC is at chance (0.45–0.49) at 160M,
    consistent with (Duan et al., 2024). The divergence result is
    therefore established in a regime where the membership signal is
    itself weak. Whether the calibrated detectors gain *independent*
    leakage-predictive value once membership separation becomes
    non-trivial at scale is an open question our design is poised to
    answer.

-   **Near-degenerate extraction outcome.** Extractable memorization at
    160M is rare (3/300 items fully extracted, mean fractional
    extraction 0.037), so the correlation analysis leans on a small
    high-extraction tail. We mitigate with rank statistics, bootstrap
    CIs, and a zero-robust Kendall check, but a less zero-inflated
    outcome at scale would sharpen all estimates.

-   **PII not yet demonstrated.** On the Enron-in-Pile subset we
    observed *zero* verbatim PII leakage at 160M (8/36 documents
    contained PII in the held suffix, none were regurgitated). The PII
    limb of the threat model is thus a designed capability with a null
    result at this scale, not a demonstrated leak. We report it as such
    and do not claim PII exposure.

-   **Benchmark-level test underpowered.** The Oren
    permutation/exchangeability test is run only at sanity scale on
    160M. Membership-based, it is underpowered here and is flagged as
    GPU-gated rather than used to draw contamination conclusions.

-   ***n*-gram contamination is a lower bound.** Our model-free *n*-gram
    overlap uses a public *sample* of the Pile as the reference index,
    so measured benchmark↔Pile overlap underestimates the true overlap
    against the full corpus.

-   **Observational, members-only correlation.** The headline analysis
    correlates detector scores with extraction across known members. It
    is observational, not interventional. We address the most important
    confound (loss) by pre-registered partial correlation and mediation,
    and the obvious alternatives (frequency, duplication, non-linearity,
    distribution shift) by explicit controls, but residual confounding
    cannot be excluded.

-   **Collinearity of detectors with loss.** The calibrated detectors
    are deterministic transforms of the same per-token log-probabilities
    as loss and are empirically collinear with it (Spearman 0.74–0.90,
    VIF up to 6.2 for Min-K%). Consequently we interpret the negative
    partial/direct terms as possible *suppression artifacts* of
    near-collinearity and claim only the conservative “no positive
    residual” result. We do not assert the detectors inversely predict
    leakage.

-   **Construct validity of the leakage proxy.** The outcome (greedy
    prefix-continuation extraction over the held suffix) is itself
    likelihood-related, so part of the loss↔ extraction association is
    mechanical/definitional. Our control removes the loss component, but
    a decisive separation would compute prefix-only loss against
    extraction. We flag this as a known construct-validity limitation
    rather than claiming the two are independent by construction.

-   **Selection and aggregation.** Members are drawn from a non-uniform
    public Pile sample (`pile-10k`), so member-selection bias is
    possible, and the pooled correlation aggregates domains whose
    effects flip sign
    (Section <a href="#sec:res-headline" data-reference-type="ref" data-reference="sec:res-headline">6.2</a>),
    so the pooled *ρ* should be read as a domain-mixture, not a
    homogeneous effect.

-   **Linearity (now addressed).** An earlier version controlled for
    loss only linearly. We added a cubic-residual and decile-stratified
    non-linear control, under which no positive independent signal
    revives. We note it here because it was a live threat to the claim
    until tested.

# Conclusion

We argued that benchmark contamination is best understood as a
privacy/security vulnerability and asked, on models with ground-truth
public training data, whether the contamination/membership signal that a
benchmark leaks actually predicts concrete extraction. Using a
pre-registered partial-correlation and mediation analysis that controls
for raw per-item loss, we found that it does, but only through loss: the
calibrated reference-free detectors (Min-K%, Min-K%++, zlib) add no
independent predictive value beyond loss, and two are negatively
associated with extraction once loss is held fixed. The result is robust
to a non-linear loss control and to deduplication, and is not a
frequency or zero-inflation artifact. The practical message is a
divergence: the detectors optimized for membership inference are not the
right instrument for the leakage question, and an auditor should measure
loss/extractability directly. We claim no new detector or metric. The
contribution is the security reframing and the controlled,
pre-registered measurement. These findings are preliminary, on the
smallest Pythia model. The immediate next step, and the design target of
our released pipeline, is the GPU-scale replication across model sizes,
where memorization, extraction, and any PII leakage are expected to
strengthen, and where the question of whether calibrated detectors gain
independent leakage-predictive value at scale can be settled.

# References

Abadi, M., Chu, A., Goodfellow, I., McMahan, H. B., Mironov, I., Talwar,
K., & Zhang, L. (2016). Deep learning with differential privacy.
*Proceedings of the 2016 ACM SIGSAC Conference on Computer and
Communications Security (CCS)*, 308–318.
<https://doi.org/10.1145/2976749.2978318>

Al Sahili, A., Chehab, A., & Tajeddine, R. (2025). *On the effectiveness
of membership inference in targeted data extraction from large language
models*. <https://arxiv.org/abs/2512.13352>

Biderman, S., Schoelkopf, H., Anthony, Q., Bradley, H., O’Brien, K.,
Hallahan, E., Khan, M. A., Purohit, S., Prashanth, U. S., Raff, E.,
Skowron, A., Sutawika, L., & Wal, O. van der. (2023). Pythia: A suite
for analyzing large language models across training and scaling.
*Proceedings of the 40th International Conference on Machine Learning
(ICML), PMLR*, *202*. <https://arxiv.org/abs/2304.01373>

Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal,
P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S.,
Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A.,
Ziegler, D. M., Wu, J., Winter, C., … Amodei, D. (2020). Language models
are few-shot learners. *Advances in Neural Information Processing
Systems 33 (NeurIPS 2020)*. <https://arxiv.org/abs/2005.14165>

Carlini, N., Chien, S., Nasr, M., Song, S., Terzis, A., & Tramèr, F.
(2022). Membership inference attacks from first principles. *2022 IEEE
Symposium on Security and Privacy (SP)*, 1897–1914.
<https://doi.org/10.1109/SP46214.2022.9833649>

Carlini, N., Ippolito, D., Jagielski, M., Lee, K., Tramèr, F., & Zhang,
C. (2023). Quantifying memorization across neural language models. *The
Eleventh International Conference on Learning Representations (ICLR)*.
<https://arxiv.org/abs/2202.07646>

Carlini, N., Liu, C., Erlingsson, Ú., Kos, J., & Song, D. (2019). The
secret sharer: Evaluating and testing unintended memorization in neural
networks. *28th USENIX Security Symposium (USENIX Security 19)*,
267–284.

Carlini, N., Tramèr, F., Wallace, E., Jagielski, M., Herbert-Voss, A.,
Lee, K., Roberts, A., Brown, T., Song, D., Erlingsson, Ú., Oprea, A., &
Raffel, C. (2021). Extracting training data from large language models.
*30th USENIX Security Symposium (USENIX Security 21)*, 2633–2650.

Chen, B., Han, N., & Miyao, Y. (2025). A statistical and
multi-perspective revisiting of the membership inference attack in large
language models. *Proceedings of the 63rd Annual Meeting of the
Association for Computational Linguistics (ACL), Volume 1: Long Papers*,
22854–22874. <https://arxiv.org/abs/2412.13475>

Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H. P. de O., Kaplan, J.,
Edwards, H., Burda, Y., Joseph, N., Brockman, G., Ray, A., Puri, R.,
Krueger, G., Petrov, M., Khlaaf, H., Sastry, G., Mishkin, P., Chan, B.,
Gray, S., … Zaremba, W. (2021). Evaluating large language models trained
on code. *arXiv Preprint arXiv:2107.03374*.

Clark, C., Lee, K., Chang, M.-W., Kwiatkowski, T., Collins, M., &
Toutanova, K. (2019). BoolQ: Exploring the surprising difficulty of
natural yes/no questions. *Proceedings of the 2019 Conference of the
North American Chapter of the Association for Computational Linguistics
(NAACL)*. <https://arxiv.org/abs/1905.10044>

Cobbe, K., Kosaraju, V., Bavarian, M., Chen, M., Jun, H., Kaiser, L.,
Plappert, M., Tworek, J., Hilton, J., Nakano, R., Hesse, C., & Schulman,
J. (2021). Training verifiers to solve math word problems. *arXiv
Preprint arXiv:2110.14168*.

Common Crawl Foundation. (n.d.). *Common crawl*.
<https://commoncrawl.org>.

Das, D., Zhang, J., & Tramèr, F. (2024). *Blind baselines beat
membership inference attacks for foundation models*.
<https://arxiv.org/abs/2406.16201>

Dodge, J., Sap, M., Marasović, A., Agnew, W., Ilharco, G., Groeneveld,
D., Mitchell, M., & Gardner, M. (2021). Documenting large webtext
corpora: A case study on the colossal clean crawled corpus. *Proceedings
of the 2021 Conference on Empirical Methods in Natural Language
Processing (EMNLP)*. <https://arxiv.org/abs/2104.08758>

Duan, M., Suri, A., Mireshghallah, N., Min, S., Shi, W., Zettlemoyer,
L., Tsvetkov, Y., Choi, Y., Evans, D., & Hajishirzi, H. (2024). Do
membership inference attacks work on large language models? *Conference
on Language Modeling (COLM)*. <https://arxiv.org/abs/2402.07841>

Gao, L., Biderman, S., Black, S., Golding, L., Hoppe, T., Foster, C.,
Phang, J., He, H., Thite, A., Nabeshima, N., Presser, S., & Leahy, C.
(2020). The Pile: An 800GB dataset of diverse text for language
modeling. *arXiv Preprint arXiv:2101.00027*.

Golchin, S., & Surdeanu, M. (2024). Time travel in LLMs: Tracing data
contamination in large language models. *The Twelfth International
Conference on Learning Representations (ICLR)*.
<https://arxiv.org/abs/2308.08493>

Groeneveld, D., Beltagy, I., Walsh, P., Bhagia, A., Kinney, R., Tafjord,
O., Jha, A. H., Ivison, H., Magnusson, I., Wang, Y., Arora, S.,
Atkinson, D., Authur, R., Chandu, K. R., Cohan, A., Dumas, J., Elazar,
Y., Gu, Y., Hessel, J., … Hajishirzi, H. (2024). OLMo: Accelerating the
science of language models. *Proceedings of the 62nd Annual Meeting of
the Association for Computational Linguistics (ACL)*.
<https://arxiv.org/abs/2402.00838>

Hayes, J., Shumailov, I., Choquette-Choo, C. A., Jagielski, M., Kaissis,
G., Nasr, M., Ghalebikesabi, S., Annamalai, M. S. M. S., Mireshghallah,
N., Shilov, I., Meeus, M., Montjoye, Y.-A. de, Lee, K., Boenisch, F.,
Dziedzic, A., & Cooper, A. F. (2025). Exploring the limits of strong
membership inference attacks on large language models. *Advances in
Neural Information Processing Systems 38 (NeurIPS 2025)*.
<https://arxiv.org/abs/2505.18773>

Hendrycks, D., Burns, C., Basart, S., Zou, A., Mazeika, M., Song, D., &
Steinhardt, J. (2021). Measuring massive multitask language
understanding. *International Conference on Learning Representations
(ICLR)*. <https://arxiv.org/abs/2009.03300>

Huang, J., Shao, H., & Chang, K. C.-C. (2022). Are large pre-trained
language models leaking your personal information? *Findings of the
Association for Computational Linguistics: EMNLP 2022*, 2038–2047.

Ippolito, D., Tramèr, F., Nasr, M., Zhang, C., Jagielski, M., Lee, K.,
Choquette-Choo, C. A., & Carlini, N. (2023). Preventing generation of
verbatim memorization in language models gives a false sense of privacy.
*Proceedings of the 16th International Natural Language Generation
Conference (INLG)*, 28–53. <https://arxiv.org/abs/2210.17546>

Kim, S., Yun, S., Lee, H., Gubri, M., Yoon, S., & Oh, S. J. (2023).
ProPILE: Probing privacy leakage in large language models. *Advances in
Neural Information Processing Systems (NeurIPS)*, *36*.

Li, X., Tramèr, F., Liang, P., & Hashimoto, T. (2022). Large language
models can be strong differentially private learners. *The Tenth
International Conference on Learning Representations (ICLR)*.
<https://arxiv.org/abs/2110.05679>

Lin, S., Hilton, J., & Evans, O. (2022). TruthfulQA: Measuring how
models mimic human falsehoods. *Proceedings of the 60th Annual Meeting
of the Association for Computational Linguistics (ACL)*.
<https://arxiv.org/abs/2109.07958>

Lukas, N., Salem, A., Sim, R., Tople, S., Wutschitz, L., &
Zanella-Béguelin, S. (2023). Analyzing leakage of personally
identifiable information in language models. *2023 IEEE Symposium on
Security and Privacy (SP)*, 346–363.

Mattern, J., Mireshghallah, F., Jin, Z., Schölkopf, B., Sachan, M., &
Berg-Kirkpatrick, T. (2023). Membership inference attacks against
language models via neighbourhood comparison. *Findings of the
Association for Computational Linguistics: ACL 2023*, 11330–11343.

Meeus, M., Shilov, I., Jain, S., Faysse, M., Rei, M., & Montjoye, Y.-A.
de. (2025). SoK: Membership inference attacks on LLMs are rushing
nowhere (and how to fix it). *2025 IEEE Conference on Secure and
Trustworthy Machine Learning (SaTML)*.
<https://arxiv.org/abs/2406.17975>

Nasr, M., Carlini, N., Hayase, J., Jagielski, M., Cooper, A. F.,
Ippolito, D., Choquette-Choo, C. A., Wallace, E., Tramèr, F., & Lee, K.
(2025). Scalable extraction of training data from (production) language
models. *The Thirteenth International Conference on Learning
Representations (ICLR)*. <https://arxiv.org/abs/2311.17035>

Oren, Y., Meister, N., Chatterji, N., Ladhak, F., & Hashimoto, T. B.
(2024). Proving test set contamination in black-box language models.
*The Twelfth International Conference on Learning Representations
(ICLR)*. <https://arxiv.org/abs/2310.17623>

Raffel, C., Shazeer, N., Roberts, A., Lee, K., Narang, S., Matena, M.,
Zhou, Y., Li, W., & Liu, P. J. (2020). Exploring the limits of transfer
learning with a unified text-to-text transformer. *Journal of Machine
Learning Research*, *21*(140), 1–67.

Ravaut, M., Ding, B., Jiao, F., Chen, H., Li, X., Zhao, R., Qin, C.,
Xiong, C., & Joty, S. (2024). A comprehensive survey of contamination
detection methods in large language models. *arXiv Preprint
arXiv:2404.00699*.

Shi, W., Ajith, A., Xia, M., Huang, Y., Liu, D., Blevins, T., Chen, D.,
& Zettlemoyer, L. (2024). Detecting pretraining data from large language
models. *The Twelfth International Conference on Learning
Representations (ICLR)*. <https://arxiv.org/abs/2310.16789>

Shokri, R., Stronati, M., Song, C., & Shmatikov, V. (2017). Membership
inference attacks against machine learning models. *2017 IEEE Symposium
on Security and Privacy (SP)*, 3–18.

Soldaini, L., Kinney, R., Bhagia, A., Schwenk, D., Atkinson, D., Authur,
R., Bogin, B., Chandu, K., Dumas, J., Elazar, Y., Hofmann, V., Jha, A.
H., Kumar, S., Lucy, L., Lyu, X., Lambert, N., Magnusson, I., Morrison,
J., Muennighoff, N., … Lo, K. (2024). Dolma: An open corpus of three
trillion tokens for language model pretraining research. *Proceedings of
the 62nd Annual Meeting of the Association for Computational Linguistics
(ACL)*. <https://arxiv.org/abs/2402.00159>

Touvron, H., Lavril, T., Izacard, G., Martinet, X., Lachaux, M.-A.,
Lacroix, T., Rozière, B., Goyal, N., Hambro, E., Azhar, F., Rodriguez,
A., Joulin, A., Grave, E., & Lample, G. (2023). LLaMA: Open and
efficient foundation language models. *arXiv Preprint arXiv:2302.13971*.

Weber, M., Fu, D., Anthony, Q., Oren, Y., Adams, S., Alexandrov, A.,
Lyu, X., Nguyen, H., Yao, X., Adams, V., Athiwaratkun, B., Chalamala,
R., Chen, K., Ryabinin, M., Dao, T., Liang, P., Ré, C., Rish, I., &
Zhang, C. (2024). RedPajama: An open dataset for training large language
models. *Advances in Neural Information Processing Systems (NeurIPS),
Datasets and Benchmarks Track*. <https://arxiv.org/abs/2411.12372>

Yeom, S., Giacomelli, I., Fredrikson, M., & Jha, S. (2018). Privacy risk
in machine learning: Analyzing the connection to overfitting. *2018 IEEE
31st Computer Security Foundations Symposium (CSF)*, 268–282.
<https://doi.org/10.1109/CSF.2018.00027>

Yu, D., Naik, S., Backurs, A., Gopi, S., Inan, H. A., Kamath, G.,
Kulkarni, J., Lee, Y. T., Manoel, A., Wutschitz, L., Yekhanin, S., &
Zhang, H. (2022). Differentially private fine-tuning of language models.
*The Tenth International Conference on Learning Representations (ICLR)*.
<https://arxiv.org/abs/2110.06500>

Zellers, R., Holtzman, A., Bisk, Y., Farhadi, A., & Choi, Y. (2019).
HellaSwag: Can a machine really finish your sentence? *Proceedings of
the 57th Annual Meeting of the Association for Computational Linguistics
(ACL)*. <https://arxiv.org/abs/1905.07830>

Zhang, C., Ippolito, D., Lee, K., Jagielski, M., Tramèr, F., & Carlini,
N. (2023). Counterfactual memorization in neural language models.
*Advances in Neural Information Processing Systems (NeurIPS)*, *36*.

Zhang, J., Sun, J., Yeats, E., Ouyang, Y., Kuo, M., Zhang, J., Yang, H.
F., & Li, H. (2025). Min-k%++: Improved baseline for detecting
pre-training data from large language models. *The Thirteenth
International Conference on Learning Representations (ICLR)*.
<https://arxiv.org/abs/2404.02936>

