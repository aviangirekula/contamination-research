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
