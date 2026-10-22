---
name: wf-05-crm
description: Use when updating, segmenting or acting on customer/agent records — the single customer source of truth, follow-up cadence and quiet-account revival.
license: MIT
compatibility: "Shared workflow skill for Hannah (Hermes) and Nova (OpenClaw). Canonical file in ~/AI工作台/团队协同/skills/."
metadata:
  category: workflow
  owner: shared
  tags: [CRM, 客户, 代理, 跟单, WCA, 唤醒]
  related_skills: [lishun-mail-acquisition, team-hq, wf-01-inquiry-quote]
---

# 工作流 05：客户管理（CRM）

## 唯一客户源

`~/.openclaw/workspace/crm/customers.csv`（Nova 与 Hannah 共用，已在知识库 cat05 里）。
**不允许再建第二张客户表**；新客户先入这里，再谈别的。

字段基线：`名称,类型,国家/地区,联系人,邮箱,电话/其他,业务/线路,价值等级,状态,最近联系`
状态机：`新 → 在谈 → 报价中 → 成交 → 复购 → 沉默(90天) → 流失`

## 步骤

1. **新增/更新**：先查重（按邮箱域 + 公司名模糊），确认不是同一家再写。
2. **分级**：A（年出货 >10 票或战略）/ B（有稳定询盘）/ C（零散）/ D（只读资料）。
3. **跟进节奏**（写进任务，不靠记忆）
   - 报价后 48 小时无回音 → 跟进 1 次
   - 成交客户 30 天无互动 → 问需求
   - 沉默 90 天 → 唤醒（一条有价值的市场信息，不是干巴巴"最近好吗"）
4. **WCA 新会员**：Nova 采集 → `projects/wca-bd/data/new-members-*.csv` → Hannah 生成开发信（批次制，
   每批进 OUTBOX 待批）。**群发特征命中的直接判废**，别浪费额度。
5. **周报**：每周一 09:00 与 WCA 获客 cron 一起输出：新增/推进/停滞/需 Chris 介入。

## 交付标准

- [ ] 客户名、国家、联系人、邮箱四项不为空
- [ ] 状态有变化就更新「最近联系」日期
- [ ] 每次对外发送都能在 `mail/sent-log.md` 找到对应记录

## 红线

- 客户名单、邮箱、成交价不外传；不进任何外部 SaaS 表单。
- 不做"猜邮箱"式群发；退订请求立即永久标记。
- 同一客户同一批次只发一次，避免内部撞车（Hannah 与 Nova 发送前互查 sent-log）。

## 现状缺口

- CSV 无并发写保护：两个 agent 同时写会覆盖。**约定**：写前读、只追加改动行、写完回读校验；
  批量改动优先由 Hannah 一人执行。
- 客户状态机尚未落地成字段枚举，目前靠「状态」列自由文本。
