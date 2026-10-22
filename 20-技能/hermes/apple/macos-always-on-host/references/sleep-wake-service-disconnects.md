# 睡眠 / DNS 怎么把后台服务搞断：症状 → 根因 → 动作

笔记本当 7×24 主机时，绝大多数「服务自己断了」都能归到三件事：整机睡眠、解析卡住、自动重启/更新。先按症状查表，再取证。

## 症状 → 根因对照

| 症状 | 机制 | 取证命令 | 处置 |
|---|---|---|---|
| 定时任务没准点跑，唤醒后才补跑，且唤醒瞬间因无网失败 | 机器在睡，wake 后才有网 | `pmset -g log \| grep "Entering Sleep state"` | `sudo pmset -c sleep 0` |
| 网关/agent 反复重启，launchd `runs` 一直涨 | state 租约心跳（`utimes` 续约）60s 超时 → 进程判定失去 state 所有权 → 自杀重启；诱因=睡眠让心跳过期，或 DNS 解析占满 libuv 线程池 | 在网关日志里 grep `Gateway state ownership` / `heartbeat renewal did not complete` | 先修电源 + DNS；确有必要再给该进程抬高 `UV_THREADPOOL_SIZE`（需用户同意） |
| 通道日志刷 `getaddrinfo ENOTFOUND` / `fetch failed type=dns` | resolver #1 是不可达的 IPv6 link-local 地址 | `scutil --dns \| head -12` + ping 该地址 | 固定显式 DNS（见 SKILL.md），连测 10 次 |
| 浏览器标签被回收、扫码登录态丢失 | 机器睡过，页面被回收 | `pmset -g log` 睡眠记录 | 同时修电源；并把「登录 + 干活」放进同一次 browser 调用 |
| 长连接/远程会话莫名重置 | 插电档 `tcpkeepalive 0` | `pmset -g custom` | `sudo pmset -c tcpkeepalive 1` |
| 深夜自动重启 | macOS 自动装更新 | `defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates` | 设为 `false` |
| 断电恢复后服务全都不在 | FileVault 挡在登录界面，launchd agent 只在用户登录后才起 | `fdesetup status` | 告知用户这是硬缺口；auto-login 与 FileVault 不可兼得 |

## `pmset -g log` 怎么读

```bash
pmset -g log | grep -E "Entering Sleep state|Wake from" | tail -20
```

- `Entering Sleep state due to 'Maintenance Sleep':TCPKeepAlive=active` —— 就是空闲睡眠（TCP keepalive 保活也拉不住它）。短时间内反复出现 = 睡眠定时器设得极短（如 1 分钟）。
- `Wake from Deep Idle … due to … lid` —— 开盖唤醒；`DarkWake` = 短暂后台唤醒，不算真正上线。
- 每行末尾的 `Using BATT (Charge:…%)` / `Using AC` 能直接对上「当时插没插电」。

## launchd 进程健康检查

```bash
launchctl list | grep <label>                                   # PID · 上次退出码 · label
launchctl print gui/$(id -u)/<label> | grep -E "state|runs|last exit|path"
```

- `runs` 持续增长但 `last exit code = 0` → 进程是**正常退出后被 KeepAlive 拉起**，属于它自己的 self-restart（去进程日志里找 restart 原因），不是系统崩溃。
- 退出码非 0 + runs 暴涨 → 真崩溃，看 stderr 日志。
- 判据：先看「谁在睡」和「谁在解析」，再看代码。

## 改完怎么确认

1. `pmset -g custom` 的 AC 段 `sleep 0` 正确；若开了合盖不睡，`pmset -g | grep SleepDisabled` 应为 1。
2. 插电状态下静置观察：`pmset -g log | grep "Entering Sleep state"` 之后**不应再出现新行**。
3. DNS 连测 10 次全通。
4. 隔一段时间回看 `launchctl list` 里网关的 `runs` 计数是否停止暴涨 —— 这才是「睡眠导致的自我重启」真正被止住的证据。
