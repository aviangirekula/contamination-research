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
