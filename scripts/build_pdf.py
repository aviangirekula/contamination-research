#!/usr/bin/env python
"""Render the full paper (PAPER_DRAFT_FULL.md, pandoc-gfm of paper/*.tex) to a real PDF via
reportlab. No LaTeX engine needed. Handles ATX headings, paragraphs, bullet lists, blockquotes,
pipe tables, and inline **bold**/*italic*/`code`. Uses DejaVuSans (bundled with matplotlib) for
full Unicode coverage (ρ, →, ≈, etc.).

This is a readable working-draft PDF, NOT the LaTeX typesetting. For the camera-ready, compile
paper/main.tex with pdflatex/Overleaf.

Run: python scripts/build_pdf.py --md PAPER_DRAFT_FULL.md --out paper/main.pdf
"""
from __future__ import annotations

import argparse
import os
import re
import sys


def register_unicode_font():
    import matplotlib
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    d = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    faces = {"DejaVu": "DejaVuSans.ttf", "DejaVu-Bold": "DejaVuSans-Bold.ttf",
             "DejaVu-Oblique": "DejaVuSans-Oblique.ttf",
             "DejaVu-BoldOblique": "DejaVuSans-BoldOblique.ttf",
             "DejaVuMono": "DejaVuSansMono.ttf"}
    for name, fn in faces.items():
        pdfmetrics.registerFont(TTFont(name, os.path.join(d, fn)))
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold",
                       italic="DejaVu-Oblique", boldItalic="DejaVu-BoldOblique")


def clean(text: str) -> str:
    text = text.replace("<!-- -->", "")
    # unescape common pandoc gfm backslash-escapes
    for a in ["[", "]", "%", "_", "&", "$", "#", "~", "*", "\\"]:
        text = text.replace("\\" + a, a)
    return text


def inline(text: str) -> str:
    """Escape XML then apply bold/italic/code -> reportlab markup."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r'<font face="DejaVuMono" size="8.5">\1</font>', text)
    return text


def is_table_sep(row: str) -> bool:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return all(re.fullmatch(r":?-{2,}:?", c or "-") for c in cells) and len(cells) > 0


def build(md_path: str, out_path: str, title: str):
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (ListFlowable, ListItem, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle)

    register_unicode_font()
    ss = getSampleStyleSheet()
    def style(name, **kw):
        base = dict(fontName="DejaVu", fontSize=10, leading=13.5, spaceAfter=6)
        base.update(kw); return ParagraphStyle(name, **base)
    S = {
        "title": style("t", fontName="DejaVu-Bold", fontSize=16, leading=20, spaceAfter=14, alignment=TA_LEFT),
        "h1": style("h1", fontName="DejaVu-Bold", fontSize=13.5, leading=17, spaceBefore=12, spaceAfter=6),
        "h2": style("h2", fontName="DejaVu-Bold", fontSize=11.5, leading=15, spaceBefore=9, spaceAfter=4),
        "h3": style("h3", fontName="DejaVu-Bold", fontSize=10.5, leading=13, spaceBefore=7, spaceAfter=3),
        "body": style("b", alignment=TA_JUSTIFY),
        "bullet": style("bu", alignment=TA_LEFT, leftIndent=6),
        "quote": style("q", fontName="DejaVu-Oblique", leftIndent=14, textColor=colors.HexColor("#444444")),
        "cell": style("c", fontSize=8, leading=10, spaceAfter=0),
        "cellh": style("ch", fontName="DejaVu-Bold", fontSize=8, leading=10, spaceAfter=0),
    }

    lines = open(md_path, encoding="utf-8").read().split("\n")
    flow = [Paragraph(title, S["title"])]
    i, n = 0, len(lines)
    para, bullets = [], []

    def flush_para():
        nonlocal para
        if para:
            flow.append(Paragraph(inline(clean(" ".join(para))), S["body"])); para = []

    def flush_bullets():
        nonlocal bullets
        if bullets:
            items = [ListItem(Paragraph(inline(clean(b)), S["bullet"]), leftIndent=12) for b in bullets]
            flow.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=10)); bullets = []

    while i < n:
        ln = lines[i]
        if re.match(r"^\s*\|", ln) and i + 1 < n and is_table_sep(lines[i + 1]):
            flush_para(); flush_bullets()
            rows = []
            header = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2  # skip header + separator
            while i < n and re.match(r"^\s*\|", lines[i]):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            data = [[Paragraph(inline(clean(c)), S["cellh"]) for c in header]]
            for r in rows:
                r = (r + [""] * len(header))[:len(header)]
                data.append([Paragraph(inline(clean(c)), S["cell"]) for c in r])
            avail = 7.0 * inch
            t = Table(data, colWidths=[avail / len(header)] * len(header), hAlign="LEFT")
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            flow.append(Spacer(1, 4)); flow.append(t); flow.append(Spacer(1, 8))
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m:
            flush_para(); flush_bullets()
            lvl = len(m.group(1)); txt = inline(clean(m.group(2)))
            flow.append(Paragraph(txt, S.get(f"h{min(lvl,3)}", S["h3"])))
        elif re.match(r"^\s*[-*]\s+", ln):
            flush_para(); bullets.append(re.sub(r"^\s*[-*]\s+", "", ln))
        elif ln.strip().startswith(">"):
            flush_para(); flush_bullets()
            flow.append(Paragraph(inline(clean(ln.strip().lstrip(">").strip())), S["quote"]))
        elif not ln.strip():
            flush_para(); flush_bullets()
        else:
            if bullets and ln.startswith("  "):
                bullets[-1] += " " + ln.strip()
            else:
                flush_bullets(); para.append(ln.strip())
        i += 1
    flush_para(); flush_bullets()

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    doc = SimpleDocTemplate(out_path, pagesize=letter, topMargin=0.8 * inch,
                            bottomMargin=0.8 * inch, leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                            title=title)
    doc.build(flow)
    print(f"wrote {out_path}  ({os.path.getsize(out_path)//1024} KB, {len(flow)} flowables)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", default="PAPER_DRAFT_FULL.md")
    ap.add_argument("--out", default="paper/main.pdf")
    ap.add_argument("--title", default="Benchmark Contamination as a Privacy/Security "
                    "Vulnerability in Large Language Models (working draft, Pythia-160m)")
    a = ap.parse_args()
    build(a.md, a.out, a.title)


if __name__ == "__main__":
    main()
