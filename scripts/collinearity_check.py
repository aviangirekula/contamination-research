#!/usr/bin/env python
"""Collinearity diagnostic (reviewer concern V/W3): the calibrated detectors are functions of
the same per-token logprobs as loss, so a negative PARTIAL correlation may be a suppression
artifact rather than substantive inverse prediction. Reports detector~loss correlation, VIF,
and the condition number of the [loss, detector] design. Cached data; no model inference.

Run: python scripts/collinearity_check.py --scores results/controls_scores_pythia-160m.jsonl --tag pythia-160m
"""
from __future__ import annotations

import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from eval.partial import spearman

CAL = ["min_20_prob", "min_20_plusplus", "zlib_ratio"]


def pearson(a, b):
    a = a - a.mean(); b = b - b.mean()
    return float((a * b).sum() / np.sqrt((a**2).sum() * (b**2).sum()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--results", default="results")
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.scores)]
    loss = np.array([r["loss"] for r in rows], float)
    out = {"tag": a.tag, "n": len(rows), "detector_vs_loss": {}}
    print(f"{a.tag}: N={len(rows)}")
    print(f"{'detector':<16}{'pearson_loss':>14}{'spearman_loss':>15}{'VIF':>8}{'cond':>8}")
    for n in CAL:
        d = np.array([r[n] for r in rows], float)
        rp = pearson(loss, d); rs = spearman(loss, d); vif = 1 / (1 - rp**2)
        A = np.column_stack([(loss - loss.mean()) / loss.std(), (d - d.mean()) / d.std()])
        cond = float(np.linalg.cond(A))
        out["detector_vs_loss"][n] = {"pearson": rp, "spearman": rs, "vif": vif, "cond": cond}
        print(f"{n:<16}{rp:>14.3f}{rs:>15.3f}{vif:>8.1f}{cond:>8.1f}")
    os.makedirs(a.results, exist_ok=True)
    with open(os.path.join(a.results, f"collinearity_{a.tag}.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote results/collinearity_{a.tag}.json")


if __name__ == "__main__":
    main()
