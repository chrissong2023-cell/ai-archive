---
name: lishun-mail-acquisition
description: "Use for Chris's inbox triage, RFQ replies and WCA BD."
version: 1.0.0
author: Hannah (Hermes Agent)
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Email, RFQ, WCA, Freight, BD, Automation, Cron]
    related_skills: [email-inbox-triage, himalaya, openclaw-bridge]
---

# 利顺邮件获客流水线

Chris 的 24/7 邮件战情室 + 海外代理开发。代码在 `~/AI工作台/邮件获客自动化/`（`README.md` 是权威说明）。

## 何时用

- 「看邮件 / 整理邮件 / 回邮件 / 给客户报价」
- 「通过 WCA 会员获客」
- 排查自动回信是否发错、为什么没发、为什么跳过某封
- 改动分类规则、政策开关、定时任务

## 快速上手

```bash
cd ~/AI工作台/邮件获客自动化
python3 hunter/engine.py run --dry-run   # 永远先预演
python3 hunter/engine.py run             # 真跑：回确认函 + 转 Jackson + 日报
python3 hunter/engine.py status
python3 hunter/engine.py reclassify      # 改规则后重跑分类，不必重下邮件
python3 hunter/engine.py explain         # 本轮“为什么发/为什么没发”（政策+处置原因）
python3 hunter/engine.py backfill --since 15-Sep-2026   # 回补水位以下的历史邮件（不发任何邮件）
python3 hunter/engine.py approve                    # 预览：Chris 批准后要补发的确认函（按客户合并）
python3 hunter/engine.py approve --yes              # 真发（不含价格），默认只覆盖最近 16 天
python3 hunter/wca_batch.py --limit 12 --exclude-tld .com.au
```

日报：`data/reports/<日期>-digest.md`；待报盘台账：`data/pending.json`；拟稿：`drafts/`。

## 历史回补（挖存量客户）

增量扫描只看 `inbox_last_uid` 水位之后的新邮件；收件箱里往往还堆着几周未读（实测 224 封）。处理规则：

- `backfill --since <IMAP日期>` 对水位以下邮件只做**分类 + 抽字段 + 写台账/CRM**，`auto_ok` 强制 false——**历史邮件一律不自动回复**；向一周前的客户补发“已收到”比不回更失礼。
- 回补完看 `data/reports/backlog-<since>.md`，按客户合并成「未报价清单」再逐家发（同一家 15+ 封 RFQ 时单封回已无意义）。
- 除询盘外，回补的真正收益在「同行/代理主动找来」那一类——全部写 CRM，标注「历史台账 · 按需跟进」。
- 回补与自动动作都把询盘写进 `data/pending.json`（待报盘台账），三态：`等 Jackson 成本` / `过时询盘待确认` / `已回过，待出报盘`。每日早报脚本读它出「今日必做」；报盘完成或客户已回后要清账（`pending_resolve`），否则台账只增不减、早报会拿旧账当今日重点。

## 铁律（违反会真发错邮件）

1. **先 `--dry-run`**。改动分类/抽取规则后，先 `reclassify` + `act --dry-run` 看 `ack_sent` 列表是否合理，再真跑。
2. **只有 `is_direct_request()==True`（STRONG_DIRECT 句式）才允许自动回确认函。** 对方群发运价表常带 POL/POD 表格和 "please advise" 尾巴，靠 `labeled`/`inbound` 自动回会把促销信当询盘回。
3. **含价格的报盘永不自动发**（`policy.auto_send_quote=false`）。开这个开关前必须 Chris 明确给加价规则。
4. **重复回复防护三道**：Message-ID 在 Sent 的 In-Reply-To/References → 同主题+同域名 → Sent 全文 `TEXT "<RFQ编号>"` 搜索。缺一道就会给同一客户连发两封确认函。
5. **超时阈值 `ack_max_age_days`（4 天）**：更早的询盘只出草稿（汇总到 `drafts/<日期>-过时询盘-待批.md`），不自动补发。
6. **港口字段 `ports_source`**：`label`(POL/POD 标签)>`subject`(标题港口对)>`guess`(正文兜底)。是 `guess` 时确认函里必须请对方核对 POL/POD，绝不假装确定。3 字母机场码（DEL/BOM/CAN）必须大小写敏感匹配，否则会命中西班牙语 `del`、英语 `can`。
7. **群发特征**（unsubscribe / "dear valuable partner" / "as per your previous request I am sending"）命中即判定不可能询盘。
8. **静默时段 + 每日发送上限**（`quiet_hours_cst`、`daily_send_cap`）在发送前检查。
9. 每封外发都要写 `data/sent.jsonl` + `~/.openclaw/workspace/mail/sent-log.md`（`common.register_send` 已做）。
10. **正则的捕获组数必须与代码索引一致**。`EQUIP_WORD` 只写了 2 个捕获组，代码却读 `m.group(3)` → 第 86 封邮件抛 `IndexError: no such group`，**整轮 191 封回补全部中止**。改正则后跑一次真实数据（而非仅两个样例）验证。
11. **单封邮件的异常不得终止整批**：classify/extract 包 `try/except` 记为 `「解析异常」` 并继续；发信环节同理。另：循环里每 10 封 `save_state()` 一次——回补一轮去掉几十分钟，中途崩掉不能丢掉全部进度。
12. **改了行内缩进/重构后，确认旁路分支仍被赋值**：`backfill --limit N`、`--retry-vlm` 这类“指定子集”模式都靠 override 变量接手，漏掉赋值就会静默空转（输出“新文件 0 个”）。
13. **“我们自己发出去的开发信被回复了”必须排在分类链最前面**。WCA 开发信的主题是 `China ⇄ <国家> partner — Lishun Intl Logistics (WCA #136296)`，对方回信带着这一串并冠以 `Re:`；若先跑群发/运价特征（它们常附一整页运价表），这类**最热的线索会被归档成“对方运价群发”**，永远不会有人跟。判定规则：主题或正文出现 `WCA #136296` / `Lishun Intl Logistics` 且带 Re:/FW: → `CUSTOMER_DEV`（重点线索），放在 SYSTEM/WCA/群发判定之前。新加分类规则后务必 `reclassify` 回洗历史邮件。

14. **外发前必须清掉主题里的换行**。询盘主题常是两行（`... ||\r\n ...`），`email` 库编码 Header 时直接抛 `ValueError: Header values may not contain linefeed or carriage return characters`，整封发不出去。`common.send_reply` 与 `~/.nova-tools/mail.py` 的 `cmd_reply` 都已做 `re.sub(r"\s+", " ", subj)`；**任何新建的发信函数都要同样处理**——这条踩过第二次（`mail.py reply` 当时没做，一封印度客户的回信直接卡在 Header 编码）。

15. **发完必须回读 Sent 确认，不要信 SMTP 的 250**。网易 Sent 文件夹是 `&XfJT0ZAB-`；用 `M.fetch_header(im, uid)` 读头部（直接 `uid fetch (BODY.PEEK[HEADER...])` 在这个服务器上会返回 `None`，别以为是没发出去）。批量回复的验证判据：Sent 里出现对应收件人 + 时间戳落在刚才那一分钟内。批量回复的验证判据：Sent 里出现对应收件人 + 时间戳落在刚才那一分钟内。
15b. **`hold_reason` 必须保留**（`it.setdefault("hold_reason", "")`）：否则「为什么没发」的记录被抹掉，之后无法重建待批清单——重分类后曾导致 16 封待批询盘找不到来源。
16. **补发确认函一律按客户合并、一封列全部在手 RFQ**（`draft.ack_recap`），不要一询盘一封：同一家 9 封 RFQ 会收到 9 封几乎相同的邮件。另：`approve` 默认 `--days 16` 只看近期，旧邮件不补发；自己人/自家域名（`config.team`）自动排除，免得给自己发确认函。

17. **`mail.py search` 中文崩、英文 0 命中——两个病因叠在一起**：imaplib 用 ascii 编码 str 参数（中文直接 `UnicodeEncodeError`），而裸 `UID SEARCH <词>` 只搜 BODY（主题里的 RFQ 搜不到）。已落地的改法：ASCII 走 `OR SUBJECT/FROM/TEXT` 三字段，非 ASCII 或服务端无结果时**本地扫最近 N 封的主题/发件人/收件人**（`--scan`，默认 400）。改完必须 `RFQ`/`报价`/`WCA` 各测一次，中英都要有命中才算修好；只测英文会漏掉崩溃路径。
18. **打印 `~/.nova-secrets/*.json` 做审计时用允许列表，不要用敏感词黑名单**：网易企业邮的字段叫 `authcode`，不含 token/secret/key/password 任何一词，黑名单过滤会把应用密码原样打进对话。只打印账号、主机名这类非密字段，其余一律 `<redacted>`；万一误打印，立刻告知用户去后台重置。
19. **WCA 新会员 CSV 有三处脏点，不处理就会发错国家和重复联系人**：① `email` 列常混入 `Name: … Title: …` 或多个邮箱 → 正则取第一个合法邮箱；② `city` 常是 `Head Office`，不能当国家；③ `.com` 域名的中国公司在 TLD 上看起来是“海外”，只能靠**城市名→中国**（深圳/宁波/青岛/上海/大连/厦门/天津/广州…，必须硬编码）判定。**国内同行与海外代理分两批、两套话术**：把“China-side partner”的开发信发给中国货代是废信。
20. **发送权限（Chris 已授权，常驻）**：每日一发的**信息类**客户邮件（确认收到 / 跟进 / 物流状态 / 例行询问 / 内部转发）与**已定稿的开发信、唤醒信**可以直接发，不必逐封等批；报价、价格、条款、账期、交期承诺、新客户首次商务条件、银行/账户/付款、合同与签章、涉合规判断的对外表述**仍必须 Chris 一句**。每封照旧写 `sent.jsonl` + `sent-log.md`，并在每天 18:00 汇总「今日已发清单」给他抽查——授权的前提是留痕可回溯。

## 历史邮件挖掘（存量档案 → 知识库）

收件箱体量决定训练量：`lslogistics` ~7.8k 封、**`cbloom` ~25.9k 封**（十几年客户/报价/清关记录）。增量学习只看最近几百封，历史的必须单独挖。

```bash
~/.nova-kb/venv/bin/python ~/.nova-tools/mail_mine.py --account cbloom --n 1000
# cron「历史邮件挖掘·每晚0200」已挂：wrapper ~/.hermes/scripts/mail_mine_nightly.sh
# 游标 ~/.nova-kb/mail-mine-cursor.json：{account: 已处理到的最小 UID}，从最新往回走
```

规则：

- **只把有价值邮件写进知识库**：主题+正文命中的业务词（rfq/报价/运单/清关/合同/发票/gpu/idc…）**至少 2 个**才落 `~/.openclaw/workspace/knowledge/feed/mailmine/<account>/<uid>.md`，每轮上限 120 封；其余只进 `mail_facts.jsonl`。
- **噪音必须硬过滤**：账户安全/异地登录/验证码/登录提醒/unsubscribe/newsletter 一律不进库——否则两三晚就把检索淹掉（实测 40 封里混进 3 封登录提醒）。
- 每轮结束跑 `kb.sh index`（增量，有新文件时秒级）；只在有新文件时跑，避免空转。
- 速率实测 **100 封 / 62 秒** → 1000 封约 10 分钟，2.5 万封约 26 晚。夜里跑、白天不占 I/O。
- 邮件正文里常有整段引用（`> ...`），入库前剥掉，否则同一段话被索引多次。

## 从 mail_facts.jsonl 反推客户池（不做网页自动化也能开发客户）

`00-总控/STATE/mail_facts.jsonl` 每行一封已学邮件（`account / uid / date / from / from_domain / subject / category`），是现成的 CRM 底稿：按域名聚合就能回答「谁跟我们往来过、多久没联系、值不值得唤醒」。

**定位某一封旧邮件并取回附件**（Chris 常问「那封邮件在哪 / 再发我一次」）：

```bash
# 1) 先查索引——比 IMAP 全量搜快得多，而且能直接拿到 folder/uid
grep -i '<主题关键词或域名>' ~/AI工作台/00-总控/STATE/mail_facts.jsonl | head -3
#    行内 key 形如 cbloom|INBOX|1587506134 → 依次是 account / folder / uid
# 2) 读正文与头部
python3 ~/.nova-tools/mail.py show --account cbloom --uid 1587506134
# 3) 取附件（show 只印正文，从来不列附件）
python3 ~/.hermes/skills/productivity/lishun-mail-acquisition/scripts/fetch_attach.py \
        cbloom INBOX 1587506134 "$HOME/AI工作台/<项目>/<日期>"
```

- **`mail.py search` 返回 0 命中 ≠ 没有这封邮件**：它只扫指定 folder 的最近窗口，几个月前归档的信搜不到。先查 facts 索引，再打 `show`。
- **附件往往才是正事**（问卷、合同、报价表、对账单）：取回后落项目目录（敏感件进隔离区），回复里用 `MEDIA:<绝对路径>` 发给 Chris——他要的是能直接打开的文件，不是一条路径。

```bash
~/.nova-kb/venv/bin/python ~/.hermes/skills/productivity/lishun-mail-acquisition/scripts/counterparty_recon.py
```

规则（每条都踩过）：

- **按 `from_domain` 聚合，排除自家域名与公共邮箱域**（163/gmail/qq/outlook/hotmail）；再把 `fedex.com`、`casslink2.iata.org` 这类**承运人/结算平台**单列为「运营往来」，它们不是客户。
- **同一对手方会同时出现在多个邮箱**（cbloom 2.5 万封 + lslogistics 7.8 千封）。断言「这封询价在哪个邮箱」之前先看 facts 里的 `account`——归错邮箱会让后续 `reply` 用错线程、报错或发到错地址。
- **B2B 平台的自动买家线索（`no-reply@service.*`）不是客户来信**：邮件回复无效，必须回平台内操作。正确处理是登记线索 + 判断「以货代身份报运费」还是「货物贸易」，不要塞进邮件回复草稿。
- **银行/合规类邮件按时效单列**：制裁问卷、KYC 补件压几个月没回属于账户风险，要放到当天最前面；但**问卷正文与签字只能 Chris 本人做**，我只出草稿、列清单、给截止日。
- 结果落 `00-总控/STATE/customers.csv`（域名/往来数/最近联系/主营/分级），对话里只给 top N + 可唤醒家数，不要刷几十行。

## 授权码 / 凭据的处置（Chris 会把码贴在聊天里）

Chris 会直接把网易「客户端授权码」发到对话里，并且可能**说错账号归属**（实测他给“cbloom 的码”其实是主邮箱的）。按这个顺序处理，不反复说教：

1. **先判定归属**：拿这个码对 `mail.json` 里每个账号各做一次 IMAP 登录（`imaplib`，15s 超时），哪个通过就写哪个。多账号都通过时不写，先问。
2. **写入不回显**：python 读 json → 改字段 → `chmod 600` → `os.replace`，输出只说“已更新 X 账号”。
3. **立刻双向验证**：IMAP 读 1 封 + SMTP 只做登录握手（不发信）。两小时内的多次反复登录会触发网易限流（表现为 IMAP 间歇 `error`，SMTP 正常）——**等 10–20 分钟再测**，别当成码坏了。
4. **提醒轮换一次就够**：贴进聊天等于已泄露，说一次“下次改文件、不贴聊天”，然后继续干活；重复劝告只会浪费他的时间（他会继续贴）。

## Gmail 接入（与网易完全不同的一套）

Gmail 没有「授权码」，只有 **App Password（应用专用密码，16 位）**，而且三个前提缺一不可：

1. 账号已开**两步验证**（没开则 `myaccount.google.com/apppasswords` 直接提示不可用；企业/学校账号被管理员禁用也一样）；
2. 生成后**去掉空格**才是 16 位；
3. Gmail 网页 → 设置 → 转发和 POP/IMAP → **启用 IMAP**。

写进 `~/.nova-secrets/mail.json`：`imap: imap.gmail.com:993`、`smtp: smtp.gmail.com:465`，密码字段同 `authcode`。

**现实约束（决定要不要接）**：Gmail 只有在**隧道起来时**才可达（解析常落在 `198.18.x.x` 假 IP 段）。隧道一断，IMAP 立刻报错，而国内邮箱不受影响。所以 **Gmail 不进每 2 小时的自动扫描**，只按需拉；否则一天会刷出十几条“Gmail 连不上”的噪音。

## 语气校准（Chris 的英文邮件风格）

从 Sent 文件夹实测（`draft.py` 已固化）：

```
Dear <First>,

Good day. Thank you for your enquiry (RFQ-xxx); noted as below:

- POL / POD : ...
- Equipment : ...

We are now working on the rates and will revert shortly with our best offer, transit time, ETD and free time.

Best regards,
Chris Song
Lishun International Logistics Co., Ltd.  (WCA ID 136296)
```

短句、事实、不寒暄、不承诺价格。WCA 开发信用 `SIG_SHORT` 一行签名。

## 环境要点

- 邮件凭据：`~/.nova-secrets/mail.json`（与 Nova 共用）；IMAP 需要 `xatom("ID", ...)`，网易企业邮才会允许 SELECT——`~/.nova-tools/mail.py` 已处理。
- Sent 文件夹是修改版 UTF-7 编码的 `&XfJT0ZAB-`（= 已发送）。
- WCA：`~/.nova-secrets/wca.json` + cookie `~/.nova-secrets/wca_cookies.txt`（过期跑 `~/.nova-tools/wca_login.sh`）。会员区偶被 VPN（小地球仪）劫持默认路由导致超时；`curl --interface <内网IP>` 可绕过验证。
- WCA 新会员数据源：`~/.openclaw/workspace/projects/wca-bd/data/new-members-*.csv`（Nova 采集）。CSV 无国家列 → `country_of()` 按 网站 TLD → Address 段 → "based in" → 城市 推断；推断不出国家名时开发信写 `your market`，不硬写错的国家。
- 学习/开发信脚本：`~/.nova-tools/bd_learn.py`（只读扫邮箱 → `00-总控/STATE/mail_facts.jsonl` + `00-总控/业务规律.md`：客户热度、回复中位时延、来访时段、沉默客户）、`bd_outreach.py`（WCA 会员 → `00-总控/OUTBOX/` 开发信草稿，按 `outreach_seen.json`+sent-log+CRM 三重去重，只出草稿不发送）、`mail_mine.py`（存量邮件夜间挖掘）。三者都按 UID/邮箱幂等，可直接挂 cron。
- 批量回复：`~/.nova-tools/send_replies.py <draft.md> <uid...> [--dry]` —— 从 OUTBOX 草案抽正文、按 UID 取原邮件头做线程回复（`In-Reply-To/References`），每封写 sent-log + `00-总控/LEDGER.jsonl`。
- 定时任务：`mail_tick.sh`(30m) / `mail_morning.sh`(08:30) / `wca_weekly.sh`(周一 09:00)，在 `~/.hermes/scripts/`，用 `hermes cron list` 管。
- **静默时段 23:00–07:00 只归档/拟稿不外发**（`policy.quiet_hours_cst`），夜里跑不代表停工；Chris 若问“夜里怎么没动静”先看这条。
- cron 任务的**投递目标要显式设置并核对**：任务在跑 ≠ 简报能到人。`hermes cron list` 看 `last_status` / `last_delivery_error`；发现问题先改 `deliver: local`（简报落 `data/reports/`，不再刷失败），再决定推送到哪。原理见 hermes-agent 的 background-systems 参考。

## 排错

| 现象 | 原因 / 处理 |
|---|---|
| 该回的没回 | 查 `data/items.jsonl` 该封的 `auto_ok`/`reasons`；大概率缺 STRONG_DIRECT 句式或超过 `ack_max_age_days` |
| 不想发的要发 | 把 `policy.auto_send_ack` 设 false（全部转草稿），或加关键词到 `MASS_MAIL_PATTERNS` |
| 分类错了 | 改 `hunter/classify.py` 的规则 → `engine.py reclassify` → `act --dry-run` 验证 |
| Jackson 回信没变成报盘 | 目前只导出到 `drafts/jackson-cost-*.md`，需人工配对 RFQ 与定价（见 README「已知缺口」） |
| 首扫只覆盖 14 天 | `config.scan.first_run_days` 调大后重跑；水位以下的存量用 `backfill --since`，别改水位 |
| 回补跑一半崩了 | `state.json` 未存→下轮重做，items.jsonl 会出重复行；`load_ledger` 抛异常时多半是台账哈希字段名不匹配（`sha` vs `sha256`），不要用裸 `except: pass` 包住取值 |
| 任务在跑但人收不到简报 | 看 cron 的 `last_status` / `last_delivery_error`（投递目标没解析成功、平台会话失效）；先把 `deliver` 改 `local` 止住报错，简报在 `data/reports/`，再选一条能落地的通道 |
