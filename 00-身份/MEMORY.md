User's Mac is in mainland China. github.com is UNREACHABLE (git clone tap fails with HTTP2 framing error), so `brew install <user>/<tap>/<formula>` always fails; Homebrew's own bottles (Aliyun mirror) are fine. huggingface.co is blocked — use https://hf-mirror.com/... for models (~24MB/s). npmmirror is the npm registry.
§
Hermes 桌面端：源码 ~/.hermes/hermes-agent（default profile）；App /Applications/Hermes.app（自建 ad-hoc 签名，self 更新）；桌面有 Hermes 别名。
§
OpenClaw / Nova 🦞（openclaw 2026.10.1，网关 ws://127.0.0.1:18789）：用 `openclaw agent --session-key agent:main:hx-<name> --model deepseek/deepseek-v4-flash --json -m "…"` 驱使它干活；工作区 ~/.openclaw/workspace。桥接细节见技能 openclaw-bridge。
§
Chris named this Hermes agent **Hannah** (2026-10-12) — his OpenClaw agent is Nova; Hannah and Nova are expected to work together as a team.
§
Hermes.app 缺 com.apple.security.automation.apple-events → osascript/AppleEvents 控制其它 App（Notes/Reminders/memo）超时(-1712)或静默拒绝，无提示、内部不可修，别重试；已有 personal-information.reminders/calendars、audio-input、camera。Reminders 绕法：带 personal-information.reminders 签名的 EventKit helper 打包成 .app（裸二进制会被静默拒绝）。
§
本机常驻在线(2026-10-14生效)：AC sleep=0、合盖不睡、DNS 固定 223.5.5.5/119.29.29.29、关 macOS 自动更新重启；电池 15 分钟睡眠。脚本 ~/AI工作台/系统设置/*.command。FileVault 开着→断电重启须人工登录。
§
browser_exec 的标签页会在两次调用之间被回收（页面状态与登录态丢失）：凡涉及登录的操作（如微信公众号扫码）必须把「登录 + 干活」放进同一次 browser_exec 调用。
§
API 密钥类凭据放 ~/.hermes-secrets/<name>.json（chmod 600），不要让用户贴在聊天里；同目录留 .template 供用户填写。
§
投喂/知识库：投喂箱 ~/AI工作台/投喂/inbox（桌面别名「投喂给Hannah」）+ Nova 箱；launchd com.hannah.feed-watch 秒级捕捉、cron 每 5 分钟读正文。语料 → knowledge/feed/hermes/ → chroma ~/.nova-kb/chroma（增量索引；改切块规则要 +PIPE_VER 触发全量重建）；检索 com.hannah.kb-serve 127.0.0.1:8765。总控 ~/AI工作台/00-总控：tasks.jsonl 唯一任务源 + bin/ctl.py + DAILY/OUTBOX/LEDGER。共享技能 ~/AI工作台/团队协同/skills（team-hq + wf-01..06），改完跑 scan_skills.py。细节见技能 feed-capture / team-hq。
§
邮件获客自动化（Hannah 侧）：~/AI工作台/邮件获客自动化/，3 个 Hermes cron（战情室 30 分钟一跳 / 每日 08:30 早报 / 周一 09:00 WCA 获客）；含价格的报盘默认人工批准（auto_send_quote=false）。细节见技能 lishun-mail-acquisition。
§
两个官网由 Hannah 全权运维(2026-10-22 Chris 明确)：源码 ~/AI工作台/网站/{lslogistics.com.cn,wuzhounexus.com}，后台改动与每日内容更新都她做；托管阿里云 OSS 香港桶。做法见技能 static-site-delivery。