---
name: web-presence-audit
description: Audit domain site uptime, TLS, SEO and mailbox readiness.
version: 1.0.0
author: Hannah (Hermes Agent)
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [web, dns, tls, seo, ops, due-diligence]
    related_skills: [blocked-page-recovery, wf-04-contract-kyc, competitor-news-monitor]
---

# 站点体检（集团自有站 / 客户与供应商尽调）

「官网打不开」「客户搜不到我们」「对方公司靠不靠谱」——都是同一类活：**用命令拿到硬证据，再按修复成本排序**。Chris 有 8 个实体站，这类问题会反复出现。

## When to Use（何时用）

- 他说某站打不开 / 页面空白 / 客户点链接失败
- 月度体检（集团自有域名 + 关键客户/代理官网）
- 尽调对方公司：有没有站、是不是空壳、有没有 TLS
- 新域名/新企业邮箱上线：邮件收不收得到（MX/SPF/DKIM）、账号能不能登录
- 上线新站前后做一次基线

## 一、批量探活（先跑脚本，不要一个个肉眼看）

```bash
python3 scripts/site_probe.py domain1.com domain2.com … [--json out.json] [--ports]
```

输出每站：DNS 解析、HTTP/HTTPS 状态码、正文字节数、`<title>`、是否 JS 壳。**全部按 http 与 https 分别测**，很多站只有一半能用。

## 二、判定表（照着说，别猜）

| 现象 | 结论 | 依据 |
|---|---|---|
| HTTPS 502/503，但 22/80/443 端口都通 | **服务器活着，Web 服务（nginx 上游）挂了** → 重启服务即可 | `nc -z` 三端口 + 状态码 |
| 000/超时，且端口不通 | 机器/防火墙/解析问题，不是网站代码问题 | `nc -z` 全不通 |
| 多个域名同时 502 且解析到**同一个 IP** | 单点故障，一家挂全挂 → 报告要点名这个 IP | `dig +short <每个域名>` 一致 |
| HTTP 200 有内容，**HTTPS 返回 0 字节** | 443 未配 / 证书错误 → 客户点 https 直接失败 | 两协议分别取 body |
| 首页 HTML **< 2 KB 且带 `<script>`** | 纯 JS 单页壳，爬虫读到空白 → 出海获客等于没有站 | 字节数 + 无正文文本 |
| 同域名 www 与非 www 返回**不同公司内容** | 虚拟主机/证书配错，可能指向别人的默认站 | 分别取 title 比对 |

## 三、出报规范（Chris 只看结论和证据）

1. **第一句就是判定**：「4 个中国站全挂，4 个海外站活着但搜不到」——不要先讲过程。
2. **每条结论带一条命令证据**（状态码、字节数、IP）。没证据的写「未验证」。
3. 修复按 **P0 / P1 / P2** 排，并标明**我能不能自己做**：
   - P0 重启 Web 服务 / 配 Let's Encrypt —— 需要 SSH 凭据（**要用户写文件或加密框，不接聊天里的密码**）
   - P1 给 SPA 加可爬取的静态内容（型号/库存/流程/案例/联系方式/JSON-LD）
   - P2 统一规范：强制 HTTPS、www 与非 www 一致、OG 分享卡
4. 落文件到 `~/AI工作台/00-总控/研究/<日期>-站点体检.md`，对话里给表格摘要。
5. 顺手算钱：打不开对「代理互查 / 客户 KYC / Google 询盘」各意味着什么损失——这是他真正在意的换算。

## 四、邮箱就绪度（新域名最常见的「假好消息」）

邮箱控制台里账号一个个显示「正常」，**不等于能收信**。收信只看 MX 记录。实测过的情形：域名刚注册、6 个账号建好、面板全绿，但 `A` 与 `MX` 全空 → 官网打不开，外部邮件一封也投不进来。

```bash
python3 scripts/mail_probe.py <domain> <addr@domain> [--vault ~/.hermes-secrets/<x>.json]
```

判据链（依次做，别跳）：

1. **解析**：`dig +short MX <domain> @223.5.5.5`，并在 119.29.29.29 / 8.8.8.8 / 1.1.1.1 复验，最后直问权威 NS（`dig @<ns> <domain> MX`）。全空 = 真的没配，不是缓存。
2. **注册状态**：`whois <domain>` 看 `Creation Date` / `Expiry` / `Registrar` —— 新注册的域名往往只配了 NS，A/MX 都没动。
3. **服务商指纹**：拿账号密码去撞候选 IMAP 端点，**错误串就是指纹**：

| 端点 | 错误串 | 结论 |
|---|---|---|
| `imap.qiye.aliyun.com` | `LOGIN failed.` | 阿里云企业邮，凭据/服务开关问题 |
| `imap.exmail.qq.com` | `Account is abnormal, service is not open…` | 腾讯企业邮未开通此域 |
| `imap.qiye.163.com` | `ERR.LOGIN.DOMAINNOTEXIST` | 网易无此域 |

4. **登录被拒先怀疑服务开关，不是密码错**：企业邮默认关闭 IMAP/SMTP。先让用户去后台开启「客户端/IMAP/SMTP」，再生成**客户端专用密码**；拿登录密码去撞 IMAP 在阿里云上只会得到 `LOGIN failed`。
5. **给修复清单时写全四条**，少一条都是白干：

| 类型 | 主机 | 值 |
|---|---|---|
| MX | `@` | `mx1.qiye.aliyun.com`（10）、`mx2.qiye.aliyun.com`（20）——阿里云企业邮 |
| TXT | `@` | `v=spf1 include:spf.qiye.aliyun.com ~all` |
| TXT | `default._domainkey` | 服务商后台生成的 DKIM 值 |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:…` |

6. **账号别全做成独立收件箱**：一个域名开 6 个箱就是 6 个没人看的坑。只保留 1–2 个真收件箱（本人 + 自动化），`info@/sales@/finance@` 全部转发过去。

**凭据纪律**：授权码只进 `~/.hermes-secrets/<name>.json`（chmod 600），收到后不回显、不复述；用户已在聊天里贴过的，提醒他生成专用密码后作废旧码。

## 五、红线

- **不动 DNS、不动证书、不动服务器配置**，除非他明确批准；SSH 凭据只接受文件/加密框。
- 抓首页只用 GET + 常规 UA，超时设 15–20 s；不要并发几十个线程去打人家站。
- 尽调他方站点时只读公开页面，不试目录爆破、不试默认口令。
- 「域名被别家公司内容占用」这类发现要先复核 **www 与非 www、http 与 https 四种组合**再下结论——很可能只是某个虚拟主机配错，不是域名被抢。
