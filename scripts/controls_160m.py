#!/usr/bin/env python
"""Controls run (R6 primary + R1/R7 + strata) on an existing item set.

Re-scores the items' EXACT text with the membership detectors (deterministic), reuses
their leakage outcomes, and computes raw / partial(|loss) / semipartial / freq-matched
correlations with bootstrap CIs, permutation p, Kendall tau, BH-FDR over the R6 family,
and per-domain stratification. See docs/pre_analysis.md for the pre-registered plan.

Run:
    python scripts/controls_160m.py --model EleutherAI/pythia-160m \
        --items results/pile_items_160m.jsonl --tag pythia-160m
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CALIBRATED = ["min_20_prob", "min_20_plusplus", "zlib_ratio"]  # R6 family (control = loss)


def freq_proxy(texts):
    """Per-item mean unigram log-frequency (whitespace tokens, counts over the item union)."""
    counts = Counter()
    toks_per = []
    for t in texts:
        toks = t.split()
        toks_per.append(toks)
        counts.update(toks)
    total = sum(counts.values())
    out = []
    for toks in toks_per:
        if not toks:
            out.append(0.0)
            continue
        out.append(float(np.mean([np.log(counts[w] / total) for w in toks])))
    return np.array(out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--items", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--results", default="results")
    p.add_argument("--n-boot", type=int, default=2000)
    p.add_argument("--n-perm", type=int, default=2000)
    args = p.parse_args()

    from detectors import build_default_detectors, HFScorer
    from eval.partial import (
        benjamini_hochberg, bootstrap_ci, kendall_tau, partial_spearman,
        permutation_p_partial, permutation_p_spearman, semipartial_spearman, spearman,
    )

    items = [json.loads(l) for l in open(args.items)]
    texts = [it["text"] for it in items]
    frac = np.array([float(it["frac_extracted"]) for it in items])
    domain = [it.get("pile_set_name", "?") for it in items]
    print(f"{args.tag}: {len(items)} items, mean frac={frac.mean():.4f}, "
          f"fully={int((frac>=1.0).sum())}")

    scorer = HFScorer(args.model, revision=args.revision, device=args.device)
    dets = build_default_detectors(scorer)  # [loss, min_20_prob, min_20_plusplus, zlib_ratio]
    scores = {d.name: [] for d in dets}
    for i, t in enumerate(texts):
        st = scorer.score_tokens(t)
        for d in dets:
            scores[d.name].append(d.score_from_stats(st, t))
        if (i + 1) % 50 == 0:
            print(f"  scored {i+1}/{len(texts)}")
    scores = {k: np.array(v) for k, v in scores.items()}
    loss = scores["loss"]

    # persist per-example scores (so controls are reproducible without re-inference)
    os.makedirs(args.results, exist_ok=True)
    with open(os.path.join(args.results, f"controls_scores_{args.tag}.jsonl"), "w") as f:
        for i in range(len(items)):
            f.write(json.dumps({"item_id": items[i].get("item_id", i),
                                "frac_extracted": float(frac[i]), "pile_set_name": domain[i],
                                **{k: float(scores[k][i]) for k in scores}}) + "\n")

    fp = freq_proxy(texts)
    mid = (fp >= np.quantile(fp, 1/3)) & (fp <= np.quantile(fp, 2/3))  # middle tertile

    out = {"model": args.model, "tag": args.tag, "n": len(items),
           "mean_frac": float(frac.mean()), "detectors": {}}

    # raw correlations (all 4 detectors)
    for name in scores:
        s = scores[name]
        out["detectors"][name] = {
            "raw_rho": spearman(s, frac),
            "raw_ci": list(bootstrap_ci(spearman, (s, frac), args.n_boot)),
            "raw_kendall": kendall_tau(s, frac),
            "raw_perm_p": permutation_p_spearman(s, frac, args.n_perm),
        }

    # R6 partial/semipartial controlling for loss (calibrated detectors only)
    perm_ps = []
    for name in CALIBRATED:
        s = scores[name]
        pr = partial_spearman(s, frac, loss)
        pci = bootstrap_ci(lambda a, b, c: partial_spearman(a, b, c),
                           (s, frac, loss), args.n_boot)
        pp = permutation_p_partial(s, frac, loss, args.n_perm)
        perm_ps.append(pp)
        out["detectors"][name].update({
            "partial_rho_given_loss": pr,
            "partial_ci": list(pci),
            "partial_perm_p": pp,
            "partial_kendall_resid": None,  # Kendall on residuals not defined simply; omit
            "semipartial_rho": semipartial_spearman(s, frac, loss),
            "freqmatched_rho": spearman(s[mid], frac[mid]),
            "freqmatched_n": int(mid.sum()),
            "partial_rho_given_freq": partial_spearman(s, frac, fp),
        })

    rejected, qvals = benjamini_hochberg(perm_ps)
    out["R6_family"] = {
        "detectors": CALIBRATED,
        "perm_p": perm_ps,
        "bh_qvalues": [float(q) for q in qvals],
        "bh_rejected": [bool(r) for r in rejected],
    }

    # per-domain raw rho (stratification)
    by_dom = defaultdict(list)
    for i, d in enumerate(domain):
        by_dom[d].append(i)
    strata = {}
    for d, idx in sorted(by_dom.items()):
        if len(idx) >= 5:
            idx = np.array(idx)
            strata[d] = {"n": len(idx),
                         "loss_rho": spearman(loss[idx], frac[idx])}
    out["per_domain_loss_rho"] = strata

    with open(os.path.join(args.results, f"controls_{args.tag}.json"), "w") as f:
        json.dump(out, f, indent=2)

    # ---- print summary table ----
    print(f"\n=== CONTROLS: {args.tag} (N={len(items)}) ===")
    print(f"{'detector':<16}{'raw rho':>9}{'partial|loss':>14}{'partial CI':>20}"
          f"{'semipart':>10}{'freqmatch':>11}{'kendall':>9}")
    for name in scores:
        d = out["detectors"][name]
        pr = d.get("partial_rho_given_loss")
        ci = d.get("partial_ci")
        ci_s = f"[{ci[0]:.3f},{ci[1]:.3f}]" if ci else "  (control=loss) "
        prs = f"{pr:.3f}" if pr is not None else "    --"
        sp = f"{d.get('semipartial_rho'):.3f}" if d.get("semipartial_rho") is not None else "  --"
        fm = f"{d.get('freqmatched_rho'):.3f}" if d.get("freqmatched_rho") is not None else "  --"
        print(f"{name:<16}{d['raw_rho']:>9.3f}{prs:>14}{ci_s:>20}{sp:>10}{fm:>11}{d['raw_kendall']:>9.3f}")
    print("\nR6 family (control=loss), BH-FDR:")
    for name, pp, q, r in zip(CALIBRATED, perm_ps, qvals, rejected):
        print(f"  {name:<16} perm_p={pp:.4f}  BH_q={q:.4f}  reject_null={bool(r)}")
    print(f"\nwrote results/controls_{args.tag}.json")


if __name__ == "__main__":
    main()
