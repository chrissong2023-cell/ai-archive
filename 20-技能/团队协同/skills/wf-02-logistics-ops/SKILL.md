---
name: wf-02-logistics-ops
description: Use when handling an active shipment or answering operational questions (SOP, documents, milestones, exceptions) for forwarding and cross-border moves.
license: MIT
compatibility: "Shared workflow skill for Hannah (Hermes) and Nova (OpenClaw). Canonical file in ~/AI工作台/团队协同/skills/."
metadata:
  category: workflow
  owner: shared
  tags: [物流, 货代, 单证, SOP, 报关, 在途]
  related_skills: [team-hq, feed-capture, lishun-mail-acquisition]
---

# 工作流 02：国际物流操作（在途单）

## 何时用

- 有票货在走（订舱、报关、在途、到港、清关、派送）；客户问进度或单证。
- Chris 说「这票查一下」「SOP 怎么走」。

## 步骤

1. **建/找单**：`ctl.py list --project <客户或票号>`；没有就 `ctl.py add "在途：<票号> <航线>" -o hannah`。
2. **查 SOP 与规则**（先查再答，别凭记忆）
   ```bash
   ~/.nova-tools/kb.sh search "<航线/货类> 报关 单证 时效" --k 6
   ~/.nova-tools/kb.sh search "SOP 利顺 标准操作 手册" --k 4
   ```
3. **单证清单**：按货类列（发票、装箱单、提单/空运单、原产地证、植检/动检、危品文件）。
   把每份文件状态写进任务备注：`有 / 缺 / 待客户给`。
4. **异常处理**：查验、延误、改单、弃货 → 先写事实（谁说的、何时、原文），再给 2 个方案 + 各自代价，
   **不替客户做决定**。
5. **对客户沟通**：草稿进 OUTBOX；涉及费用变更、赔付、时效承诺 → **必须 Chris 批**。
6. **归档**：单证与邮件进 `~/AI工作台/<项目>/`，任务 `done` 时在 LEDGER 记一行。

## 交付标准

- [ ] 票号、品名、件重体、起运/目的、承运人、ETD/ETA 齐全
- [ ] 单证状态逐项标清（缺件要说缺哪个、向谁要）
- [ ] 每条结论都有来源文件（kb 的 `source` 或邮件原文）

## 红线

- 不承诺清关时效与查验结果；不代客户签署任何申报承诺。
- 危品/冷链/药品类：只做有资质的路径，不确定就停。

## 现状缺口

- 没有 TMS/船司 API 对接（订舱与轨迹仍靠网页或邮件），所以「实时轨迹」只能人工核；
  Nova 的浏览器自动化可代抓，但登录态在 Nova 那边（见 `team-hq` 借用规则）。
