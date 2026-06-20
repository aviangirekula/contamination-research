#!/usr/bin/env python
"""Experiment runner: Models x Detectors x Datasets, with result caching.

Computes `TokenStats` once per (model, text) and feeds every detector, then writes
per-item scores + labels to a cache so the matrix is resumable. Metrics and figures
are produced by `eval/`. This is the scaffold entry point; the real data loaders
(Pile membership, MIMIR splits, benchmark items) plug into `load_dataset_split`.

Usage:
    python run.py --self-test                  # mock end-to-end, no model download
    python run.py --config configs/pythia160m_pilemia.yaml   # real run (needs torch+HF)
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass

import numpy as np


@dataclass
class Item:
    text: str
    label: int          # 1 = member / contaminated, 0 = non-member / clean
    item_id: str


def load_dataset_split(name: str):
    """Return a list[Item]. Real loaders (Pile/MIMIR/benchmarks) go here.

    The scaffold ships a tiny synthetic split so `--self-test` exercises the full path.
    """
    if name == "synthetic":
        rng = np.random.default_rng(0)
        items = []
        for i in range(50):
            items.append(Item(text=f"member document number {i} " * 5, label=1, item_id=f"m{i}"))
            items.append(Item(text=f"unseen heldout text {rng.integers(1e9)} " * 5, label=0, item_id=f"n{i}"))
        return items
    raise NotImplementedError(
        f"dataset loader '{name}' not implemented yet; see docs/experiment_design.md section 3"
    )


def build_scorer(args):
    if args.self_test:
        from detectors import MockScorer

        members = set()  # populated below once items are known
        return MockScorer(), members
    from detectors import HFScorer

    return HFScorer(args.model, revision=args.revision, device=args.device), None


def run(args):
    from detectors import build_default_detectors
    from eval.metrics import mia_report

    items = load_dataset_split(args.dataset)

    if args.self_test:
        from detectors import MockScorer

        member_texts = {it.text for it in items if it.label == 1}
        scorer = MockScorer(membership_fn=lambda t: t in member_texts, signal=1.5)
    else:
        scorer, _ = build_scorer(args)

    detectors = build_default_detectors(scorer)
    rows = []
    for it in items:
        try:
            stats = scorer.score_tokens(it.text)
        except ValueError:
            continue
        row = {"item_id": it.item_id, "label": it.label}
        for det in detectors:
            row[det.name] = det.score_from_stats(stats, it.text)
        rows.append(row)

    os.makedirs(args.out, exist_ok=True)
    cache_path = os.path.join(args.out, f"{args.dataset}_scores.jsonl")
    with open(cache_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    labels = np.array([r["label"] for r in rows])
    print(f"\nWrote {len(rows)} rows -> {cache_path}\n")
    print(f"{'detector':<18}{'AUC':>8}{'TPR@1%':>10}{'TPR@0.1%':>10}")
    for det in detectors:
        scores = np.array([r[det.name] for r in rows])
        rep = mia_report(scores, labels)
        print(f"{det.name:<18}{rep.auc:>8.3f}{rep.tpr_at_1:>10.3f}{rep.tpr_at_0p1:>10.3f}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true", help="mock run, no model download")
    p.add_argument("--config", default=None, help="YAML config path (real runs)")
    p.add_argument("--dataset", default="synthetic")
    p.add_argument("--model", default="EleutherAI/pythia-160m")
    p.add_argument("--revision", default=None)
    p.add_argument("--device", default="cpu")
    p.add_argument("--out", default="results")
    args = p.parse_args()

    if args.config:
        import yaml  # optional dep; only needed for real configs

        with open(args.config) as f:
            cfg = yaml.safe_load(f)
        for k, v in cfg.items():
            setattr(args, k.replace("-", "_"), v)

    run(args)


if __name__ == "__main__":
    main()
