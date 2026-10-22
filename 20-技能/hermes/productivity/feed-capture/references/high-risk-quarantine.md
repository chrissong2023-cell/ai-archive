# 高风险文件隔离（Chris 的常驻要求）

原话要求：关于服务器/GPU 的文件要**单独出来**，将来可能删除；看到银行/账号密码也要这么处理。
因此 ingest 管道对敏感内容做**自动分流**，与普通语料物理分开，随时可一件事清干净。

## 三类隔离区

| kind | 目录（原件副本 + 原文提取 + 清单.md） | 检索副本（可一并删） | 判定特征 |
|---|---|---|---|
| `cred` | `~/AI工作台/敏感-凭据/` | `knowledge/feed/hermes-cred/` | 账号密码/密码/password/passwd/IBAN/RIB/SWIFT/银行账号/API key/secret/access key/token/私钥/快递账号/credentials |
| `pii` | `~/AI工作台/敏感-个人证件/` | `knowledge/feed/hermes-pii/` | 身份证/护照/通行证/台胞证/驾驶证/户口本/出生证明/结婚证/居留许可/passport/id card/resident permit |
| `gpu` | `~/AI工作台/高风险-GPU服务器/` | `knowledge/feed/hermes-risk-gpu/` | GPU/H200/B300/H100/L40S/NVIDIA/加速卡/服务器/机柜/托管/colocation/数据中心/HBM/出口管制/BIS/实体清单/EAR/最终用户/再出口/转口 |

判定优先级：**cred > pii > gpu**（越敏感越先判）。清除：`purge_risk.py --kind gpu|cred|pii|all [--confirm]`。

## 判定规则（宁严不宽，两段式）

- `cred` **优先于** `pii` **优先于** `gpu`。
- `cred` 命中条件：≥2 个特征词，**或** 文件名里直接带特征词。
- `pii` 命中条件：文件名带特征词，**或** 正文 ≥2 个特征词（证件正文很简短，单靠正文一两个词会误伤）。
- `gpu` 命中条件：文件名带特征词，**或** 正文 ≥3 个强特征词，**或** ≥2 个强特征词 + 商业上下文词（进出口/报关/合同/invoice/报价/采购/运输/清关/代理）。单靠 “服务器/托管” 这类泛词不够，避免误伤运维文档。

## 分流动作（命中时同时做四件）

1. 提取的正文另存 `{隔离区}/原文提取/<sha12>-<name>.txt`
2. 原件**副本**存 `{隔离区}/原件/`（源文件永不移动、永不删）
3. 追写 `{隔离区}/清单.md`（时间 / 文件名 / 原始路径 / sha256 / 命中特征）
4. 知识库语料写进独立的 `hermes-risk-*/` 目录（而不是普通 `feed/hermes/`），这样删除隔离区时它在检索里一起消失；台账记录打 `risk: gpu|cred` + `risk_hits`

## 三件事要记住

- **隔离区要真「锁上」**：管道创建的目录默认是 `755`（同机其他账户可读），Chris 要的是「单独锁上」。建区或批量搬家后必跑：目录 `chmod 700`、文件 `chmod 600`（`find <隔离区> -type d -exec chmod 700 {} \;` / `-type f -exec chmod 600 {} \;`），Nova 侧检索副本 `knowledge/feed/hermes-risk-gpu`、`hermes-cred` 同样 700。
- **手工补录也要走同一套**：源件被直接放在 Hermes 侧（如聊天上传的附件）时，按约定补三件——`原件/` 副本 + `原文提取/<sha12>-<name>.txt`（用 `~/.nova-tools/office.py md`，不用 text）+ `清单.md` 追一行（**按 sha 去重**），再 chmod。同时把副本放进 `投喂/inbox/`，让管道下一跳补上向量索引（`ledger.jsonl` 查得到才算索引完成）。
- **规则升级后要能回刷**：`python3 bin/ingest.py --reroute-risk` 会把已入库文件重判、搬家、补清单、改分类表登记。新加一类风险词后必跑。
- **清除默认只预览**：`python3 bin/purge_risk.py --kind all` 先看清单；`--confirm` 才真删（删隔离区 + 检索副本 + 台账改写为 `risk_purged` + 重建索引）。删除属于 Chris 的红线，只能他点头后执行，脚本本身不做任何自动删除。
- **清单要按 sha 去重**：同一文件被重解析过会在台账出现多行，写清单时按 sha 去重，否则清单里同一文件重复列。

## 已知会落进各区的具型文件

- `gpu`：GPU/服务器采购协议与 LOI（NVA/NVIDIA B300 LOI、BTMind 55xB300 GPU Server Agreement）、IDC 托管主协议（colocation 64 racks）、供货商 KYC 包、PT Mindai/SuperX 类主体资料、NVIDIA 全球 AI 云开发数据库。凡涉最终用户/再出口/转口描述的文件一律进 gpu 区。
- `cred`：快递账号密码（UPS/联邦/DHL）、RIB/IBAN、境外银行账号信息（如俄罗斯 VTB）。这类文件往往叫“账号及密码”“账户信息”，**文件名命中即隔离**，不要等正文累积到两个特征词。
- `pii`：身份证、护照、注册公司信息（含法人证件）等。
