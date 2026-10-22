# SKILLS-MAP — 两个 agent 的技能总账

_自动生成 2026-10-22T13:05:01+0800 · Hannah 73 / Nova 76 / 共享 7_

> 由 `~/AI工作台/团队协同/bin/scan_skills.py` 生成，**不要手改**。查：`scan_skills.py search 关键词`；派活：`scan_skills.py who 能力`。

## 一、分工路由（先看谁主责，避免两套并行）

| 能力 | 主责 | 备手 | 怎么用 |
|---|---|---|---|
| 邮件：收件箱分诊 / 草拟 / 发信 / 获客外发 | **hannah** | nova | Hannah: 金技能 lishun-mail-acquisition（3 个 cron + 审批闸门）；Nova: ~/.nova-tools/mail.py 实际投递，凭据共用 ~/.nova-secrets/mail.json，发送记录写 mail/sent-log.md |
| WCA 会员采集 / 开发信名单 | **nova** | hannah | Nova 采集 → ~/.openclaw/workspace/projects/wca-bd/data/new-members-*.csv；Hannah 读同一份 CSV 生成开发信 |
| 会议录音转写 / 纪要 | **hannah** | nova | Hannah: whisper.cpp 本地转写 + 纪要（音频不出本机）；Nova: 飞书知识库归档/多维表格待办（分工待双方确认，勿并行建第二套） |
| 浏览器多步操作 / 国内工商尽调 | **nova** | hannah | Nova: browser-automation 插件（登录态在它那边）；Hannah 用 browser_exec 但不占它的登录态 |
| 知识库检索（RAG）/ 投喂入库 | **shared** | - | 同一套语料 + 同一套 chroma：~/.nova-tools/kb.sh search "词" / http://127.0.0.1:8765/api/search；投喂箱两个都盯，索引增量重建 |
| 文档解析 / OCR / 报表 | **shared** | - | Hannah: pdf/docx/xlsx/powerpoint 技能 + office.py；Nova: mineru（云端，敏感件禁用）、excel-xlsx |
| 公众号 / 对外内容发布 | **hannah** | - | Hannah 已获授权直接发表（不勾原创）；Nova 不做公众号发布 |
| 合规与高风险文件 | **hannah** | - | 出口管制/转运规避类先报 Chris，不做；敏感证件凭据隔离区由 Hannah 管，任何 agent 不得把内容贴进外部服务 |
| Mac 主机/网关/电源运维 | **hannah** | nova | Hannah: macos-always-on-host、launchd、openclaw-bridge 排障；Nova 只读自查 |

## 二、共享技能（两边都加载，同一份文件）

- **team-hq** — Use when a task may belong to the other agent, needs the other agent's skills or knowledge, or when Hannah and Nova must divide work. Shared by Hermes (Hannah) and OpenClaw (Nova).  
  `/Users/xiaochensong/AI工作台/团队协同/skills/team-hq/SKILL.md`
- **wf-01-inquiry-quote** — Use when an RFQ or new inquiry arrives and a quotation must be produced, priced and sent. Covers cost gathering, quote document, approval gate and follow-up.  
  `/Users/xiaochensong/AI工作台/团队协同/skills/wf-01-inquiry-quote/SKILL.md`
- **wf-02-logistics-ops** — Use when handling an active shipment or answering operational questions (SOP, documents, milestones, exceptions) for forwarding and cross-border moves.  
  `/Users/xiaochensong/AI工作台/团队协同/skills/wf-02-logistics-ops/SKILL.md`
- **wf-03-gpu-procurement** — Use when sourcing, vetting, pricing or moving GPU/IDC hardware and capacity (H200/B200/L40S, colo, bare metal), including the compliance gate.  
  `/Users/xiaochensong/AI工作台/团队协同/skills/wf-03-gpu-procurement/SKILL.md`
- **wf-04-contract-kyc** — Use when a contract, agreement or KYC pack must be reviewed, negotiated, signed off and archived — including red-flag extraction and approval routing.  
  `/Users/xiaochensong/AI工作台/团队协同/skills/wf-04-contract-kyc/SKILL.md`
- **wf-05-crm** — Use when updating, segmenting or acting on customer/agent records — the single customer source of truth, follow-up cadence and quiet-account revival.  
  `/Users/xiaochensong/AI工作台/团队协同/skills/wf-05-crm/SKILL.md`
- **wf-06-mail-calendar** — Use when triaging the inbox, drafting or sending mail, or scheduling/answering calendar questions — with the approval gate and the known scheduling gap.  
  `/Users/xiaochensong/AI工作台/团队协同/skills/wf-06-mail-calendar/SKILL.md`

## 三、Hannah（Hermes）技能


### 

- **macos-browser-profile-ops** — Use when driving the user's own Chrome on macOS.
- **macos-network-triage** — Use when the Mac is offline or a VPN won't connect.
- **web-presence-audit** — Audit domain site uptime, TLS, SEO and mailbox readiness.

### apple

- **apple-notes** — Manage Apple Notes via memo CLI: create, search, edit.
- **apple-reminders** — Apple Reminders via remindctl: add, list, complete.
- **findmy** — Track Apple devices/AirTags via FindMy.app on macOS.
- **imessage** — Send and receive iMessages/SMS via the imsg CLI on macOS.
- **macos-always-on-host** — Use when a Mac must stay online 24/7 as an always-on host.

### autonomous-ai-agents

- **claude-code** — Delegate coding to Claude Code CLI (features, PRs).
- **codex** — Delegate coding to OpenAI Codex CLI (features, PRs).
- **hermes-agent** — Use, configure, theme, extend, and orchestrate Hermes Agent.
- **openclaw-bridge** — Use when driving the OpenClaw agent (Nova) from Hermes.
- **opencode** — Delegate coding to OpenCode CLI (features, PR review).

### creative

- **architecture-diagram** — Dark-themed SVG architecture/cloud/infra diagrams as HTML.
- **ascii-video** — ASCII video: convert video/audio to colored ASCII MP4/GIF.
- **baoyu-infographic** — Infographics: 21 layouts x 21 styles (信息图, 可视化).
- **claude-design** — Design one-off HTML artifacts (landing, deck, prototype).
- **design-md** — Author/validate/export Google's DESIGN.md token spec files.
- **humanizer** — Humanize text: strip AI-isms and add real voice.
- **manim-video** — Manim CE animations: 3Blue1Brown math/algo videos.
- **p5js** — p5.js sketches: gen art, shaders, interactive, 3D.
- **popular-web-designs** — 54 real design systems (Stripe, Linear, Vercel) as HTML/CSS.
- **songwriting-and-ai-music** — Songwriting craft and Suno AI music prompts.

### desktop

- **computer-use** — Drive the desktop background-first; escalate on signal.

### devops

- **sdlc-review** — Review Kanban handoffs and route verified outcomes.

### email

- **email-inbox-triage** — Triage an inbox: prioritize threads, draft replies safely.
- **himalaya** — Himalaya CLI: IMAP/SMTP email from terminal.

### media

- **gif-search** — Search/download GIFs from Tenor via curl + jq.
- **songsee** — Audio spectrograms/features (mel, chroma, MFCC) via CLI.
- **youtube-content** — YouTube transcripts to summaries, threads, blogs.

### note-taking

- **obsidian** — Read, search, create, and edit notes in the Obsidian vault.

### productivity

- **airtable** — Airtable REST API via curl. Records CRUD, filters, upserts.
- **box** — Box manages cloud files, sharing, search, and metadata.
- **client-meeting-minutes** — Use when the user hands over a meeting/phone-call recording or asks to record and organize a client conversation. Transcribe locally with whisper.cpp, produce a cited minutes file, and push action items into Apple Reminders with due dates.
- **document-to-action-items** — Extract cited obligations, deadlines, tasks from documents.
- **docx** — Create, read, edit, template, and review Word .docx files.
- **feed-capture** — Use when files are dropped for Hannah to read and index.
- **google-workspace** — Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python.
- **lishun-mail-acquisition** — Use for Chris's inbox triage, RFQ replies and WCA BD.
- **maps** — Geocode, POIs, routes, timezones via OpenStreetMap/OSRM.
- **meeting-action-items** — Turn meeting notes into cited decisions, owners, tickets.
- **ncu-phd-dissertation** — Use for Chris's NCU PhD thesis, 学术报告, survey or R analysis.
- **notion** — Notion API + ntn CLI: pages, databases, markdown, Workers.
- **pdf** — PDF files: create, read, merge, fill, OCR, edit text.
- **powerpoint** — Create, read, edit .pptx decks with python-pptx.
- **product-price-monitor** — Watch product, flight, or listing prices; alert on target.
- **teams-meeting-pipeline** — Teams meeting summaries, job replay, Graph subscriptions.
- **trade-quotation-and-agency-agreement** — Use when drafting freight quotes or agency contracts.
- **weekly-review-planning** — Weekly reset: commitments, stalled work, next-week plan.
- **xlsx** — Create, read, edit Excel .xlsx workbooks and CSVs.

### research

- **arxiv** — Search arXiv papers by keyword, author, category, or ID.
- **competitor-news-monitor** — Watch named companies for material news; cited digests.
- **cross-border-trade-daily-digest** — Use when producing the daily cross-border trade digest.
- **grounded-citations** — Ground answers and documents in cited, verifiable sources.
- **llm-wiki** — Karpathy's LLM Wiki: build/query interlinked markdown KB.
- **stockpile-resale-deal-analysis** — Use when judging a stockpile/buy-to-resell deal (囤货/倒卖).

### social-media

- **wechat-miniprogram** — Use when building or launching a WeChat mini program.
- **wechat-official-account** — Use when operating Chris's WeChat Official Account.
- **xurl** — X/Twitter via xurl CLI: raw post search, posting, DM, media.

### software-development

- **codebase-inspection** — Inspect codebases w/ pygount: LOC, languages, ratios.
- **dogfood** — Exploratory QA of web apps: find bugs, evidence, reports.
- **github** — GitHub via gh CLI: PRs, issues, reviews, repos, auth.
- **hermes-agent-skill-authoring** — Author in-repo SKILL.md files: frontmatter and structure.
- **inspecting-hermes-desktop-dom** — Read the live Hermes desktop DOM/CSS over CDP.
- **node-inspect-debugger** — Debug Node.js via --inspect + Chrome DevTools Protocol CLI.
- **python-debugpy** — Debug Python: pdb REPL + debugpy remote (DAP).
- **requesting-code-review** — Pre-commit review: security scan, quality gates, auto-fix.
- **simplify-code** — Parallel 4-agent cleanup of recent code changes.
- **spike** — Throwaway experiments to validate an idea before build.
- **systematic-debugging** — 4-phase root cause debugging: understand bugs before fixing.
- **test-driven-development** — TDD: enforce RED-GREEN-REFACTOR, tests before code.

### team

- **chris-work-control** — Use when running Chris's task ledger and daily reports.

### web

- **blocked-page-recovery** — Use when a fetch fails: 403/429, paywall, WAF, bot wall.

## 四、Nova（OpenClaw）技能


### openclaw-bundled

- **1password** — Set up and use 1Password CLI for sign-in, desktop integration, and reading or injecting secrets. · ⚠️ 缺依赖 bins:op
- **apple-notes** — Create, view, edit, delete, search, move, or export Apple Notes via the memo CLI on macOS. · ⚠️ 缺依赖 bins:memo
- **apple-reminders** — List, add, edit, complete, or delete Apple Reminders and reminder lists via remindctl. · ⚠️ 缺依赖 bins:remindctl
- **bear-notes** — Create, search, and manage Bear notes via grizzly CLI. · ⚠️ 缺依赖 bins:grizzly
- **blogwatcher** — Monitor blogs and RSS/Atom feeds for updates using the blogwatcher CLI. · ⚠️ 缺依赖 bins:blogwatcher
- **blucli** — BluOS CLI (blu) for discovery, playback, grouping, and volume. · ⚠️ 缺依赖 bins:blu
- **camsnap** — Capture frames or clips from RTSP/ONVIF cameras and local webcams, including USB pan/tilt/zoom control. · ⚠️ 缺依赖 bins:camsnap
- **clawhub** — Search ClawHub for plugins by default, or skills when explicitly requested; install, verify, update, uninstall, publish, or sync skills.
- **coding-agent** — Delegate coding work to Codex, Claude Code, or OpenCode as background workers; not simple edits or read-only code lookup. · ⚠️ 缺依赖 anyBins:claude,codex,opencode,config:skills.entries.coding-agent.enabled
- **control-ui** — Operate and troubleshoot the OpenClaw Control UI: navigate connected clients, organize sessions, build session dashboards, and handle direct or Tailscale-hosted Gateways.
- **diagram-maker** — Create SVG/HTML or Excalidraw diagrams for concepts, architecture, flows, and whiteboards.
- **eightctl** — Control Eight Sleep pods (status, temperature, alarms, schedules). · ⚠️ 缺依赖 bins:eightctl
- **gemini** — Gemini CLI one-shot prompts, summaries, generation, skills, hooks, MCP, or Gemma routing. · ⚠️ 缺依赖 bins:gemini
- **gh-issues** — Fetch GitHub issues, select candidates, spawn background fix agents, open PRs, and optionally process PR review comments. · ⚠️ 缺依赖 bins:gh
- **gifgrep** — Search GIF providers with CLI/TUI, download results, and extract stills/sheets. · ⚠️ 缺依赖 bins:gifgrep
- **github** — GitHub CLI for issues, PRs, CI/check logs, comments, reviews, releases, repos, and gh api queries. · ⚠️ 缺依赖 bins:gh
- **gog** — Google Workspace CLI for Gmail, Calendar, Drive, Contacts, Sheets, and Docs. · ⚠️ 缺依赖 bins:gog
- **goplaces** — Query Google Places for text search, place details, resolve, reviews, or scriptable JSON via goplaces. · ⚠️ 缺依赖 bins:goplaces,env:GOOGLE_PLACES_API_KEY
- **healthcheck** — Audit/harden OpenClaw hosts: SSH, firewall, updates, exposure, backups, disk encryption, gateway security.
- **himalaya** — Himalaya CLI for IMAP/SMTP mail: list, read, search, compose, reply, forward, copy, move, delete.
- **mcporter** — List, configure, authenticate, call, and inspect MCP servers/tools with mcporter over HTTP or stdio. · ⚠️ 缺依赖 bins:mcporter
- **meme-maker** — Search meme templates, suggest formats, and generate local or hosted image memes.
- **model-usage** — Summarize CodexBar local cost logs by model for Codex or Claude, including current or full breakdowns. · ⚠️ 缺依赖 bins:codexbar
- **nano-pdf** — Edit PDFs with natural-language instructions using the nano-pdf CLI. · ⚠️ 缺依赖 bins:nano-pdf
- **node-connect** — Diagnose OpenClaw Control UI browser and native Android, iOS, or macOS node connection failures across route, auth, pairing, QR/setup-code, and reconnect states.
- **node-inspect-debugger** — Debug Node.js with node inspect, --inspect, breakpoints, CDP, heap, and CPU profiles.
- **notion** — Notion CLI/API for pages, Markdown content, data sources, files, comments, search, Workers, and raw API calls.
- **obsidian** — Work with Obsidian vaults using the official obsidian CLI: read/search/create/edit notes, tasks, links, properties, plugins. · ⚠️ 缺依赖 bins:obsidian
- **openai-whisper** — Local speech-to-text with the Whisper CLI (no API key). · ⚠️ 缺依赖 bins:whisper
- **openai-whisper-api** — OpenAI Audio Transcriptions API via curl; gpt-4o-transcribe, mini, diarize, or whisper-1. · ⚠️ 缺依赖 env:OPENAI_API_KEY
- **openhue** — Control Philips Hue lights and scenes via the OpenHue CLI. · ⚠️ 缺依赖 bins:openhue
- **oracle** — Oracle CLI second-model review/debug/refactor/design with selected files, dry-run token checks, API or browser engine. · ⚠️ 缺依赖 bins:oracle
- **ordercli** — Foodora-only CLI for checking past orders and active order status (Deliveroo WIP). · ⚠️ 缺依赖 bins:ordercli
- **peekaboo** — Capture and automate macOS UI with the Peekaboo CLI. · ⚠️ 缺依赖 bins:peekaboo
- **python-debugpy** — Debug Python with pdb, breakpoint(), post-mortem inspection, and debugpy remote attach.
- **sag** — ElevenLabs text-to-speech with mac-style say UX. · ⚠️ 缺依赖 bins:sag
- **sherpa-onnx-tts** — Local text-to-speech via sherpa-onnx (offline, no cloud) · ⚠️ 缺依赖 env:SHERPA_ONNX_RUNTIME_DIR,SHERPA_ONNX_MODEL_DIR
- **skill-creator** — Author or review AgentSkills: create, repair, validate, or restructure SKILL.md files and bundled resources.
- **songsee** — Generate spectrograms and feature-panel visualizations from audio with the songsee CLI. · ⚠️ 缺依赖 bins:songsee
- **sonoscli** — Control Sonos speakers (discover/status/play/volume/group). · ⚠️ 缺依赖 bins:sonos
- **spike** — Run throwaway prototypes to validate feasibility, compare approaches, and report a verdict.
- **spotify-player** — Terminal Spotify playback/search via spogo (preferred) or spotify_player. · ⚠️ 缺依赖 anyBins:spogo,spotify_player
- **summarize** — Summarize or transcribe URLs, YouTube/videos, podcasts, articles, transcripts, PDFs, and local files. · ⚠️ 缺依赖 bins:summarize
- **things-mac** — Add, update, list, search, or inspect Things 3 todos, inbox, today, projects, areas, and tags on macOS. · ⚠️ 缺依赖 bins:things
- **tmux** — Control tmux sessions/panes for interactive CLIs: list, capture output, send keys, paste text, monitor prompts.
- **trello** — Manage Trello boards, lists, and cards via the Trello REST API. · ⚠️ 缺依赖 env:TRELLO_API_KEY,TRELLO_TOKEN
- **visualize** — Create inline visuals for code and explanations, or author persistent OpenClaw dashboard widgets with show_widget.
- **weather** — Current weather and forecasts with web_fetch, falling back to wttr.in curl for locations, rain, temperature, travel planning.
- **xurl** — xurl CLI for authenticated X posts, replies, reads/search, DMs, media upload, followers, auth status, or raw v2 API calls. · ⚠️ 缺依赖 bins:xurl

### openclaw-custodian

- **add-model-provider** — Add and live-prove a model provider with non-interactive config one-liners, without exposing credentials.
- **cloud-image-bake** — Bake, select, prove, and safely retire a Cloud Worker image with crabbox and config one-liners.
- **configure-channel** — Configure and prove a chat channel with non-interactive one-liners; secrets only as SecretRefs.
- **diagnose-gateway** — Diagnose Gateway, config, secrets, channels, and port failures with read-only one-liners.

### openclaw-extra

- **browser-automation** — Use when controlling web pages with the OpenClaw browser tool, especially multi-step flows, login checks, tab management, or recovery from stale refs/timeouts.
- **canvas** — Present hosted widget documents on a connected macOS panel and control panel visibility or navigation.
- **feishu-doc** — Feishu document read/write workflows. Activate when the user mentions Feishu docs, cloud docs, or docx links.
- **feishu-drive** — Feishu cloud-storage and comment workflows. Activate when the user mentions cloud space, folders, Drive files, or document comments.
- **feishu-perm** — Feishu collaborator and permission workflows. Activate when the user explicitly asks to inspect or change sharing, permissions, or collaborators.
- **feishu-wiki** — Feishu knowledge-base navigation workflows. Activate when the user mentions a knowledge base, wiki, or wiki link.
- **obsidian-vault-maintainer** — Maintain an Obsidian-friendly memory wiki vault with wikilinks, frontmatter, and official Obsidian CLI awareness.
- **wiki-maintainer** — Maintain the OpenClaw memory wiki vault with deterministic pages, managed blocks, and source-backed updates.

### openclaw-workshop

- **contract-review** — 审阅本地 PDF/Word/Excel 合同与商务文档：提条款、多文档比对、标风险、出报告。触发：合同、比对、风险检查、文档审核、审一下、有没有坑。
- **diagnose-channel-silence** — 渠道(微信/飞书)收不到消息、怀疑网关没启动时的诊断：查渠道桥连接、识别「小地球仪」网络扩展 TLS 劫持并修复。触发：微信不回、飞书不回、渠道没反应、是不是网关没启动。
- **diagnose-local-job-failure** — 诊断本机定时任务/脚本失败：先读任务日志（exit 124 等），再判定是文件系统读挂起还是权限拒绝。触发：收割器/入库任务失败、退出码 124、输出目录为空、ls/opendir 卡住、读文件挂起、定时任务挂了、hang。
- **email-assistant** — 跨境商务邮件助手：据报告生成中英双语邮件，适配外贸。触发：写邮件、回邮件、报价邮件。
- **host-capability-inventory** — 如实盘点本机能力：工作区结构、已装技能、Hannah+Nova 团队技能总账、IM 通道实测状态、依赖/凭据。触发：资产盘点、能力清单、你能干什么、团队技能总账、盘点技能/通道/凭据。
- **knowledge-base-ops** — 本机 Chroma 知识库：按分类检索/新增/删除、把 source 定位回原文件，以及建库、判分类、重建索引、起检索页面。触发：查知识库、搜知识库、新增/删除知识、找原始文件、建知识库、重建索引、加分类、Chroma collection。
- **local-corpus-search** — 本地优先检索：在邮件/工作区/知识库/日历里查人、事、行程、联系人、历史往来、待办。触发：查邮件、查工作区、找一下、有没有记录、行程/联系人/项目在哪、本地有没有。
- **openclaw-deployment-audit** — 只读体检 OpenClaw 部署并规划安全远程接入：版本、Gateway 绑定/鉴权、渠道、插件来源、已配对设备、远程访问、iOS/iPad 配对、外部执行节点（Hermes）互通。触发：检查 OpenClaw 配置、部署体检、能不能远程用、iPad/手机接入、接执行节点、Nova 2.0 架构。
- **security-guardrails** — 高危操作审批、凭据保护、外部指令隔离、操作审计。触发：安全、审批、权限、密钥泄露、审计。
- **vision-image-recognition** — 识别图片/扫描件用视觉模型 psydo/gpt-5.5 转 Markdown，替代 OCR。触发：识图、看图、扫描件、转文字。
- **web-research** — 实时网页检索与行业调研：多源搜索→抓取→交叉验证→带引用简报。触发：查企业/供应商/GPU/IDC/行业资料。

### openclaw-workspace

- **Excel / XLSX** — Create, inspect, and edit Microsoft Excel workbooks and XLSX files with reliable formulas, dates, types, formatting, recalculation, and template preservation. Use when (1) the task is about Excel, `.xlsx`, `.xlsm`, `.xls`, `.csv`, or `.tsv`; (2) formulas, formatting, workbook structure, or compatibility matter; (3) the file must stay reliable after edits.
- **MinerU Document Extractor** — MinerU document extraction — convert PDFs, scanned documents, images, Word (DOC/DOCX), PowerPoint (PPT/PPTX), Excel (XLS/XLSX), and web pages into clean Markdown, HTML, LaTeX, or DOCX. MinerU is an all-in-one CLI tool and agent skill for reliable, high-fidelity document parsing. Struggling with unreadable PDFs, messy table formatting, or garbled formulas after conversion? MinerU solves these with two extraction modes: MinerU flash-extract for instant zero-setup conversion with table recognition, formula recognition, and OCR (no token, no login, no configuration — just run and get results), and MinerU precision extract with VLM-based layout analysis, multiple output formats, and batch processing of hundreds of files. Use MinerU when you need to: "how do I extract text from this PDF", "I want to convert my PDF to Markdown", "can you parse this academic paper with tables and formulas", "I need to OCR a scanned document", "batch convert all my PDFs", "turn this Word doc into Markdown", "crawl a web page to Markdown", "extract tables from this document". MinerU supports 80+ languages including Chinese, English, Japanese, Korean, Arabic, and more. Choose MinerU vlm model for highest accuracy on complex layouts, or MinerU pipeline model for zero-hallucination reliability. Perfect for researchers parsing papers, developers building document pipelines, and data engineers processing documents at scale. MinerU文档提取工具，PDF转Markdown、扫描件OCR、表格识别、公式识别、批量PDF处理、Word转Markdown、Excel转Markdown、网页爬取、图片OCR、学术论文解析。MinerU支持PDF、Word、PPT、Excel（XLS/XLSX）、图片等多格式文档智能转换，命令行一键提取，免登录快速模式或高精度专业模式。
- **company-research** — Free company research for AI agents: give it a company domain and get a cited company brief — what it does, products, pricing, target market, integrations, and key pages — from first-party evidence, with no API key and no signup.
- **tavily-search** — Search the public web through Tavily and return structured results with URLs and snippets. Use when an agent needs current information, source discovery, link lookup, news or finance search, or a fallback for unavailable built-in web search. Do not use for private or authenticated pages.
