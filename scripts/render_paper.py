#!/usr/bin/env python
"""Render the full paper from paper/*.tex to APA-cited Markdown, HTML, and PDF.

Pipeline: sanitize references.bib (strip the inline % comments that break pandoc's bib
reader) -> concatenate paper sections (inline the datasets table) keeping \\citep/\\citet ->
pandoc --citeproc with the APA CSL (paper/apa.csl) to render in-text (Author, Year) APA
citations and an APA "References" section -> reportlab PDF from the rendered Markdown.

Run from the repo root:  python scripts/render_paper.py
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)
ORDER = ["abstract", "introduction", "background", "threat_model", "related_work",
         "evaluation", "results", "discussion", "limitations", "conclusion"]


def sanitize_bib():
    s = pathlib.Path("references.bib").read_text()
    clean = "\n".join(re.sub(r"(?<!\\)%.*$", "", ln) for ln in s.split("\n"))
    pathlib.Path("/tmp/refs_clean.bib").write_text(clean)


def combine_tex():
    parts = []
    for fn in ORDER:
        t = pathlib.Path(f"paper/{fn}.tex").read_text()
        if fn == "evaluation":
            t = t.replace(r"\input{datasets_table}", pathlib.Path("paper/datasets_table.tex").read_text())
        parts.append(t)
    pathlib.Path("/tmp/full_cites.tex").write_text("\n\n".join(parts))


def main():
    sanitize_bib()
    combine_tex()
    csl = "paper/apa.csl"
    common = ["--citeproc", "--bibliography=/tmp/refs_clean.bib",
              "--metadata", "reference-section-title=References"]
    if os.path.exists(csl):
        common += ["--csl", csl]
    else:
        print("WARNING: paper/apa.csl missing; falling back to pandoc default (Chicago) style")

    subprocess.run(["pandoc", "/tmp/full_cites.tex", *common, "-t", "gfm",
                    "-o", "PAPER_DRAFT_FULL.md"], check=True)
    # Strip citeproc's <div> wrappers around the bibliography so the references render as
    # clean APA paragraphs (one per entry) in the Markdown and the reportlab PDF.
    md = pathlib.Path("PAPER_DRAFT_FULL.md")
    kept = []
    for ln in md.read_text().split("\n"):
        if re.match(r"^\s*</?div\b", ln) or re.match(r'^\s*[\w-]+="[^"]*">\s*$', ln):
            continue
        kept.append(ln)
    md.write_text(re.sub(r"\n{3,}", "\n\n", "\n".join(kept)))
    subprocess.run(["pandoc", "/tmp/full_cites.tex", *common, "-s", "--toc",
                    "-o", "paper/main.html", "--metadata",
                    "title=Benchmark Contamination as a Privacy/Security Vulnerability in LLMs (working draft)"],
                   check=True)
    subprocess.run([sys.executable, "scripts/build_pdf.py", "--md", "PAPER_DRAFT_FULL.md",
                    "--out", "paper/main.pdf"], check=True)
    print("rendered: PAPER_DRAFT_FULL.md, paper/main.html, paper/main.pdf (APA citations + References)")


if __name__ == "__main__":
    main()
