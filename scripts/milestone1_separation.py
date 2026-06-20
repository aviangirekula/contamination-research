#!/usr/bin/env python
"""Milestone 1: load Pythia, score Pile member vs non-member text, plot separation.

This is the first REAL-compute milestone (gated on torch + transformers + data). It:
  1. loads Pythia-160m,
  2. computes LOSS, Min-K%, Min-K%++, zlib scores for a set of known Pile members and
     known non-members,
  3. reports AUC + TPR@low-FPR per detector,
  4. saves score-distribution + log-scale ROC plots.

Run:
    pip install -r requirements.txt
    python scripts/milestone1_separation.py --n 200 --device cpu

Provide member/non-member text via --members-file / --nonmembers-file (one text per
line). If omitted, the script exits with instructions rather than inventing data --
ground truth must be real Pile membership (see docs/experiment_design.md section 3).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f if ln.strip()]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--members-file", required=True, help="known Pile members, one text/line")
    p.add_argument("--nonmembers-file", required=True, help="known non-members, one text/line")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--out", default="figures")
    args = p.parse_args()

    from detectors import build_default_detectors, HFScorer
    from eval.metrics import mia_report

    members = read_lines(args.members_file)[: args.n]
    nonmembers = read_lines(args.nonmembers_file)[: args.n]
    print(f"Loaded {len(members)} members, {len(nonmembers)} non-members")

    scorer = HFScorer(args.model, revision=args.revision, device=args.device)
    detectors = build_default_detectors(scorer)

    texts = members + nonmembers
    labels = np.array([1] * len(members) + [0] * len(nonmembers))
    per_det = {d.name: [] for d in detectors}
    keep = []
    for i, t in enumerate(texts):
        try:
            stats = scorer.score_tokens(t)
        except ValueError:
            continue
        keep.append(labels[i])
        for d in detectors:
            per_det[d.name].append(d.score_from_stats(stats, t))
    y = np.array(keep)

    print(f"\n{'detector':<18}{'AUC':>8}{'TPR@1%':>10}{'TPR@0.1%':>10}")
    for name, scores in per_det.items():
        rep = mia_report(np.array(scores), y)
        print(f"{name:<18}{rep.auc:>8.3f}{rep.tpr_at_1:>10.3f}{rep.tpr_at_0p1:>10.3f}")

    try:
        _plots(per_det, y, args.out)
        print(f"\nPlots written to {args.out}/")
    except ImportError:
        print("\n(matplotlib not installed; skipping plots)")


def _plots(per_det, y, out):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from eval.metrics import roc_curve

    os.makedirs(out, exist_ok=True)
    # score distributions
    fig, axes = plt.subplots(1, len(per_det), figsize=(4 * len(per_det), 3.2))
    for ax, (name, scores) in zip(np.atleast_1d(axes), per_det.items()):
        s = np.array(scores)
        ax.hist(s[y == 1], bins=30, alpha=0.6, label="member", density=True)
        ax.hist(s[y == 0], bins=30, alpha=0.6, label="non-member", density=True)
        ax.set_title(name)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "milestone1_score_distributions.png"), dpi=150)

    # log-scale ROC
    fig2, ax2 = plt.subplots(figsize=(4.5, 4.5))
    for name, scores in per_det.items():
        fpr, tpr, _ = roc_curve(np.array(scores), y)
        ax2.plot(np.clip(fpr, 1e-4, 1), np.clip(tpr, 1e-4, 1), label=name)
    ax2.plot([1e-4, 1], [1e-4, 1], "k--", lw=0.6)
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("FPR")
    ax2.set_ylabel("TPR")
    ax2.set_title("Log-scale ROC (Pythia-160m, Pile membership)")
    ax2.legend(fontsize=7)
    fig2.tight_layout()
    fig2.savefig(os.path.join(out, "milestone1_logroc.png"), dpi=150)


if __name__ == "__main__":
    main()
