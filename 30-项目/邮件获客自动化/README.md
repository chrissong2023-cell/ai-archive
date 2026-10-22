# 邮件获客自动化（Hermes · Hannah 运行）

给 Chris（利顺国际物流）用的 24/7 邮件战情室 + 客户开发流水线。
发件箱：`chris@lslogistics.com.cn`（凭据沿用 `~/.nova-secrets/mail.json`，与 Nova 共用一套）。

## 一分钟看懂

| 环节 | 做什么 | 是否自动 |
|---|---|---|
| 扫描 | 增量读收件箱（按 UID，14 天首扫窗口） | ✅ 每 30 分钟 |
| 分类 | 询盘 / 对方报盘 / 开发线索 / 财务 / 操作 / WCA / 系统 / 推广 | ✅ |
| 抽取 | POL·POD·箱型·货名·重量·条款·免箱期·有效期·RFQ 编号 | ✅ |
| 回确认函 | 「已收到+复述+承诺回价」，**不含任何价格** | ✅ 仅当"明确向我方询价"且 ≤4 天且未回过 |
| 转 Jackson | 汇总 RFQ 核成本（cc Chris） | ✅ |
| 报盘（含价） | 生成草稿，**等 Chris 批准**（`auto_send_quote` 默认 false） | ⛔ 默认人工 |
| WCA 开发信 | 新会员个性化英文开发信 | ✅ 政策开关 `auto_send_wca_outreach` |
| 台账 | 待报盘 `data/pending.json`，日报 `data/reports/` | ✅ |

## 目录

```
config.json          账户 / 政策开关 / 关键词
state.json           增量水位（inbox_last_uid）+ 已处理 msgid
run.sh               一跳：run + quote + status（cron 用）
hunter/common.py     邮件桥接（复用 Nova 的 mail.py）、状态、CRM 回写、发送登记
hunter/classify.py   规则分类 + RFQ 字段抽取（纯规则，不依赖大模型）
hunter/draft.py      英文拟稿（基于 Chris 已发邮件校准的语气）
hunter/engine.py     CLI：scan / act / run / digest / status / quote / reclassify
hunter/wca_batch.py  WCA 新会员开发信批量生成与发送
data/                items.jsonl（全量邮件）、queue-<日期>.json、pending.json、sent.jsonl、reports/
drafts/              所有拟稿（含过时询盘汇总、Jackson 转信留档）
logs/                每跳日志
```

## 常用命令

```bash
cd ~/AI工作台/邮件获客自动化
python3 hunter/engine.py run            # 一跳（发确认函+转Jackson+日报）
python3 hunter/engine.py run --dry-run  # 预演，不发任何邮件
python3 hunter/engine.py act --dry-run  # 只预演动作（用当天队列）
python3 hunter/engine.py reclassify     # 改规则后重跑分类，不必重下邮件
python3 hunter/engine.py status         # 水位/分类/发送数
python3 hunter/wca_batch.py --limit 12 --exclude-tld .com.au
```

## 政策开关（config.json → policy）

- `auto_send_ack` —— 询盘信息确认（不含价）自动发。
- `auto_send_internal` —— 自动转 Jackson 核成本。
- `auto_send_quote` —— **含价格报盘自动发（默认 false，须 Chris 开）**。
- `auto_send_wca_outreach` —— WCA 新会员开发信自动发。
- `ack_max_age_days` —— 超过 N 天的询盘只出草稿（避免补发过期确认函）。
- `quiet_hours_cst` / `daily_send_cap` —— 静默时段与每日上限。

## 安全阀（为什么它不会乱发）

1. 群发/含退订的邮件一律不进询盘桶；`auto_ok` 只认 STRONG_DIRECT 句式。
2. 已回过（Message-ID / 主题+域名 / Sent 全文搜 RFQ 编号）→ 跳过，不重复轰炸。
3. 超过 `ack_max_age_days` 天 → 只出草稿，汇总到 `drafts/<日期>-过时询盘-待批.md`。
4. 港口是"猜"出来的（`ports_source=guess`）→ 确认函里请对方核对 POL/POD，绝不假装确定。
5. 所有外发登记到 `~/.openclaw/workspace/mail/sent-log.md` 与 `data/sent.jsonl`。
6. 报价类内容永不自动发（除非 Chris 显式打开 `auto_send_quote`）。

## 定时任务（Hermes cron）

| 任务 | 频率 | 脚本 |
|---|---|---|
| 邮件战情室·30分钟一跳 | every 30m | `~/.hermes/scripts/mail_tick.sh` |
| 邮件获客·每日早报 | 每天 08:30 | `~/.hermes/scripts/mail_morning.sh` |
| WCA新会员获客 | 每周一 09:00 | `~/.hermes/scripts/wca_weekly.sh` |

`hermes cron list` 查看；`hermes cron pause <job_id>` 暂停。

## 依赖

- `~/.nova-secrets/mail.json`（IMAP/SMTP 授权码）——已就位
- `~/.nova-tools/mail.py`、`~/.nova-tools/wca_scrape.py`（WCA 抓取，需 cookie 未过期）
- WCA 会员区 cookie：`~/.nova-secrets/wca_cookies.txt`（过期时跑 `~/.nova-tools/wca_login.sh` 刷新）

## 已知缺口（下一步）

1. **报盘自动化**：Jackson 回成本后，目前把回信导出到 `drafts/jackson-cost-*.md`，需要人工配对 RFQ 并定价。若 Chris 给定价规则（加价率/最低毛利），可自动生成报盘并进批准队列。
2. **收件箱 5 周历史未读**（约 220 封）只处理了最近 14 天的 80 封；更早的按需回补（`first_run_days` 调大后重跑）。
3. **附件解析**：报价类 PDF/Excel 附件目前只记录文件名，未解析内容。
