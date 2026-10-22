#!/bin/bash
# AI 档案镜像：每天生成一个全量快照，投进移动云盘（自动上云），
# 并（可选）推一份到 Chris 自己的服务器。三重保险：GitHub 主库 / 云盘 bundle / 服务器 git。
set -u
REPO="$HOME/AI工作台/AI档案"
BUNDLE_DIR="$HOME/AI工作台/移动云盘/备份"
LOG="$REPO/.mirror.log"
mkdir -p "$BUNDLE_DIR"
ts() { date '+%F %T'; }
log() { echo "[$(ts)] $*" | tee -a "$LOG"; }

cd "$REPO" || { log "❌ 仓库不存在"; exit 1; }

# 0) 先提交本地未保存的改动（只提交，不推送——推送由 sync.sh 负责）
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git -c user.name="Chris Song" -c user.email="chris@wuzhounexus.com" \
      commit -q -m "auto: $(date '+%F %H:%M') 每日镜像前快照" || true
  log "已提交本地变更"
fi

# 1) 先推 GitHub 主库（有 origin 才执行；网络偶发被代理重置，重试 3 次）
if git remote get-url origin >/dev/null 2>&1; then
  OK=0
  for i in 1 2 3; do
    if git push -q origin --all 2>>"$LOG" && git push -q origin --tags 2>>"$LOG"; then OK=1; break; fi
    sleep 5
  done
  [ "$OK" = 1 ] && log "✅ GitHub 已推送 $(git rev-parse --short HEAD)" || log "⚠️ GitHub 推送失败（已重试 3 次）"
else
  log "⏭ 未配置 origin（跳过 GitHub）"
fi

# 2) 云盘 bundle（整仓历史打成一个文件，自带校验）
OUT="$BUNDLE_DIR/ai-archive-$(date '+%Y-%m-%d').bundle"
if git bundle create "$OUT" --all 2>>"$LOG"; then
  git bundle verify "$OUT" >/dev/null 2>&1 && log "✅ 云盘快照 $(basename "$OUT") $(du -h "$OUT" | cut -f1)" || log "⚠️ bundle 校验失败"
else
  log "❌ bundle 生成失败"
fi
# 只留最近 14 天
ls -1t "$BUNDLE_DIR"/ai-archive-*.bundle 2>/dev/null | tail -n +15 | while read -r old; do rm -f "$old"; log "清理旧快照 $(basename "$old")"; done

# 3) 服务器镜像（配置了才执行）
if [ -f "$HOME/.hermes-secrets/ai-archive-server.json" ]; then
  python3 - "$REPO" "$LOG" <<'PY'
import json, os, subprocess, sys, datetime
repo, logf = sys.argv[1], sys.argv[2]
cfg = json.load(open(os.path.expanduser("~/.hermes-secrets/ai-archive-server.json")))
host, user, port = cfg.get("host"), cfg.get("user"), int(cfg.get("port", 22))
def log(m):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {m}"
    print(line); open(logf, "a").write(line + "\n")
if not (host and user):
    log("⏭ 服务器配置不完整（需要 host/user）"); sys.exit(0)
remote = f"ssh://{user}@{host}:{port}/~/repos/ai-archive.git"
ok = True
for args in (["push", "--quiet", remote, "--all"], ["push", "--quiet", remote, "--tags"]):
    r = subprocess.run(["git"] + args, cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        ok = False; log(f"⚠️ 服务器镜像失败: {r.stderr.strip()[:160]}")
log("✅ 服务器镜像完成" if ok else "⚠️ 服务器镜像未完成（检查密钥或远端裸库）")
PY
else
  log "⏭ 服务器镜像未配置（缺 ~/.hermes-secrets/ai-archive-server.json）"
fi

log "完成"
