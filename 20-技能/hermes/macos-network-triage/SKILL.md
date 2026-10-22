---
name: macos-network-triage
description: Use when the Mac is offline or a VPN won't connect.
version: 1.0.0
author: Hannah (Hermes Agent)
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [macos, network, vpn, proxy, dns, troubleshooting]
    related_skills: [macos-always-on-host, blocked-page-recovery]
---

# Mac 网络 / VPN 排障

先在只看不改的层面把事实拿全，再决定是否动网络。这条链路上"修"的代价很高：一次错的隧道操作能让整机断网。

## When to Use（何时用）

- 「上不了网 / 网断了 / 刚重启还是慢」
- 「小地球仪 / VPN / 代理 连不上」
- 自己或别人动过隧道、DNS、代理之后出现异常

## 一、一次取证（只读）

```bash
date; uptime                      # 刚重启？
scutil --nc list                  # 有哪些 VPN 配置，是否 Connected
netstat -rn -f inet | grep '^default'   # 默认路由走 en0 还是 utun
ifconfig | awk '/^utun|^en0/{i=$1} /inet /{print i,$2}'   # utun 有没有 IPv4（只有 fe80 = 隧道没承载流量）
scutil --proxy                    # 有没有被设成系统代理
scutil --dns | head -20           # resolver 是否可达
ping -c2 -t2 223.5.5.5            # 出网（不要用网关做判据）
curl -s -m6 -o /dev/null -w '%{http_code}\n' https://www.baidu.com
curl -s -m6 -o /dev/null -w '%{http_code}\n' https://www.google.com
```

## 二、判读（别把正常现象当故障）

| 现象 | 真相 |
|---|---|
| 网关 `192.168.x.1` ping 不通 | 多数路由器禁 ICMP，**能出网就不是故障** |
| 某站返回 403 | WAF 拦机器人，不是断网 |
| `utun0..5` 只有 `fe80::` 地址 | macOS 自带隧道，正常；**关键看 utun 有无 IPv4** |
| 重启后负载 20+ | 开机索引，会自行下降 |
| `scutil --nc list` 显示 `(Disconnected)` 但带 `*` | `*` = 在"当前集合"里启用，不代表已连接 |
| `dig` 解析出 `198.18.x.x` | 代理/隧道的**假 IP 池** —— “通”是借道隧道，隧道一断立刻不通 |

判据永远用"能出网"（DNS 解析 + 一次真实 HTTPS 200），不要用单个中间设备。

**“可达”要再问一句“借道谁”**：`dig +short <host>` 落在 `198.18.0.0/15` 说明流量走隧道。依赖境外服务的自动化（Gmail IMAP、境外 API、海外代理站点）只在隧道活着时成立——要么给降级路径，要么不接进高频定时任务；否则 VPN 一断，整条链路看起来像“程序坏了”，实际是网络入口没了。

## 三、VPN 客户端连不上：先看扩展，再看账号

```bash
systemextensionsctl list        # [activated enabled] 还是 [activated disabled]
scutil --nc list                # 每条配置归属哪个 bundle id
scutil --nc show "<名称>" | grep -iE 'OnDemand|Plugin'
log show --last 30m --predicate 'subsystem == "com.apple.networkextension"' | grep -i '<名称>'
```

两个决定性的日志串：

- `Plugin is not installed` / `last stop reason Plugin was disabled` → **网络扩展在系统设置里被禁用**。不是 DNS、不是墙、不是服务器挂了；旧客户端在系统大版本升级后常被要求重新授权。
- `93006 invalid chatid` 之类的服务端错误与本地网络无关，别去改 DNS。

修法只有两条，二选一：
1. 用**新客户端**（扩展 enabled 的那个 bundle）从它自己的 GUI 连；
2. `系统设置 › 通用 › 登录项与扩展 › 网络扩展` 把旧扩展打开（需管理员密码，只能 GUI）。

SIP 开启时 `systemextensionsctl` 不能程序化启用扩展，别在这上面耗时间。

## 四、硬规则：不要用 `scutil --nc start` 做诊断

应用型隧道（NETunnelProvider 客户端）连上后**自己会设系统代理**（配置里常见 `systemProxyEnabled=true`）。用 `scutil --nc start` 强起的隧道是"空壳"：壳在、节点没握手、代理已指向本地端口 → **DNS 和 HTTP 一起黑洞，整机表现为断网**。

- 要验证连通，让用户在客户端 GUI 里点连接，你只读状态。
- 已经踩了：立刻 `scutil --nc stop "<名称>"`；停不掉就重启，重启后先确认 `OnDemandEnabled : FALSE`（不会再自动劫持）。
- 断网期间所有依赖网络的自动化（cron 拉模型、IMAP）都会失败，报错是 `can't reach the model provider` 之类——先对时间线，别去查模型配置。

## 五、DNS 被固定过的情况

固定公共 DNS（阿里/腾讯/百度）会让某些客户端自己的解析策略失效，但**不会**造成 `Plugin is not installed`。排障顺序永远是：扩展状态 → 隧道状态 → 路由 → 代理 → 最后才是 DNS。把 DNS 放第一会浪费整轮。

## 六、收尾验证

```bash
scutil --nc status "<名称>"          # 确认目标状态
curl -s -m6 -o /dev/null -w '%{http_code}\n' https://www.baidu.com
scutil --proxy                        # 断开后不应残留代理
```

给用户的结论要写清：哪一层坏了（扩展/隧道/路由/代理/DNS）、判据是哪条日志、修法需要谁动手（GUI 授权只有本人能做）。
