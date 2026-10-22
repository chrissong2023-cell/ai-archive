---
name: wf-01-inquiry-quote
description: Use when an RFQ or new inquiry arrives and a quotation must be produced, priced and sent. Covers cost gathering, quote document, approval gate and follow-up.
license: MIT
compatibility: "Shared workflow skill for Hannah (Hermes) and Nova (OpenClaw). Canonical file in ~/AI工作台/团队协同/skills/."
metadata:
  category: workflow
  owner: shared
  tags: [RFQ, 报价, 外贸, 询盘, 报价单, 闸门]
  related_skills: [lishun-mail-acquisition, trade-quotation-and-agency-agreement, email-inbox-triage, team-hq]
---

# 工作流 01：询盘 → 报价 → 跟单

## 何时用

- 收到 RFQ / 新询盘 / 客户问「报个价」；或 Chris 说「这单报一下」。
- 已有报价要改价、延期、加条款。

## 一条铁律

**成本不到手不出价，Chris 不点头不外发。** 含价格的报盘默认 `auto_send_quote=false`（见 `lishun-mail-acquisition`）。

## 步骤

1. **建任务**（否则这单会丢）
   ```bash
   python3 ~/AI工作台/00-总控/bin/ctl.py add "报价：<客户> <航线/货品>" -p <项目名> -o hannah --due <+2天>
   ```
2. **检索历史**（别从零报价）
   ```bash
   ~/.nova-tools/kb.sh search "<航线> <货品> 运价" --k 6
   ~/.nova-tools/docsearch "<客户名> 报价"
   ```
   命中后**落到原始文件**再引用运价与条款。
3. **取成本**：向 Jackson 要成本价（邮件/微信），把回信存 `项目/成本-<日期>.md`，任务标 `blocked` 直到成本到。
4. **出报价单**：用 `trade-quotation-and-agency-agreement` 技能（模板、条款、有效期）。产出落
   `~/AI工作台/<项目>/报价单-<客户>-<日期>.md`（同时留 docx 给客户，md 给知识库）。
5. **闸门**：把报价单 + 一句话摘要放进 `~/AI工作台/00-总控/OUTBOX/`，任务备注写「待批」。**不自动发。**
6. **发送**（仅在 Chris 明确同意后）：走 `lishun-mail-acquisition` 的 `common.send_reply`；
   主题里不得含换行；发完写 `data/sent.jsonl` + `mail/sent-log.md` + 总控 LEDGER。
7. **收尾**：`ctl.py done <ID> --note "报价号 X / 有效期 Y"`；48 小时后无回音 → 新建跟进任务。

## 交付标准（缺一项不算完成）

- [ ] 报价号、日期、有效期（默认 30 天）、币种、单价口径（是否含税/含通道费）
- [ ] 成本来源可追（谁给的、哪天）
- [ ] 客户主体、联系人、港口/地址无错
- [ ] 风险与例外单列（旺季舱位、燃油、清关抽查、汇率）

## 红线

- 不猜成本、不垫价、不替 Chris 承诺舱位与时限。
- 出口管制/转运规避类询盘：先报 Chris，**不做、也不给规避方案**。
- 客户名单与运价不得进任何外部云服务。

## 现状缺口（如实标注）

- Jackson 成本是人工环节，没有接口；`blocked` 是正常状态，不是失败。
- 报价单模板版本化尚未落地，改模板要同步改技能，否则两边口径会飘。
