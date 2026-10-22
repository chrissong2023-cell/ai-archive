#!/usr/bin/env python3
"""团队技能总账 — 把 Hannah(Hermes) 与 Nova(OpenClaw) 的技能扫成一张表，两边都能查。

产出:
  ~/AI工作台/团队协同/registry.json    机器可读总账（含分工路由 routing）
  ~/AI工作台/团队协同/SKILLS-MAP.md    人读的对照表

用法:
  scan_skills.py                 # 重新扫一遍，写总账
  scan_skills.py search 邮件       # 跨两个 agent 搜技能
  scan_skills.py who 邮件          # 查某项能力该派给谁（路由表）
  scan_skills.py --json          # 打印总账
"""
import os, re, sys, json, time, subprocess

HOME = os.path.expanduser("~")
ROOT = os.path.join(HOME, "AI工作台", "团队协同")
HERMES_SKILLS = os.path.join(HOME, ".hermes", "skills")
NOVA_WS = os.path.join(HOME, ".openclaw", "workspace")
SHARED_SKILLS = os.path.join(ROOT, "skills")
REG = os.path.join(ROOT, "registry.json")
MAP = os.path.join(ROOT, "SKILLS-MAP.md")

# 能力 → 主责 / 备手（依据实测能力，不按猜测）
ROUTING = [
    {"capability": "邮件：收件箱分诊 / 草拟 / 发信 / 获客外发",
     "primary": "hannah", "fallback": "nova",
     "how": "Hannah: 金技能 lishun-mail-acquisition（3 个 cron + 审批闸门）；Nova: ~/.nova-tools/mail.py 实际投递，凭据共用 ~/.nova-secrets/mail.json，发送记录写 mail/sent-log.md"},
    {"capability": "WCA 会员采集 / 开发信名单",
     "primary": "nova", "fallback": "hannah",
     "how": "Nova 采集 → ~/.openclaw/workspace/projects/wca-bd/data/new-members-*.csv；Hannah 读同一份 CSV 生成开发信"},
    {"capability": "会议录音转写 / 纪要",
     "primary": "hannah", "fallback": "nova",
     "how": "Hannah: whisper.cpp 本地转写 + 纪要（音频不出本机）；Nova: 飞书知识库归档/多维表格待办（分工待双方确认，勿并行建第二套）"},
    {"capability": "浏览器多步操作 / 国内工商尽调",
     "primary": "nova", "fallback": "hannah",
     "how": "Nova: browser-automation 插件（登录态在它那边）；Hannah 用 browser_exec 但不占它的登录态"},
    {"capability": "知识库检索（RAG）/ 投喂入库",
     "primary": "shared", "fallback": "-",
     "how": "同一套语料 + 同一套 chroma：~/.nova-tools/kb.sh search \"词\" / http://127.0.0.1:8765/api/search；投喂箱两个都盯，索引增量重建"},
    {"capability": "文档解析 / OCR / 报表",
     "primary": "shared", "fallback": "-",
     "how": "Hannah: pdf/docx/xlsx/powerpoint 技能 + office.py；Nova: mineru（云端，敏感件禁用）、excel-xlsx"},
    {"capability": "公众号 / 对外内容发布",
     "primary": "hannah", "fallback": "-",
     "how": "Hannah 已获授权直接发表（不勾原创）；Nova 不做公众号发布"},
    {"capability": "合规与高风险文件",
     "primary": "hannah", "fallback": "-",
     "how": "出口管制/转运规避类先报 Chris，不做；敏感证件凭据隔离区由 Hannah 管，任何 agent 不得把内容贴进外部服务"},
    {"capability": "Mac 主机/网关/电源运维",
     "primary": "hannah", "fallback": "nova",
     "how": "Hannah: macos-always-on-host、launchd、openclaw-bridge 排障；Nova 只读自查"},
]


def _front(path):
    try:
        txt = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return {}, ""
    if not txt.startswith("---"):
        return {}, txt
    end = txt.find("\n---", 3)
    head = txt[3:end] if end > 0 else txt[:2000]
    body = txt[end + 4:] if end > 0 else txt
    meta = {}
    for line in head.split("\n"):
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if v.startswith('"') and v.endswith('"') and len(v) > 1:
                v = v[1:-1]
            elif v.startswith('"'):
                v = v[1:]
            meta[k] = v
    m = re.search(r"hermes:\s*\n((?:\s{4,}.*\n)+)", head)
    if m:
        block = m.group(1)
        mt = re.search(r"tags:\s*\[([^\]]*)\]", block)
        if mt:
            meta["tags"] = [t.strip() for t in mt.group(1).split(",") if t.strip()]
        mc = re.search(r"category:\s*(\S+)", block)
        if mc:
            meta["category"] = mc.group(1)
    return meta, body


def scan_hermes():
    out = []
    for root, dirs, files in os.walk(HERMES_SKILLS):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "index-cache"]
        if "SKILL.md" not in files:
            continue
        p = os.path.join(root, "SKILL.md")
        meta, body = _front(p)
        rel = os.path.relpath(root, HERMES_SKILLS)
        cat = rel.split(os.sep)[0] if os.sep in rel else (meta.get("category") or "")
        out.append({"name": meta.get("name") or os.path.basename(root),
                    "owner": "hannah", "kind": "hermes-skill",
                    "category": meta.get("category") or cat,
                    "description": (meta.get("description") or "").strip(),
                    "tags": meta.get("tags") or [],
                    "path": p, "ready": True,
                    "updated": time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(p)))})
    return sorted(out, key=lambda x: (x["category"], x["name"]))


def scan_nova():
    try:
        raw = subprocess.run(["openclaw", "skills", "list", "--json"],
                             capture_output=True, text=True, timeout=90).stdout
        data = json.loads(raw)
    except Exception as e:
        return [{"name": "_scan_error", "owner": "nova", "description": f"openclaw skills list 失败: {e}"}]
    wsdir = data.get("workspaceDir", "")
    managed = data.get("managedSkillsDir", "")
    out = []
    for s in data.get("skills", []):
        miss = s.get("missing") or {}
        missing = [f"{k}:{','.join(v)}" for k, v in miss.items() if v]
        ready = not s.get("disabled") and bool(s.get("eligible", True))
        src = s.get("source", "")
        path = ""
        if "workspace" in src and wsdir:
            path = os.path.join(wsdir, "skills", s["name"], "SKILL.md")
        elif managed:
            path = os.path.join(managed, s["name"], "SKILL.md")
        # 共享技能在 Nova 侧是同步副本，归 shared 计，避免重复记账
        if path and os.path.isfile(path):
            try:
                if "AUTO-SYNCED" in open(path, encoding="utf-8", errors="ignore").read(3000):
                    continue
            except Exception:
                pass
        out.append({"name": s.get("name"), "owner": "nova", "kind": "openclaw-skill",
                    "category": src, "description": (s.get("description") or "").strip(),
                    "tags": [], "path": path, "ready": ready,
                    "missing": missing, "invocable": s.get("userInvocable", True)})
    return sorted(out, key=lambda x: (x["category"], str(x["name"])))


def scan_shared():
    out = []
    if not os.path.isdir(SHARED_SKILLS):
        return out
    for name in sorted(os.listdir(SHARED_SKILLS)):
        p = os.path.join(SHARED_SKILLS, name, "SKILL.md")
        if not os.path.isfile(p):
            continue
        meta, _ = _front(p)
        out.append({"name": meta.get("name") or name, "owner": "shared", "kind": "team-skill",
                    "category": meta.get("category") or "team",
                    "description": (meta.get("description") or "").strip(),
                    "tags": meta.get("tags") or [], "path": p, "ready": True})
    return out


def sync_shared():
    """共享技能 → Nova 工作区（OpenClaw 不跟随符号链接，只能实体复制并打同步标记）。
    Hermes 侧用符号链接（~/.hermes/skills/team/<name>），无需复制。"""
    made = []
    if not os.path.isdir(SHARED_SKILLS):
        return made
    for name in sorted(os.listdir(SHARED_SKILLS)):
        src = os.path.join(SHARED_SKILLS, name, "SKILL.md")
        if not os.path.isfile(src):
            continue
        dst_dir = os.path.join(NOVA_WS, "skills", name)
        dst = os.path.join(dst_dir, "SKILL.md")
        os.makedirs(dst_dir, exist_ok=True)
        txt = open(src, encoding="utf-8").read()
        end = txt.find("\n---", 3)
        mark = (f"\n<!-- AUTO-SYNCED 共享技能：源 = {src}\n"
                "     改内容请改源文件，然后跑 ~/AI工作台/团队协同/bin/scan_skills.py -->\n")
        if end > 0:
            txt = txt[:end + 4] + mark + txt[end + 4:]
        else:
            txt = txt + mark
        if not os.path.isfile(dst) or open(dst, encoding="utf-8").read() != txt:
            open(dst, "w", encoding="utf-8").write(txt)
            made.append(name)
        # Hermes 侧符号链接（loader 跟随）
        link_dir = os.path.join(HERMES_SKILLS, "team")
        link = os.path.join(link_dir, name)
        os.makedirs(link_dir, exist_ok=True)
        if not os.path.islink(link) or os.path.realpath(link) != os.path.realpath(os.path.join(SHARED_SKILLS, name)):
            try:
                if os.path.isdir(link) and not os.path.islink(link):
                    import shutil
                    shutil.rmtree(link)
                elif os.path.islink(link):
                    os.remove(link)
                os.symlink(os.path.join(SHARED_SKILLS, name), link)
            except Exception:
                pass
    return made


def build():
    synced = sync_shared()
    skills = scan_shared() + scan_hermes() + scan_nova()
    reg = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "machine": "MacBook Pro (Hannah + Nova)",
           "counts": {}, "routing": ROUTING, "skills": skills}
    for s in skills:
        reg["counts"][s["owner"]] = reg["counts"].get(s["owner"], 0) + 1
    os.makedirs(ROOT, exist_ok=True)
    tmp = REG + ".tmp"
    json.dump(reg, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, REG)
    write_map(reg)
    return reg


def write_map(reg):
    L = ["# SKILLS-MAP — 两个 agent 的技能总账", "",
         f"_自动生成 {reg['generated']} · Hannah {reg['counts'].get('hannah',0)} / "
         f"Nova {reg['counts'].get('nova',0)} / 共享 {reg['counts'].get('shared',0)}_", "",
         "> 由 `~/AI工作台/团队协同/bin/scan_skills.py` 生成，**不要手改**。查：`scan_skills.py search 关键词`；派活：`scan_skills.py who 能力`。", "",
         "## 一、分工路由（先看谁主责，避免两套并行）", "",
         "| 能力 | 主责 | 备手 | 怎么用 |", "|---|---|---|---|"]
    for r in reg["routing"]:
        L.append(f"| {r['capability']} | **{r['primary']}** | {r['fallback']} | {r['how']} |")
    L += ["", "## 二、共享技能（两边都加载，同一份文件）", ""]
    for s in [x for x in reg["skills"] if x["owner"] == "shared"]:
        L.append(f"- **{s['name']}** — {s['description']}  \n  `{s['path']}`")
    L += ["", "## 三、Hannah（Hermes）技能", ""]
    cur = None
    for s in [x for x in reg["skills"] if x["owner"] == "hannah"]:
        if s["category"] != cur:
            cur = s["category"]
            L.append(f"\n### {cur}\n")
        L.append(f"- **{s['name']}** — {s['description']}")
    L += ["", "## 四、Nova（OpenClaw）技能", ""]
    cur = None
    for s in [x for x in reg["skills"] if x["owner"] == "nova"]:
        if s["category"] != cur:
            cur = s["category"]
            L.append(f"\n### {cur}\n")
        flag = "" if s.get("ready") else f" · ⚠️ 缺依赖 {','.join(s.get('missing') or []) or '未启用'}"
        L.append(f"- **{s['name']}** — {s['description']}{flag}")
    open(MAP, "w", encoding="utf-8").write("\n".join(L) + "\n")


def search(q):
    reg = json.load(open(REG, encoding="utf-8")) if os.path.isfile(REG) else build()
    ql = q.lower()
    hits = []
    for s in reg["skills"]:
        name = str(s.get("name")).lower()
        tags = " ".join(s.get("tags") or []).lower()
        blob = (name + " " + s.get("description", "") + " " + tags + " " + str(s.get("category", ""))).lower()
        if ql in blob:
            score = 3 if ql in name else 2 if ql in tags else 1
            hits.append((score, s))
            continue
        # 名字/描述没写中文关键词时，退而搜正文（技能正文里通常有“微信/飞书/报价”这类业务词）
        p = s.get("path") or ""
        if p and os.path.isfile(p):
            try:
                body = open(p, encoding="utf-8", errors="ignore").read(120000).lower()
                n = body.count(ql)
                if n:
                    hits.append((0.5 + min(1.5, n * 0.25), s))
            except Exception:
                pass
    hits.sort(key=lambda x: (-x[0], x[1]["owner"], str(x[1]["name"])))
    if not hits:
        print(f"没有技能命中「{q}」。试试更短的关键词（邮件/GPU/PDF/浏览器/会议）。")
        return
    print(f"命中 {len(hits)} 个技能（「{q}」）：")
    for score, s in hits[:25]:
        tag = {"hannah": "🟦 Hannah", "nova": "🟥 Nova", "shared": "🟨 共享"}.get(s["owner"], s["owner"])
        rdy = "" if s.get("ready", True) else " · ⚠️未就绪"
        print(f"  {tag} · {s['name']}{rdy}\n      {s['description'][:150]}\n      {s.get('path','')}")


def who(q):
    reg = json.load(open(REG, encoding="utf-8")) if os.path.isfile(REG) else build()
    ql = q.lower()
    hit = [r for r in reg["routing"] if ql in r["capability"].lower() or ql in r["how"].lower()]
    if not hit:
        print("路由表里没有这项能力。看全部：`scan_skills.py who ''`")
        print("\n".join(f"  - {r['capability']} → {r['primary']}" for r in reg["routing"]))
        return
    for r in hit:
        print(f"【{r['capability']}】\n  主责: {r['primary']}   备手: {r['fallback']}\n  {r['how']}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        reg = build()
        print(f"总账已更新：{REG}")
        print(f"  Hannah {reg['counts'].get('hannah',0)} · Nova {reg['counts'].get('nova',0)} · 共享 {reg['counts'].get('shared',0)}")
    elif a[0] == "--json":
        print(json.dumps(json.load(open(REG, encoding="utf-8")), ensure_ascii=False)[:4000])
    elif a[0] == "search":
        search(" ".join(a[1:]))
    elif a[0] == "who":
        who(" ".join(a[1:]))
    else:
        print(__doc__)
