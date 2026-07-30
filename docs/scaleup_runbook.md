# Scale-up runbook: Pythia-1.4B on a free cloud GPU

Goal: remove the single biggest reviewer objection ("160M on CPU, N=300, 3 extraction
events") without needing the lab GPU. Everything below runs on a free Colab or Kaggle T4.

The pipeline is unchanged. Only three flags differ: `--device cuda`, `--dtype float16`,
and a larger `--n`. That matters for the paper: it is the *same* code at both scales, so
the comparison is not confounded by an implementation change.

## Why float16 is safe here

- Extraction uses greedy decoding, which is an argmax. Half precision changes the chosen
  token only in near-exact ties.
- `HFScorer.score_tokens` upcasts logits to float32 *before* the log-softmax, so the
  per-token statistics (and the mu/sigma that Min-K%++ depends on) stay stable.

Memory, roughly: 1.4B in fp16 is about 2.8GB of weights, which fits a 16GB T4 with lots
of headroom. 2.8B is about 5.6GB and also fits. 6.9B in fp16 is about 14GB and is tight
on a T4, so treat it as a stretch goal or save it for the lab A100.

## Resume is the whole trick

Free Colab sessions disconnect, often around the 12 hour mark and sometimes much sooner.
`extraction_pile.py` now appends each scored item to JSONL and fsyncs every
`--flush-every` items, then on restart reads the file, skips finished `item_id`s, and
continues. The document selection is cached too, so a restart scores the identical
item_id to document mapping.

**This only works if `--results` points at Google Drive.** The Colab VM filesystem is
erased on disconnect. Drive is not.

## Colab cells

### 1. Confirm you actually got a GPU

Runtime menu, then Change runtime type, then select a T4 GPU. Then:

```python
!nvidia-smi
```

If that errors, you are on CPU and the run will take days instead of hours.

### 2. Mount Drive (this is what makes resume work)

```python
from google.colab import drive
drive.mount('/content/drive')

import os
RESULTS = '/content/drive/MyDrive/contamination-results'
os.makedirs(RESULTS, exist_ok=True)
print(RESULTS)
```

### 3. Get the code and dependencies

```python
!git clone https://github.com/aviangirekula/contamination-research.git
%cd contamination-research
!pip -q install "transformers>=4.40" datasets numpy matplotlib
```

### 4. Extraction (the long step, fully resumable)

```python
!python scripts/extraction_pile.py \
    --model EleutherAI/pythia-1.4b \
    --device cuda --dtype float16 \
    --n 3000 --prefix-len 32 --suffix-len 50 --seed 0 \
    --results "/content/drive/MyDrive/contamination-results" \
    --flush-every 25
```

Expect roughly 1 to 3 hours for 3000 items, though this varies with the GPU you are
assigned. **If the session dies, just re-run this exact cell.** It picks up where it
stopped and prints how many items it is resuming from.

### 5. Headline correlation

```python
!python scripts/correlation_160m.py \
    --model EleutherAI/pythia-1.4b \
    --device cuda --dtype float16 \
    --results "/content/drive/MyDrive/contamination-results"
```

### 6. Controls (the pre-registered R6 analysis: partial correlation given loss)

```python
!python scripts/controls_160m.py \
    --model EleutherAI/pythia-1.4b \
    --device cuda --dtype float16 \
    --items "/content/drive/MyDrive/contamination-results/pile_items_pythia-1.4b.jsonl" \
    --tag pythia-1.4b \
    --results "/content/drive/MyDrive/contamination-results"
```

### 7. Hardening and collinearity, which reuse the cached scores

```python
!python scripts/hardening_160m.py --tag pythia-1.4b \
    --results "/content/drive/MyDrive/contamination-results"
!python scripts/collinearity_check.py --tag pythia-1.4b \
    --results "/content/drive/MyDrive/contamination-results"
```

Check each script's `--help` if a flag name differs.

## Important: do not confound model size with sample size

Comparing 160M at N=300 against 1.4B at N=3000 changes two things at once, and a reviewer
will say so immediately. Run the 160M arm at the same N so the only difference is scale:

```python
!python scripts/extraction_pile.py \
    --model EleutherAI/pythia-160m \
    --device cuda --dtype float16 \
    --n 3000 --prefix-len 32 --suffix-len 50 --seed 0 \
    --results "/content/drive/MyDrive/contamination-results"
```

That gives a clean 160M vs 1.4B comparison at fixed N, which is the scaling claim the
paper actually wants to make.

## If extraction is still near-zero at 1.4B

The root problem is that 3 events out of 300 cannot support any correlation claim. If the
rate is still tiny after scaling, the fix is to make extraction easier rather than to
give up on the outcome variable:

- Longer prefixes give the model more context to latch onto. Try `--prefix-len 64` or
  `--prefix-len 100` alongside 32 and report the rate as a function of prefix length.
  That curve is a legitimate result in itself.
- Shorter suffixes are easier to reproduce exactly. Try `--suffix-len 25`.
- `frac_extracted` (leading matched-token fraction) is already the softer, less
  zero-inflated outcome. If exact-match stays degenerate, lead with the fractional
  outcome and report exact match as secondary.

## What to record for the paper

For each configuration, log: model, N, prefix length, suffix length, seed, exact-match
extraction rate, mean fractional extraction, zero-order Spearman, and the partial
correlation given loss with its confidence interval. That table is the scaling result.
