#!/usr/bin/env python
"""Regenerate score-distribution + log-ROC plots from a cached scores JSONL.

Cheap (no model): reads results/<...>.jsonl rows {"label": 0/1, "<detector>": float, ...}
and writes distribution + log-scale ROC figures. Used to (re)produce figures for runs whose
per-item scores were cached, e.g. the Pythia-1.4B WikiMIA run, without re-scoring.

Run:
    python scripts/plot_from_scores.py results/wikimia64_pythia-1.4b.jsonl --tag wikimia64_pythia-1.4b
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
    p.add_argument("scores", help="path to scores JSONL with a 'label' key")
    p.add_argument("--tag", default=None, help="filename tag (default: derived from path)")
    p.add_argument("--out", default="figures")
    p.add_argument("--title", default="")
    args = p.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from eval.metrics import roc_curve

    rows = [json.loads(l) for l in open(args.scores)]
    y = np.array([r["label"] for r in rows])
    det_names = [k for k in rows[0] if k != "label"]
    per_det = {n: np.array([r[n] for r in rows]) for n in det_names}
    tag = args.tag or os.path.splitext(os.path.basename(args.scores))[0]
    title = args.title or tag
    os.makedirs(args.out, exist_ok=True)

    fig, axes = plt.subplots(1, len(det_names), figsize=(3.6 * len(det_names), 3.0))
    for ax, name in zip(np.atleast_1d(axes), det_names):
        s = per_det[name]
        ax.hist(s[y == 1], bins=25, alpha=0.6, label="member", density=True)
        ax.hist(s[y == 0], bins=25, alpha=0.6, label="non-member", density=True)
        ax.set_title(name, fontsize=9)
        ax.legend(fontsize=7)
    fig.suptitle(f"{title}: score distributions", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, f"{tag}_dists.png"), dpi=150)

    fig2, ax2 = plt.subplots(figsize=(4.5, 4.5))
    for name in det_names:
        fpr, tpr, _ = roc_curve(per_det[name], y)
        ax2.plot(np.clip(fpr, 1e-3, 1), np.clip(tpr, 1e-3, 1), label=name)
    ax2.plot([1e-3, 1], [1e-3, 1], "k--", lw=0.6)
    ax2.set_xscale("log"); ax2.set_yscale("log")
    ax2.set_xlabel("FPR"); ax2.set_ylabel("TPR")
    ax2.set_title(f"Log-scale ROC ({title})", fontsize=10)
    ax2.legend(fontsize=7)
    fig2.tight_layout()
    fig2.savefig(os.path.join(args.out, f"{tag}_logroc.png"), dpi=150)
    print(f"wrote {args.out}/{tag}_dists.png and {args.out}/{tag}_logroc.png  (N={len(y)})")


if __name__ == "__main__":
    main()
