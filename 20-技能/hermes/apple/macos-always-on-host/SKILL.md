---
name: macos-always-on-host
description: "Use when a Mac must stay online 24/7 as an always-on host."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [macos, pmset, power, sleep, dns, always-on, uptime, launchd, cron]
    related_skills: [hermes-agent, openclaw-bridge]
---

# 让这台 Mac 7×24 常驻在线（电源 / DNS / 自动重启）

## When to Use

- 「帮我设置电脑长时间运行 / 优化待机 / 不要睡眠 / 常驻在线」。
- 后台东西莫名其妙地断：定时任务没准点跑（被唤醒后才补跑）、长连接重置、浏览器登录态丢失、agent 网关反复重启、飞书/微信通道刷 ENOTFOUND。
- 换了机器或重装后，要把机器重新配成常驻主机。

本机事实：MacBook Pro M5 Max（Mac17,7）是 Chris 的 AI 工作台主机，常驻 Hermes 网关 + OpenClaw(Nova) 网关 + cron。系统脚本目录 `~/AI工作台/系统设置/`。

## 先取证（30 秒，别跳过）

```bash
pmset -g custom      # 各电源档位当前生效值
pmset -g batt        # 插电还是电池 —— AC 的设置只在插电时生效
pmset -g log | grep -E "Entering Sleep state" | tail -20   # ← 最有诊断力的一条
launchctl list | grep -E "hermes|openclaw"                 # 第一列 PID，第二列上次退出码
```

`pmset -g log` 里成片的 `Entering Sleep state due to 'Maintenance Sleep'`（几分钟一次）就是所有「后台断线」的答案：**机器在睡**。排查任何「agent / 定时任务老断」之前先看这一条，不要先去读软件日志。

## 设置（一次做完，幂等）

本机 `~/.hermes/.env` 里配了 `SUDO_PASSWORD`，所以 terminal 里的 `sudo` 非交互可用。**直接跑 sudo，不要向 Chris 要密码，也不要让他双击脚本来授权。**（若某次 sudo 报要密码，就是这条配置丢了 —— 让他补回 `~/.hermes/.env`，仍然不要在聊天里要密码。）

```bash
# 插电（AC）：永不睡眠
sudo pmset -c sleep 0          # 关键。本机出厂是 1 = 闲置 1 分钟整机睡眠
sudo pmset -c disksleep 0
sudo pmset -c displaysleep 15  # 屏 15 分钟熄灭，后台照跑（省电降温）
sudo pmset -c tcpkeepalive 1   # 长连接不被掐
sudo pmset -c womp 1           # 网络唤醒
sudo pmset -c powernap 1
sudo pmset -c lowpowermode 0   # 插电不降频
# 电池：保命（拔电就该睡，别指望拔电还 24h）
sudo pmset -b sleep 15; sudo pmset -b displaysleep 5; sudo pmset -b lowpowermode 1
# 掉电恢复自动开机
sudo pmset -a autorestart 1
# 合盖不睡（先设再看值，别照抄「M 系列不支持」的说法）
sudo pmset -a disablesleep 1 && pmset -g | grep SleepDisabled
# 关掉「自动安装 macOS 更新」——否则深夜自动重启，打断 24h
sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates -bool false
```

规则：

- **`-c` / `-b` 是分电源档的。** 做完必须 `pmset -g batt` 报一句「现在在电池上，插上电才生效」。别让用户以为已经好了。
- **`disablesleep 1` 有代价**：拔电 + 合盖 = 一直耗到强制关机。必须同时给「关」的开关并当面说清代价，不要静默打开。
- **FileVault（`fdesetup status`）开着时 auto-login 不可用** → 断电重启会停在输密码界面，launchd 里的 agent 全都不会起。这是唯一改不掉的缺口，要明说，不要承诺「绝对 24h」。

## DNS：笔记本上的第二个隐形杀手

```bash
scutil --dns | head -12        # resolver #1 是不是 fe80::…%en0（IPv6 link-local）
ping -c1 -t2 <那个地址>        # 通常不通 → 每次解析先卡一次
networksetup -getdnsservers Wi-Fi
sudo networksetup -setdnsservers Wi-Fi 223.5.5.5 119.29.29.29 180.76.76.76
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
for i in $(seq 1 10); do dscacheutil -q host -a name <host> | grep ip_address | head -1; done  # 连测 10 次全通才算过
```

`networksetup -setdnsservers` 按**网络服务**（Wi-Fi）生效、跟随该服务，不是按 SSID，所以换到别的网络依然有效。副作用一句提示即可：个别需要门户认证的 Wi-Fi 可能受影响。

## 为什么「睡一觉」会把 agent 搞崩（机制）

Node 进程（OpenClaw 网关这类）的 state 租约心跳、单文件锁续约都走 libuv 线程池（默认 4 线程）。整机睡眠让心跳过期；卡住的 DNS 解析又把 4 个线程全占满 —— 两者叠加 → `heartbeat renewal did not complete within 60 seconds` → 进程判定自己失去 state 所有权并**自杀重启**。所以「网关反复重启」在笔记本上往往是**电源/DNS 问题，不是软件 bug**。

症状 → 根因 → 动作对照表：`references/sleep-wake-service-disconnects.md`。

## 给 agent 网关加线程池余量（要 Chris 同意才动）

Node 网关（OpenClaw）的 libuv 线程池默认 4 线程。卡住的 DNS 解析会把它占满，进而饿死 state 租约心跳 → 自杀重启。这是治本的第二道保险：

1. **启动环境是唯一可靠的位置** —— 必须在 node 启动前注入，只在运行时改 process.env 无效。文件：`~/.openclaw/service-env/ai.openclaw.gateway.env`，由 wrapper 在 `exec node` 前 source。
   - `export UV_THREADPOOL_SIZE='16'`
   - `export NODE_OPTIONS='--dns-result-order=ipv4first'`（本机没有可用 IPv6，解析优先 IPv4）
   - 改前 `cp -p` 备份；**第一行 header 必须逐字节不动**，wrapper 会校验，不匹配就 exit 78 起不来。
2. 同时写进受支持的配置，免得将来 `openclaw gateway install --force` 重建 env 文件时丢掉：
   `openclaw config patch --file <json5>`，内容 `{env:{vars:{UV_THREADPOOL_SIZE:"16",NODE_OPTIONS:"--dns-result-order=ipv4first"}}}`；先 `--dry-run`。
3. 重启 + 三层验证（缺一层就等于没验证）：
   - 重启：`launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway`
   - 环境真进了进程：`ps -Eww -p <pid> | tr ' ' '\n' | grep -E '^UV_THREADPOOL_SIZE=|^NODE_OPTIONS='`
   - 活着：`curl -s http://127.0.0.1:18789/health` → `{"ok":true,...}`、`openclaw gateway status`
   - **真干得动**：按 openclaw-bridge 派一个只读小任务，读 `result.payloads[0].text`（Nova 实测回「Nova 在线」）。
4. 基线：改前记 `launchctl print gui/$(id -u)/ai.openclaw.gateway | grep runs`，改后自行重启一次 = runs +1，之后不该再涨；`awk '$0>="<重启时刻>"' ~/Library/Logs/openclaw/gateway.log` 里 `ENOTFOUND` 与 `heartbeat renewal did not complete` 都应为 0 行。

Hermes 自己的网关是 Python（`hermes gateway run`），不适用这条 —— 别照搬。

## 网络断了 / VPN 连不上（与“机器在睡”并列的另一类断网）

按这个顺序取证，别一上来读应用日志：

```bash
scutil --nc list                  # 有哪些 VPN 配置、连没连
scutil --nc status "<profile>"    # 单个配置状态；--nc show 看 bundle id / OnDemandEnabled
systemextensionsctl list          # 网络扩展：activated enabled / activated disabled
scutil --proxy                    # 有没有系统代理被装上
ifconfig | awk '/^utun|^en0/{i=$1}/inet /{print i,$2}'   # utun 只有 IPv6 link-local = 隧道没承载流量
netstat -rn -f inet | grep '^default'
curl -s -m5 -o /dev/null -w '%{http_code}\n' https://www.baidu.com
log show --last 10m --predicate 'subsystem == "com.apple.networkextension"' | grep -i '<客户端名>'
```

日志里这两句就是结论，不是线索：

- `NESMVPNSession[Primary Tunnel:<name>:<uuid>]: Plugin is not installed`
- `… status changed to disconnected, last stop reason: Plugin was disabled`

= 该配置绑定的网络扩展在系统里被停用（macOS 大版本升级后旧扩展常被要求重新授权）。修复只能在 `系统设置 › 通用 › 登录项与扩展 › 网络扩展` 里手动打开（要管理员密码）；**`systemextensionsctl` 在 SIP 开启时被禁用**，不要试图用命令绕。

**硬规矩：客户端 GUI 没在跑时，绝不用 `scutil --nc start` 起隧道。** 这类客户端通常同时打开系统代理（可在它的容器 prefs 里查到，如 `Zion.systemProxyEnabled = True`）；命令行硬起的隧道没有节点握手、代理却已生效 → **整机断网**，用户会以为电脑坏了。要判断“是不是墙/服务器挂了”，测服务器侧可达性就够（`curl` 官方接口域名、`nc -z` 备用 IP:端口），不要起隧道。已经起了立刻 `scutil --nc stop "<profile>"`，并明确告诉用户是你做的。

- **两个客户端抢同一个名字是常态**：旧客户端和新客户端各有自己的 VPN 配置，显示名可能都叫「小地球仪」。只有 `scutil --nc show` 里的 bundle id 能区分；报告里写清“你点的那条属于哪个 bundle”。
- **Hermes 缺 automation / accessibility**：`osascript activate` 置顶不了别人的窗口，也读不到 UI；`screencapture` 只截得到最前面的窗口。别反复试——直接请用户点一下 Dock / 菜单栏图标，或者改读应用自己的 prefs 与日志（往往能看出登录账号、接口域名、代理开关）。
- **网关/本机服务的可达性与“能上网”是两件事**：修完网络先 `curl 127.0.0.1` 验本机服务，再用公网 HTTP 码验出口，两者都过才算恢复。

## 交付形态（照 Chris 的规格）

1. 双击可跑的脚本放 `~/AI工作台/系统设置/*.command`：主设置脚本 + **不需要 sudo 的查看状态脚本** + 危险开关的正/反两个开关（如合盖不睡 开/关）。主脚本要幂等；开头 `set -u`、`sudo -v || exit 1`；结尾 `read -n 1 -s -r -p "按任意键关闭…"`（双击窗口不会闪退）。
2. 回复先给**改前/改后对照表**（只放实测值），再给 ≤3 条「剩余风险」，最后问一句要不要做下一步。不写过程叙述、不奉承。
3. **验证要真跑**：跑一遍状态脚本并把真实输出贴出来；DNS 用连测 10 次，不是跑一次 `dig` 就算。

## 附带文件

- `scripts/check-always-on-state.sh` — 无需 sudo，一条命令看清电源/合盖/DNS/最近睡眠/AI 进程；改完跑它验证。
- `references/sleep-wake-service-disconnects.md` — 症状→根因对照表、`pmset -g log` 读法、launchd 进程健康检查。

## Pitfalls

- **`pmset -g custom` 的输出顺序是 Battery Power 在前、AC Power 在后。** 只截电池段要用 `sed -n '/^Battery Power:/,/^AC Power:/p'`；`awk '/^Battery Power:/,0'` 这类写法会静默打印全文，脚本里就会出现重复段落。
- **不要把出厂睡眠值当成硬件限制**：本机 sleep=1 完全可设，`sleep 0` 就是它。同理 `disablesleep` 在本机（M5/Mac17,7）实测可用 —— 先设、再看 `pmset -g | grep SleepDisabled`，别凭机型传说下结论。
- **`pmset -g` 里 `sleep prevented by powerd/Hermes/...` 只是当前断言**，不代表设置生效。作数的是 `pmset -g custom` 的值和 `pmset -g log` 里的睡眠记录。
- **别在电池上宣布完成**：改完如果 `pmset -g batt` 显示 `Now drawing from 'Battery Power'`，明确说「插上电才生效」。
- **不要在 openclaw 的 `dist/` 里宽泛 grep**：`dist/control-ui/assets/locale-*.js` 一个文件就能吐 300 万字符（一次实测把上下文打爆）。要查行为用精确文件名或 `grep -rl` 先定位；查配置项用 `openclaw config schema` 配 Python 递归。
- **`ps eww -p PID` 在 macOS 上看不到环境变量**，要用 `ps -Eww -p PID`（同用户进程可读）。验证注入是否生效只认这一条。
- **要动另一个 agent 的运行时**（例如给 OpenClaw 网关加 `UV_THREADPOOL_SIZE`）先问 Chris —— 不要顺手改 Nova 的配置。
