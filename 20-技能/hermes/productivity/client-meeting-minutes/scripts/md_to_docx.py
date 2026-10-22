#!/usr/bin/env python3
"""md_to_docx.py —— 把纪要 md 转成可直接转发/打印的 .docx（中文字体正确）。

用法：
    python3 md_to_docx.py 纪要.md [输出.docx]      # 省略输出名则同名 .docx
    python3 md_to_docx.py *.md                     # 批量

依赖：python-docx（`pip install python-docx`，本机已装）。
支持：#/##/### 标题、| 表格 |、``` 代码块 ```、- 项目符号、1. 编号、> 引用、**加粗**。

用户习惯：docx 是交付格式（要转发给同事/对方看），md 只是工作底稿 —— 每次改完 md 都要重跑一遍，
否则会出现「md 已更新、docx 是旧版」的错版交付。
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt

FONT = "PingFang SC"
BODY_PT = 10.5
TABLE_PT = 9
CODE_FONT = "Menlo"


def add_runs(paragraph, text):
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        else:
            paragraph.add_run(part)


def add_table(doc, rows):
    table = doc.add_table(rows=0, cols=len(rows[0]))
    table.style = "Light Grid Accent 1"
    for ri, row in enumerate(rows):
        cells = table.add_row().cells
        for ci, val in enumerate(row[: len(rows[0])]):
            cells[ci].text = ""
            add_runs(cells[ci].paragraphs[0], val)
            for run in cells[ci].paragraphs[0].runs:
                run.font.size = Pt(TABLE_PT)
                if ri == 0:
                    run.bold = True
    doc.add_paragraph()


def md_to_docx(md_path, out_path):
    lines = Path(md_path).read_text(encoding="utf-8").split("\n")
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(BODY_PT)

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("```"):
            i += 1
            block = []
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Pt(14)
            run = para.add_run("\n".join(block))
            run.font.name = CODE_FONT
            run.font.size = Pt(9)
            i += 1
            continue

        # 表格：连续的 | 行，第二行是 --- 分隔
        if line.startswith("|") and i + 1 < len(lines) and set(
            lines[i + 1].replace("|", "").strip()
        ) <= set("-: "):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not set("".join(cells)) <= set("-: "):
                    rows.append(cells)
                i += 1
            if rows:
                add_table(doc, rows)
            continue

        if line.startswith("# "):
            doc.add_heading(line[2:], level=0)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=2)
        elif re.match(r"^\s*[-*] ", line):
            add_runs(doc.add_paragraph(style="List Bullet"), re.sub(r"^\s*[-*] ", "", line))
        elif re.match(r"^\s*\d+\. ", line):
            add_runs(doc.add_paragraph(style="List Number"), re.sub(r"^\s*\d+\. ", "", line))
        elif line.startswith("> "):
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Pt(18)
            add_runs(para, line[2:])
            for run in para.runs:
                run.italic = True
        elif line.strip() and line.strip() != "---":
            add_runs(doc.add_paragraph(), line)
        i += 1

    doc.save(out_path)
    return out_path


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    if len(argv) == 2:
        targets = [(p, str(Path(p).with_suffix(".docx"))) for p in Path().glob(argv[1])] or [
            (argv[1], str(Path(argv[1]).with_suffix(".docx")))
        ]
    else:
        targets = [(argv[1], argv[2])]
    for md, out in targets:
        print(f"{md} -> {md_to_docx(md, out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
