---
name: wf-03-gpu-procurement
description: Use when sourcing, vetting, pricing or moving GPU/IDC hardware and capacity (H200/B200/L40S, colo, bare metal), including the compliance gate.
license: MIT
compatibility: "Shared workflow skill for Hannah (Hermes) and Nova (OpenClaw). Canonical file in ~/AI工作台/团队协同/skills/."
metadata:
  category: workflow
  owner: shared
  tags: [GPU, H200, B200, L40S, IDC, 采购, 合规, 尽调]
  related_skills: [team-hq, company-research, stockpile-resale-deal-analysis, product-price-monitor, wf-04-contract-kyc]
---

# 工作流 03：IDC / GPU 服务器采购

## 何时用

- 客户要卡/整机/算力；或 Chris 说「这批货能不能接」「查下这个供应商」。

## 步骤

1. **需求固化**：型号（H200/B200/L40S…）、数量、成色（全新/拆机/翻新）、交付地、交付期、付款方式。
   写成一张表放进 `~/AI工作台/<项目>/00-需求-<日期>.md`。任务：
   ```bash
   python3 ~/AI工作台/00-总控/bin/ctl.py add "GPU采购：<型号>x<数量> <交付地>" -p <项目> -o hannah --approval
   ```
2. **供应商清单**：Nova 采集（浏览器/`company-research`）；Hannah 补历史成交与黑名单。
   每个供应商一行：主体全名、注册地、成立年、实控人、官网、可核验的过往案例。
3. **尽调**：域名→公司简报（`company-research`）；国内主体查工商；境外查 registry。
   **查不到就写查不到**，不要用"应该是"填表。
4. **合规闸门（硬闸，不可跳过）**
   - 终端用户、最终用途、转运路径三者必须能自洽；
   - 涉及受控地区/受控主体/规避痕迹 → **停，报 Chris，不做，也不提供规避方案**；
   - 结论写进 `项目/合规-<日期>.md`，含判断依据与不确定点。
5. **价格与条款**：向 Jackson 取成本；比价时同口径（含税/运费/保修/关税）。
   囤货类用 `stockpile-resale-deal-analysis` 算净利与周转。
6. **合同**：转 `wf-04-contract-kyc`；付款条件、验收标准、违约与退税条款逐条核。
7. **跟单**：交付节点任务化；每节点写证据（提单/入库单/验收单）。

## 交付标准

- [ ] 型号/数量/成色/交付期/付款方式五项齐全
- [ ] 供应商主体可核验（有官网或注册号，不是只有微信名）
- [ ] 合规结论有依据，且有"不确定点"清单
- [ ] 价格有成本来源，净利与风险敞口算过

## 红线（Chris 明确要求）

- 出口管制/转运规避：宁可不做。发现风险先报，不提供规避方案。
- 涉及 GPU 服务器的高风险资料单独隔离（`高风险-GPU服务器/`），不进知识库、不进云。
- 不代付、不垫资、不承诺"包清关"。

## 现状缺口

- 行情数据靠人工/网页，`product-price-monitor` 可试点盯 3 个型号但不是实时报价源。
- 海外供应商背景查证深度受限于公开信息，结论要标注置信度。
