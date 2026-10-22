---
name: feed-capture
version: 1.0.0
author: Hannah (Hermes Agent)
description: "Use when files are dropped for Hannah to read and index."
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [RAG, KnowledgeBase, Ingestion, launchd, OCR, Whisper]
    related_skills: [obsidian, pdf, docx, xlsx, powerpoint]
---

# 投喂捕获（文件自动识别入库）

Chris 把文件丢进投喂箱，系统自动：识别类型 → 提正文 → 写共享知识库语料 → 重建向量索引 → LLM 读一遍并汇报。权威说明在 `~/AI工作台/投喂/README.md`。

**两个箱子都盯**（`SOURCE_DIRS`）：桌面「投喂给Hannah」= `~/AI工作台/投喂/inbox`，桌面「Nova投喂」= `~/.openclaw/workspace/inbox`（Nova 的箱子）。他常问“投哪个”，答案固定：**投「投喂给Hannah」**，但两边都会被捕捉。两箱进同一份共享语料，Nova 也能检索到；敏感文件无论从哪箱进来都自动进隔离区。

## When to Use

- “我把文件投喂给你 / 看 inbox 里有没有新文件 / 这文件你读一下”
- 排查“投进去了没反应”“中文扫描件识别乱码”“检索不到刚投的文件”
- 改分类规则、支持新文件类型、调索引用量

## 架构（两层触发 + 一套 KB）

| 层 | 触发 | 干什么 | 耗时 |
|---|---|---|---|
| launchd `com.hannah.feed-watch` | WatchPaths 监听**两个** inbox 目录 | `bin/watch.sh` → `ingest.py --no-index`：只提取正文（秒级） | 3-30s |
| Hermes cron “投喂捕获·Hannah读取掌握” | 每 5 分钟（带 monitor 变更检测） | `feed_ingest.sh` → `ingest.py`（含索引）+ LLM 读正文、写笔记、登记 INDEX.md、汇报 | 秒级~分钟 |

语料落在**共享知识库**：`~/.openclaw/workspace/knowledge/feed/hermes/*.md` → chroma 索引 `~/.nova-kb/chroma`（BAAI/bge-small-zh-v1.5，fastembed）→ 检索服务 `com.hannah.kb-serve`（launchd KeepAlive，http://127.0.0.1:8765）。

## 常用命令

```bash
cd ~/AI工作台/投喂
python3 bin/ingest.py --status        # 台账
python3 bin/ingest.py --dry-run       # 看会处理哪些（只读，不占锁）
python3 bin/ingest.py --no-index      # 快跑
python3 bin/ingest.py --force         # 强制重解析（改了规则/解析器后）
python3 bin/ingest.py --retry-vlm     # 限流降级的文件重跑视觉大模型
python3 bin/ingest.py --max-files 80 --budget-secs 1500 --no-index   # 大批量：限量限时
python3 bin/ingest.py --reroute-risk  # 规则升级后对已入库文件重判高风险并搬入隔离区
python3 bin/purge_risk.py --kind gpu|cred|pii|all [--confirm]       # 清除敏感隔离区（默认只预览）
~/.nova-tools/kb.sh search "关键词" --k 5   # 语义检索（需 8765 在跑）
~/.nova-tools/docsearch "关键词"            # 全文 rg 快搜
```

批量投喂（整个文件夹、几百个文件）一律用 `--max-files` + `--budget-secs` 分批：一次吃完会占着锁几十分钟，期间落盘的新文件全被跳过。cron 那跳也要带这两个参数。

高风险文件的分类规则、隔离目录、清除流程见 `references/high-risk-quarantine.md`（Chris 明确要求高风险文件单独存放以便将来整体删除，这是常驻要求）。

## 铁律 / 已踩过的坑

1. **台账哈希字段名统一为 `sha`**。`load_ledger()` 曾按 `sha256` 取键，异常被 `except: pass` 吞掉 → 台账永远为空 → 去重失效、同一文件反复重解析。改 `load_ledger` 时**不要用裸 `except: pass` 包住取值**。
2. **PDF/docx 必须用 `office.py md` 而不是 `text`**：docx/xlsx 的关键内容（报价单“费用明细”）常在表格里，text 模式会丢表格。
3. **扫描件判定**：原生提取 <300 字（PDF）视为扫描件 → 视觉大模型 `docvlm.py` → 再兜底 `office.py text --ocr`（tesseract）。VLM 报 `rate-limited` 时写入 `out/vlm-retry.txt`，之后 `--retry-vlm` 重跑；**不要把限流当成功**。
4. **两把锁分开**：`.ingest.lock` 只锁提取阶段，`.index.lock` 锁向量重建。最初让提取和索引共锁 → 索引要跑几分钟，期间落盘的文件全被“已有任务在跑”跳过。
5. **不要在 shell 层和 python 层加同一把锁**：watch.sh 先 mkdir 锁再调 ingest，python 看到锁被占会直接返回，永不干活。锁只在 `ingest.py` 里管。
6. **launchd `WatchPaths` 只在目录 mtime 变化时触发**；用桌面**符号链接**指向真实 inbox 可正常工作（Chris 的习惯是桌面别名）。
7. **原文只读**：不移动、不改名、不删除投喂文件；失败写 `out/failed.log`，不编造内容。
8. **中文 OCR 依赖 `chi_sim`**：tesseract 默认只有 eng。`brew install tesseract-lang` 后 `ingest.py` 会自动用 `chi_sim+eng`；否则中文扫描件只能靠 VLM。
9. **tesseract 不带 `timeout` 命令**（macOS 无 GNU coreutils 的 timeout），用 python 的 `subprocess(timeout=)` 包。
10. 投喂目录不要放到 TCC 保护的 Desktop/Downloads 本体上（launchd 进程读会被拦）；用 `~/AI工作台/投喂/` + 桌面符号链接。
11. **Chris 会把整个文件夹做成符号链接丢进来**（`Nova投喂_副本 -> ~/.openclaw/workspace/inbox`）。`os.walk(INBOX)` 默认 `followlinks=False` → 目录链接只被当成一个文件条目，sha256 抛 IsADirectoryError 全被跳过，表现为“投喂了但一个文件都没读”。必须 `followlinks=True` + realpath 去重 + 访问过的 realpath 目录集合防环，并且只读目标目录、绝不写入。
12. **`--dry-run` 不占锁**：预演是只读的，占锁会把真正的批次挡在“已有一次捕获在跑”外面（曾在批次开跑前白锁 5 分钟）。
13. **`stable()` 只对刚落盘的文件等待**：对每个文件 sleep 1.2s 检查“两次大小一致”，几百个历史文件就是几分钟纯等待。规则：mtime 超过 2 分钟的文件直接视为写完。
14. **VLM 熔断**：视觉大模型限流时 `docvlm.py` 会自己重试 3 次，单个文件能白耗 5 分钟。规则：本轮内一旦收到 rate-limited 就置全局标志，后面的文件直接走本地 OCR（chi_sim）；只有显式 `--retry-vlm` 才逐文件重试（每次进入新文件前清标志）。限流不是失败——本地 OCR 兑底后仍然入库。
15. **重试清单不要提前清空**：曾经在处理前就 `open(RETRYLIST,'w')` 清空，一旦本轮没真处理就永久丢掉待重试项。改成从台账反推（`note == 'vlm-rate-limited'` 且有路径）重建清单，自愈。
16. **老 `.xls` 不走 `office.py`**：它的 xls 分支依赖 pandas（本机可能没装）会直接抛异常。在 extract 里加 xlrd 直读兑底（逐 sheet 转 `|` 分隔文本），只在 office.py 结果 <30 字时才用。同理 `.ppt/.rtf/.odt/.ods` 走 `textutil -convert txt`。
17. **加“指定文件”旁路（如 `--retry-vlm`）时，必须真的把 override 赋给待处理列表**：一次重构把 `todo = todo_override` 那行丢了，模式跑完报“新文件 0 个”，静默空转。改旁路后跑一次并确认输出里出现过处理行。
18. **单文件解析异常不得拖垮整轮**：几百个文件的批次里一个坏文件就终止会丢失全部后续进度（配合“每 N 个存一次台账/state”的增量落盘）。
19. **三种“非 ok”终态要分清，别都写成 failed**：`ok`（有正文）/ `ok_notext`（图片本来就没字，如公章、现场照片）/ `needs_password`（加密文件，xlrd 报 `Workbook is encrypted`）。扫描跳过逻辑必须同时认这三态：`ok_notext` 写进 `out/vlm-retry.txt` 等视觉大模型恢复后重试，`needs_password` 写 `out/needs-password.txt` 交给 Chris 要密码/未加密副本。否则无字图片与加密件每轮重跑，台账永远显示“失败”，加密件每次白耗 70s+。
20. **“加密”要在扫描兜底之前判**：加密的 xls/xlsx/pdf 交给 VLM/OCR 也读不出，先看提取错误里有没有 `encrypt/password` → 直接返回并标 `needs_password`，不要再走 VLM→OCR 链路。
21. **图片按文件头判定，不按后缀**：微信的 `.pic_hd` / `.dat` 没有正经后缀（实测内容是 PNG），按后缀判类型会全部落进“不支持”。`sniff_image()` 读 magic bytes（JPEG/PNG/GIF/WEBP/TIFF/BMP），命中就走图片识别；tesseract/VLM 认后缀，喂之前先复制一份带正确后缀的临时文件。
22. **Office 正文为空 → 解包取内嵌图片**：docx/xlsx/pptx 里整页是一张扫描图时（身份证、盖章文件、报价截图）文字层为空，解包 `*/media/*` 图片逐个 VLM/OCR（上限 8 张）才能读出内容。
23. **索引已是增量（2026-10-17 起）**：`kb_index.py` v2 用 `~/.nova-kb/index-state.json` 记 路径→(size,mtime,sha,cat,ids)，每跳只向量化 size/mtime 变过的文件，并删掉已消失文件的旧向量 —— 842 文件全量 150 秒的老代价不再每跳都付。按 pid 判断的话：`kb.sh index` 秒级完成说“没有变更”；要真正重算（改了切块/清洗规则、换了模型）必须 `kb.sh index --rebuild`，**且 --rebuild 期间正在跑的服务会 500**（collection 被删了），重建完 `launchctl kickstart -k gui/$(id -u)/com.hannah.kb-serve` 再验 `/api/health`。
23b. **同一份材料会有两个来源**：Nova 的 `knowledge/feed/extracted2/*.txt` 与本管道写的 `feed/hermes/*.md` 是同一批文件的两种提取件。索引层按“正文归一化签名”跨来源去重（保留优先级高的 hermes 版），检索层再按片段文本去重、`per_source` 每条来源最多 2 条、`per_doc` 同一份文档最多 2 条，所以碎片不会重复刷屏。判断“为什么片段数变了”先看 `curl -s 127.0.0.1:8765/api/stats`。
23c. **检索是向量 + 关键词混合**：`/api/search` 默认 `hybrid=1`，对 “H200 / WCA 136296 / 080-8890” 这类精确串走 chroma `where_document $contains` 补召回，再与余弦分数合并、去重、限每来源条数。片段首行是 `【标题·小节】`，引用时应落到 `source` 那个原始文件。`kb.sh search` 走 HTTP 服务，报“知识库服务没在跑”就是 8765 没起（launchd `com.hannah.kb-serve` 常驻；它以前每 60 秒因端口占用重启一次，2026-10-17 已加端口守卫）。
23d. **切块质量门槛别放松**：清洗会剔页码行、竖线空表行、低字符密度行、重复行；块要 ≥140 字且有效字符占比 ≥0.45 才入库。实测一封 6773 字符的 HTML 邮件正文只剩 993 字符有效内容 —— 这是正常的（其余是排版噪声），**不是丢正文**；但把门槛再抬高会开始误删真内容，改规则后先拿 `mail/bodies/` 和 `extracted2/` 各抽 5 个文件 `--dry-run` 看块数再重建。

24. **多投喂箱要同时改三处**：`SOURCE_DIRS`（扫描范围）、launchd plist 的 `WatchPaths` 数组（两个目录都要列为独立 `<string>`，否则第二个箱子只剩 5 分钟 cron 兜底、失去“秒级”体验）、`--dry-run` 核对 total = 两箱之和。realpath 去重保证“直接放 + 经符号链接可达”的同一文件只算一次。改完 `launchctl unload && launchctl load -w` 重载，并往第二个箱子真丢一个文件验证捕捉。
25. **用 stat 索引做免哈希快跳**：每跳对几百个文件全量 sha256 是纯 I/O 浪费。从台账建 `realpath → (size, mtime)` 索引，两者都没变就直接判“已处理过”，只有变动过才重算哈希。实测 234 个文件的全量扫描从秒级降到 0.098 秒——加第二个投喂箱之前必须先有这一步。

26. **chroma 「Nothing found on disk」是索引重建把正在跑的服务句柄弄脏了**，典型表现：`/api/search` 里 `degraded: ["catXX"]`，单条 `cat=` 查询可能正常；新建进程手测又一切正常。处理顺序：① 先 `launchctl kickstart -k gui/$(id -u)/com.hannah.kb-serve`（重建后本来就该重启）；② 仍不行的单个 collection，`delete_collection` + 把 `index-state.json` 里该 cat 的条目删掉 → `kb.sh index` 会把它当新文件重建（实测一次就好，cat03 406 块 4 秒重灌）；③ 服务里已带自愈：某个 collection 连续 4 次失败会自己 `launchctl kickstart` 一次，并把真实异常打到 `~/.nova-kb/serve-launchd.log` 的 `[search-fail/...]`（**stdout 在那个 .log，不是 .err**）。
27. **重建后必须摸一下每个 collection**：chroma 的 HNSW 索引不查询不落盘，写完就跑会让最后几个 collection 缺 `index_metadata.pickle`。`kb_index.py` 末尾已对 8 个 collection 各打一次 probe 查询强制持久化——改索引器时不要删这段。
28. **调切块/打分/清洗规则前先读 `references/kb-index-tuning.md`**：里面有语料取舍、清洗顺序、增量版本闸门、混合检索打分公式、chroma 句柄运维五节；改这些参数会静默改变检索质量或整份丢弃文档，不要凭感觉调。

## 给 Chris 的“掌握”汇报格式

LLM 那层每有新文件输出：文件名+类型+归类 → 一句话定性 → 关键事实（主体/金额/日期/标的/条款/项目）→ 风险与待确认 → 建议下一步；涉及金额、合同、主体变更、法律文书、出口管制单列「需 Chris 确认」；并把要点追加到 `knowledge/feed/hermes-notes-<日期>.md` 与 `INDEX.md`。
