---
name: macos-browser-profile-ops
description: Use when driving the user's own Chrome on macOS.
version: 1.0.0
author: Hannah (Hermes Agent)
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [macos, chrome, browser, profile, bookmarks, desktop, shortcuts]
    related_skills: [hermes-agent, macos-network-triage, blocked-page-recovery]
---

# 用用户自己的 Chrome（macOS）

Hermes 的 `browser.use_real_profile: true` 会复制用户的 Chrome profile 来继承登录态。这条路能走，但有四个固定的坑，每个都能让人以为“浏览器坏了”。

## 何时用

- 要在他常登录的站点上操作（外贸通、企业邮箱、CASS、平台后台）
- 要读他的书签 / 浏览历史 / 已保存的登录
- 他报告“Chrome 双击打不开 / 桌面图标没反应”
- 要在桌面或 Dock 放程序快捷方式

## 三条硬规则

1. **密码永远不经过对话**：不接受聊天里的密码、不自己输。只能用加密输入框（vault）收集，或让用户自己登录一次。
2. **不擅自杀他的浏览器**：Chrome 里可能有未保存的标签页。要退就先问一句；他说退了但进程还在时，说明“还在跑，我发 TERM 还是你自己 Cmd+Q”。
3. **不承诺“以后自动登录”**：能承诺的是“你登录一次，我用你的 profile 复用”，不是“我记住你的密码”。

## 一、启动前置：Chrome 必须完全退出

`browser.use_real_profile` 要把 `Login Data` / `Web Data` 拷出来，Chrome 活着就锁着：

```
chrome is running and holds the profile's Login Data For Account, Web Data with a
write lock, so their SQLite backup made no progress within five seconds
```

- 判据：`pgrep -x "Google Chrome"` 有主进程就是没退干净（关窗口 ≠ 退出，`Cmd+Q` 才是）。
- 这个工具**不会**退回裸文件复制（会丢已提交的登录），所以别指望重试几次就过去。

## 二、致命冲突：同一个 bundle id 会吞掉他的双击

Hermes 托管的浏览器（`--user-data-dir=~/.hermes/browser-profile/chrome`）和用户的 Chrome 是**同一个 App**。它一在跑，用户双击 Chrome / 桌面图标，macOS 就把请求路由给那个**没有可见窗口**的实例——表现为“双击毫无反应”，很容易被误判成“Chrome 坏了”。

- 判据：`ps -eo pid,command | grep "[G]oogle Chrome.app/Contents/MacOS"`，命令行里带 `--user-data-dir=…/browser-profile` 的就是托管实例。
- 修法：`zsh scripts/chrome_release.sh`（等价 `pkill -TERM -f "browser-profile/chrome"`），然后 `open -a "Google Chrome" <url>` 才会起他自己的实例。
- **用完就释放**：每次拿他的 profile 干完活（登录、抓页面、读书签），立刻释放，不要留着过夜。
- 汇报时明说“托管实例已释放”，否则他下次双击打不开时无从判断。

## 三、登录态不能靠复制 profile 迁移

Chrome ≥127 的 cookie 用 **App-Bound Encryption**，绑定本机应用。实测：profile 复制成功、cookie 行数一致，但目标站点的**会话 cookie 根本不在里面**（只有 `__snaker__id` 这类防爬 cookie），页面依旧停在登录页。

- 结论：**能复用的是“用户自己的 profile + 他真登录过”**，不是“我拿到文件就等于拿到登录”。
- 会话 cookie 常常是内存态，Chrome 退出即丢；跨实例更不可能。
- 带**二次验证**的站点（新设备必须手机确认）在托管实例里几乎必定被拦，反复扫码只会一遍遍看到“需要二次验证，请使用其它方式登录”。

**正确取舍**：2FA 平台（外贸通、银行、CASS）**不做网页自动化**，改走它的 API/IMAP；网页只留给“看一眼”的场合，由用户自己操作。

## 三之二、CDP 接管「他正登录的窗口」——先用两条命令判定，不要反复试

想直接操作 Chris 已登录的 Chrome（外贸通、CASS、银行后台），最自然的想法是给 Chrome 开远程调试端口再 attach。**Chrome ≥136 在默认 profile 上会静默忽略 `--remote-debugging-port`**：进程确实带着参数起来了，但端口不监听、`curl` 空响应 —— 看起来像“参数写错”，实际是防 cookie 被窃的设计。

判据（30 秒出结论）：

```bash
lsof -nP -iTCP:9222 -sTCP:LISTEN          # 无输出 = 没起来
curl -s -m 3 http://127.0.0.1:9222/json/version
```

对照组（证明限制来自 profile 策略而非命令行）：

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --user-data-dir=/tmp/cdp-test --remote-debugging-port=9223 --no-first-run --headless=new
# 独立 user-data-dir 立刻监听 → 结论确定
```

拿到这个结果就停手。**不要**把“在他登录的窗口里一起干活”当承诺许出去；可行路径按优先级：

1. **站点自带导出**（CSV/Excel/PDF）—— 让他点一次导出，我接文件处理。比接管浏览器稳，也不碰他的凭据。
2. **独立 `--user-data-dir` + 他登录一次** —— 能跑，但等于新设备，2FA 平台必被拦（见第三节）。
3. **换协议**：邮件走 IMAP/SMTP，清单/行情走公开接口。

收尾：`pkill -f cdp-test`，再 `open -a "Google Chrome"` 把他的 Chrome 正常起回来。**绝不能留一个“带调试参数但没端口”的实例**——他下次双击会以为浏览器坏了。

## 四、读书签：没有 `Bookmarks` 文件时看 `AccountBookmarks`

如果书签是**账号同步**的，`Default/Bookmarks` 这个文件根本不存在（`find … -name "Bookmarks"` 为空），而 `Default/AccountBookmarks` 是 **JSON，含完整 url/name/树路径**：

```bash
python3 scripts/dump_chrome_bookmarks.py          # 打印分类统计 + 样例
```

- `Default/EncryptedAccountBookmarks2` 是加密体（`v10…`），别在那上面耗时间。
- 读完把结果落到 `~/AI工作台/00-总控/STATE/bookmarks.json`，并按业务域分类（物流/海关政府/供应商/银行/自有公司），这份分类本身就是“他关心什么”的证据。

## 五、桌面 / Dock 快捷方式

```bash
ln -sf "/Applications/Google Chrome.app" ~/Desktop/"Google Chrome.app"   # 双击可用，不占空间
```

Dock 追加（只追加、不打乱已有顺序，随后 Dock 会闪一下）：

```bash
defaults write com.apple.dock persistent-apps -array-add '<dict><key>tile-data</key><dict><key>file-data</key><dict><key>_CFURLString</key><string>/Applications/X.app</string><key>_CFURLStringType</key><integer>0</integer></dict></dict></dict>'
killall Dock
```

注意：plist 里的 `&&` 会被 `plutil` 判为非法转义——多命令要写成 wrapper 脚本，别塞进 `ProgramArguments`。

## 六、桌面上的“文件”可能是挂载镜像

用户说“桌面的 install xxx 删不掉/碍眼”时，先 `ls /Volumes` 和 `hdiutil info`：多半是他双击过 `.dmg`，桌面那个白盘是挂载点。

```bash
hdiutil detach "/Volumes/<卷名>"        # 或 diskutil eject
mkdir -p ~/AI工作台/安装包 && mv ~/Downloads/<x>.dmg ~/AI工作台/安装包/
```

**移动/弹出可以，删除要先问。**

## 七、验证与汇报

1. `pgrep -x "Google Chrome"` 看到的是**他的**实例（没有 `--user-data-dir` 参数）
2. `open ~/Desktop/"X.app"` 返回 0
3. 需要看界面时 `screencapture -x`，再确认前台应用是 Chrome
4. 汇报要写：哪一步是我做的、他需要做什么、失败时报错原文（不猜）
