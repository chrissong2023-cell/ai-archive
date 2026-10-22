#!/bin/bash
# AI 档案同步：pull 拉最新记忆，push 把本地更新推上去
set -e
cd "$(dirname "$0")/.."
case "$1" in
  pull)  git pull --rebase --autostash && echo "✅ 已同步到最新" ;;
  push)  git add -A
         git diff --cached --quiet && { echo "没有变更"; exit 0; }
         git commit -m "update: $(date '+%F %H:%M') auto-sync"
         git push && echo "✅ 已推送" ;;
  *)     echo "用法: sync.sh {pull|push}"; exit 1 ;;
esac
