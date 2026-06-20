#!/usr/bin/env python
"""Validate the n-gram overlap check and the Oren permutation test on real Pile data.

Reuses the Pile train-vs-val construction from milestone1_pile.py:
  * MEMBERS     = Pile *train* docs (NeelNanda/pile-10k)        -> in Pythia's training data
  * NON-MEMBERS = Pile *validation* docs (mit-han-lab/pile-val-backup) -> held out

n-gram overlap (corpus-side, no model):
  Build the index from MEMBER texts, then score members vs non-members. Members are *in* the
  index corpus, so they should show much higher n-gram overlap than the held-out non-members.
  We report mean overlap for each group and a separation number (member_mean - nonmember_mean).

Oren permutation test (model-side, order-sensitive):
  Treat ~10 member examples as a "contaminated ordered set" and ~10 non-members as a control,
  and report each group's p-value under the target model. With a small CPU model and short
  examples this is a sanity demonstration of the interface on real text, not a strong claim.

Run:
    python scripts/validate_ngram_oren.py --model EleutherAI/pythia-160m \
        --n-per-class 50 --max-words 60 --device cpu
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.milestone1_pile import build_split  # reuse the exact split logic


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default="main")
    p.add_argument("--device", default="cpu")
    p.add_argument("--n-per-class", type=int, default=50)
    p.add_argument("--max-words", type=int, default=60)
    p.add_argument("--min-words", type=int, default=25)
    p.add_argument("--ngram-n", type=int, default=13)
    p.add_argument("--oren-k", type=int, default=10, help="examples per Oren group")
    p.add_argument("--oren-words", type=int, default=20, help="truncate Oren examples to keep CPU cheap")
    p.add_argument("--n-permutations", type=int, default=500)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    from detectors import NGramOverlapDetector, OrenPermutationTest, HFScorer

    texts, labels = build_split(args.n_per_class, args.max_words, args.min_words, args.seed)
    texts = np.array(texts, dtype=object)
    labels = np.asarray(labels)
    members = list(texts[labels == 1])
    nonmembers = list(texts[labels == 0])

    # ---------------------------------------------------------------- n-gram overlap
    print(f"\n=== n-gram overlap (n={args.ngram_n}), index built from {len(members)} MEMBER texts ===")
    det = NGramOverlapDetector(n=args.ngram_n).build_index(members)
    print(f"index size: {det.index_size} distinct {args.ngram_n}-grams")

    mem_scores = np.array([det.score(t) for t in members])
    non_scores = np.array([det.score(t) for t in nonmembers])
    mem_mean, non_mean = float(mem_scores.mean()), float(non_scores.mean())
    print(f"member   mean overlap: {mem_mean:.4f}  (min {mem_scores.min():.3f}, max {mem_scores.max():.3f})")
    print(f"nonmember mean overlap: {non_mean:.4f}  (min {non_scores.min():.3f}, max {non_scores.max():.3f})")
    print(f"separation (member - nonmember): {mem_mean - non_mean:+.4f}")
    flagged_non = int((non_scores > 0).sum())
    print(f"non-members with ANY {args.ngram_n}-gram overlap: {flagged_non}/{len(nonmembers)} "
          f"(near-duplicate / boilerplate leakage)")

    # ---------------------------------------------------------------- Oren permutation test
    def trunc(t):
        return " ".join(t.split()[: args.oren_words])

    k = args.oren_k
    contaminated = [trunc(t) for t in members[:k]]
    control = [trunc(t) for t in nonmembers[:k]]

    print(f"\n=== Oren permutation test (model={args.model}, {k} examples/group, "
          f"{args.n_permutations} permutations) ===")
    scorer = HFScorer(args.model, revision=args.revision, device=args.device)
    test = OrenPermutationTest(scorer)

    cont_res = test.test(contaminated, n_permutations=args.n_permutations, seed=args.seed)
    ctrl_res = test.test(control, n_permutations=args.n_permutations, seed=args.seed)

    def show(tag, r):
        print(f"{tag:<26} p={r['p_value']:.4f}  canonical_ll={r['canonical_loglik']:.2f}  "
              f"null_mean={r['null_mean']:.2f}  null_std={r['null_std']:.2f}")

    show("contaminated (members)", cont_res)
    show("control (non-members)", ctrl_res)

    print("\n--- SUMMARY ---")
    print(f"ngram: member_mean={mem_mean:.4f} nonmember_mean={non_mean:.4f} "
          f"separation={mem_mean - non_mean:+.4f}")
    print(f"oren:  contaminated_p={cont_res['p_value']:.4f} control_p={ctrl_res['p_value']:.4f}")


if __name__ == "__main__":
    main()
