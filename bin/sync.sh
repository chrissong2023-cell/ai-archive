#!/bin/bash
# AI 档案同步：pull 拉最新记忆，push 把本地更新推上去
set -e
cd "$(dirname "$0")/.."
case "$1" in
  pull)  git pull --rebase --autostash && echo "✅ 已同步到最新" ;;
  push)  git add -A
         git diff --cached --quiet && { echo "没有变更"; exit 0; }
         git commit -m "update: $(date '+%F %H:%M') auto-sync"
         # 网络偶发被代理重置，重试 3 次
         for i in 1 2 3; do
           git push -q && { echo "✅ 已推送"; exit 0; }
           echo "第 $i 次推送失败，5 秒后重试…"; sleep 5
         done
         echo "❌ 三次推送均失败（检查网络/VPN）"; exit 1 ;;
  *)     echo "用法: sync.sh {pull|push}"; exit 1 ;;
esac
