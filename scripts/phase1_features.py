#!/usr/bin/env python
"""What makes a document reproducible? Run on BOTH arms so the two explanations separate.

This implements the advisor's suggested analysis (compare the properties of the documents
that get reproduced against the ones that do not) and runs it on the trained-on arm AND the
never-trained-on arm. The comparison is what makes it diagnostic:

  * a feature that predicts reproduction in BOTH arms is a PREDICTABILITY feature. It says
    the text is easy to complete, whether or not the model was trained on it.
  * a feature that predicts reproduction ONLY in the trained-on arm is a MEMORIZATION
    feature. It says something about what the model retained.

Features are the ones the advisor listed, restricted to those computable without a full
Pile index. Duplication count is NOT computable here (it needs an index of the whole
corpus) and is left to the deduplicated-model comparison instead. Prefix and suffix length
are fixed at 32 and 50 in this item set, so they have no variance to analyse.

Run:
    python scripts/phase1_features.py --model EleutherAI/pythia-160m --device cpu \
        --members results/pile_items_160m.jsonl \
        --nonmembers results/pile_items_nonmem_pythia-160m.jsonl
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import zlib
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def text_features(text):
    b = text.encode("utf-8", "ignore")
    comp = len(zlib.compress(b, 6)) / max(1, len(b))
    words = text.split()
    ttr = len(set(words)) / max(1, len(words))
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    line_rep = 1.0 - (len(set(lines)) / max(1, len(lines))) if lines else 0.0
    digits = sum(c.isdigit() for c in text) / max(1, len(text))
    punct = sum(not c.isalnum() and not c.isspace() for c in text) / max(1, len(text))
    return {
        "compressibility": 1.0 - comp,   # higher = more templated / repetitive
        "repeated_lines": line_rep,
        "digit_frac": digits,
        "punct_frac": punct,
        "type_token_ratio": ttr,         # lower = more repetitive
    }


def rarity_scores(all_texts):
    """Mean unigram log-frequency per text, counts pooled over BOTH arms for comparability."""
    counts = Counter()
    toks = []
    for t in all_texts:
        w = re.findall(r"\w+", t.lower())
        toks.append(w)
        counts.update(w)
    total = sum(counts.values()) or 1
    out = []
    for w in toks:
        if not w:
            out.append(0.0)
            continue
        out.append(float(np.mean([math.log(counts[x] / total) for x in w])))
    return out  # higher = more common words


def spearman(a, b):
    from eval.metrics import spearman as sp
    return sp(np.asarray(a, float), np.asarray(b, float))


def perm_p(a, b, n=5000, seed=0):
    a = np.asarray(a, float); b = np.asarray(b, float)
    obs = abs(spearman(a, b))
    rng = np.random.default_rng(seed)
    ge = sum(1 for _ in range(n) if abs(spearman(a, rng.permutation(b))) >= obs)
    return float((ge + 1) / (n + 1))


def build(rows, prefix_loss, rarity):
    feats = defaultdict(list)
    y = []
    for r, pl, ra in zip(rows, prefix_loss, rarity):
        f = text_features(r["text"])
        for k, v in f.items():
            feats[k].append(v)
        feats["prefix_loss_score"].append(pl)
        feats["word_commonness"].append(ra)
        y.append(r["matched_tokens"])
    return feats, np.array(y, float)


def prefix_loss_for(rows, model, revision, device, dtype, prefix_len):
    """Loss-based score on the PREFIX ONLY, so it never overlaps the extraction target."""
    from detectors import HFScorer, LossDetector
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model, revision=revision)
    sc = HFScorer(model, revision=revision, device=device, dtype=dtype)
    det = LossDetector()
    out = []
    for i, r in enumerate(rows):
        ids = tok(r["text"], add_special_tokens=False)["input_ids"]
        ptxt = tok.decode(ids[:prefix_len], skip_special_tokens=True)
        try:
            out.append(det.score_from_stats(sc.score_tokens(ptxt), ptxt))
        except ValueError:
            out.append(float("nan"))
        if (i + 1) % 150 == 0:
            print(f"    scored {i+1}/{len(rows)}")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--dtype", default=None)
    p.add_argument("--members", required=True)
    p.add_argument("--nonmembers", required=True)
    p.add_argument("--prefix-len", type=int, default=32)
    p.add_argument("--results", default="results")
    args = p.parse_args()

    mem, non = load(args.members), load(args.nonmembers)
    print(f"members={len(mem)}  nonmembers={len(non)}")

    print("  scoring prefixes (members)...")
    pl_m = prefix_loss_for(mem, args.model, args.revision, args.device, args.dtype, args.prefix_len)
    print("  scoring prefixes (non-members)...")
    pl_n = prefix_loss_for(non, args.model, args.revision, args.device, args.dtype, args.prefix_len)

    rar = rarity_scores([r["text"] for r in mem] + [r["text"] for r in non])
    rar_m, rar_n = rar[: len(mem)], rar[len(mem):]

    fm, ym = build(mem, pl_m, rar_m)
    fn, yn = build(non, pl_n, rar_n)

    print("\n" + "=" * 86)
    print("WHICH PROPERTIES PREDICT REPRODUCTION?  (Spearman rho vs matched tokens)")
    print("=" * 86)
    print(f"{'feature':<22}{'MEMBERS':>10}{'p':>9}{'NON-MEMBERS':>14}{'p':>9}   reading")
    report = {}
    for k in fm:
        a, pa = spearman(fm[k], ym), perm_p(fm[k], ym)
        b, pb = spearman(fn[k], yn), perm_p(fn[k], yn)
        sig_a, sig_b = pa < 0.05, pb < 0.05
        if sig_a and sig_b:
            reading = "PREDICTABILITY (both arms)"
        elif sig_a and not sig_b:
            reading = "members only -> possible memorization"
        elif sig_b and not sig_a:
            reading = "non-members only"
        else:
            reading = "no effect"
        report[k] = {"members_rho": a, "members_p": pa, "nonmembers_rho": b,
                     "nonmembers_p": pb, "reading": reading}
        print(f"{k:<22}{a:>+10.3f}{pa:>9.4f}{b:>+14.3f}{pb:>9.4f}   {reading}")

    print("\nper-domain mean matched tokens, both arms (n>=8 members):")
    dm, dn = defaultdict(list), defaultdict(list)
    for r in mem:
        dm[r["pile_set_name"]].append(r["matched_tokens"])
    for r in non:
        dn[r["pile_set_name"]].append(r["matched_tokens"])
    print(f"{'domain':<24}{'members':>10}{'non-mem':>10}")
    for d in sorted(dm, key=lambda x: -np.mean(dm[x])):
        if len(dm[d]) < 8:
            continue
        print(f"{d:<24}{np.mean(dm[d]):>10.2f}{np.mean(dn.get(d,[0])):>10.2f}")

    os.makedirs(args.results, exist_ok=True)
    tag = args.model.split("/")[-1]
    outp = os.path.join(args.results, f"phase1_features_{tag}.json")
    with open(outp, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nwrote {outp}")
    print("\nNOTE: duplication count is not computable without a full-Pile index and is "
          "left to the deduplicated-model comparison. Prefix and suffix lengths are fixed "
          "in this item set, so they have no variance to analyse here.")


if __name__ == "__main__":
    main()
