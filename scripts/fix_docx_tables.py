#!/usr/bin/env python
"""Fix pandoc's zero-width tables in a .docx.

pandoc 2.12 emits <w:tblW w:type="pct" w:w="0.0"/> with no <w:tblGrid> and no cell
widths for tables that have no explicit LaTeX column widths. Renderers (Word, Pages,
Quick Look) then collapse every column to ~one character wide and text wraps vertically.

This rewrites each table to: fixed layout, full text-width (9360 dxa = 6.5in), an explicit
tblGrid, and per-cell widths sized in proportion to each column's longest content. Columns
then render at sensible widths and long cells wrap normally.

Usage:  python scripts/fix_docx_tables.py paper/main.docx
"""
from __future__ import annotations
import io, re, sys, zipfile, pathlib

TOTAL = 9360           # text width in twips (US Letter, 1in margins)
MIN_COL = 620          # never let a column get narrower than ~0.43in
CLAMP = 60             # cap a column's content-weight so one huge cell can't starve others


def cell_text(tc: str) -> str:
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", tc))


def col_widths(rows):
    ncol = max((len(r) for r in rows), default=0)
    maxlen = [1] * ncol
    for r in rows:
        for i, txt in enumerate(r):
            maxlen[i] = max(maxlen[i], len(txt.strip()))
    weights = [min(max(m, 3), CLAMP) for m in maxlen]
    s = sum(weights) or 1
    widths = [max(int(TOTAL * w / s), MIN_COL) for w in weights]
    widths[-1] += TOTAL - sum(widths)   # absorb rounding into last column
    return widths


def fix_table(tbl: str) -> str:
    trs = re.findall(r"<w:tr\b.*?</w:tr>", tbl, re.S)
    rows = [[cell_text(tc) for tc in re.findall(r"<w:tc>.*?</w:tc>", tr, re.S)] for tr in trs]
    if not any(rows):
        return tbl
    widths = col_widths(rows)
    ncol = len(widths)

    # --- tblPr: full width + fixed layout (schema order: ... tblW, tblLayout, tblLook ...)
    def fix_tblpr(m):
        pr = re.sub(r"<w:tblLayout[^/]*/>", "", m.group(0))
        pr = re.sub(r"<w:tblW[^/]*/>",
                    f'<w:tblW w:type="dxa" w:w="{TOTAL}"/><w:tblLayout w:type="fixed"/>',
                    pr, count=1)
        return pr
    tbl = re.sub(r"<w:tblPr>.*?</w:tblPr>", fix_tblpr, tbl, count=1, flags=re.S)

    # --- tblGrid (replace or insert right after tblPr)
    grid = "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"
    if "<w:tblGrid>" in tbl:
        tbl = re.sub(r"<w:tblGrid>.*?</w:tblGrid>", grid, tbl, count=1, flags=re.S)
    else:
        tbl = re.sub(r"</w:tblPr>", "</w:tblPr>" + grid, tbl, count=1)

    # --- per-cell widths (tcW is the first child of tcPr per schema)
    def fix_row(trm):
        idx = [0]

        def fix_tc(tcm):
            tc = tcm.group(0)
            i = min(idx[0], ncol - 1)
            idx[0] += 1
            tcw = f'<w:tcW w:type="dxa" w:w="{widths[i]}"/>'
            if "<w:tcPr>" in tc:
                if "<w:tcW" in tc:
                    tc = re.sub(r"<w:tcW[^/]*/>", tcw, tc, count=1)
                else:
                    tc = tc.replace("<w:tcPr>", "<w:tcPr>" + tcw, 1)
            else:
                tc = tc.replace("<w:tc>", "<w:tc><w:tcPr>" + tcw + "</w:tcPr>", 1)
            return tc
        return re.sub(r"<w:tc>.*?</w:tc>", fix_tc, trm.group(0), flags=re.S)

    return re.sub(r"<w:tr\b.*?</w:tr>", fix_row, tbl, flags=re.S)


def main(path):
    p = pathlib.Path(path)
    zin = zipfile.ZipFile(p)
    xml = zin.read("word/document.xml").decode("utf-8")
    n = [0]

    def repl(m):
        n[0] += 1
        return fix_table(m.group(0))
    xml = re.sub(r"<w:tbl>.*?</w:tbl>", repl, xml, flags=re.S)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = xml.encode("utf-8") if item.filename == "word/document.xml" else zin.read(item.filename)
            zout.writestr(item, data)
    zin.close()
    p.write_bytes(buf.getvalue())
    print(f"fixed {n[0]} tables in {p}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "paper/main.docx")
