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


def load_or_cache_docs(args, tokenizer, tag):
    """Select the member docs, caching the selection to disk.

    The selection is deterministic in (n, min_tokens, prefix_len, suffix_len, seed), but
    building it tokenizes all 10k Pile docs, which is slow enough that we do not want to
    repeat it on every resume. Caching also guarantees a resumed run scores exactly the
    same item_id -> document mapping as the interrupted one.
    """
    key = f"{tag}_n{args.n}_p{args.prefix_len}_s{args.suffix_len}_m{args.min_tokens}_seed{args.seed}"
    cache_path = os.path.join(args.results, f"pile_docs_{key}.json")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            docs = [(row[0], row[1]) for row in json.load(f)]
        print(f"Loaded {len(docs)} cached member docs from {cache_path}")
        return docs
    docs = load_member_docs(
        args.n, args.min_tokens, args.prefix_len, args.suffix_len, tokenizer, args.seed
    )
    with open(cache_path, "w") as f:
        json.dump([[s, list(ids)] for s, ids in docs], f)
    print(f"Cached doc selection -> {cache_path}")
    return docs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--dtype", default=None,
                   help="float16/bfloat16/float32. Use float16 to fit large models on a 16GB GPU")
    p.add_argument("--n", type=int, default=300)
    p.add_argument("--prefix-len", type=int, default=32)
    p.add_argument("--suffix-len", type=int, default=50)
    p.add_argument("--min-tokens", type=int, default=80)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--results", default="results")
    p.add_argument("--out", default=None,
                   help="defaults to pile_items_<model-tag>.jsonl, which the correlation step expects")
    p.add_argument("--flush-every", type=int, default=25,
                   help="fsync the output every k items so an interrupted run loses at most k")
    p.add_argument("--restart", action="store_true",
                   help="ignore and overwrite any existing partial output")
    args = p.parse_args()

    from transformers import AutoTokenizer

    tag = args.model.split("/")[-1]
    os.makedirs(args.results, exist_ok=True)
    out_path = os.path.join(args.results, args.out or f"pile_items_{tag}.jsonl")

    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
    docs = load_or_cache_docs(args, tokenizer, tag)

    # ---- resume: keep whatever is already on disk, score only the missing item_ids.
    if args.restart and os.path.exists(out_path):
        os.remove(out_path)
        print(f"--restart: removed {out_path}")
    done = {}
    if os.path.exists(out_path):
        with open(out_path) as f:
            raw = f.read()
        torn = 0
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                torn += 1  # a hard kill can leave a partially written final line
                continue
            done[int(row["item_id"])] = row  # keyed by item_id, so duplicates collapse
        # Rewrite the file whenever it is not already a clean, newline-terminated JSONL.
        # Without this, appending after a torn last line concatenates onto it and
        # silently corrupts the record, which then breaks every downstream script.
        if torn or (raw and not raw.endswith("\n")):
            with open(out_path, "w") as f:
                for i in sorted(done):
                    f.write(json.dumps(done[i]) + "\n")
            print(f"Compacted partial output: dropped {torn} torn line(s), kept {len(done)} items")
        print(f"Resuming: {len(done)}/{len(docs)} items already scored in {out_path}")

    todo = [(i, d) for i, d in enumerate(docs) if i not in done]
    if not todo:
        print("Nothing left to score.")
    else:
        # Only pay the model-load cost if there is actually work to do.
        generate = hf_greedy_generator(
            args.model, revision=args.revision, device=args.device, dtype=args.dtype
        )
        with open(out_path, "a") as f:
            for k, (i, (pile_set_name, ids)) in enumerate(todo, 1):
                # text = exact decoded prefix+suffix window that is scored here.
                text = tokenizer.decode(ids, skip_special_tokens=True)
                r = is_extractable(ids, prefix_len=args.prefix_len, generate=generate)
                row = {
                    "item_id": i,
                    "text": text,
                    "prefix_len": r.prefix_len,
                    "suffix_len": r.suffix_len,
                    "extracted": bool(r.extracted),
                    "matched_tokens": int(r.matched_tokens),
                    "frac_extracted": float(r.matched_tokens / r.suffix_len if r.suffix_len else 0.0),
                    "pile_set_name": pile_set_name,
                }
                f.write(json.dumps(row) + "\n")
                done[i] = row
                if k % args.flush_every == 0:
                    f.flush()
                    os.fsync(f.fileno())
                    print(f"  scored {k}/{len(todo)} this run ({len(done)}/{len(docs)} total)")
            f.flush()
            os.fsync(f.fileno())

    # ---- summary over the FULL item set on disk, so resumed runs report correctly.
    rows = [done[i] for i in sorted(done)]
    fracs = np.array([r["frac_extracted"] for r in rows], dtype=np.float64)
    n_full = int(sum(bool(r["extracted"]) for r in rows))
    rate = (n_full / len(rows)) if rows else 0.0

    print(f"\nModel={args.model}  N={len(rows)}  prefix_len={args.prefix_len}  dtype={args.dtype}")
    print(f"extraction_rate (exact full-suffix match): {rate:.4f}  ({n_full}/{len(rows)})")
    if len(rows):
        print(f"mean frac_extracted: {fracs.mean():.4f}   median: {np.median(fracs):.4f}")
        edges = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0, 1.0001]
        labels = ["[0,0.1)", "[0.1,0.25)", "[0.25,0.5)", "[0.5,0.75)",
                  "[0.75,0.9)", "[0.9,1.0)", "==1.0"]
        hist, _ = np.histogram(fracs, bins=edges)
        print("frac_extracted histogram:")
        for lab, c in zip(labels, hist):
            print(f"  {lab:<12}: {int(c)}")
    print(f"Items on disk: {len(rows)} -> {out_path}")


if __name__ == "__main__":
    main()
