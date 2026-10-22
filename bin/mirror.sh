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

# 1) 云盘 bundle（整仓历史打成一个文件，自带校验）
OUT="$BUNDLE_DIR/ai-archive-$(date '+%Y-%m-%d').bundle"
if git bundle create "$OUT" --all 2>>"$LOG"; then
  git bundle verify "$OUT" >/dev/null 2>&1 && log "✅ 云盘快照 $(basename "$OUT") $(du -h "$OUT" | cut -f1)" || log "⚠️ bundle 校验失败"
else
  log "❌ bundle 生成失败"
fi
# 只留最近 14 天
ls -1t "$BUNDLE_DIR"/ai-archive-*.bundle 2>/dev/null | tail -n +15 | while read -r old; do rm -f "$old"; log "清理旧快照 $(basename "$old")"; done

# 2) 服务器镜像（配置了才执行）
CFG="$HOME/.hermes-secrets/ai-archive-server.json"
if [ -f "$CFG" ]; then
  HOST=$(python3 -c "import json;print(json.load(open('$CFG')).get('host',''))" 2>/dev/null)
  USER_=$(python3 -c "import json;print(json.load(open('$CFG')).get('user',''))" 2>/dev/null)
  P=$(python3 -c "import json;print(json.load(open('$CFG')).get('port',22))" 2>/dev/null)
  if [ -n "$HOST" ] && [ -n "$USER_" ]; then
    if git push --quiet "ssh://$USER_@$HOST:$P/~/repos/ai-archive.git" --all 2>>"$LOG" &&
       git push --quiet "ssh://$USER_@$HOST:$P/~/repos/ai-archive.git" --tags 2>>"$LOG"; then
      log "✅ 服务器镜像完成 $USER_@$HOST"
    else
      log "⚠️ 服务器镜像失败（检查密钥或远端裸库）"
    fi
  fi
else
  log "⏭ 服务器镜像未配置（缺 $CFG）"
fi

log "完成"
