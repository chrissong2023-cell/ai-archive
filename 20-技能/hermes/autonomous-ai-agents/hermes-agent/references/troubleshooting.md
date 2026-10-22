# Troubleshooting

### Voice not working
1. Check `stt.enabled: true` in config.yaml
2. Verify provider: `python -c "import pm; pm.sync_venv(['stt-whisper'], explicit=True)"` or set API key
3. In gateway: `/restart`. In CLI: exit and relaunch.

### Tool not available
1. `hermes tools` — check if toolset is enabled for your platform
2. Some tools need env vars (check `.env`)
3. `/reset` after enabling tools

### Model/provider issues
1. `hermes doctor` — check config and dependencies
2. `hermes auth` — re-authenticate OAuth providers (or `hermes auth add <provider>`)
3. Check `.env` has the right API key
4. **Copilot 403**: `gh auth login` tokens do NOT work for Copilot API. You must use the Copilot-specific OAuth device code flow via `hermes model` → GitHub Copilot.

### Changes not taking effect
- **Tools/skills:** `/reset` starts a new session with updated toolset
- **Config changes:** In gateway: `/restart`. In CLI: exit and relaunch.
- **Code changes:** Restart the CLI or gateway process

### web_extract shows a stale page (result caching)
`web_search`/`web_extract` cache results for 20 minutes (PR #94618) — a
repeat fetch of the same URL within the TTL is served from cache, which
can look like "my website changes aren't showing up."

Automatic carveouts (always fetched live, never cached):
- localhost / 127.0.0.1 / `*.local` / `*.localhost` / single-label LAN
  hostnames / private + link-local IP ranges (dev servers, hot-reload
  builds, chat-GUI artifact previews)
- URLs matched by `security.website_blocklist`
- failed responses and keyless-rescue-served responses

Developing a site tested over the PUBLIC internet (Vercel/Netlify
preview, ngrok/cloudflared tunnel, staging domain)? Public DNS isn't
auto-carved-out — list the host in config.yaml:

```yaml
web:
  cache_exempt_hosts:      # always fetched live; effective immediately
    - mysite.vercel.app
    - "*.ngrok-free.app"
    - mysite.dev           # suffix match: also covers preview.mysite.dev
```

Blunt instruments: `web.cache_ttl_minutes: 1` (min) or
`web.cache_enabled: false` disables both caches entirely.

### Skills not showing
1. `hermes skills list` — verify installed
2. `hermes skills config` — check platform enablement
3. Load explicitly: `hermes -s name` (or the skill's own `/<name>` slash command)

### Gateway issues
Check logs first:
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

Common gateway problems:
- **Gateway dies on SSH logout**: Enable linger: `sudo loginctl enable-linger $USER`
- **Gateway dies on WSL2 close**: WSL2 requires `systemd=true` in `/etc/wsl.conf` for systemd services to work. Without it, gateway falls back to `nohup` (dies when session closes).
- **Gateway crash loop**: Reset the failed state: `systemctl --user reset-failed hermes-gateway`

### Platform-specific issues
- **Discord bot silent**: Must enable **Message Content Intent** in Bot → Privileged Gateway Intents.
- **Slack bot only works in DMs**: Must subscribe to `message.channels` event. Without it, the bot ignores public channels.
- **Windows-specific issues** (`Alt+Enter` newline, WinError 10106, UTF-8 BOM config, line endings): see `references/windows-quirks.md`.

### Desktop app build stalls on the Electron binary (slow/blocked GitHub CDN)
`hermes desktop` (and `hermes update`, which rebuilds the desktop app) runs
`npm ci` for `apps/desktop`, whose Electron postinstall downloads
`electron-v<ver>-<os>.zip` (~110 MB) from the GitHub CDN. Behind a slow or
blocked route this shows up as the build sitting on
`→ Preparing Node dependencies…` for tens of minutes with an
`electron-download-*` temp dir growing at dial-up speed.

Diagnose (confirm the host and the rate before assuming a dead build):
```bash
lsof -p $(pgrep -f 'node install.js') | grep -E 'cwd|TCP'   # shows the download host
ls -l /private/var/folders/*/*/T/electron-download-*/         # size growth = real progress
```
Fix: point Electron (and electron-builder's binaries) at a mirror and rerun —
env is inherited straight through `hermes desktop`:
```bash
export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
export ELECTRON_BUILDER_BINARIES_MIRROR="https://npmmirror.com/mirrors/electron-builder-binaries/"
hermes desktop --build-only
```
The mirror path is `<mirror><version>/electron-v<version>-<os>.zip`, so the
same pattern works for any regional mirror. The npm cache survives the kill,
so restarting the build costs little.

### Browser won't start: "profile … write lock"
`browser.use_real_profile: true` clones the user's real Chromium profile, so a
running Chrome blocks it:

```
chrome is running and holds the profile's Login Data For Account, Web Data
with a write lock … does not fall back to a raw file copy
```

Order of operations:
1. `pgrep -x "Google Chrome"` — **closing the window is not quitting**; the app
   keeps running and keeps the lock. Require 0 PIDs, not "I closed it".
2. Ask the user to Cmd+Q. If `osascript -e 'tell application "Google Chrome" to quit'`
   has no effect (no Automation permission), stop the main PID gracefully:
   `kill -TERM <pid>`, then re-check with `pgrep -x`.
3. Retry the browser call. Profile cookies come with it, so an already-logged-in
   site loads straight into the session.
4. Only if the user refuses to quit: run the isolated profile instead and let
   them log in through the vault prompt (never a password typed by you).

Never `kill -9` a browser holding unsaved tabs — TERM lets it flush state and
Chrome restores the session on next launch.

**Inverse symptom — the user says their own Chrome "won't open".** Once the
managed copy is running it holds the `com.google.Chrome` bundle id, so
double-clicking the Dock/Desktop icon (or `open -a "Google Chrome" <url>`)
just re-targets the *invisible* managed instance and nothing appears. Check
which instance is alive before debugging anything else:

```bash
ps -eo pid,command | grep '[G]oogle Chrome.app/Contents/MacOS' | grep -o 'user-data-dir=[^ ]*'
pgrep -f browser-profile/chrome          # the managed copy
```

If the only live process carries `--user-data-dir=…/.hermes/browser-profile/chrome`,
the user's Chrome is simply not running: release the copy
(`pkill -TERM -f browser-profile/chrome`, or the helper
`~/.nova-tools/chrome_release.sh`) and relaunch theirs. **Release it after
every browser task** — leaving it up silently breaks the user's browser, and
"I verified the icon works" from inside the same session proves nothing
because `open` was routed to the managed instance too.

### Auxiliary models not working
If `auxiliary` tasks (vision, compression, session_search) fail silently, the `auto` provider can't find a backend. Either set `OPENROUTER_API_KEY` or `GOOGLE_API_KEY`, or explicitly configure each auxiliary task's provider:
```bash
hermes config set auxiliary.vision.provider <your_provider>
hermes config set auxiliary.vision.model <model_name>
```

### "Reset permissions" / auto-approving everything
See `references/security-privacy.md` — wipe the "Always allow" stores, don't touch yolo mode.

