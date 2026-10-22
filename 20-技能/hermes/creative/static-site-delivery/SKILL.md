---
name: static-site-delivery
description: Use when building or relaunching a site for a domain.
version: 1.0.0
author: Hannah
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [website, static-site, html, dns, hosting, seo, bilingual, delivery]
    related_skills: [claude-design, popular-web-designs, web-presence-audit]
---

# Static site delivery

Company and service sites delivered as hand-written static pages: no build step, no CMS, no database, nothing that expires with a server. `claude-design` owns composition and taste; this skill owns diagnosis, file layout, verification and shipping.

## When to Use

- The user wants a website: "帮我建个网站", "把官网重做", "we need a landing page for <company>", or hands over new/expired domains to relaunch.
- A company site is dark because its server or hosting plan expired.
- A domain needs a one-page corporate site with real company facts, zh/en copy, and a host + DNS cutover.

Not for: web apps with auth or data (a real stack applies), throwaway design mockups with no host (`claude-design` alone), or auditing a live site you did not build (`web-presence-audit`).

## Rules for every delivery

- **Deliver the site, not a mockup.** Per domain, one directory:
  `index.html`, `assets/style.css`, `assets/app.js`, `assets/og.png`, `robots.txt`, `sitemap.xml`, `README.md`.
  Plus a launcher `index.html` one level up linking every site. The README carries the deploy steps and the launch-blocker list — it is part of the deliverable.
- **Hand-written HTML/CSS/vanilla JS. No framework, no bundler, no remote fonts or CDN scripts.** Audience and host are in mainland China: remote font/JS hosts stall the first paint and sometimes never resolve. Use the system stack (`-apple-system, "PingFang SC", "Microsoft YaHei"`) plus `ui-monospace` for figures.
- **Every fact comes from `~/.openclaw/workspace/knowledge/company-dossier.md`** — certifications, WCA IDs, addresses, phones, entity names, business scope. Never from memory, never plausible-sounding invention. Anything unconfirmed stays a visible placeholder *and* goes on the README launch-blocker list.
- **Bilingual zh/en by default**: one page, `data-zh`/`data-en` attribute pairs, header toggle, `?lang=` deep link. Details and pitfalls in `references/bilingual-zh-en-site.md`.
- **Mainland hosting requires a real ICP备案号** in the footer, linked to `https://beian.miit.gov.cn`. Ship `京ICP备 — 待填 号` inside a `<!-- TODO -->` comment and report it as a blocker — never invent a number.
- **Filter public copy for compliance risk.** Do not put controlled-hardware model names (H200/B200/L40S …) or "cross-border GPU sales" on an open website: it hands customs, BIS and competitors a screenshot. Write the capability instead ("compute and IT hardware flows, subject to export-control and end-user screening") and state the no-circumvention position. Tell the user this is a deliberate omission so they can overrule it.
- **Sell a freight operator on what a fellow forwarder screens.** WCA / IATA are not badges: pair the WCA ID with a member-directory verification link ("会员库核验 →"), and expand IATA into accredited cargo agent + CASS settlement. Then add a short agent-partnership block — capacity and rate swap, destination services, WCA 30-day terms, one bilingual ops contact — because that is what an overseas agent checks before sending a first shipment. A certification strip alone does not answer it.
- **A second entity is positioned by who it works with, not by its own org chart.** For a supply-chain / tech sister company, lead with the collaboration model: name the overseas counterparties (with registration numbers — the French SAS and its RCS number, the Thai holding company, the Indonesian entity), state the split of labour per counterparty, and list the ways to cooperate (joint bidding, capacity/warehouse swap, sourcing-and-shipping, EU import landing). A group-matrix table is supporting evidence, never the pitch. When the user corrects the positioning ("they can work with several overseas companies, the French supply chain company"), cut a new section — do not rewrite the whole page.
- **Copy voice**: 18-year freight operator, not a brochure. Concrete lanes, ports, temperatures, days, certification IDs; no "专业高效/值得信赖" filler. A services page reads as an operator's manual, not marketing.
- **Aim at the premium bar, not at "modern".** These sites are shown to customers and partners, and the ask arrives as "高端/高级/高大上". The levers that actually carry it: display headings in a serif stack (`"Songti SC", "Noto Serif SC", Georgia, serif`) with the body kept sans; a calmer section rhythm with fewer rules and borders; real photography in the two or three places that carry proof (cold-chain, yard, rail, team). Gradients, glass and animation read as template, not as expensive. **A zero-image site reads as 素 however good the typography is** — either design deliberate image slots and ask for his own photos, or say plainly that photos are the next upgrade rather than calling the page finished.
- **He will paste AccessKeys, secrets and SMS codes straight into chat.** Treat a pasted credential as compromised: write it to `~/.hermes-secrets/<name>.json` (chmod 600) without echoing it, never reprint it, and tell him to rotate it once the deploy is done. **Never use a code he pasted in chat** — the masked prompt (`browser_vault_enter_code`) is the only supported path; say the pasted one is void instead of silently burning it, and do not ask for another code in text.
- **When the blocker is his clicks, open the page for him.** Prose navigation loses: he reported "我没有找到" twice for a page that exists. `open -na "Google Chrome" --args --new-window "<url>"` lands him on the exact console page, then give ONE table of control name → value to paste → record to delete, nothing else. Ask for the standing API permissions once (OSS + DNS + certificate + CDN) rather than a chain of one-off favours, and refuse `AdministratorAccess`, ECS and billing access on least-privilege grounds.
- **Chat deliverables**: paths + inline screenshots. Never docx/xlsx/pptx.

## Procedure

### 1. Diagnose the domain before writing a line of HTML

```bash
for d in example.com example.com.cn; do
  whois "$d" | egrep -i "Registrar|Registration Time|Expiration|Name Server|Registrant"
  dig +short NS "$d"; dig +short A "$d"; dig +short A "www.$d"
  curl -sS -m 20 -o /dev/null -w "%{http_code} %{remote_ip}\n" "https://www.$d/"
done
```

"The server expired" almost always means **DNS still points at a released IP**: `dig` returns an address, `curl` gets a TCP timeout with no HTTP response. Say that explicitly and name the IP to delete. Check the registrar and expiry too — domains outlive servers, so the fix is a new host, not a new domain.

### 2. Recover the old site's content and structure

```python
web_extract(urls=["http://archive.org/wayback/available?url=<domain>"])
web_extract(urls=["http://web.archive.org/web/<timestamp>/https://<domain>/"])
```

Route archive.org through `web_extract`; a direct `urllib`/`curl` fetch from this Mac times out. Salvage real assets: legal entity name in the footer, address, service list, 备案号. Expect a template site whose content belongs to a different company — say so and rebuild rather than patch.

### 3. Build

One page per site unless the user asks for sub-pages. Layout per `claude-design` (commit to a surface first; a company site is a **Decide/Learn** surface, so the hero is legitimate). Give each site its own palette so two sister companies do not read as one template: e.g. light paper + rust signal for the freight operator, charcoal + brass mono-grid for the tech entity. Include `curl`-checkable SEO basics: `<title>`, description, canonical, OG/Twitter tags, JSON-LD `Organization`, `robots.txt`, `sitemap.xml`.

Generate the share card (WhatsApp/WeChat/LinkedIn previews need it): render a 1200×630 HTML card and screenshot it.

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --hide-scrollbars --user-data-dir=/tmp/chrome-shot-profile \
  --window-size=1200,630 --screenshot=assets/og.png file:///tmp/og_card.html
```

Reference it as an absolute URL (`https://<domain>/assets/og.png`) — previews do not fetch relative paths usefully.

### 4. Verify visually at real sizes (this is the step that gets skipped)

```bash
python3 "$SKILL_DIR/scripts/cdp_shot.py" '[{"url":"http://127.0.0.1:8781/a.com/","out":"/tmp/a-desktop.png","width":1440,"height":900},
 {"url":"http://127.0.0.1:8781/a.com/","out":"/tmp/a-mobile.png","width":390,"height":844,"mobile":true}]'
```

Then look at every image with vision, cropping regions for detail. Two traps that fake a passing check:

- **`--window-size` below 500 is clamped to 500.** A "390px" `--screenshot` is a cropped desktop layout — text clipped at the right edge proves nothing about phones. Real mobile needs CDP `Emulation.setDeviceMetricsOverride` (the script does it, plus the iOS UA).
- **`--screenshot` captures the viewport only**, and concurrent CDP jobs on one tab all capture the same frame. Full-page capture needs `Page.captureScreenshot` with a clip built from `Page.getLayoutMetrics().cssContentSize`, and jobs must run sequentially (or on separate targets).

Overflow check that actually catches bugs: `document.documentElement.scrollWidth - window.innerWidth` must be `0` at 390px. The usual offender is one unbreakable string in a flex row (a phone number in a CTA button) — stack CTAs full-width under 640px and keep a `body{overflow-x:hidden}` belt.

### 5. Smoke-test behaviour over CDP

Assert, do not eyeball: language toggle both directions, every `data-zh`/`data-en` pair switching, `?lang=` deep link, form submit, no console exceptions. Two things that silently break:

- **Call the language applier unconditionally on first load**, not only when the saved/incoming language differs from the HTML default — otherwise a page authored in Chinese but intended to open in English shows the Chinese fallback text until someone clicks the toggle. Resolve precedence as **URL param → localStorage → HTML default**: if the remembered toggle wins over `?lang=`, the deep link is dead and every "EN mode" screenshot quietly comes back Chinese.
- **Expose the composed URL before navigating** (`window.__lastMailto = url`) so a mailto/checkout handler is assertable; `window.location.href` cannot be stubbed.

Scan for translation leaks by walking leaf elements for `/[\u4e00-\u9fa5]/` in EN mode — it catches half-translated copy and CJK accidentally embedded in `data-en` values.

### 6. Ship

**Ongoing maintenance is part of the delivery.** Chris expects the agent to own both the site and its daily content updates, not just the first launch. Set up a credentialled publish path so updates never need his browser again: a RAM sub-account with `AliyunOSSFullAccess` only, AccessKey JSON in `~/.hermes-secrets/`, `ossutil` (or `oss2`) uploading `--update` from the site directory, wrapped in one `publish.sh` per site. Then a content update is: edit the HTML/Markdown, run the script, verify the live URL.

Beware: the OSS **console** can return `AccessDenied (ecCode 0003-00000905)` on bucket detail pages even for the account root, while list pages and re-login still work — this is a console/role problem, not a credentials problem. Do not burn turns re-authenticating; go straight to the API/CLI path with an AccessKey, which is unaffected.

The console's **绑定域名** button fails the same way, so bind the custom domain over the API instead:

1. `POST /<bucket>/?cname&comp=token` with `<BucketCnameConfiguration><Cname><Domain>www.example.com</Domain></Cname></BucketCnameConfiguration>` → returns `<Token>` (valid ~3 days, `ExpireTime` in the response).
2. Have the user add `TXT _dnsauth.www = <token>` and `CNAME www → <bucket>.<endpoint>`; a conflicting `A` record for `www` must be deleted first or the CNAME cannot be created.
3. `POST /<bucket>/?cname&comp=add` with the same body → 200 means bound. Without the TXT step it answers `NeedVerifyDomainOwnership`. A 200 on the bind is not proof of a working site — check `curl -sS -o /dev/null -w '%{http_code}' https://www.<domain>/` after propagation, then open the live URL in the headless harness, not localhost.

If DNS sits in the same account, ask for `AliyunDNSFullAccess` on the RAM user as well — then the whole bind (TXT, CNAME, deleting the dead A record) is one agent-side script and the user never enters the console.

Give the user the decision, with the trade-off in one line each (full table in `references/hosting-and-dns-cn.md`):

- **Aliyun OSS + CDN static hosting** — fastest in China, needs the ICP备案号 to bind the domain.
- **Cloudflare Pages / Netlify / Vercel** — no 备案, fast for overseas agents, slower but usable in China.
- **Aliyun OSS in a Hong Kong region** — no ICP备案 needed to bind the custom domain, mainland access far better than a free overseas CDN, and everything stays inside the cloud account the user already owns. The default when the account is Aliyun but has no 备案.

Before promising "put it on the server you already have", inventory the account: ECS / 轻量应用服务器 (SWAS) lists **per region** (a dashboard resource count of "1 ECS" can be an empty region, a security group, or a stale entry — open the region's instance list and read `共 N 条`), and the 备案 console's 可备案实例 page. No 备案-eligible instance means mainland hosting is a multi-day 备案接入 project, not an afternoon job — say that before touching DNS.

Ship the asset-sync steps in the site README (bucket, static-index settings, custom domain, free certificate) and the DNS step that removes the dead A record. Writing to the user's cloud account or changing DNS needs their explicit go-ahead and their own logged-in session; if the browser is blocked, ask them to quit Chrome and drive their session, or hand them a click-by-click list.

### 7. Report

Paths, what the two sites are (design stance + why), the diagnosis of the old site, and the blockers as a short list (备案号, mailbox for a new domain, real photos). Offer the two decisions that are actually the user's: omit-or-include the sensitive product copy, and which host.

## Pitfalls

- Asking for domain and purpose, then stalling when the answer does not come: a company site's structure is inferable from the dossier. Pick the obvious positioning, build it, and label the assumption.
- A bilingual toggle that only fires on change leaves the fallback language on screen. Apply on load, every load.
- Long unbreakable CTA strings (WhatsApp numbers) blow out mobile width far more often than Chinese body text does.
- Chinese headline size chosen for desktop wraps a 12-character line onto a third line with an orphaned character — cap the clamp maximum and eyeball the rendered line count (`h1.getBoundingClientRect().height / lineHeight`).
- Parallel screenshot jobs on one tab return N copies of the same image; and a shared Chrome profile carries `localStorage` between jobs, so clear origin storage before each navigation or half the runs show the previous language.
- **HTTPS on a bound OSS custom domain is the step that strands the delivery.** Aliyun's free DV quota is typically exhausted (`InsufficientQuota` from `cas.aliyuncs.com`, Version 2020-04-07 — the *version* is `2020-04-07`, not the 2018 one, or you get `InvalidVersion`), and `curl https://get.acme.sh` from this network returns a ~1 KB error page instead of the ~40 KB installer, so Let's Encrypt is not reachable in one hop either. Say plainly that plain HTTP is live and working, then offer the two real options — buy a DV certificate, or move the zone's NS to Cloudflare for permanent auto-renewed SSL plus CDN — and warn that the NS move must rebuild MX/SPF/DKIM/DMARC first or the company mailbox dies with the switch. If the user picks Cloudflare, drive it by API rather than by hand, but get the token shape right — it needs **Zone → Edit (create)**, a zone is created with the account id in the request body, and `/user/tokens/verify` reports a valid account-scoped token as invalid (test it on `/zones` instead). Recipe in `references/hosting-and-dns-cn.md`. Do not let the missing padlock read as "the site is not finished".
- Placeholder 备案号 on a live site is a legal problem, not a cosmetic one; it belongs in the README blocker list, not only in the HTML comment.
- **Do not promise a `trycloudflare` quick tunnel as a phone preview.** `brew install cloudflared` succeeds (ghcr.io bottle, works despite github.com being blocked), the connector registers, but the `*.trycloudflare.com` name resolves only intermittently from mainland China and HTTP returns 000 — the user sees a dead link. Preview locally (launcher `index.html` + `python3 -m http.server`), and get a real URL by deploying to the chosen host instead.
- The user's own Chrome holds the profile's Login Data lock, so `browser_exec` with `use_real_profile` fails outright. Screenshot and smoke-test with an independent headless Chrome (`--user-data-dir=/tmp/chrome-*`) rather than asking them to quit the browser.
- **A screenshot that still shows the old copy may be a cache, not a failed fix.** The harness's Chrome profile caches `assets/app.js`; call `Network.setCacheDisabled` (or append a `?v=` query) before concluding a patch did not take. Re-reading correct code because of a stale frame burns whole rounds.
- **Do not diagnose a freshly activated cloud product as broken configuration.** Immediately after enabling OSS/buckets, list pages render while inner pages can answer `AccessDenied` (`ecCode 0003-00000905`) — that is session/permission propagation, not your bucket. Re-check the authenticated session before re-creating resources; re-created buckets leave orphans that cost money and confuse the next session.
- **Read the OSS 403 code before touching anything.** `SecondLevelDomainForbidden` = path-style `/<bucket>/<key>` was used instead of `<bucket>.<endpoint>/<key>` (virtual-hosted is mandatory); `SignatureDoesNotMatch` = wrong string-to-sign — the canonical resource carries the bucket (`/<bucket>/<key>`) while the HTTP path does not, and every `x-oss-*` request header must be prepended as canonicalized OSS headers; `AccessDenied` with a `PolicyType` field (`You are forbidden to oss:ListBuckets`) = the RAM policy, not the signature. Each of these needs a different fix; guessing re-signs the request for twenty turns.
- **`Put public object acl is not allowed` is the fresh-bucket block, not a permission bug.** New buckets ship with 阻止公共访问 on, so every object-level `x-oss-object-acl: public-read` upload fails while `PUT /?website` still returns 200. Turn the toggle off in the console (or upload without per-object ACL and set bucket ACL afterwards) — an API-only publish cannot get past it on its own.
- **The Cloudflare cutover has three steps that silently break mail.** (1) The scanned import marks `mail`/`imap`/`pop3`/`smtp` CNAMEs as **proxied (orange)** — patch each to `{"proxied": false}` before the NS swap or mail clients stop connecting (MX records import grey, the CNAMEs do not). (2) With an http-only origin such as OSS, set `/zones/{id}/settings/ssl` to `flexible`; `full` returns 522/526. (3) The NS change is the user's to make, and **verify it against a public resolver plus a liveness probe**, never a bare local `dig` — the local resolver keeps serving the old NS set from cache and reports a phantom rollback, which sent both parties chasing a change that had already worked. Query `dig +short NS <domain> @8.8.8.8`, then `dig +short A www.<domain> @8.8.8.8` and `curl -o /dev/null -w '%{http_code}' http://www.<domain>/`: edge IPs plus a 200 mean the cutover is done regardless of what the local resolver says. Expect `https` to answer `000` for 5–30 minutes while the edge certificate is issued — HTTP up and HTTPS not yet is the normal middle state; say so before the user sees it, or they will ask to roll back. Zones also cannot be created by a token lacking `Zone → Edit (create)`, and `/user/tokens/verify` rejects a perfectly good account-scoped token, so test permissions against `/zones`.
- Do not restate the group's org chart or certification list from memory — the dossier is the single source, and a wrong WCA ID on a company site is a business problem.

## Support files

- `scripts/cdp_shot.py` — full-page desktop/mobile screenshots + DOM assertions over CDP, launches its own headless Chrome.
- `scripts/oss_publish.py` — stdlib-only Aliyun OSS publisher (V1 signature, virtual-hosted): uploads a site directory and enables static website hosting; the console-free replacement for the click-path when the API path is the only one that works.
- `scripts/oss_bind_domain.py` — two-phase custom-domain binding over the same API: `token` prints the exact TXT/CNAME rows for the user to paste, `bind` retries until ownership propagates, `check` does the outside-in http/https probe. Use it instead of retyping the signing code when the console's 绑定域名 button answers `AccessDenied`.
- `references/bilingual-zh-en-site.md` — the two-language single-page pattern, code and pitfalls.
- `references/hosting-and-dns-cn.md` — host decision table (incl. the Hong Kong no-备案 route), ICP rules, DNS diagnosis, and the verified Aliyun console click-path (login iframes, OSS activation, bucket creation, `AccessDenied` symptom).
