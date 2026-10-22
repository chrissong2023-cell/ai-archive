---
name: cross-border-trade-daily-digest
description: "Use when producing the daily cross-border trade digest."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Trade, Shipping, Freight, Digest, Monitoring, WeChat]
    related_skills: [competitor-news-monitor, himalaya]
---

# 跨境贸易资讯日报（本机版，替代扣子 Coze）

每天生成 Chris 要的「跨境贸易资讯日报」，并附一篇公众号初稿。原为扣子(Coze)上的两条日程任务（08:00 话题追踪 + 08:30 采集与排版），2026-10-13 迁到本机 cron，无平台费。

## When to Use

- cron 任务「跨境贸易资讯日报」触发时（每天 08:30）。
- Chris 说「出今天的日报 / 资讯」时。
- 需要重跑某天的候选池时。

## 输出位置（固定，不要改）

```
~/AI工作台/资讯日报/YYYY-MM-DD-跨境贸易资讯日报.md     ← 内部版（含动作建议）
~/AI工作台/资讯日报/YYYY-MM-DD-公众号初稿.html         ← 公众号排版版，内联样式，可直接粘贴
~/AI工作台/_state/候选池-*.md                          ← 原始候选池留档
```

日期用**送达当天**（早上 08:30 触发 → 写当天日期）。

## 步骤

1. **抓取**：`python3 ~/.hermes/scripts/trade_news_fetch.py`（cron 的 `script` 参数已自动把 stdout 注入上下文；手动跑时先看输出）。
   - 去重状态在 `~/.hermes/state/trade-news/seen.json`（14 天滚动）；重跑加 `--reset`，看历史加 `--all`，改窗口加 `--hours N`。
2. **筛**：候选池已按 6 个主题分好（运价·舱位 / 政策·关税 / GPU·算力 / 航线·区域 / 鲜切花·生鲜 / 货代网络），并已过滤美线国内卡车类噪声。「未归类」区一般忽略。
3. **补漏**：脚本未覆盖的源用 `web_search` / `web_extract` 补——海关总署（WAF 拦脚本，412）、财联社电报（JS 渲染）、美国 BIS 出口管制、EU EUR-Lex、汇率。查不到就在「覆盖缺口」写明，**不要编**。
4. **写日报**：固定 9 段结构 —— ①一句话 ②运价与舱位 ③政策·关税·合规 ④航线与区域风险 ⑤GPU·算力·数据中心 ⑥货代网络与整合 ⑦今日动作建议 ⑧公众号选题 ⑨覆盖缺口。
   - 每条给**事实 + 对我们的影响**（不要只抄标题）；影响属推断时标「判断」。
   - **每个数字、每个法规号、每条政策都必须带可直接点开的 URL**（写 `[来源名](url)`），只写「据新华社」「多源交叉」不算——Chris 要看的是能自己点开核的原文。给不出 URL 就标「**未溯源·待核**」并降级，不得当成事实写进建议。
   - **不要凭记忆写法规编号**（如「条例 2026/382」）：编号拿不到原文就只写政策内容 + 官方页面链接，宁可少一个编号也不要写错。
   - 动作建议标注是否需 Chris 决策（✅/⬜）；涉及价格只写「需 Chris 定价」，绝不自己定。
5. **写公众号初稿**：挑 1 条选题，800–1000 字，**全内联样式**的 HTML（公众号编辑器只吃内联样式），结尾必须带 `［草稿 · 未发布 · 由 Hermes 起草，发布前需 Chris 确认］`。
   - **题材禁区（硬红线）**：对外稿**绝不写服务器、GPU、AI 算力、数据中心设备、BIS 出口管制题材**——这些业务受 BIS 管制，公开讨论有合规风险。内部日报照写，对外稿必须自检并换题。
   - 对外稿优先选：海关/检验检疫/归类/单证/信用管理/通关实务（安全且吃搜一搜流量）。
   - 排版规范、标题校验、转载合规与发布铁律见技能 `wechat-official-account`；本技能止于初稿，**不碰后台、不发布**。
6. **交付**：最终回复 = 给 Chris 的精简版（今日一句话 + 3–5 条要点 + 文件路径），不要复述整份日报。

## 红线

- **不发布、不群发、不对外发送任何内容**：公众号只出初稿，发布由 Chris 手动逐篇确认（发布流程见技能 `wechat-official-account`）。
- 不自己定价；不把邮件/客户信息写进对外稿件。
- 抓不到就报覆盖缺口——「没抓到」不等于「没有消息」。

## 标准源（已验证，引用优先用这些）

| 题材 | 用这个源 | URL |
|---|---|---|
| 欧盟关税/低值包裹/清关新规 | 欧委会 Taxation & Customs（含法律文本） | https://taxation-customs.ec.europa.eu/customs/eu-customs-reform_en |
| 美国出口管制（GPU/芯片） | BIS 新闻稿 + 联邦公报原文 | https://www.bis.gov/press-release/ · https://www.federalregister.gov/ |
| 人民币汇率中间价 | 中国外汇交易中心 / 中国货币网 | https://www.chinamoney.com.cn/chinese/bkccpr/ |
| 运价指数 | 上海航交所 | https://www.sse.net.cn/ |
| 中国贸易政策/公告 | 商务部 | https://www.mofcom.gov.cn/ |
| 鲜切花·生鲜（行业媒体） | FloralDaily / HortiDaily / FreshPlaza RSS | https://www.floraldaily.com/rss.xml · https://www.hortidaily.com/rss.xml · https://www.freshplaza.com/rss.xml （均在脚本 SOURCES 里） |
| 鲜切花·生鲜（国内） | 云南省农业农村厅 · 农业农村部 · 斗南花卉 | https://nync.yn.gov.cn/ · https://www.moa.gov.cn/ · https://www.dounanflowers.com/ |
| 进口国植物检疫新规（美国） | Federal Register API（APHIS 机构过滤，JSON、无 WAF） | https://www.federalregister.gov/api/v1/documents.json?per_page=25&order=newest&conditions[agencies][]=animal-and-plant-health-inspection-service |
| 花卉行业国际组织 | AIPH / FloraCulture（新闻页能抓，但需按文章 URL 选择器过滤，否则全是导航噪声——尚未接入） | https://www.aiph.org/news/ · https://www.floracultureinternational.com/news |

## 无人值守（cron）运行

cron 里没有人可以批准命令、也没人会替你重试，所以这三条是硬约束：

1. **最终回复是发往微信的纯文本**：不要用反引号、代码块、Markdown 表格、`[文字](url)` 链接语法和 `|` 分隔线——微信端不渲染 Markdown，用户会直接当成「乱码」。链接写成裸 URL，重点用「·」「1. 2. 3.」这种纯文本排版，长度控制在手机屏幕几屏内。
2. **不要用内联脚本标志**：`python3 -c "…"`、`sh -c "…"`、`python3 -e` 这类命令会被安全策略判为危险命令，而 cron 无人可批准 → 工具直接报 BLOCKED。要算日期或解析文本，把逻辑写进 `~/.hermes/scripts/` 下的脚本文件再调用；别在回复里现写 one-liner。
3. **浏览器源用独立 profile**：`browser.use_real_profile` 在 Chrome 正在运行时会因 profile 的 SQLite 写锁（Login Data / Web Data）失败；需要浏览器时先确认 Chrome 状态，或改用独立 profile。

### 运行失败时的诊断顺序（`agent reported failure`）

这条错不代表没干活——runner 被硬中断时最终回复为空（`response_len=0`），产物却可能已经落盘。按这个顺序查，**不要先重跑**：

1. 用 `search_files`（target='files'）看输出目录，看当天的文件是否已经写好（写好了就直接人工汇总交付，别重跑）。
2. `hermes cron runs <job_id>` 看每次执行的状态与时间线。
3. `~/.hermes/logs/agent.log` 搜 `turn lease` / `interrupted_by_system`：常见真因是 cron 交付会**镜像进与用户实时对话同一个会话**，两边抢会话锁 → 本任务被 `session_turn_lease_lost` 硬中断。

已知的失败通知长这样（英文 + 反引号 + 路径），用户会当成乱码：收到后**用中文人话复述一句**「今天这条中断了 / 产物在不在 / 是否重跑」，并把重点放回内容本身。

兜底：`hermes cron run <job_id>` 手动重跑；更稳的是在用户在线时手动执行同一个任务（此时需要批准的命令不会被拦）。

**交付失败 ≠ 任务失败**（两种报错别混）：`hermes cron list` 里写 `ran, but the result was not delivered (… sendmessage session not ready …)` 表示任务跑完了、只是没送出去，别再重跑一遍浪费额度。先用通道自检把两件事分开：`hermes send -t weixin --json "通道自检"` —— 返回 `success: true` + message_id 则通道正常，问题只在 cron 的投递上下文（旧会话 / 旧 context token），等下次触发或让 Chris 在微信侧重连即可；只有 `hermes send` 自己也失败，才是通道（而不是任务）坏了。

## 坑（踩过的）

- **海关总署 `customs.gov.cn` 返回 412**：WAF 挡脚本 UA，别当源反复重试。
- **财联社电报页无内嵌内容**：Next.js 客户端渲染，脚本取不到，需浏览器。
- **FreightWaves 大量美线国内卡车新闻**（truckload/diesel/FMCSA）：已在 `NOISE` 列表过滤；新增噪声词往 `NOISE` 里加。
- **Hellenic Shipping News 偶尔超时**：`fetch()` 已内置 25s + 2 次重试。
- **相对链接拼接**：商务部子页 href 无前导斜杠，必须用 `urljoin`，否则拼成 `index.html/xwfb/...`。
- **`--all` 仍会被 seen 去重**：要重看全部必须配 `--reset`。
- **SCFI 数值**抓自上海航交所页面正则；页面改版会解析失败 → 报缺口，不猜数字。
- **「鲜切花·生鲜 0 条」并不意味着没有消息**：花卉类源本来就少（3 个英文 RSS + 国内几个站），条目一进 14 天 seen 池就被去重掉，而航运类源每天几十条 → 花卉主题经常显示 0。脚本已加**回溯池**：该主题今日无新增时，自动补上最近抓到的 8 条并标注说明。**日报里绝不要因此写「该主题无消息」，要写「今日无新增，最近条目如下」**。
- **花卉类源可用性（2026-10-14 实测）**：kifa.com.cn（昆明花拍）DNS 失败、chinaflower.org.cn 已死、royalfloraholland.com/en/news 与 aphis.usda.gov 返回 403（WAF）→ 别当源反复重试；用上面的替代源（斗南花卉 / 云南农业农村厅 / Federal Register API）。
- **国内花卉站会带政务噪声**（如「食品安全宣传周」因含「昆明」被归入花卉段）：日报写作时自己筛一遍，只留与鲜切花进口/冷链/检疫相关的。

## 验证

- [ ] 日报 9 段齐全，每条有影响判断，动作建议有 ✅/⬜ 标注。
- [ ] **每个数字/法规/政策都带可点 URL，无 URL 的已标「未溯源·待核」**。
- [ ] 公众号初稿含未发布标记，HTML 全内联样式。
- [ ] 覆盖缺口已写明失败源。
- [ ] 文件落在固定路径（当天日期）。
- [ ] 交付文本是纯文本（无反引号/表格/代码块/Markdown 链接语法），链接为裸 URL。
