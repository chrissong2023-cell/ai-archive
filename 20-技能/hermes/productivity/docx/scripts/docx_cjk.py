#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chinese-friendly docx helpers + CLI (part of the Hermes docx skill).

CLI:
  python3 docx_cjk.py fonts  <file.docx>        # force CJK fonts on styles + runs
  python3 docx_cjk.py export <file.docx> [dir]  # write sibling .txt and .md

Library use:
  import docx_cjk as C
  doc = C.new_doc()
  C.title(doc, "标题"); C.h(doc, "一、小节", 2); C.para(doc, "正文")
  C.table(doc, ["表头"], [["值"]], widths=[16.0])
  C.footer(doc, "页脚文字")
  doc.save(path); C.export(path)
"""
from __future__ import annotations

import os
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor

SONG, HEI, EN = "宋体", "黑体", "Times New Roman"


# ---------------------------------------------------------------- font plumbing
def _rfonts(pr):
    rf = pr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rstyle = pr.find(qn("w:rStyle"))
        (rstyle.addnext(rf) if rstyle is not None else pr.insert(0, rf))
    return rf


def apply_font(obj, ea=SONG, ascii_f=EN):
    """obj: a python-docx Run or a Style."""
    if hasattr(obj, "element") and not hasattr(obj, "_element"):  # style
        pr = obj.element.get_or_add_rPr()
        _rfonts(pr)
    else:  # run
        pr = obj._element.get_or_add_rPr()
        _rfonts(pr)
        obj.font.name = ascii_f
    rf = _rfonts(pr)
    rf.set(qn("w:eastAsia"), ea)
    rf.set(qn("w:ascii"), ascii_f)
    rf.set(qn("w:hAnsi"), ascii_f)


def new_doc(top=25, bottom=25, left=25, right=25, body_pt=10.5):
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Mm(210), Mm(297)
    s.top_margin, s.bottom_margin = Mm(top), Mm(bottom)
    s.left_margin, s.right_margin = Mm(left), Mm(right)
    n = doc.styles["Normal"]
    n.font.name = EN
    n.font.size = Pt(body_pt)
    apply_font(n)
    for name, size in (("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 11)):
        st = doc.styles[name]
        st.font.name = EN
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.space_before = Pt(8)
        st.paragraph_format.space_after = Pt(4)
        apply_font(st, ea=HEI)
    return doc


def _field(par, instr):
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), instr)
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    par._p.append(fld)


def footer(doc, text):
    f = doc.sections[0].footer.paragraphs[0]
    f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for chunk in (text + "    第 ", None, " 页  共 ", None, " 页"):
        if chunk is None:
            continue
        r = f.add_run(chunk)
        apply_font(r)
        r.font.size = Pt(8)
        if chunk.endswith("第 "):
            _field(f, "PAGE")
        if chunk.endswith("共 "):
            _field(f, "NUMPAGES")


def title(doc, text, size=17, ea=HEI, space_after=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    apply_font(r, ea=ea)
    r.font.size = Pt(size)
    r.bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(space_after)
    return p


def subtitle(doc, text, size=10.5, space_after=8):
    p = doc.add_paragraph()
    r = p.add_run(text)
    apply_font(r)
    r.font.size = Pt(size)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(space_after)
    return p


def h(doc, text, level=2):
    p = doc.add_heading(level=level)
    r = p.add_run(text)
    apply_font(r, ea=HEI)
    r.font.size = Pt({1: 14, 2: 12, 3: 11}.get(level, 11))
    r.bold = True
    r.font.color.rgb = RGBColor(0, 0, 0)
    return p


def para(doc, text, size=10.5, bold=False, ea=SONG, indent=False, align=None,
         space_after=3, runs=None):
    p = doc.add_paragraph()
    if runs:
        for spec in runs:
            r = p.add_run(spec.get("text", ""))
            apply_font(r, ea=ea)
            r.font.size = Pt(spec.get("size", size))
            r.bold = spec.get("bold", False)
            r.italic = spec.get("italic", False)
    else:
        r = p.add_run(text)
        apply_font(r, ea=ea)
        r.font.size = Pt(size)
        r.bold = bold
    if indent:
        p.paragraph_format.first_line_indent = Pt(size * 2)
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.25
    return p


def bullet(doc, text, size=10.5):
    return para(doc, text, size=size, space_after=2)


def table(doc, header, rows, widths=None, size=10, header_bold=True):
    t = doc.add_table(rows=0, cols=len(header) if header else len(rows[0]))
    t.style = doc.styles["Table Grid"]
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, row in enumerate(([header] if header else []) + rows):
        cells = t.add_row().cells
        for j, val in enumerate(row):
            cells[j].text = ""
            p = cells[j].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(str(val))
            apply_font(r)
            r.font.size = Pt(size)
            if i == 0 and header and header_bold:
                r.bold = True
    if widths:
        for row in t.rows:
            for j, w in enumerate(widths):
                row.cells[j].width = Cm(w)
    return t


# ------------------------------------------------------------------ conversion
def _iter_blocks(doc):
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    for child in doc.element.body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, doc)
        elif child.tag.endswith("}tbl"):
            yield Table(child, doc)


def _table_md(t):
    rows = [[" ".join(p.text.strip() for p in c.paragraphs if p.text.strip()) for c in r.cells]
            for r in t.rows]
    if not rows:
        return []
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * n]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return out


def _table_txt(t):
    lines = []
    for r in t.rows:
        cells = [" ".join(p.text.strip() for p in c.paragraphs if p.text.strip()) for c in r.cells]
        seen = []
        for c in cells:
            if c and c not in seen:
                seen.append(c)
        lines.append("  ".join(seen))
    return lines


def export(path, outdir=None):
    """Write <stem>.txt and <stem>.md next to the docx (or into outdir)."""
    outdir = outdir or os.path.dirname(os.path.abspath(path))
    stem = os.path.splitext(os.path.basename(path))[0]
    doc = Document(path)
    md, txt = [], []
    for blk in _iter_blocks(doc):
        if blk.__class__.__name__ == "Table":
            md += _table_md(blk) + [""]
            txt += _table_txt(blk) + [""]
            continue
        text = blk.text.strip()
        if not text:
            continue
        style = blk.style.name or ""
        if style.startswith("Heading"):
            try:
                lvl = int(style.split()[-1])
            except ValueError:
                lvl = 2
            md += ["#" * min(lvl + 1, 6) + " " + text, ""]
            txt += [text, "-" * max(len(text) * 2, 12)]
        else:
            md += [text, ""]
            txt += [text]
    txt_path = os.path.join(outdir, stem + ".txt")
    md_path = os.path.join(outdir, stem + ".md")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(txt).strip() + "\n")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md).strip() + "\n")
    return txt_path, md_path


def force_fonts(path):
    """Idempotently set CJK fonts on every style and run of an existing docx."""
    doc = Document(path)
    for st in doc.styles:
        try:
            if st.name in ("Normal",) or st.name.startswith("Heading"):
                apply_font(st, ea=HEI if st.name.startswith("Heading") else SONG)
        except Exception:
            pass
    def fix(paragraphs):
        for p in paragraphs:
            for r in p.runs:
                apply_font(r)
    fix(doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                fix(c.paragraphs)
    for s in doc.sections:
        for part in (s.header, s.footer):
            fix(part.paragraphs)
    doc.save(path)
    return path


def _main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, path = argv[1], argv[2]
    if cmd == "fonts":
        print(force_fonts(path))
    elif cmd == "export":
        print("\n".join(export(path, argv[3] if len(argv) > 3 else None)))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
