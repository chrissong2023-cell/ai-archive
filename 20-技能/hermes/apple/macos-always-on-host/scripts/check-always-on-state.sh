#!/bin/bash
# 一眼看清这台 Mac 的「常驻在线」状态。不需要 sudo，可随时运行。
# 用法：bash check-always-on-state.sh

date

echo
echo "【电源来源】"
pmset -g batt | head -2

echo
echo "【插电 AC】目标：sleep=0（永不睡眠）"
pmset -g custom | sed -n '/^AC Power:/,/^Battery Power:/p' \
  | grep -E "^\s*(sleep|displaysleep|disksleep|tcpkeepalive|womp|powernap|powermode)"

echo
echo "【电池】目标：sleep=15（保命；24h 常驻必须插电）"
# 注意：pmset -g custom 先打印 Battery Power 再打印 AC Power
pmset -g custom | sed -n '/^Battery Power:/,/^AC Power:/p' \
  | grep -E "^\s*(sleep|displaysleep|disksleep|powermode)"

echo
echo "【合盖不睡】SleepDisabled = $(pmset -g | awk '/SleepDisabled/{print $2}')  （1=合盖也跑；拔电+合盖会耗到关机）"

echo
echo "【谁在阻止睡眠】"
pmset -g | grep -i "sleep prevented" || echo "  无（插电 sleep=0 本来就不睡）"

echo
echo "【DNS】$(networksetup -getdnsservers Wi-Fi 2>/dev/null | tr '\n' ' ')"
echo "【resolver #1 的域名服务器】"
scutil --dns | grep -m3 "nameserver\[" | head -3

echo
echo "【最近 10 次睡眠/唤醒】"
pmset -g log 2>/dev/null | grep -E "Entering Sleep state|Wake from" | tail -10 | sed 's/Using .*//'

echo
echo "【AI 进程】"
launchctl list | grep -E "hermes|openclaw" | awk '{printf "  PID %-8s 上次退出码 %-4s %s\n", $1, $2, $3}'

echo
echo "【FileVault / 自动装更新】"
fdesetup status
printf "AutomaticallyInstallMacOSUpdates = "; \
  defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates 2>/dev/null || echo "(未设置)"
