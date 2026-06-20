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
