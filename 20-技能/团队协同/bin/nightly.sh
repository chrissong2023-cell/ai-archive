#!/bin/zsh
# 每日/每班次：刷新技能总账（并把共享技能同步到 Nova 工作区）+ 增量重建知识库索引
set -u
LOG=$HOME/.nova-kb/team-sync.log
echo "===== $(date '+%F %T') =====" >> "$LOG"
/usr/bin/python3 "$HOME/AI工作台/团队协同/bin/scan_skills.py" >> "$LOG" 2>&1
"$HOME/.nova-tools/kb.sh" index >> "$LOG" 2>&1
echo "exit=$?" >> "$LOG"
