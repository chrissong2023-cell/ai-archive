---
name: openclaw-bridge
description: Use when driving the OpenClaw agent (Nova) from Hermes.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [openclaw, nova, agent-bridge, mcp, macos]
    related_skills: [hermes-agent]
---

# Bridging Hermes ↔ OpenClaw (Nova)

## When to Use

- 用户要求指挥/委托 OpenClaw（Nova 🦞）干活（委托任务、发消息、跑自动化）。
- 需要 Chris / 集团背景资料时（读 Nova 工作区的 USER.md / MEMORY.md / knowledge/）。
- 排查 OpenClaw 网关、模型、通道问题，或做 Hermes ↔ OpenClaw 的 MCP 互换。
- 用户问到「小龙虾」，通常就是指这台机器上的 OpenClaw / Nova。

OpenClaw is a second, independent agent on the same Mac. Hermes can drive it, read its knowledge, and exchange MCP tools with it.

## 协同层（2026-10-17 起）：共享技能总账 + 共用 RAG

两边不再各记一套能力清单。**唯一真源**：`~/AI工作台/团队协同/`

```bash
SK=~/AI工作台/团队协同/bin/scan_skills.py
$SK                # 重扫两边技能 → registry.json + SKILLS-MAP.md（顺带把共享技能同步到 Nova）
$SK search 邮件     # 跨 Hannah / Nova 搜技能（owner + 路径 + 是否就绪）
$SK who 会议        # 这项能力该派给谁（路由表）
```

- 共享技能 `team-hq`（分工路由 + 交接协议 + 共用知识库 + 红线）是**同一份文件**：Hermes 走符号链接 `~/.hermes/skills/team/team-hq`；**OpenClaw 不跟随 symlink**（实测），所以由同步脚本实体复制到 `~/.openclaw/workspace/skills/team-hq/SKILL.md`（头带 `AUTO-SYNCED`）。改内容→改真源→跑一次 `scan_skills.py`。
- **只读任务不要跑无参 `scan_skills.py`**：无参数时会重写 `registry.json`/`SKILLS-MAP.md` 并把共享技能同步进 Nova 工作区，是写操作。只读场景改读 `registry.json`/`SKILLS-MAP.md`（或只用 `search`/`who`），并在汇报里说明读的是哪一份、`generated` 是什么时候。
- **`team-hq` 的真源在 `~/AI工作台/团队协同/skills/team-hq/SKILL.md`，不在 skills 树里**：skill 管理工具只能看到 `~/.hermes/skills/team/team-hq` 这个符号链接，改不动它；要改就改真源文件，再跑 `scan_skills.py` 同步到 Nova 并刷新总账。
- `openclaw skills list --json` 是 Nova 能力的权威来源（带 ready/缺依赖）；不要采信它自报的技能清单，也不要采信上周写的 `SKILLS-INVENTORY.md`。
- 知识库同一套：`~/.nova-tools/kb.sh search "词"` / `127.0.0.1:8765`；增量索引 + 混合检索（详见 `feed-capture` 技能 23 系列坑）。
- 活跃本机口径：Hannah 68 技能 / Nova 75 / 共享 1（以 `registry.json` 的 `generated` 时间为准，数字会变；共享技能在 Nova 侧的副本不计入 nova 计数）。
- **任务与决策在 `~/AI工作台/00-总控/`**（另一层，不属技能）：`tasks.jsonl` 是唯一任务源，`bin/ctl.py add|list|start|block|done|digest` 读写它，`DAILY/` 每日汇总、`OUTBOX/` 待 Chris 批、`LEDGER.jsonl` 追加流水。派活前后都在这里落一个任务号，不要另起 TODO。业务工作流技能是 `wf-01-inquiry-quote` … `wf-06-mail-calendar`（报价/物流/GPU采购/合同KYC/CRM/邮件日程），两边同时可见。

## Environment (verified 2026-10-12)

- CLI: `/opt/homebrew/bin/openclaw` (npm global, 2026.10.1). Gateway: `ws://127.0.0.1:18789`, LaunchAgent `ai.openclaw.gateway`.
- Config `~/.openclaw/openclaw.json` (contains plaintext secrets — never print values). **导出任何凭证类文件只打白名单键**：黑名单正则（`pass|secret|token|key|cookie`）会漏掉 `authcode` 这种字段名——网易企业邮的授权码就叫这个，一“脱敏”就等于把密码原样打出来。未知字段一律当秘密。
- Logs: `/tmp/openclaw/openclaw-<YYYY-MM-DD>.log`; service status `openclaw gateway status`.
- Nova's workspace: `~/.openclaw/workspace` — `USER.md` (the human), `IDENTITY.md`/`SOUL.md` (Nova), `MEMORY.md` (curated long-term), `AGENTS.md`, `WORKFLOW.md`, `INDEX.md` (file index), `knowledge/company-dossier.md`, `projects/`, `memory/YYYY-MM-DD.md`, `briefings/`, `inbox/` (Desktop alias 「Nova投喂」 → `workspace/inbox`). Read these before asking Nova about the business.

## Direct Nova to work

```bash
openclaw agent --session-key agent:main:hx-<label> --model deepseek/deepseek-v4-flash \
  --json --timeout 300 -m "<task>"
```

Result shape (**2026.10 verified**): the reply text lives at `result.payloads[0].text` — **not** `result.terminalReply.text` (that path is stale, returns None). Model/cost at `result.meta.agentMeta.model`. Redirect stdout to a file and parse; `--json` output is pretty-printed multi-line and mixes banners on failure.

Verified working invocation:

```bash
openclaw agent --session-key agent:main:hx-<label> \
  --model deepseek/deepseek-v4-flash --json --timeout 180 \
  -m "<task>" > /tmp/out.json 2>&1
# 然后解析 result.payloads[0].text
```

Only `deepseek/deepseek-v4-flash` is configured in `openclaw models list` — other ids (e.g. kimi) have no credential.

More levers: `openclaw message send --channel <ch> --target <t> -m "…"`; `openclaw sessions list` (171 sessions on this Mac's agent); `openclaw cron`/`automations`; `openclaw skills`; `openclaw channels status`.

**Nova's self-reported channel status is unreliable.** In a verified handshake Nova claimed 「已连接 IM 通道：webchat（唯一在线）」while `openclaw channels status` showed Feishu enabled+connected and two openclaw-weixin bots. Always check the CLI, never relay Nova's self-description as fact.

## Reaching a SECOND machine (e.g. the Lenovo X1) — mechanism confirmed, not yet wired

**Correction to an earlier note**: this IS supported — via `openclaw connect`, not via `openclaw nodes`. Do not repeat the "impossible" claim.

The right commands (verified present in 2026.10.1):

```bash
openclaw devices join-code      # 在主机上生成一次性节点入网 URL（不是手机配对码）
openclaw connect <url> --service --display-name "X1-北京顺义"   # 在另一台机器上跑
openclaw devices list / approve # 主机侧批准
openclaw nodes status / invoke  # 验证 + 发命令（nodes 是连接后的管理面）
openclaw dns setup              # Tailscale + CoreDNS 广域发现
```

Blockers on this Mac (2026-10-13):

| Path | Status |
|---|---|
| Gateway bind | `loopback` — must be opened to the Tailscale iface or LAN before a remote node can reach it |
| `gateway.tailscale.mode` | `off`; **Tailscale not installed** on this Mac |
| Paired nodes | none (`Pending: 0 · Paired: 0`) |
| LAN | the X1 is in a different city; not on `192.168.78.0/24` |

**`openclaw nodes` alone was the wrong read** — on its own it looks like a companion-device API (camera/canvas/location/notify/screen/APNs push), but it is the *management* surface for nodes created by `openclaw connect`, and `nodes invoke --command` can run system commands on the remote box.

**企业微信 (WeCom)** is supported but not installed (`openclaw channels list --all` → `WeCom: not installed`). 微信 and WeCom are separate plugins (`openclaw-weixin` ≠ WeCom).

**给第二台机器建独立飞书应用**，不要两台共用一个 appId —— 否则客户分不清是哪个机器人在回话；工作组里"谁干的"必须可区分。

Do NOT claim you can drive a remote machine until you have actually executed something on it and read back the result.

## Pitfalls (all hit for real)

- **Always pass `--model`.** `agents.main.model` is misconfigured as `deepseek/deepseek-v4-pro@deepseek:setup-…` → `Unknown model`; the `moonshot/kimi-k2.6` fallback has no auth. Default turns fail with model/auth errors until the config is fixed.
- **Use a private `--session-key`** (`agent:main:hx-…`) so you never inject text into the user's live main conversation.
- **Interrupted run poisons the session**: after a gateway restart mid-turn the next run fails `SESSION_WORK_START_CHANGED. Retry.` — retry or switch to a fresh session key.
- **Long turns can outlive my client**: the CLI's output file can still be **0 bytes while the turn is running** — that is not truncation. Check size/mtime first (`ls -la`, wait, re-check); the file can fill in minutes later with a complete answer. Only if the process has already exited with an empty file should you send a short follow-up to the SAME `--session-key`: "your last conclusion was cut off, restate it, don't re-investigate" — never re-issue the task (it would run twice).
- **Run long turns in the background**: `terminal(background=true, notify=true)` then poll the output file, instead of a foreground call that times out and gets promoted unpredictably. Keep task text in a file (`--message-file`) to dodge shell-quoting bugs with Chinese text.
- **Inspect state cheaply**: `openclaw sessions list` shows age/context%/model per session (the model column reveals whether your `--model` override took effect); `openclaw transcripts list` was empty on this install.
- **The gateway restarts itself** (LaunchAgent + handoff restarts; expect ECONNREFUSED windows). Wait 10–20 s, then `curl -s http://127.0.0.1:18789/health` → `{"ok":true}` before retrying. **Root cause on this Mac (verified) — the restart is self-inflicted:** the gateway's state-lease heartbeat (`utimes` renewal on its own lock) must complete within 60 s, and it starves when the Mac sleeps, or when stalled DNS lookups occupy Node's 4-thread libuv pool; the log line is `Gateway state ownership is no longer current … utimes heartbeat renewal did not complete within 60 seconds; restart`. So a restart storm is a **host power/DNS problem, not an OpenClaw bug** — read `pmset -g log` for sleep cycles and `scutil --dns` for a dead IPv6 nameserver before blaming the agent, and fix it per the `macos-always-on-host` skill. This is also the common reason a delegated turn comes back with an empty output file.
  **这台机器已做的缓解（2026-10-14，Chris 同意后由 Hermes 实施）**：`~/.openclaw/service-env/ai.openclaw.gateway.env` 加了 `UV_THREADPOOL_SIZE='16'` 与 `NODE_OPTIONS='--dns-result-order=ipv4first'`（wrapper 在 `exec node` 前 source，所以这是唯一生效的位置；同值也写进了 `openclaw config env.vars`）。重启 `launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway`，用 `ps -Eww -p <pid> | tr ' ' '\n' | grep UV_THREADPOOL_SIZE` 确认，用 `openclaw agent … "只读，回一句你在线"` + `result.payloads[0].text` 确认它真能干活。详见技能 `macos-always-on-host`。
- **Get the JSON reliably**: redirect stdout to a file (`> /tmp/x.json 2>&1`) and parse; interactive tails mix error banners into the JSON.

## 委托任务的写法（每次照做）

1. **任务写进文件、用 `--message-file` 传**：中文引号、换行、多行清单不会被 shell 吃掉，也方便自己复查发了什么。
2. **每条任务开头写清边界**，例如「只读任务（不要修改任何文件、不要对外发送任何消息、不要动日历）」，或明确列出本任务允许的动作。Nova 会在结尾自发回一行「未改/未外发/未动日历」的确认——**把这行确认当作交付内容一起核对**，它撒谎或含糊过就要复问。
3. **要证据，不要结论**：问「为什么失败」时必须要求引用具体日志行 / errno / 代码位置 / 文件路径，并加一句「查不到就明说查不到，不要猜」。实测它能给出完整证据链（内核级阻塞、退出码、时间线）。
4. **做集成前先问它手上有什么**：发一句「你是否持有 X 的登录态/凭据？只回答有/没有 + 存放方式，不要输出任何密码或 token」。它的凭据清点可信（实测确认它**没有**携程/航旅纵横/京东/淘宝登录态，避免了白做一套方案）。用户说「账号都给过它了」时也要以这份清点为准，不要直接采信。
5. **绝不替用户收账号密码**：聊天里不接受密码（哪怕用户主动发），自己也不替它输入。密码只能由用户在自己的加密提示框里输入，或用户自己扫码登录后我沿用登录态。
6. **一次只派一件、互不依赖的任务**：它有自己的内存/会话/通道，但一个长任务会独占一个会话；同一 session-key 串行派活，别并发塞两件。

## MCP bridges

- `hermes mcp serve` exposes Hermes conversations over MCP → register in OpenClaw with `openclaw mcp add`.
- `openclaw mcp serve` exposes OpenClaw channels over MCP stdio → `hermes mcp add <name> --command openclaw --args mcp serve`.

## Business red lines (Chris's rules — **revised 2026-10-13**)

**Hermes may decide on its own** (report after, don't ask): 条款类邮件、报价类邮件、信息类邮件, plus routine retrievals / document work / local file ops.

**Still requires Chris's explicit approval**: 银行 related operations, 合同 signing/changes, **动钱** (payment/transfer/refund/deposit), 盖章, deletions, and major customer commitments (delivery-date changes, compensation, exclusivity terms).

**Not approval but an input dependency**: pricing still needs cost figures aligned with **Jackson** — Chris delegated *the selling price*, not the cost basis.

When handing anything to Nova, restate the red lines in the task itself — Nova's own `AGENTS.md` still carries the older, stricter rule ("报价须先与 Jackson 对齐成本、再请 Chris 定价"). Do not silently rewrite another agent's guardrails; flag the inconsistency to Chris instead.

## Nova's verified capabilities (measured 2026-10-13, self-report cross-checked)

Reliable reporter — its inventory matched the filesystem exactly on every checkable claim. Working: email send/receive via 网易企业邮箱 SMTP/IMAP (`~/.nova-tools/mail.py`, account `chris@lslogistics.com.cn`, 13 sends logged in `workspace/mail/sent-log.md` with per-send 授权 notes), daily inbox triage, RFQ tracking, contract review, Excel/PDF/OCR parsing, 飞书 docs/drive/wiki, local corpus search (inbox 471M + knowledge 409M), 国内工商尽调 via browser automation.

Missing: `mineru` CLI, `gh`, Notion/GitHub credentials; `himalaya` binary present but **no account config** (so use `mail.py`, not himalaya); international search engines often TLS-reset.

**Overlap warning**: Nova already has a `workspace/meeting-minutes/` project (created 2026-10-08 Nova × 飞书) targeting the *same* pipeline as Hermes's `client-meeting-minutes` skill (recording → transcript → minutes → archive), planning to use 飞书妙记 for transcription. Do not build a second parallel pipeline — agree a split first. Working proposal: **Hermes does transcription + minutes (free, unlimited, audio stays local); Nova does 飞书 knowledge-base archiving, the 多维表格 action-item ledger, and customer email follow-up.**
