#!/usr/bin/env python
"""St — statistical hardening on cached per-example controls scores (no model inference).

For each calibrated detector D in {Min-K%, Min-K%++, zlib}, vs leakage outcome frac_extracted,
controlling for loss: zero-order rho, linear partial rho|loss, NON-LINEAR partial controls
(PRIMARY = cubic-polynomial residualization; SECONDARY = decile-of-loss stratification), and
rank mediation (direct/indirect/proportion). FDR over the 3 cubic-residual permutation p-values
(St-1 confirmatory family). Plus per-domain breakdown. See docs/pre_analysis.md (Round 2, St).

Run:
    python scripts/hardening_160m.py --scores results/controls_scores_pythia-160m.jsonl --tag pythia-160m
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CALIBRATED = ["min_20_prob", "min_20_plusplus", "zlib_ratio"]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scores", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--results", default="results")
    p.add_argument("--n-boot", type=int, default=2000)
    p.add_argument("--n-perm", type=int, default=2000)
    p.add_argument("--n-bins", type=int, default=10)
    args = p.parse_args()

    from eval.partial import benjamini_hochberg, bootstrap_ci, partial_spearman, spearman
    from eval.mediation import (
        cubic_residual_perm_p, cubic_residual_spearman, decile_stratified_spearman,
        mediation_stat, rank_mediation, stratified_permutation_p,
    )

    rows = [json.loads(l) for l in open(args.scores)]
    frac = np.array([r["frac_extracted"] for r in rows], float)
    loss = np.array([r["loss"] for r in rows], float)
    domain = [r["pile_set_name"] for r in rows]
    print(f"{args.tag}: N={len(rows)}, mean frac={frac.mean():.4f}")

    out = {"tag": args.tag, "n": len(rows), "detectors": {}}
    cubic_ps = []
    for name in CALIBRATED:
        d = np.array([r[name] for r in rows], float)
        # PRIMARY non-linear control: cubic-residual
        cubic = cubic_residual_spearman(d, frac, loss)
        cubic_ci = bootstrap_ci(lambda a, b, c: cubic_residual_spearman(a, b, c),
                                (d, frac, loss), args.n_boot)
        cubic_p = cubic_residual_perm_p(d, frac, loss, n_perm=args.n_perm)
        cubic_ps.append(cubic_p)
        # SECONDARY model-free control: decile stratification (coarse)
        dec = decile_stratified_spearman(d, frac, loss, args.n_bins)
        dec_ci = bootstrap_ci(lambda a, b, c: decile_stratified_spearman(a, b, c, args.n_bins),
                              (d, frac, loss), args.n_boot)
        dec_p = stratified_permutation_p(d, frac, loss, args.n_bins, args.n_perm)
        med = rank_mediation(d, frac, loss)
        med_ci = {k: list(bootstrap_ci(lambda a, b, c, kk=k: mediation_stat(a, b, c, kk),
                                       (d, frac, loss), args.n_boot))
                  for k in ["direct", "indirect", "total"]}
        out["detectors"][name] = {
            "zero_order_rho": spearman(d, frac),
            "linear_partial_rho": partial_spearman(d, frac, loss),
            "cubic_residual_rho": cubic, "cubic_residual_ci": list(cubic_ci),
            "cubic_residual_perm_p": cubic_p,
            "decile_rho": dec, "decile_ci": list(dec_ci), "decile_perm_p": dec_p,
            "mediation": med, "mediation_ci": med_ci,
        }

    rejected, qvals = benjamini_hochberg(cubic_ps)
    out["St1_family"] = {"control": "cubic_residual", "detectors": CALIBRATED,
                         "perm_p": cubic_ps, "bh_q": [float(q) for q in qvals],
                         "bh_reject": [bool(r) for r in rejected]}

    # per-domain (descriptive)
    by_dom = defaultdict(list)
    for i, dm in enumerate(domain):
        by_dom[dm].append(i)
    strata = {}
    for dm, idx in sorted(by_dom.items()):
        if len(idx) >= 10:
            idx = np.array(idx)
            strata[dm] = {"n": len(idx), "loss_vs_frac_rho": spearman(loss[idx], frac[idx])}
            for name in CALIBRATED:
                d = np.array([rows[i][name] for i in idx], float)
                strata[dm][f"{name}_vs_frac_rho"] = spearman(d, frac[idx])
    out["per_domain"] = strata

    os.makedirs(args.results, exist_ok=True)
    with open(os.path.join(args.results, f"hardening_{args.tag}.json"), "w") as f:
        json.dump(out, f, indent=2)

    # ---- print ----
    print(f"\n=== St HARDENING: {args.tag} (N={len(rows)}) ===")
    print(f"{'detector':<16}{'zero':>8}{'lin|loss':>10}{'cubic(P)':>10}{'cubic CI':>20}"
          f"{'decile(S)':>11}{'med.prop':>10}{'BHq':>8}")
    for name, q in zip(CALIBRATED, qvals):
        x = out["detectors"][name]
        ci = x["cubic_residual_ci"]
        prop = x["mediation"]["prop_mediated"]
        print(f"{name:<16}{x['zero_order_rho']:>8.3f}{x['linear_partial_rho']:>10.3f}"
              f"{x['cubic_residual_rho']:>10.3f}{f'[{ci[0]:.3f},{ci[1]:.3f}]':>20}"
              f"{x['decile_rho']:>11.3f}{prop:>10.3f}{q:>8.3f}")
    revived = [n for n, q in zip(CALIBRATED, qvals)
               if out["detectors"][n]["cubic_residual_ci"][0] > 0 and q < 0.05]
    print("\nSt-1 decision (PRIMARY = cubic-residual nonlinear control):")
    print(f"  REVIVED detectors (positive CI excl. 0 + FDR-sig): "
          f"{revived if revived else 'NONE -> null/negative confirmed, not a linearity artifact'}")
    print(f"\nwrote results/hardening_{args.tag}.json")


if __name__ == "__main__":
    main()
