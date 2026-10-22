# 团队协同（Hannah × Nova）

一台 Mac，两个 agent：**Hannah**（Hermes，总指挥）+ **Nova 🦞**（OpenClaw，数字员工）。
这个目录是它们之间的"合同 + 总账"，两边读同一份东西，避免各干一套、各记一套。

| 文件 | 作用 |
|---|---|
| `skills/team-hq/SKILL.md` | **共享技能（唯一真源）**。分工路由、交接协议、共用知识库、红线 |
| `bin/scan_skills.py` | 扫两边全部技能 → 生成总账；`search / who` 查询；顺带把共享技能同步到两边 |
| `registry.json` | 机器可读总账（技能 + owner + 就绪状态 + 路由） |
| `SKILLS-MAP.md` | 人读对照表（自动生成，勿手改） |

## 怎么更新

```bash
python3 ~/AI工作台/团队协同/bin/scan_skills.py          # 重扫 + 同步
python3 ~/AI工作台/团队协同/bin/scan_skills.py search 邮件
python3 ~/AI工作台/团队协同/bin/scan_skills.py who 会议
```

改了 `skills/team-hq/SKILL.md` 之后**必须**跑一次 `scan_skills.py`：

- Hermes 侧是符号链接 `~/.hermes/skills/team/team-hq` → 自动生效；
- OpenClaw **不跟随符号链接**（实测），所以同步脚本会实体复制到 `~/.openclaw/workspace/skills/team-hq/SKILL.md`，文件头带 `AUTO-SYNCED` 标记 —— 别直接改那份副本。

新增共享技能：在 `skills/<name>/SKILL.md` 建目录，跑一次同步，两边都会看到。

## 知识库（RAG）

一套语料、一套索引、一个服务，两边共用：`~/.nova-tools/kb.sh search "词"` · `http://127.0.0.1:8765`。
索引是增量的（`~/.nova-kb/index-state.json`），只重建改动过的文件；投喂新文件会自动触发。
