---
name: wf-06-mail-calendar
description: Use when triaging the inbox, drafting or sending mail, or scheduling/answering calendar questions — with the approval gate and the known scheduling gap.
license: MIT
compatibility: "Shared workflow skill for Hannah (Hermes) and Nova (OpenClaw). Canonical file in ~/AI工作台/团队协同/skills/."
metadata:
  category: workflow
  owner: shared
  tags: [邮件, 分诊, 发送, 日历, 日程, 闸门]
  related_skills: [lishun-mail-acquisition, email-inbox-triage, himalaya, google-workspace, team-hq]
---

# 工作流 06：邮件 + 个人日程

## 邮件（Hannah 主责，Nova 提供投递）

1. **分诊**（30 分钟一跳的 cron 已在跑）：按「客户询盘 / 供应商 / 平台通知 / 垃圾」四类。
   群发特征（unsubscribe / dear valuable partner / as per your previous request）→ 判废，不进待办。
2. **可自主处理**：条款类、报价类、信息类回复（Chris 2026-10-13 授权）。**仍要**：
   发送后写 `data/sent.jsonl` + `mail/sent-log.md` + 总控 LEDGER，并在日报里报一句。
3. **必须 Chris 批**：承诺赔付、改交付期、独家条款、任何金额变动、正式合同附件。
4. **技术坑**（都踩过）：主题不得含换行；网易企业邮 IMAP 需 `xatom("ID",…)`；Sent 文件夹是修改版 UTF-7。
5. **静默时段与日发送上限**：发前检查 `quiet_hours_cst` 与 `daily_send_cap`。

## 日程（当前**断的**，别假装能用）

- Hermes.app 缺 `com.apple.security.automation.apple-events` entitlement → `osascript` 驱动日历/提醒事项
  会被静默拒绝或超时 -1712。**不要反复重试。**
- 可行替代（按优先级）：
  1. 生成 `.ics` 文件让 Chris 双击导入（最稳，零权限）；
  2. `google-workspace` 技能直接读写 Google 日历（需 OAuth，属待批试点）；
  3. 修复 automation 权限：重新签名打包带该 entitlement 的 helper .app（需 Chris 批准）。
- 排会/约客户前先问清：时区（CST）、参与人、时长、是否线上。

## 交付标准

- [ ] 邮件类结论标明「已发 / 待批 / 已判废」，且能追到 sent-log
- [ ] 日程条目必须带时区、起止、参与人、地点/链接
- [ ] 涉及他人的时间承诺，先确认再回复

## 红线

- 零自动对外发送：除已授权的条款/报价/信息类，其余一律 OUTBOX 等批。
- 不在邮件里写凭证、账号、身份证号；对方发来的敏感件按隔离区处理。
- 不改他人日历邀请、不代客户确认会议。
