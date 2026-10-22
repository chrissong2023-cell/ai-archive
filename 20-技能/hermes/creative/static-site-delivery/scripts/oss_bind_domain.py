#!/usr/bin/env python3
"""Bind a custom domain to an Aliyun OSS bucket over the REST API — stdlib only.

    python3 oss_bind_domain.py token  <bucket> <domain> [endpoint]
    python3 oss_bind_domain.py bind   <bucket> <domain> [endpoint]
    python3 oss_bind_domain.py check  <domain>

Why this exists: the console's 绑定域名 button answers `AccessDenied` on bucket
pages even for the account root (console/role problem, not credentials), while
the API is unaffected. Usage is two-phase:

  1. `token` prints the TXT row the user must add, and the CNAME row too.
     The TXT host is `_dnsauth.<sub>` — `_dnsauth.www` for www.example.com,
     NOT the full FQDN (that produces _dnsauth.www.example.com.example.com).
  2. After the TXT is live (`dig +short TXT _dnsauth.www.<domain>`), run `bind`.
     `bind` before propagation answers `NeedVerifyDomainOwnership` — that is a
     waiting condition, so re-run it rather than re-issuing the token.

A conflicting A record on `www` blocks the new CNAME; the user has to delete
the old record before adding the CNAME. Binding returning 200 is not proof the
site serves: `check` does the outside-in HTTP probe (a 403 right after a 200
bind is propagation — re-check after a few seconds).
"""
import sys, json, base64, hmac, hashlib, re, subprocess, time
import urllib.request, urllib.error, email.utils
from pathlib import Path

AK = json.loads((Path.home() / ".hermes-secrets/aliyun-oss.json").read_text())


def call(verb, host, path, canonical, body=b"", ctype="application/xml"):
    """canonical carries the bucket AND the subresource; path is what goes on the wire."""
    date = email.utils.formatdate(usegmt=True)
    md5 = base64.b64encode(hashlib.md5(body).digest()).decode() if body else ""
    to_sign = f"{verb}\n{md5}\n{ctype}\n{date}\n{canonical}"
    sig = base64.b64encode(hmac.new(AK["access_key_secret"].encode(),
                                   to_sign.encode(), hashlib.sha1).digest()).decode()
    headers = {"Authorization": f"OSS {AK['access_key_id']}:{sig}", "Date": date,
               "Content-Type": ctype}
    if md5:
        headers["Content-MD5"] = md5
    req = urllib.request.Request(f"https://{host}{path}", data=body or None,
                                headers=headers, method=verb)
    try:
        r = urllib.request.urlopen(req, timeout=45)
        return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300].decode(errors="replace")


def main():
    mode, bucket, domain = sys.argv[1], sys.argv[2], sys.argv[3]
    endpoint = sys.argv[4] if len(sys.argv) > 4 else "oss-cn-hongkong.aliyuncs.com"
    host = f"{bucket}.{endpoint}"
    xml = (f'<BucketCnameConfiguration><Cname><Domain>{domain}</Domain></Cname>'
           '</BucketCnameConfiguration>').encode()

    if mode == "token":
        code, body = call("POST", host, "/?cname&comp=token",
                          f"/{bucket}/?cname&comp=token", xml)
        token = re.search(r"<Token>([^<]+)</Token>", body)
        if code != 200 or not token:
            print(f"token FAILED {code}: {body[:200]}")
            return
        sub = domain.split(".")[0] if not domain.startswith("www.") else "www"
        print(f"TXT   host=_dnsauth.{sub}   value={token.group(1)}")
        print(f"CNAME host={sub}            value={host}")
        print("add both in the registrar DNS, then run: bind")

    elif mode == "bind":
        for attempt in range(1, 4):
            code, body = call("POST", host, "/?cname&comp=add",
                              f"/{bucket}/?cname&comp=add", xml)
            print(f"bind attempt {attempt}: {code} {body[:160]}")
            if code == 200:
                break
            if "NeedVerifyDomainOwnership" not in body:
                return
            time.sleep(20)
        print(subprocess.run(["curl", "-sS", "-m", "25", "-o", "/dev/null",
                              "-w", "http=%{http_code}", f"http://{domain}/"],
                             capture_output=True, text=True).stdout)

    elif mode == "check":
        for scheme in ("http", "https"):
            print(scheme, subprocess.run(["curl", "-sS", "-m", "25", "-o", "/dev/null",
                                          "-w", "%{http_code}", f"{scheme}://{domain}/"],
                                         capture_output=True, text=True).stdout)


if __name__ == "__main__":
    main()
