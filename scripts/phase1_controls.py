#!/usr/bin/env python
"""Phase 1 controls: is the extraction signal memorization, or ordinary predictability?

Two checks, both cheap, both aimed at the same question.

CONTROL A (member vs non-member).
  Compare the extraction outcome on Pile *train* documents (in Pythia's training data)
  against Pile *validation* documents (held out), matched on domain mix. If trained-on
  documents are reproduced no more often than never-trained-on ones, the outcome is
  measuring how predictable the text is rather than what the model retained.

CONTROL B (disjoint predictor and outcome).
  The headline analysis scores the detectors over the whole prefix+suffix window, but
  the outcome lives inside the suffix, so predictor and outcome share most of their
  support. Here we rescore using ONLY the prefix and redo the correlation, so the two
  quantities are computed from disjoint text.

Run:
    python scripts/phase1_controls.py --model EleutherAI/pythia-160m --device cpu \
        --members results/pile_items_160m.jsonl \
        --nonmembers results/pile_items_nonmem_pythia-160m.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def hist(vals, edges=(0, 1, 2, 3, 5, 10, 25, 51)):
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        out.append((f"{lo}" if hi == lo + 1 else f"{lo}-{hi-1}",
                    int(sum(1 for v in vals if lo <= v < hi))))
    return out


def mannwhitney_u_p(a, b, n_perm=20000, seed=0):
    """Permutation p for 'a is stochastically greater than b', tie-aware via ranks."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    both = np.concatenate([a, b])
    order = both.argsort(kind="mergesort")
    ranks = np.empty(len(both), float)
    ranks[order] = np.arange(1, len(both) + 1)
    # average ranks over ties
    _, inv, cnt = np.unique(both, return_inverse=True, return_counts=True)
    sums = np.zeros(len(cnt))
    np.add.at(sums, inv, ranks)
    ranks = (sums / cnt)[inv]
    obs = ranks[: len(a)].mean() - ranks[len(a):].mean()
    rng = np.random.default_rng(seed)
    ge = 0
    for _ in range(n_perm):
        p = rng.permutation(ranks)
        if p[: len(a)].mean() - p[len(a):].mean() >= obs:
            ge += 1
    return float(obs), float((ge + 1) / (n_perm + 1))


def control_a(members, nonmembers):
    print("=" * 74)
    print("CONTROL A: trained-on (members) vs never-trained-on (non-members)")
    print("=" * 74)
    m = [r["matched_tokens"] for r in members]
    n = [r["matched_tokens"] for r in nonmembers]
    mf = [r["frac_extracted"] for r in members]
    nf = [r["frac_extracted"] for r in nonmembers]

    print(f"\n{'':22}{'MEMBERS':>14}{'NON-MEMBERS':>16}")
    print(f"{'N':22}{len(m):>14}{len(n):>16}")
    print(f"{'exact extraction':22}{sum(1 for v in m if v>=50):>14}{sum(1 for v in n if v>=50):>16}")
    print(f"{'mean matched tokens':22}{np.mean(m):>14.3f}{np.mean(n):>16.3f}")
    print(f"{'median matched':22}{np.median(m):>14.1f}{np.median(n):>16.1f}")
    print(f"{'mean frac extracted':22}{np.mean(mf):>14.4f}{np.mean(nf):>16.4f}")
    print(f"{'>=3 tokens':22}{sum(1 for v in m if v>=3):>14}{sum(1 for v in n if v>=3):>16}")
    print(f"{'>=5 tokens':22}{sum(1 for v in m if v>=5):>14}{sum(1 for v in n if v>=5):>16}")

    print("\nmatched-token distribution:")
    hm, hn = dict(hist(m)), dict(hist(n))
    print(f"{'bucket':<10}{'members':>10}{'non-members':>14}")
    for k in hm:
        print(f"{k:<10}{hm[k]:>10}{hn.get(k,0):>14}")

    diff, p = mannwhitney_u_p(m, n)
    print(f"\nrank-mean difference (members - non-members): {diff:+.2f}")
    print(f"permutation p (one-sided, members greater): {p:.4f}")

    print("\nper-domain mean matched tokens (domains with >=8 members):")
    dm, dn = defaultdict(list), defaultdict(list)
    for r in members:
        dm[r["pile_set_name"]].append(r["matched_tokens"])
    for r in nonmembers:
        dn[r["pile_set_name"]].append(r["matched_tokens"])
    print(f"{'domain':<24}{'n_mem':>7}{'members':>10}{'non-mem':>10}{'delta':>9}")
    for d in sorted(dm, key=lambda x: -len(dm[x])):
        if len(dm[d]) < 8 or d not in dn:
            continue
        a, b = np.mean(dm[d]), np.mean(dn[d])
        print(f"{d:<24}{len(dm[d]):>7}{a:>10.2f}{b:>10.2f}{a-b:>+9.2f}")

    return {"n_members": len(m), "n_nonmembers": len(n),
            "mean_matched_members": float(np.mean(m)),
            "mean_matched_nonmembers": float(np.mean(n)),
            "exact_members": int(sum(1 for v in m if v >= 50)),
            "exact_nonmembers": int(sum(1 for v in n if v >= 50)),
            "rank_mean_diff": diff, "perm_p_one_sided": p}


def control_b(members, model, revision, device, dtype, prefix_len):
    print("\n" + "=" * 74)
    print("CONTROL B: detectors scored on the PREFIX ONLY (disjoint from the outcome)")
    print("=" * 74)
    from detectors import build_default_detectors, HFScorer
    from eval.metrics import spearman
    from eval.partial import partial_spearman
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model, revision=revision)
    scorer = HFScorer(model, revision=revision, device=device, dtype=dtype)
    dets = build_default_detectors(scorer)

    full, pref = {d.name: [] for d in dets}, {d.name: [] for d in dets}
    frac, kept = [], 0
    for i, r in enumerate(members):
        ids = tok(r["text"], add_special_tokens=False)["input_ids"]
        ptxt = tok.decode(ids[:prefix_len], skip_special_tokens=True)
        try:
            s_full = scorer.score_tokens(r["text"])
            s_pref = scorer.score_tokens(ptxt)
        except ValueError:
            continue
        for d in dets:
            full[d.name].append(d.score_from_stats(s_full, r["text"]))
            pref[d.name].append(d.score_from_stats(s_pref, ptxt))
        frac.append(float(r["frac_extracted"]))
        kept += 1
        if kept % 100 == 0:
            print(f"  scored {kept}")
    frac = np.array(frac)
    print(f"\nN={kept}, prefix_len={prefix_len} (predictor uses only these tokens)")
    print(f"\n{'detector':<18}{'rho FULL window':>18}{'rho PREFIX only':>18}{'change':>10}")
    out = {}
    for name in full:
        a = spearman(np.array(full[name]), frac)
        b = spearman(np.array(pref[name]), frac)
        out[name] = {"rho_full": a, "rho_prefix_only": b}
        print(f"{name:<18}{a:>18.3f}{b:>18.3f}{b-a:>+10.3f}")

    loss_p = np.array(pref["loss"])
    print(f"\npartial rho given PREFIX-ONLY loss (the incremental-value test, redone):")
    for name in pref:
        if name == "loss":
            continue
        pr = partial_spearman(np.array(pref[name]), frac, loss_p)
        out[name]["partial_given_prefix_loss"] = pr
        print(f"  {name:<18}{pr:>+8.3f}")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--dtype", default=None)
    p.add_argument("--members", required=True)
    p.add_argument("--nonmembers", default=None)
    p.add_argument("--prefix-len", type=int, default=32)
    p.add_argument("--results", default="results")
    p.add_argument("--skip-b", action="store_true")
    args = p.parse_args()

    members = load(args.members)
    report = {"model": args.model, "members_file": args.members}

    if args.nonmembers and os.path.exists(args.nonmembers):
        report["control_a"] = control_a(members, load(args.nonmembers))
    else:
        print("CONTROL A skipped: no non-member file yet")

    if not args.skip_b:
        report["control_b"] = control_b(members, args.model, args.revision,
                                        args.device, args.dtype, args.prefix_len)

    os.makedirs(args.results, exist_ok=True)
    tag = args.model.split("/")[-1]
    outp = os.path.join(args.results, f"phase1_controls_{tag}.json")
    with open(outp, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nwrote {outp}")


if __name__ == "__main__":
    main()
