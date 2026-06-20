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
