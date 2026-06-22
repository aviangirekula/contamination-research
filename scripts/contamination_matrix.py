#!/usr/bin/env python
"""Mx -- contamination matrix at small scale (pre-registered in docs/pre_analysis.md).

Runs EXACTLY the Mx pre-registration, nothing more:

Mx-1 (scale-invariant, model-free): n-gram/substring overlap of benchmark items vs a public
  Pile SAMPLE (NeelNanda/pile-10k). For each benchmark (MMLU, GSM8K, HumanEval; up to 500
  items, seed 0) and each N in {13 primary, 8 secondary}, report:
    * contamination rate = fraction of items with ANY n-gram overlap (GPT-3 13-gram rule)
    * mean per-item overlap fraction.
  CAVEAT: the index is built from a SAMPLE of the Pile, so measured overlap is a LOWER BOUND
  on true benchmark<->Pile overlap. Not the contamination rate of the full corpus.

Mx-2 (underpowered, flagged): Oren exchangeability permutation test at Pythia-160m
  (n_permutations >= 1000) on each benchmark's canonical ordering, using ~25-50 short items
  per benchmark to keep CPU feasible. p-values are reported but EXPLICITLY marked as
  sanity-scale / underpowered at 160m and GPU-gated (membership-based).

Run:
    python scripts/contamination_matrix.py --model EleutherAI/pythia-160m --device cpu
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detectors import NGramOverlapDetector  # noqa: E402


# ---------------------------------------------------------------- benchmark loaders
def _try_load(names_configs, split):
    """Try each (name, config) in order; return (dataset, used_name, used_config).

    Records which loader name actually worked so it can be reported.
    """
    from datasets import load_dataset

    last_err = None
    for name, config in names_configs:
        try:
            if config is None:
                ds = load_dataset(name, split=split)
            else:
                ds = load_dataset(name, config, split=split)
            return ds, name, config
        except Exception as e:  # noqa: BLE001 -- record and try the obvious alternative
            last_err = e
            print(f"  loader failed: load_dataset({name!r}, {config!r}, split={split!r}) -> {type(e).__name__}: {e}")
    raise RuntimeError(f"all loaders failed; last error: {last_err}")


def load_mmlu(max_items, seed):
    """MMLU: text = question + choices. cais/mmlu, config 'all', split 'test'."""
    ds, used_name, used_config = _try_load(
        [("cais/mmlu", "all"), ("hendrycks_test", "all")], "test"
    )
    idx = _sample_indices(len(ds), max_items, seed)
    texts = []
    for i in idx:
        ex = ds[int(i)]
        choices = ex.get("choices", [])
        choices_str = " ".join(str(c) for c in choices)
        texts.append(f"{ex['question']} {choices_str}".strip())
    return texts, used_name, used_config, len(ds)


def load_gsm8k(max_items, seed):
    """GSM8K: text = question. openai/gsm8k or gsm8k, config 'main', split 'test'."""
    ds, used_name, used_config = _try_load(
        [("openai/gsm8k", "main"), ("gsm8k", "main")], "test"
    )
    idx = _sample_indices(len(ds), max_items, seed)
    texts = [str(ds[int(i)]["question"]).strip() for i in idx]
    return texts, used_name, used_config, len(ds)


def load_humaneval(max_items, seed):
    """HumanEval: text = prompt. openai_humaneval, split 'test'."""
    ds, used_name, used_config = _try_load(
        [("openai_humaneval", None), ("openai/openai_humaneval", None)], "test"
    )
    idx = _sample_indices(len(ds), max_items, seed)
    texts = [str(ds[int(i)]["prompt"]).strip() for i in idx]
    return texts, used_name, used_config, len(ds)


def _sample_indices(n_total, max_items, seed):
    """Deterministic sample of up to max_items indices from range(n_total)."""
    rng = np.random.default_rng(seed)
    if n_total <= max_items:
        return np.arange(n_total)
    return np.sort(rng.choice(n_total, size=max_items, replace=False))


# ---------------------------------------------------------------- Pile-sample index
def load_pile_sample_texts():
    """All texts from the NeelNanda/pile-10k public SAMPLE (lower-bound reference)."""
    from datasets import load_dataset

    ds, used_name, _ = _try_load([("NeelNanda/pile-10k", None)], "train")
    texts = [str(ex["text"]) for ex in ds]
    return texts, used_name, len(texts)


# ---------------------------------------------------------------- Mx-1
def run_mx1(benchmarks, pile_texts, ns):
    """Per benchmark, per N: contamination rate (any overlap) + mean overlap fraction."""
    results = {}
    indices = {}
    for n in ns:
        det = NGramOverlapDetector(n=n).build_index(pile_texts)
        indices[n] = det.index_size
        print(f"\n[Mx-1] built N={n} index from Pile sample: {det.index_size} distinct {n}-grams")
        for bench, texts in benchmarks.items():
            scores = np.array([det.score(t) for t in texts])
            n_with_overlap = int((scores > 0.0).sum())
            rate = n_with_overlap / len(scores)
            mean_overlap = float(scores.mean())
            results.setdefault(bench, {})[f"n{n}"] = {
                "n_items": len(scores),
                "n_with_any_overlap": n_with_overlap,
                "contamination_rate": rate,
                "mean_overlap_fraction": mean_overlap,
                "max_overlap_fraction": float(scores.max()),
            }
            print(f"    {bench:<10} N={n}: rate={rate:.4f} "
                  f"({n_with_overlap}/{len(scores)})  mean_overlap={mean_overlap:.5f}  "
                  f"max={float(scores.max()):.4f}")
    return results, indices


# ---------------------------------------------------------------- Mx-2
def run_mx2(benchmarks, model, revision, device, oren_k, oren_words, n_permutations, seed):
    """Oren permutation test per benchmark at the target model (UNDERPOWERED / GPU-gated)."""
    from detectors import HFScorer, OrenPermutationTest

    print(f"\n[Mx-2] Oren permutation test (model={model}, device={device}, "
          f"k={oren_k} items/bench, {n_permutations} permutations) -- UNDERPOWERED/GPU-gated")
    scorer = HFScorer(model, revision=revision, device=device)
    test = OrenPermutationTest(scorer)

    def trunc(t):
        return " ".join(t.split()[:oren_words])

    results = {}
    for bench, texts in benchmarks.items():
        # canonical ordering = the first oren_k sampled items, truncated for CPU feasibility
        examples = [trunc(t) for t in texts[:oren_k] if len(trunc(t).split()) >= 2]
        k_used = len(examples)
        if k_used < 2:
            results[bench] = {"error": "fewer than 2 scorable examples", "k_used": k_used}
            print(f"    {bench:<10}: SKIP (only {k_used} scorable examples)")
            continue
        res = test.test(examples, n_permutations=n_permutations, seed=seed)
        res["k_used"] = k_used
        res["oren_words"] = oren_words
        results[bench] = res
        print(f"    {bench:<10}: p={res['p_value']:.4f}  canonical_ll={res['canonical_loglik']:.2f}  "
              f"null_mean={res['null_mean']:.2f}  null_std={res['null_std']:.2f}  (k={k_used})")
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--max-items", type=int, default=500, help="up to N items per benchmark for Mx-1")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--ngram-primary", type=int, default=13)
    p.add_argument("--ngram-secondary", type=int, default=8)
    p.add_argument("--oren-k", type=int, default=30, help="items per benchmark for Oren (25-50)")
    p.add_argument("--oren-words", type=int, default=20, help="truncate Oren items (CPU feasibility)")
    p.add_argument("--n-permutations", type=int, default=1000)
    p.add_argument("--results", default="results")
    args = p.parse_args()

    ns = [args.ngram_primary, args.ngram_secondary]

    # ---- load benchmarks (record which loader worked + item counts) ----
    print("=== Loading benchmarks (up to %d items each, seed %d) ===" % (args.max_items, args.seed))
    loaders_used = {}
    benchmarks = {}

    mmlu_texts, mmlu_name, mmlu_cfg, mmlu_total = load_mmlu(args.max_items, args.seed)
    benchmarks["MMLU"] = mmlu_texts
    loaders_used["MMLU"] = {"loader": mmlu_name, "config": mmlu_cfg, "split": "test",
                            "total_in_split": mmlu_total, "n_sampled": len(mmlu_texts),
                            "text_field": "question + choices"}
    print(f"  MMLU: loader={mmlu_name} config={mmlu_cfg} total={mmlu_total} sampled={len(mmlu_texts)}")

    gsm_texts, gsm_name, gsm_cfg, gsm_total = load_gsm8k(args.max_items, args.seed)
    benchmarks["GSM8K"] = gsm_texts
    loaders_used["GSM8K"] = {"loader": gsm_name, "config": gsm_cfg, "split": "test",
                             "total_in_split": gsm_total, "n_sampled": len(gsm_texts),
                             "text_field": "question"}
    print(f"  GSM8K: loader={gsm_name} config={gsm_cfg} total={gsm_total} sampled={len(gsm_texts)}")

    he_texts, he_name, he_cfg, he_total = load_humaneval(args.max_items, args.seed)
    benchmarks["HumanEval"] = he_texts
    loaders_used["HumanEval"] = {"loader": he_name, "config": he_cfg, "split": "test",
                                 "total_in_split": he_total, "n_sampled": len(he_texts),
                                 "text_field": "prompt"}
    print(f"  HumanEval: loader={he_name} config={he_cfg} total={he_total} sampled={len(he_texts)}")

    # ---- Pile sample reference (LOWER BOUND) ----
    pile_texts, pile_name, pile_n = load_pile_sample_texts()
    print(f"\n  Pile reference: loader={pile_name} (SAMPLE) docs={pile_n} "
          f"-> measured overlap is a LOWER BOUND")

    # ---- Mx-1 ----
    mx1, index_sizes = run_mx1(benchmarks, pile_texts, ns)

    # ---- Mx-2 ----
    mx2 = run_mx2(benchmarks, args.model, args.revision, args.device,
                  args.oren_k, args.oren_words, args.n_permutations, args.seed)

    # ---- persist ----
    os.makedirs(args.results, exist_ok=True)
    out = {
        "seed": args.seed,
        "model": args.model,
        "device": args.device,
        "ngram_n_primary": args.ngram_primary,
        "ngram_n_secondary": args.ngram_secondary,
        "loaders_used": loaders_used,
        "pile_reference": {"loader": pile_name, "n_docs": pile_n,
                           "is_sample": True,
                           "caveat": "SAMPLE of the Pile; measured overlap is a LOWER BOUND "
                                     "on true benchmark<->Pile overlap"},
        "ngram_index_sizes": {f"n{n}": index_sizes[n] for n in ns},
        "mx1_ngram_overlap": mx1,
        "mx2_oren_permutation": {
            "params": {"model": args.model, "device": args.device,
                       "n_permutations": args.n_permutations,
                       "oren_k": args.oren_k, "oren_words": args.oren_words},
            "status": "UNDERPOWERED / sanity-scale at 160m; membership-based => GPU-gated; "
                      "no contamination conclusions drawn",
            "results": mx2,
        },
    }
    out_path = os.path.join(args.results, "contamination_matrix.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
