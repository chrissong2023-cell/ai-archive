# 知识库索引与检索调优（chroma + bge-small-zh）

改 `~/.nova-tools/kb_index.py` / `kb_serve.py` 前读这一份。改完必须重建 + 抽样验证，因为下面每一处失效都是**静默**的：不报错，只是检索变差或文档消失。

## 一、语料范围

- **收**：`workspace/knowledge`、`projects`、`crm`、`mail`(+`bodies`)、`briefings`、`memory`、`meeting-minutes`；Hermes 侧 `资讯日报`、`邮件获客自动化`、`公众号`、各项目目录。
- **不收**：`.jsonl`（爬虫/流水状态，不是文档）、`-raw.md`（每日简报快照，与 `crm`、`memory` 重复，会把 top-k 顶满）、敏感隔离区（`敏感-凭据`/`敏感-个人证件`/`高风险-*`）。
- 判据：**机器流水 ≠ 文档**；同一信息每天一份快照 = 多份近重复文档，检索时按来源上限也挡不住。

## 二、清洗（顺序不能颠倒）

1. NFKC → 去零宽/全角空格 → 分行 strip。
2. **先压表格空单元格 `(?:\|\s*){3,}` → `| `，再算密度**。xlsx 提取件整行都是 `| | | |`，不压就整份被判低密度丢掉——真报价单会静默消失（表现为“某些报价单搜不到”）。
3. 再剔：页码行、纯符号行、密度 <0.25 且 <200 字的行、连续重复行、单字符重复噪声（`len>15 且 len(set)<=3`）。
4. 合并中文字符间的单个空格（PDF 断字）。

## 三、切块

- 按 `\n\n` 分段、句末标点切；目标 760 字、块尾留 120 字重叠。
- 块首 `【目录/文件名 · 文档标题 · 小节】`（≤100 字）：**路径进块首**，项目名/型号（H200、巴淡、WCA）才能直接当查询词命中。
- 门槛：≥140 字且有效字符占比 ≥0.45；单文件 ≤400 块。门槛再抬会开始误删真内容。
- 邮件正文标题取 `Subject:` 行，不要用数字文件名（否则全库都是 `1587508221.txt`）。

## 四、增量与版本闸门

- state `~/.nova-kb/index-state.json`：路径 → `(size, mtime, sig, cat, ids)`。size+mtime 都没变直接跳过（实测 900+ 文件 0.3 秒）。
- 改动的文件：先按旧 `ids` 删向量再 upsert；已消失的文件按 `ids` 删除。
- `PIPE_VER` 常量：改清洗/切块规则就 +1；启动时发现 state 里的版本不符 → 自动全量重建，不靠人记得跑 `--rebuild`。
- 跨来源去重：正文归一化签名相同只索引一份，优先级 `hermes/*.md` > `extracted2/*.txt` > `extracted/`。

## 五、检索打分

```
final = 0.6 * cos + 0.4 * (命中词数 / 词数) + min(0.08, 0.04 * 路径命中词数)
```

- 候选：每 collection 向量 top-N + 关键词 `where_document={"$contains": term}`（CJK 按 2 字切、latin/数字原样）。
- **为什么必须有词覆盖项**：bge-small-zh 在这类混杂语料上会把“读起来像”的短块打虚高分（简历里的业务业绩段压过真正的报价单）。命中词数是最便宜的纠偏，成本为零。
- 去重键：**先剥掉块首 `【…】` 再比对**——否则同一段落来自不同文件（两种提取件、每日快照）因表头不同而去不掉，top-k 被同一段内容刷满。
- 文档键：文件名去掉 `YYYY-MM-DD-<hash8>-` 前缀和非字母数字后比对，`per_doc` 限 2 条；`per_source` 限 2 条。
- 低分过滤：`score < 0.40` 且零词命中的剔除；全被剔时保留最好 2 条兜底，不要返回空。

## 六、chroma 运维

- **HNSW 不查询不落盘**：写完对每个 collection 打一次 probe 查询（`query(query_embeddings=[probe], n_results=1)`），否则服务端报 `Error creating hnsw segment reader: Nothing found on disk`。
- **长驻服务的句柄会被别的进程 `--rebuild` 弄失效**：查询异常 → 重开 collection → 换新 `PersistentClient` → 仍失败则自愈重启。自愈必须用 `launchctl kickstart -k gui/$(id -u)/<label>`，**不要 `os._exit(0)`**：launchd 会记 `spawn failed` 并卡在退避里，任务从此起不来。
- 单个 collection 顽固损坏（其余正常、新建进程手测正常）：`delete_collection` + 删掉 state 里该 cat 的条目 → 下一次增量会把它当新文件重建（406 块约 4 秒）。
- `--rebuild` 期间服务必然 500（collection 已删）：重建完先 kickstart 服务再验 `/api/health`。
- 服务日志分工：stdout 进 `serve-launchd.log`（自定义 `[search-fail/...]` 打这里），traceback 进 `serve-launchd.err`。排查时两个都要看。

## 七、验证清单（每次改完必跑）

1. `curl -s 127.0.0.1:8765/api/health` → `vectors` 数量合理、`ok:true`。
2. `curl -s 127.0.0.1:8765/api/stats` → `indexed_at` 是刚才、`by_origin` 两边都有。
3. 8 个 collection 各查一次，`degraded` 必须为空数组。
4. 抽 5–8 条**真实业务查询**（带型号/项目名/客户名/舱位号），确认首条落到原始文件，而不是“读起来像”的简历或简报。
