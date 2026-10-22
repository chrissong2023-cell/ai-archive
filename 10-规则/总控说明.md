# 00-总控 —— Nova 2.0 的控制室

这里是 Hannah（Hermes）和 Nova（OpenClaw）**共用的任务与决策中枢**。所有"要做的事"只在这里存在一次，
不再各自维护 TODO。两个 agent 都按同一份规矩读写。

## 文件

| 文件 | 谁写 | 说明 |
|---|---|---|
| `tasks.jsonl` | 两边（经 `bin/ctl.py`） | **唯一真相**：每行一个任务 |
| `TASKS.md` | `ctl.py` 自动生成 | 人读视图，**不要手改**（下次生成就被覆盖） |
| `LEDGER.jsonl` | 两边追加 | 流水账：谁在何时做了什么（不可改、只追加） |
| `DAILY/YYYY-MM-DD.md` | `ctl.py digest` | 每日汇总：需批 / 卡住 / 进行中 / 逾期 / 待办 |
| `OUTBOX/` | 两边 | 待 Chris 批的草稿（报价、对外邮件、合同回稿），批完才发 |
| `DECISIONS.md` | 两边（追加） | 决策记录：谁定的、何时、依据 |
| `PROJECTS.md` | Hannah 维护 | 项目索引：目录、阶段、关键人 |

## 常用命令（两边通用）

```bash
CTL=~/AI工作台/00-总控/bin/ctl.py
python3 $CTL add "跟进瀚宇 H200 报价" -p 海南瀚宇-H200 -o hannah --due 2026-10-20 [--approval]
python3 $CTL list --open            # 或 --owner nova / --project 关键字
python3 $CTL start T-20261017-03    # doing
python3 $CTL block T-... --note "等 Jackson 成本价"
python3 $CTL done  T-... --note "已发客户，报价号 HY-..."
python3 $CTL digest                 # 生成今天的 DAILY，并打印摘要
python3 $CTL projects               # 项目聚合视图
python3 $CTL ledger -a hannah -c "发信" -t "客户 X 报价单" --note "gate=auto_send_quote"
```

## 三条硬规矩

1. **先建任务再干活**：没有任务号的事，做完也查不到。例外：一分钟内能查完的问题。
2. **需批项必须带 `--approval`**：付款、合同、盖章、删除、对外正式发送、客户承诺。
   带这个标记的任务，只有在 Chris 明确同意后才允许改状态为 done。
3. **对外动作留痕**：凡是发了邮件/消息、改了客户数据、动了文件，写一行 LEDGER。
   没有留痕等于没做——下次复盘会被当成幻觉。

## 与知识库的分工

- **总控管"事"**（谁做什么、到哪一步、卡在哪）。
- **知识库管"料"**（文件内容、历史事实、SOP）。
- 一个任务的产出文件落在项目目录，任务备注里写文件名；知识库增量索引会自动收录。
