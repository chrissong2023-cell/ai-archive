# Hosting a small site for a China-based company

## Diagnosing "the server expired"

```bash
whois <domain> | egrep -i "Registrar|Registration Time|Expiration|Name Server|Registrant"
dig +short NS <domain>; dig +short A <domain>; dig +short A www.<domain>
curl -sS -m 20 -o /dev/null -w "%{http_code} %{remote_ip}\n" https://<domain>/
done
```

Signature of a released server still in DNS: `dig` returns an IP, `curl`
exits 28 (timeout) and never gets an HTTP status. The domain is fine — the
A record points at a machine that no longer exists. Report the IP, note the
registrar and expiry, and plan a cutover instead of a renewal.

If `dig` returns nothing at all, the site was never published on this domain
(or the record was already deleted) — same conclusion, different sentence.

When several domains come in one batch, also read the registrar's 实名 state
for each: an `未实名` domain gets its resolution suspended on a deadline that
has nothing to do with the website work. Surface it in the first report — it
is the one item that silently takes a working site offline later.

## Host decision table

| Option | China speed | ICP备案 | Cost | Notes |
|---|---|---|---|---|
| Aliyun OSS static hosting, mainland region + CDN | fastest | **required** to bind the domain | pennies/month + ~0.2 CNY/GB | Bucket 公共读, 静态页面 index/error, bind custom domain, free cert |
| **Aliyun OSS, Hong Kong region** (`oss-cn-hongkong`) | good | **not required** for a custom domain | same order of magnitude | Same account, no 备案 project, better than a free overseas CDN from China; the default when the account is Aliyun with no 备案 |
| Cloudflare Pages | slow but reachable | not required | free | Best when the audience is overseas agents; needs NS moved to Cloudflare for a custom domain (and re-creating MX/TXT or mail breaks) |
| Netlify / Vercel | slow, often flaky | not required | free tier | CNAME works with the existing registrar DNS, no NS move |
| Existing web host / VPS | — | required if in mainland | — | Only if the user already pays for it |

Rules of thumb:

- Audience is domestic customers plus overseas agents → Aliyun OSS + CDN wins
  if the 备案 already exists.
- Audience is WCA/overseas agents only → overseas static host or the Hong Kong
  bucket, skip 备案 entirely, keep NS wherever they are.
- **Never buy a server for a brochure site.** Static hosting has no uptime bill
  and nothing to expire. If the user says "configure the server and publish",
  check first whether a server exists at all (see below) — the answer is often
  "you have none", and the right reply is static hosting, not a purchase.

## Inventory the cloud account before proposing a host

- ECS and 轻量应用服务器 (SWAS) consoles are **per-region**: the dashboard's
  "1 ECS" badge can be a security group, an empty region, or a stale entry.
  Open each region and read `共 0 条` from the instance table.
- The 备案 console's 可备案实例管理 page is the fastest answer to "can this
  account host in mainland at all": **no eligible instance = no 备案 path**, and
  a 备案-eligible instance needs a subscription of 3 months or more.
- 域名列表 in the domain console lists 持有者 and 实名 status; the 解析 entry on
  each row is where the A/CNAME cutover happens.

## ICP备案

- Required for any domain resolving to a mainland server **and 备案 is bound to
  the hosting provider**. A domain 备案'd under another cloud (the old server's
  IP often belongs to a different vendor) still needs 新增接入 at the new
  provider before port 80/443 serves on the mainland — plan days, not minutes.
  Hosting the site overseas (or in Hong Kong) sidesteps the whole thing.
- Footer format: `京ICP备XXXXXXXX号-1`, linked to `https://beian.miit.gov.cn`.
- Overseas-only hosting does not need it, but leaving a `待填` placeholder in
  the footer of a live site is a compliance problem, not a cosmetic one.

## Aliyun console click-path (verified)

Driving the console over CDP works, but the console fights naive automation.
These details are the difference between 4 calls and 40.

**Login.** `account.aliyun.com/login/login.htm` renders the form inside a
`passport.aliyun.com` iframe, so a top-level `document.querySelectorAll('input')`
returns `[]`. Navigate the tab straight to the iframe URL instead:

```
https://passport.aliyun.com/havanaone/login/login.htm?lang=zh_CN&appName=aliyun
  &appEntrance=aliyun_pc_pwd&styleType=vertical&notLoadSsoView=true&notKeepLogin=true
  &isMobile=false&returnUrl=https%3A%2F%2Fhome.console.aliyun.com%2Fhome%2Fdashboard%2FProductAndService
```

- Password entrance → `#fm-login-id` / `#fm-login-password`.
  `appEntrance=aliyun_pc_sms` → `#loginId` / `#smsCode` (phone + SMS code).
- Type the identifier with `fill_input`, then `browser_vault_save_login` so the
  password is entered in the masked prompt — never typed by the agent. A wrong
  password returns `密码错误` on the page; do not retry blindly (lockout risk),
  switch to the SMS entrance and ask for the code via `browser_vault_enter_code`.
- `browser_vault_enter_code` only finds fields it recognises: when it answers
  `no_code_field` on a hand-rolled form, tag the input first
  (`el.setAttribute('autocomplete','one-time-code'); el.setAttribute('name','otp')`)
  and call it again.

**Antd buttons swallow `.click()`.** `获取验证码`, `立即登录` and friends often do
nothing from JS. Click by viewport coordinates (`click_at_xy`) and re-read the
body text to confirm — a countdown (`58秒`) or a swapped panel is the proof.
A "最近登录" suggestion strip can appear after the code lands and push the
submit button down; re-screenshot before the second click.

**Region picker is virtualised.** Click the select, then find the `li` whose
text is the region and whose `offsetParent !== null`, and click that. Verify by
reading the endpoint string out of the DOM (`oss-cn-hongkong.aliyuncs.com` in
`document.body.innerText`), not by trusting the label you think you clicked.

**OSS activation.** `https://common-buy.aliyun.com/?commodityCode=oss#/open` →
tick the agreement checkbox (verify `input[type=checkbox].checked === true`) →
click 立即开通 → success lands on `cashier.aliyun.com/order/payNewSuccess`.
A bucket list that still says "您尚未开通对象存储服务 OSS" means the activation
click never registered, not that the account is blocked. Note that 立即开通
opens the purchase flow in a **new tab**: the console page you clicked from stays
byte-identical, so it reads as "the click did nothing". Enumerate
`cdp('Target.getTargets')` and drive the new target instead of clicking again.

**Bucket creation.** Bucket list → 创建 Bucket → `#name` → region → 完成创建 →
a second confirmation panel (`我知道了，确认创建`). New buckets default to
**阻止公共访问 开通**, which refuses the 公共读 ACL; the console says so —
create the bucket, then switch 阻止公共访问 off, then set 读写权限 公共读. If
the bucket list still shows 没有数据 afterwards, the creation did not go
through: re-open the dialog and confirm the region actually stuck before
submitting again.

**Symptoms that are not your bug.** A bucket's inner pages can answer
`AccessDenied` (`ecCode 0003-00000905`, `AccessDenied`) while the list page is
fine, right after a first-time activation. Treat it as session/permission
propagation: re-authenticate and re-check before changing configuration or
re-creating anything.

## OSS REST API publishing (no console)

When the console refuses bucket pages, the REST API still works with a RAM
AccessKey (`AliyunOSSFullAccess`, secret in `~/.hermes-secrets/`, chmod 600).
`scripts/oss_publish.py` implements this; the four rules it encodes:

1. **Virtual-hosted addressing is mandatory.** `PUT https://<bucket>.<endpoint>/<key>`;
   any `/<bucket>/<key>` path on the regional endpoint returns
   `403 SecondLevelDomainForbidden`.
2. **CanonicalizedResource keeps the bucket, the URL does not.** Sign against
   `/<bucket>/<key>`, send to `/<key>`. Skipping the bucket in the signature (or
   leaving it in the path) returns `403 SignatureDoesNotMatch`.
3. **`x-oss-*` headers join the string-to-sign** as lowercased
   `key:value\n` lines, sorted, inserted directly before the canonical resource.
   Omit them and every object PUT fails on a signature mismatch while
   header-free calls succeed — the confusing split that wastes the most time.
4. **Subresources stay in the canonical resource.** `PUT /?website` with
   `<WebsiteConfiguration>` sets index and error document in one call (verified
   200); `?acl`, `?blockPublicAccess` follow the same shape.

Object uploads additionally need the bucket's 阻止公共访问 switched off — a
fresh bucket answers `AccessDenied: Put public object acl is not allowed` to any
public-read object PUT even when the signature and policy are correct.

Status codes worth distinguishing: `403 SignatureDoesNotMatch` = signing;
`403 AccessDenied` with `<PolicyType>` = RAM policy missing; `409
BucketAlreadyExists` = the request was interpreted as a bucket create (bad
subresource form); `200` on `?website` = hosting enabled, so the credential and
signing chain are already proven.

**Least-privilege policy set for owning the site end to end.** Ask once, for a
RAM user (never the root account's AccessKey) carrying exactly:

| Policy | Needed for |
|---|---|
| `AliyunOSSFullAccess` | upload, static hosting, bind domain, read traffic |
| `AliyunDNSFullAccess` | TXT/CNAME records, deleting the dead A record, sub-domains |
| `AliyunYundunCertFullAccess` | free certificate + HTTPS |
| `AliyunCDNFullAccess` | CDN in front, http→https redirect |

Nothing else — refuse `AdministratorAccess`, ECS, RAM and billing. Say out loud
that a leaked key can then reach only these buckets and records, which is what
makes the request easy to approve. With OSS-only the publish works but the
domain still cannot be bound: `?cname&comp=token` returns a `<Token>` (verified
200, `ExpireTime` about three days out) and the user must hand-add the TXT
record — with `AliyunDNSFullAccess` the whole bind is one agent-side script.

## Cloudflare: the HTTPS escape hatch when Aliyun certs are unavailable

When the Aliyun free-DV quota is exhausted (`InsufficientQuota`) and the ACME
installer will not download, moving the zone to Cloudflare buys permanent
auto-renewed SSL plus CDN on the free plan. The API path works; the traps are
in token shape and route shape.

- **Verify the token against a resource endpoint, not `/user/tokens/verify`.**
  An account-scoped token answers `6003 Invalid request headers` → `6111 Invalid
  format for Authorization header` → `Invalid API Token` there while working
  perfectly on `/zones` and `/accounts`. Concluding "your token is wrong" from
  the verify endpoint sends the user round a pointless token-rebuild loop.
- **Create a zone with `POST /zones` and the account in the body:**
  `{"name": "<domain>", "account": {"id": "<account_id>"}}`. Using the
  placeholder account variable (`organization`) gives `Invalid account
  identifier`; `POST /accounts/<id>/zones` gives `Could not route ... No route
  for that URI`. The account id is the hex segment in the dashboard URL
  (`dash.cloudflare.com/<account_id>/...`).
- **The token must carry Zone → Zone → Edit (create), not just DNS Write +
  Zone Settings Write + Cache Purge.** Without it every create answers `Requires
  permission "com.cloudflare.api.account.zone.create"`. Adding the zone by hand
  in the dashboard is the faster workaround than rebuilding the token.
- **Token creation itself fails until the account email is confirmed** —
  `Please verify your email` on the create screen is an inbox task for the user,
  not a permission choice; tell them to click the Cloudflare mail and retry the
  same screen rather than reselecting scopes.
- Read the existing records out of the registrar *before* any NS move and
  recreate MX/SPF/DKIM/DMARC first: `alidns.aliyuncs.com` `DescribeDomainRecords`
  (Version `2015-01-09`) dumps them in one call with `AliyunDNSFullAccess`.

### Handing the NS change off

The one action the agent cannot perform — the registrar requires the holder.
Give it as a click path, because "change your nameservers" is where this user
stalls:

> 域名控制台 → 域名列表 → the row's **管理** → **DNS 修改** (some builds:
> 修改 DNS 服务器) → 自定义 DNS → paste the two `*.ns.cloudflare.com` lines →
> 提交 → **refresh and confirm the NS column itself now shows Cloudflare**.

- 解析设置 (records) and DNS 修改 (nameservers) are adjacent and look alike; editing
  records changes nothing about the cutover. Two rounds were lost to this.
- "好了" is not evidence. One domain silently stayed on `dnsNN.hichina.com`
  through two confirmations. Check before replying, and never re-diagnose from
  the local resolver: `dig @223.5.5.5 NS` can still hand back the old set after
  the change saved, so it reads as an unexplained rollback.

```bash
dig +short NS  <domain>              @8.8.8.8     # authoritative view
 dig +short A  www.<domain>          @8.8.8.8     # edge IPs once live
curl -sS -m 20 -o /dev/null -w '%{http_code}\n' http://www.<domain>/
```

- Expected mid-cutover state: `http` 200, `https` 000 until the edge certificate
  is issued (minutes to about half an hour). Announce that window up front, or
  the user interprets it as a broken switch and asks to roll back to the old NS.
- Rollback is cheap and always available: keep the registry's original NS values
  written down before the change so a real failure is a one-line revert.

## Cutover steps

1. Upload `index.html` + `assets/` + `robots.txt` + `sitemap.xml` (keep the
   directory shape so the relative `assets/` links resolve).
2. Enable static website hosting: default index `index.html`, error document
   `index.html` (single-page sites 404 politely this way).
3. Bind `www.<domain>` and the apex; add the CNAME/A record the console gives.
4. **Delete the dead A record** and any old `www` record pointing at the
   released IP — leaving it means one of the two names stays dark.
5. Issue the free certificate and force HTTPS.
6. Verify from outside: `curl -sSI https://www.<domain>/` returns 200 with the
   right `content-type`, then re-run the screenshot harness against the live
   URL, not just localhost.
7. Submit `sitemap.xml` in Baidu 站长平台 (domestic) and Google Search Console
   (overseas) if the site needs to rank.

## Mail

A new domain has no mailbox. Before publishing `info@<newdomain>` as the
contact, either confirm the mailbox exists or use the address that does.
Opening Aliyun 企业邮箱 / 邮件推送 for the domain is a two-step console job —
flag it as a launch blocker rather than shipping a dead address.
