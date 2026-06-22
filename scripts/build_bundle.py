#!/usr/bin/env python
"""Assemble the ENTIRE project (paper + docs + code + config + result summaries) into
one self-contained BUNDLE.md for external review. Run from the repo root."""
import glob
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)

LANG = {".py": "python", ".tex": "latex", ".md": "markdown", ".bib": "bibtex",
        ".yaml": "yaml", ".yml": "yaml", ".json": "json", ".txt": "text"}


def fence_for(content):
    """A backtick fence longer than the longest run inside the content (>=3)."""
    longest = 0
    run = 0
    for ch in content:
        run = run + 1 if ch == "`" else 0
        longest = max(longest, run)
    return "`" * max(3, longest + 1)


def block(path):
    p = pathlib.Path(path)
    if not p.exists():
        return f"\n*(missing: {path})*\n"
    content = p.read_text(errors="replace")
    lang = LANG.get(p.suffix, "")
    f = fence_for(content)
    return f"\n### `{path}`\n\n{f}{lang}\n{content}\n{f}\n"


PARTS = [
    ("PART 1 — THE PAPER (readable prose, full draft)", ["PAPER_DRAFT_FULL.md"]),
    ("PART 2 — RESULTS, EXPERIMENT DESIGN & ANALYSIS (docs)", [
        "docs/controls_report.md", "docs/hardening_report.md", "docs/contamination_matrix.md",
        "docs/results_table.md", "findings.md", "docs/pre_analysis.md",
        "docs/novelty_memo.md", "docs/consistency_audit.md", "docs/adversary_review.md",
        "docs/reviewer_concerns.md", "docs/milestone1_report.md",
        "docs/integration_report.md", "docs/method_selection_memo.md",
        "docs/experiment_design.md", "docs/glossary.md", "README.md",
    ]),
    ("PART 3 — ALL CODE (detectors / extraction / eval)", [
        "detectors/base.py", "detectors/loss.py", "detectors/mink.py",
        "detectors/minkpp.py", "detectors/zlib_ratio.py", "detectors/ngram_overlap.py",
        "detectors/oren_permutation.py", "detectors/scorers.py", "detectors/__init__.py",
        "extraction/extract.py", "extraction/pii.py", "extraction/__init__.py",
        "eval/metrics.py", "eval/partial.py", "eval/mediation.py", "eval/__init__.py",
    ]),
    ("PART 4 — ALL EXPERIMENT SCRIPTS & RUNNER", [
        "run.py", "conftest.py",
        "scripts/milestone1_pile.py", "scripts/milestone1_wikimia.py",
        "scripts/milestone1_separation.py", "scripts/extraction_pile.py",
        "scripts/pii_enron.py", "scripts/correlation_160m.py",
        "scripts/controls_160m.py", "scripts/hardening_160m.py",
        "scripts/collinearity_check.py", "scripts/contamination_matrix.py",
        "scripts/validate_ngram_oren.py", "scripts/plot_from_scores.py",
        "scripts/plot_hardening.py", "scripts/build_bundle.py",
    ]),
    ("PART 5 — ALL TESTS", sorted(glob.glob("tests/test_*.py"))),
    ("PART 6 — PAPER SOURCE (LaTeX)", [
        "paper/main.tex", "paper/abstract.tex", "paper/introduction.tex",
        "paper/background.tex", "paper/threat_model.tex", "paper/related_work.tex",
        "paper/evaluation.tex", "paper/datasets_table.tex", "paper/results.tex",
        "paper/discussion.tex", "paper/limitations.tex", "paper/conclusion.tex",
    ]),
    ("PART 7 — CONFIG, ENV & BIBLIOGRAPHY", [
        "requirements.txt", "configs/pythia160m_cpu.yaml",
        "configs/pythia1.4b_gpu.yaml", "references.bib",
    ]),
    ("PART 8 — RAW RESULT SUMMARIES (the actual numbers)", sorted(
        glob.glob("results/*summary*.json") + glob.glob("results/correlation_*.json")
        + glob.glob("results/controls_[a-z]*.json") + glob.glob("results/hardening_*.json")
        + glob.glob("results/collinearity_*.json") + glob.glob("results/contamination_matrix.json"))),
]

HEADER = """# COMPLETE PROJECT BUNDLE — Benchmark Contamination as a Privacy/Security Vulnerability in LLMs

**This single file contains the ENTIRE project for external assessment:** the full paper
(front matter), every results/analysis doc, ALL source code, all experiment scripts, all
tests, the LaTeX source, config, the verified bibliography, and the raw result-summary JSONs.

**Read me first — critical context:**
- **Honest scope:** the contribution is a security *reframing* + *systematic comparison of
  existing detectors* + an empirical contamination->leakage analysis. It is NOT a novel
  detector/metric.
- **Status:** paper = front matter only (Abstract, Method/Matrix, Results, Discussion,
  Conclusion still to be written). Experiments = real, reproducible, Pythia-160m on CPU
  (GPU scale-up pending).
- **THE KEY FINDING (R6 control, pre-registered):** the contamination->leakage correlation
  does NOT survive controlling for raw loss. Raw loss predicts extraction (Spearman rho ~0.28);
  the calibrated detectors (Min-K%, Min-K%++, zlib) add NO predictive value beyond loss
  (partial rho|loss: Min-K% -0.18, Min-K%++ -0.15, both FDR-significant & NEGATIVE; zlib ~0).
  Robust to dedup; not a frequency/zero-inflation artifact. The honest reframing is the
  DIVERGENCE between membership-detection and leakage-prediction. See PART 2 -> controls_report.
- **Tests:** 53/53 pass.

---
"""


def main():
    out = [HEADER]
    for title, files in PARTS:
        out.append(f"\n\n# {title}\n")
        for f in files:
            out.append(block(f))
    text = "\n".join(out)
    pathlib.Path("BUNDLE.md").write_text(text)
    print(f"wrote BUNDLE.md  ({len(text):,} chars, ~{len(text)//4:,} tokens est.)")


if __name__ == "__main__":
    main()
