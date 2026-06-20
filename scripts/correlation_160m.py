#!/usr/bin/env python
"""HEADLINE RESULT: contamination/membership score <-> extraction/leakage correlation.

Consumes the canonical item set emitted by scripts/extraction_pile.py
(results/pile_items_<model>.jsonl: Pile MEMBERS with per-item extraction outcomes),
re-scores the EXACT same `text` field with the membership detectors, and computes the
Spearman correlation between each detector's contamination score and the leakage outcome
(fractional extraction). Bootstrap CIs included. This is the paper's thesis as a number.

The leakage signal at 160m is heavily zero-inflated (small model, 32-token prefixes), so
a weak correlation with a wide CI is the EXPECTED preliminary result; model size is a
single --model flag for the GPU scale-up.

Run:
    python scripts/correlation_160m.py --model EleutherAI/pythia-160m --device cpu
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
    p.add_argument("--items", default=None, help="defaults to results/pile_items_<model>.jsonl")
    p.add_argument("--out", default="figures")
    p.add_argument("--results", default="results")
    args = p.parse_args()

    from detectors import build_default_detectors, HFScorer
    from eval.metrics import spearman, spearman_ci

    tag = args.model.split("/")[-1]
    items_path = args.items or os.path.join(args.results, f"pile_items_{tag}.jsonl")
    items = [json.loads(l) for l in open(items_path)]
    print(f"Loaded {len(items)} member items from {items_path}")

    scorer = HFScorer(args.model, revision=args.revision, device=args.device)
    detectors = build_default_detectors(scorer)

    det_scores = {d.name: [] for d in detectors}
    frac = []
    extracted = []
    kept = 0
    for i, it in enumerate(items):
        try:
            stats = scorer.score_tokens(it["text"])
        except ValueError:
            continue
        for d in detectors:
            det_scores[d.name].append(d.score_from_stats(stats, it["text"]))
        frac.append(float(it["frac_extracted"]))
        extracted.append(int(it["extracted"]))
        kept += 1
        if kept % 50 == 0:
            print(f"  scored {kept}")
    frac = np.array(frac)
    extracted = np.array(extracted)

    print(f"\nHEADLINE: contamination score <-> extraction (Spearman), {tag}, N={kept}")
    print(f"  leakage signal: mean frac={frac.mean():.4f}, fully-extracted={int(extracted.sum())}/{kept}")
    print(f"\n{'detector':<18}{'rho(frac)':>12}{'95% CI':>22}{'rho(extracted)':>16}")
    summary = {}
    for name in det_scores:
        s = np.array(det_scores[name])
        rho_f = spearman(s, frac)
        lo, hi = spearman_ci(s, frac, n_boot=2000, seed=0)
        rho_e = spearman(s, extracted.astype(float))
        summary[name] = {"rho_frac": rho_f, "rho_frac_ci": [lo, hi], "rho_extracted": rho_e}
        sig = "" if (lo <= 0 <= hi) else "  *CI excludes 0*"
        print(f"{name:<18}{rho_f:>12.3f}{f'[{lo:.3f}, {hi:.3f}]':>22}{rho_e:>16.3f}{sig}")

    os.makedirs(args.results, exist_ok=True)
    with open(os.path.join(args.results, f"correlation_{tag}.json"), "w") as f:
        json.dump({"model": args.model, "n": kept,
                   "leakage_mean_frac": float(frac.mean()),
                   "fully_extracted": int(extracted.sum()),
                   "summary": summary}, f, indent=2)

    try:
        _scatter(det_scores, frac, args.out, tag)
        print(f"\nScatter -> {args.out}/correlation_{tag}_scatter.png")
    except ImportError:
        print("(matplotlib missing; skipping scatter)")

    return summary


def _scatter(det_scores, frac, out, tag):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(out, exist_ok=True)
    names = list(det_scores)
    fig, axes = plt.subplots(1, len(names), figsize=(3.6 * len(names), 3.2))
    for ax, name in zip(np.atleast_1d(axes), names):
        ax.scatter(det_scores[name], frac, s=10, alpha=0.5)
        ax.set_xlabel(f"{name} score")
        ax.set_ylabel("fractional extraction")
        ax.set_title(name, fontsize=9)
    fig.suptitle(f"{tag}: contamination score vs. extraction (Pile members)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(out, f"correlation_{tag}_scatter.png"), dpi=150)


if __name__ == "__main__":
    main()
