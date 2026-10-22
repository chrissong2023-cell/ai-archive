# 只读体检与分阶段改造方案（Hermes + OpenClaw 全家桶）

用户说「先检查、先汇报、不要擅自改、给我方案等确认」时走这一套。产出物是**报告 + 待确认清单**，不是改动。

## 铁律

1. **体检阶段零改动**：不装软件、不改 `config.yaml`/plist、不删文件、不重启别人的服务。只跑读命令。
2. **凭证永不出现在输出——用白名单，不要用黑名单**：不 `cat openclaw.json`、不 `cat ~/.hermes/.env`、不遍历打印 `~/.nova-secrets/*.json`。只打印明确要的那几个键（`email` / `imap` / `smtp` / `default` / `memberId`），**其余一律 `<redacted>`**。原因：网易企业邮的字段名叫 `authcode`（等价密码），`pass|secret|token|key|cookie` 这类黑名单正则漏掉它，一次“脱敏 dump”就能把三个邮箱授权码打进对话，补救只能让用户去服务商后台重置。**未知字段名默认按秘密处理。**
3. **区分“已验证”与“未验证”**：另一台机器（Windows 节点）、iPad、未安装的组件，一律标“需在对方机器上执行”，不写成已就绪。
4. 报告结尾固定给**待确认清单**（3–5 条，每条是一个可执行决策）。

## 读命令（两三轮就能跑完）

```bash
# Hermes
hermes --version; launchctl list | grep -i hermes; hermes gateway status
hermes mcp list; find $HERMES_HOME/skills -name SKILL.md | wc -l
python3 -c "import json;d=json.load(open('$HOME/.hermes/cron/jobs.json'));print(len(d))"; \
  python3 -c "import json;[print(j['name'],j.get('schedule'),j.get('enabled')) for j in json.load(open('$HOME/.hermes/cron/jobs.json'))]"

# OpenClaw
openclaw --version; curl -s -m5 http://127.0.0.1:18789/health
openclaw gateway status | head -12; openclaw channels status; openclaw devices list; openclaw nodes status

# 权限（macOS）
codesign -d --entitlements :- /Applications/Hermes.app 2>/dev/null | grep -o 'com\.apple\.[A-Za-z.\-]*' | sort -u

# 本机服务面
LC_ALL=C lsof -nP -iTCP -sTCP:LISTEN | awk 'NR>1{print $1" "$9}' | LC_ALL=C sort -u
```

## 已知格式坑

- `~/.hermes/cron/jobs.json` 顶层是 **list**，不是 `{jobs:[...]}`；每项 `schedule` 是 dict（`kind`/`expr`/`display`）。按 dict 取会 `TypeError`。
- `lsof | sort -u` 会报 `sort: Illegal byte sequence`——进程名里有非 UTF-8 字节。`awk`/`sort` 前加 `LC_ALL=C`；也不要把它交给默认严格解码的 python 子进程。
- `launchctl list` 三列是 **PID / 上次退出码 / label**。PID 为空且退出码非 0 = 没在跑；`launchctl print gui/$(id -u)/<label>` 里的 `job state = spawn failed` 表示 launchd 卡在退避，**重启用 `launchctl kickstart -k gui/$(id -u)/<label>`**，不要反复 `bootout/bootstrap` 或让进程 `os._exit` 自愈（会加重退避）。
- **不要整份 dump `config.yaml` 再正则脱敏**：默认 2000+ 行注释会把上下文冲爆，且脱敏后仍泄露结构。只取需要的键：
  ```bash
  hermes config get model.default; hermes config get model.provider
  hermes config get gateway.allow_all_users; hermes config get terminal.backend
  python3 -c "import yaml;c=yaml.safe_load(open('$HOME/.hermes/config.yaml'));print(c['model']['default'],c['model']['provider'],c['terminal']['backend'])"
  ```
- entitlements 决定 Apple 集成能不能用：缺 `com.apple.security.automation.apple-events` 时 osascript 驱动 Notes/Reminders/Calendar 会超时 **-1712**，即使 `personal-information.calendars/reminders` 在列也没用；缺 screen-recording/accessibility 时 computer-use 类工具受限。报告里要把这是“权限缺口”而不是“功能不存在”。
- 远程可达性先看 bind：gateway 监听 `127.0.0.1` 时 iPad/另一台电脑**连不上**，此时“能从手机下命令”只可能是因为走了云端 IM 通道（微信/企业微信/飞书），不是直连。先 `lsof` 确认 bind，再谈隧道（Tailscale / Cloudflare Tunnel）。

## 审计必查的五件易漏事

1. **定时任务要分三层读**：`jobs.json` 里的 `last_status` 可能是 `delivery_failed`——**任务本身跑成功了，坏的是消息适配器**（微信/飞书侧，报 `iLink sendmessage session not ready: ret=-2 … errmsg=prepare failed`）；`last_error` 里出现 `Hermes can't reach the model provider` 才是任务级失败。历史读 `~/.hermes/cron/executions.db`（表 `executions` / `cron_incidents`），状态值是 `completed` / `failed`，**不是 `ok`**——按 `status='ok'` 统计会得到“0 成功”的假结论。
2. **同类失败卡在固定时刻 = 环境问题**：连续几天都死在 07:30 / 08:30，先怀疑那个时段机器在睡、网络没起来或出口被占，而不是模型或代码；报告里给“预检 + 重试 + 失败原因直报”，不要顺手改业务逻辑。
3. **消息通道要分“收”和“发”两端**：`channel_directory.json` 里有 DM 只能证明**能收**；cron 的 `deliver` 能不能真送达要单看 `last_delivery_error`。审计时两行分开写，别合成一句“通道正常”。
4. **邮件搜索是最容易“看起来能用”的假能力**：`mail.py search` 必须带 `--account`；英文词可能 0 命中，中文词直接 `UnicodeEncodeError: 'ascii' codec can't encode` 崩掉。**0 命中不能当成“没有这封邮件”**，要写成能力缺口并给替代路径（知识库检索 / 本地 fetch 后过滤）。
5. **拿正在生效的配置去对账用户红线**：把 `auto_send_*`、`quiet_hours`、`daily_send_cap` 与“未经批准不得对外发送”逐条比。实测存在 `auto_send_ack=true` / `auto_send_wca_outreach=true` 在自动给客户回信——这类不一致要放在报告最前面当风险，而不是埋在能力表里。

## 报告骨架（用户要的形态）

1. **体检表**：版本 / 模型+provider / 运行状态(PID、launchd、常驻时长) / 技能数 / 定时任务 / 已通消息通道 / MCP / 权限（有=✓，缺=✗ 并写后果）
2. **两个 agent 的接口可用性表**：CLI 派活、共享技能总账、共用 RAG、MCP 互换、IM 通道——逐项标 已通/机制在未接/未配置
3. **架构**：主控机（唯一有状态）／执行节点（只做手）／移动指挥端；写明 transport（IM 云通道 vs 隧道）和当前缺口
4. **工作流**：按业务线列表，每条标 谁主责 / 已有基础 / 缺口
5. **统一台账**：单一任务清单 + 项目索引 + 待批 OUTBOX + 每日汇总 + 追加式流水（两个 agent 共写，不各记一套）
6. **Skills 评估表**：名称 / 来源 / 用途 / 需要的权限 / 费用 / 风险 / 建议（装/不装/试点）。**审计阶段一个都不装**
7. **消息渠道安全**：哪个通道用于指挥、哪个只用于应急、白名单、一次性确认码、拒收敏感信息、审计留痕
8. **分阶段方案**：P1 低风险可回滚 → P2 需改配置（逐条给 diff）→ P3 逐项批准；另列“永久不做”清单
9. **待确认清单**：3–5 条决策，等用户回。
