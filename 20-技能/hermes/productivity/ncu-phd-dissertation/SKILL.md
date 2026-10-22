---
name: ncu-phd-dissertation
description: Use for Chris's NCU PhD thesis, 学术报告, survey or R analysis.
---

# NCU PhD dissertation support (宋孝臣 / Xiaochen Song)

## Facts that shape every task

- Program: PhD in Business Innovation, Innovation College, North-Chiang Mai University. Full-time in Chiang Mai; target graduation **2027-09**.
- Dissertation topic (fixed by the approved 开题): *国际物流数字创新管理：动态能力、供应链韧性与组织绩效* / Digital Innovation Management in International Logistics: Dynamic Capabilities, Supply Chain Resilience and Organisational Performance.
- Model: DTA + IMP → DC (sensing/learning/collaborative, 2nd order) → SCR (robustness/responsiveness/recovery/adaptability, 2nd order) → OP (financial/customer); moderated by TMS (DTA→DC) and NCI (DC→SCR). Ten hypotheses H1a–H10, SEM in R/lavaan, n = 300–450 plus 10–20 interviews.
- Working folder: `~/AI工作台/博士论文-北清迈/` (00 总控 / 01 开题原件 / 02 学术报告 / 03 论文大纲 / 04 数据采集 / 05 参考文献核验 / 06 学院提交).
- Deliverable format: plain `.md`/`.txt` only — never docx/xlsx/pptx (Chris's standing rule).

## Milestone chain (per the university's Beijing-centre description — confirm with 导师)

1. 开题答辩 (chapters 1–3) — done.
2. 会议论文 8–12 pages at the college academic conference = the 学术报告.
3. Journal paper: English only, from SSCI/Scopus/EBSCO/TCI lists; Chinese journals do not count.
4. Dissertation 150–250 pages / 80–100k words; bilingual defence allowed.

## Reference verification — do this before touching any chapter

The 开题 reference list was AI-generated: authors and titles roughly right, but years shifted +4–6 and journals swapped. Of 30 entries, only 2 were usable; 13 had no matching record. **Never trust a reference that has not been checked against a DOI.**

Procedure (`scripts/check_refs.py` does this in bulk): query Crossref `query.bibliographic`, fall back to OpenAlex `search`, compare title similarity + first-author surname + year, and record the real DOI / journal / volume / pages. Report each entry as ✅ / ⚠️ (located but metadata wrong) / ❌ (no record).

**The script is a first pass, not the verdict.** Similar-title matching calls a different paper by the same author group a WARN, so it under-counts ❌ and over-counts ⚠️ (a 30-entry list returned OK 1 / WARN 23 / MISS 6 while DOI-by-DOI review tightened it to 2 usable / 15 metadata-wrong / 13 nonexistent). Open the matched DOI and confirm the title *and* the claim the chapter attributes to it before it enters the bank; when the verdict decides whether a paragraph's argument survives, the manual pass wins and the CSV is only evidence of scope.

Verified reference bank: `~/AI工作台/博士论文-北清迈/05-参考文献核验/verified-references.ris` and `.bib` (28 entries, APA 7, all with DOIs). Import into Zotero; never hand-type citations.

## 开题原文 → 中英对照 Markdown

Chris hands over the bilingual 开题 as a .docx; the deliverable is plain `.md`.

1. Extract with the office pipeline, never `text` mode: `python3 ~/.nova-tools/office.py md "<docx>" > 01-开题原件/开题-中英-提取文本.txt` (text mode drops table content).
2. Restructure with `01-开题原件/build_bilingual.py` → `开题-中英对照.md` (rebuild the script from the rules below if it is missing).
3. **Acceptance test is coverage, not eyeballing**: compare every source line longer than ~20 chars against the output and require missing = 0. The only acceptable residue is pre-TOC cover lines when the parser has no preamble bucket.

Parser rules that decide whether the output is right:

- Pair at **section** level, not sentence level — the docx holds the English section first and its Chinese twin after, numbered identically, so pair by number and emit `### EN` / `### 中文` blocks.
- Whitelist headings by exact title words (`2. Introduction`, `2. 引言`). Matching any `^\d+\.` line swallows body bullets such as `1.识别并分析…`; the symptom is one section losing dozens of lines while section 1 gains them. Headings that mix both languages in parentheses (`11. References（参考文献）`) defeat a "any CJK in the title → Chinese section" test — special-case them, or the section silently drops out of the pairing and the TOC.
- Never test a sentinel cursor with `cur is None`: a `(None, None)` tuple is truthy, so the preamble branch never fires and the cover page disappears silently. Test `cur[0] is None`.
- Give the mixed-language cover page its own bucket and emit it once — do not force it into the EN/中文 split.

## R environment (installed 2026-10-17)

`brew install r` hangs on `formulae.brew.sh` on this network — do not retry it. R lives in a conda env instead:

```bash
export PATH="$HOME/miniconda3/envs/phd/bin:$PATH"   # R 4.5.3, lavaan 0.7.2, semTools 0.5.9, tidyverse, psych
Rscript analysis.R --data data/survey.csv --out out_real
```

Rebuild if the env is ever lost (2 commands, no sudo, ~6 min): Miniconda installer from `https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-arm64.sh`, installed to `~/miniconda3` (`bash mc.sh -b -p "$HOME/miniconda3"`), then

```bash
conda create -y -n phd -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge \
  --override-channels r-base r-lavaan r-semtools r-tidyverse r-psych
```

`python-docx` and `python-pptx` are NOT in conda: they live in the system interpreter `/usr/bin/python3` (3.9) — use that for reading/writing docx/pptx, never `python3` on PATH (Hermes python has no numpy/pandas/docx).

The pipeline (`04-数据采集/analysis.R`) runs end-to-end on simulated data: cleaning → descriptives → second-order CFA → reliability/AVE/HTMT → Harman CMB → structural paths → bootstrapped mediation → dimension models (H9/H10) → moderation with simple slopes → robustness. `04-数据采集/generate_sim_data.py` (stdlib only) produces the smoke-test CSV; system `python3` has no numpy/pandas, so keep that script stdlib-only.

## Pitfalls already hit

- lavaan 0.7-2 rejects `bootstrap.type`; pass only `bootstrap=` and `se="bootstrap"`, and use `estimator="ML"` (MLR + bootstrap fails).
- `dplyr::slice_sample(n = min(2, n()))` errors ("n must be a constant") — use `mutate(.rnd = runif(n())) %>% arrange() %>% slice_head(n = 2)` inside `group_by`.
- A model with 17 latent factors and 5,000 bootstrap draws takes minutes; use 500 while testing.
- `psych` and `semTools` both export `reliability` — attach order matters; call `semTools::reliability()` explicitly.

## Writing order that actually works

Method chapter + questionnaire first (data collection is the long pole), then the two construct sections (2.4 DC, 2.5 SCR), then the Chapter 4 table skeletons, then Chapter 1 (it reads differently once the results exist), then Chapter 5.

## Style notes for this work

- Chinese when talking to Chris; the dissertation body and the conference paper in English, with a Chinese 宣讲稿 for the defence.
- Never present anticipated findings as results — the conference paper is explicitly research-in-progress.
- Flag academic-integrity risks immediately and plainly (that is how the reference problem was caught).
