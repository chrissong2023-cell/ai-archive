---
name: wf-04-contract-kyc
description: Use when a contract, agreement or KYC pack must be reviewed, negotiated, signed off and archived — including red-flag extraction and approval routing.
license: MIT
compatibility: "Shared workflow skill for Hannah (Hermes) and Nova (OpenClaw). Canonical file in ~/AI工作台/团队协同/skills/."
metadata:
  category: workflow
  owner: shared
  tags: [合同, KYC, 条款, 审查, 归档, 签署]
  related_skills: [docx, pdf, document-to-action-items, trade-quotation-and-agency-agreement, team-hq]
---

# 工作流 04：合同 / KYC

## 何时用

- 收到合同、协议、代理协议、保密协议、KYC 表；或要发自己的合同给对方。
- Chris 说「这合同看看有没有坑」。

## 步骤

1. **建任务**：`ctl.py add "合同审阅：<对方> <标的>" -p <项目> -o hannah --approval`（签署本身就是需批项）。
2. **提取正文**：`~/.nova-tools/office.py md <文件>`（**必须 md，不要 text**，表格里的费用明细会丢）。
3. **条款清单**（逐条给结论，不要通篇复述）：
   - 主体与签署权（公司全名、注册号、签字人职务）
   - 标的与范围（是否含清关/仓储/保险/退税）
   - 价格与调价机制、税费承担
   - 付款与账期、逾期/违约金
   - 交付与验收、风险转移点（FOB/CIF/DAP…）
   - 责任上限、免责、不可抗力
   - 争议解决与适用法律（**境外主体特别注意管辖地**）
   - 终止与续约
4. **KYC 包**：营业执照/注册证、法人证件、UBO、银行账户证明、地址证明。
   逐项标 `有 / 缺 / 需 update`；敏感件进隔离区，**不上云、不进知识库**。
5. **风险清单交 Chris**：按「必须改 / 建议改 / 可接受」三档，每条写：原文位置 + 为什么 + 建议措辞。
6. **归档**：签定版 → `~/AI工作台/<项目>/合同-<对方>-<日期>.md`；
   Nova 同步飞书归档（目录规范见 `wf-05-crm` 的客户目录）；登记 `DECISIONS.md`。

## 交付标准

- [ ] 每条风险有原文定位（条款号或引文）
- [ ] 缺失材料列成清单，写清向谁要
- [ ] 结论区分「事实」与「我的判断」，判断要标置信度
- [ ] 未签版本与签定版分开存放，文件名带日期

## 红线

- **不代签、不盖章、不改签署页**；签署必须 Chris 本人。
- 不把合同正文上传到第三方云解析（MinerU 等）；本地提取优先。
- 对方要求修改我方模板时：给建议回稿，不直接覆盖原文件。

## 现状缺口

- 无电子签章服务；签署仍是人工打印/盖章或对方平台签。
- 合同条款比对是人工为主，`document-to-action-items` 只能辅助抽义务与期限。
