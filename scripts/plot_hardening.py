#!/usr/bin/env python
"""Forest plot of St hardening: zero-order vs linear-partial vs cubic-residual ρ (with CI)
per calibrated detector. Reads results/hardening_<tag>.json. Seeded upstream; this only plots.

Run: python scripts/plot_hardening.py --tag pythia-160m
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tag", default="pythia-160m")
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="figures")
    args = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = json.load(open(os.path.join(args.results, f"hardening_{args.tag}.json")))
    dets = ["min_20_prob", "min_20_plusplus", "zlib_ratio"]
    labels = {"min_20_prob": "Min-K%", "min_20_plusplus": "Min-K%++", "zlib_ratio": "zlib"}
    os.makedirs(args.out, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 3.6))
    yloc = np.arange(len(dets))[::-1]
    for i, det in zip(yloc, dets):
        x = d["detectors"][det]
        ax.scatter(x["zero_order_rho"], i + 0.22, color="tab:blue", zorder=3, label="zero-order" if i == yloc[0] else "")
        ax.scatter(x["linear_partial_rho"], i, color="tab:orange", zorder=3, label="linear partial|loss" if i == yloc[0] else "")
        lo, hi = x["cubic_residual_ci"]
        ax.errorbar(x["cubic_residual_rho"], i - 0.22, xerr=[[x["cubic_residual_rho"] - lo], [hi - x["cubic_residual_rho"]]],
                    fmt="o", color="tab:red", capsize=3, zorder=3, label="cubic-residual (95% CI)" if i == yloc[0] else "")
    ax.axvline(0, color="k", lw=0.8, ls="--")
    ax.set_yticks(yloc)
    ax.set_yticklabels([labels[x] for x in dets])
    ax.set_xlabel("Spearman ρ with extraction (frac_extracted)")
    ax.set_title(f"Detector→leakage correlation collapses under loss control ({args.tag})", fontsize=10)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    p = os.path.join(args.out, f"hardening_{args.tag}_forest.png")
    fig.savefig(p, dpi=150)
    print("wrote", p)


if __name__ == "__main__":
    main()
