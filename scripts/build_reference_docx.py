#!/usr/bin/env python
"""Build paper/reference.docx: a pandoc reference document that gives the .docx an
IEEE-conference typographic look (Times New Roman, justified body, small-caps centered
section headings, italic subsection headings, small-caps centered table captions, black
hyperlinks). Section/table NUMBERING is added separately by paper/ieee.lua at render time.

Run from repo root:  python scripts/build_reference_docx.py
"""
from __future__ import annotations
import pathlib, re, shutil, subprocess, zipfile, io

ROOT = pathlib.Path(__file__).resolve().parent.parent
PANDOC = shutil.which("pandoc") or "/opt/anaconda3/bin/pandoc"
TNR = 'w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman"'

# Full replacement <w:style> blocks, keyed by styleId.
STYLES = {
    "Heading1": f'''<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="260" w:after="120"/><w:jc w:val="center"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:rFonts {TNR}/><w:b/><w:bCs/><w:smallCaps/><w:color w:val="000000"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>''',
    "Heading2": f'''<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="160" w:after="60"/><w:jc w:val="left"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:rFonts {TNR}/><w:i/><w:iCs/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>''',
    "Heading3": f'''<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="Heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="120" w:after="40"/><w:jc w:val="left"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:rFonts {TNR}/><w:i/><w:iCs/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>''',
    "Heading4": f'''<w:style w:type="paragraph" w:styleId="Heading4"><w:name w:val="Heading 4"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="120" w:after="0"/><w:jc w:val="left"/><w:outlineLvl w:val="3"/></w:pPr><w:rPr><w:rFonts {TNR}/><w:i/><w:iCs/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>''',
    "Hyperlink": '''<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:basedOn w:val="BodyTextChar"/><w:rPr><w:color w:val="000000"/><w:u w:val="none"/></w:rPr></w:style>''',
    "TableCaption": f'''<w:style w:type="paragraph" w:customStyle="1" w:styleId="TableCaption"><w:name w:val="Table Caption"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="80"/><w:jc w:val="center"/></w:pPr><w:rPr><w:rFonts {TNR}/><w:smallCaps/><w:i w:val="false"/><w:iCs w:val="false"/><w:color w:val="000000"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>''',
    "Title": f'''<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="60"/><w:jc w:val="center"/></w:pPr><w:rPr><w:rFonts {TNR}/><w:b/><w:bCs/><w:color w:val="000000"/><w:sz w:val="34"/><w:szCs w:val="34"/></w:rPr></w:style>''',
}

DOC_DEFAULTS = f'''<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts {TNR}/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="ar-SA"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="240" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr></w:pPrDefault></w:docDefaults>'''


def main():
    default = ROOT / "paper" / "_ref_default.docx"
    subprocess.run([PANDOC, "-o", str(default), "--print-default-data-file", "reference.docx"], check=True)
    zin = zipfile.ZipFile(default)
    styles = zin.read("word/styles.xml").decode("utf-8")

    styles = re.sub(r"<w:docDefaults>.*?</w:docDefaults>", DOC_DEFAULTS.replace("\\", "\\\\"), styles, count=1, flags=re.S)
    for sid, block in STYLES.items():
        pat = r'<w:style [^>]*w:styleId="' + sid + r'".*?</w:style>'
        if re.search(pat, styles, re.S):
            styles = re.sub(pat, block.replace("\\", "\\\\"), styles, count=1, flags=re.S)
        else:  # style not present in default -> insert before closing tag
            styles = styles.replace("</w:styles>", block + "</w:styles>")

    out = ROOT / "paper" / "reference.docx"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = styles.encode("utf-8") if item.filename == "word/styles.xml" else zin.read(item.filename)
            zout.writestr(item, data)
    out.write_bytes(buf.getvalue())
    zin.close()
    default.unlink(missing_ok=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
