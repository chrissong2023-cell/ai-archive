#!/usr/bin/env python3
"""Publish a static site directory to an Aliyun OSS bucket — stdlib only.

    python3 oss_publish.py <site_dir> <bucket> [endpoint_host]
    python3 oss_publish.py ./lslogistics.com.cn lslogistics-web oss-cn-hongkong.aliyuncs.com

Credentials: ~/.hermes-secrets/aliyun-oss.json with access_key_id /
access_key_secret (RAM user holding AliyunOSSFullAccess only; chmod 600).

Four rules make OSS V1 signing work, and this file encodes all of them:

  1. Virtual-hosted addressing only — https://<bucket>.<endpoint>/<key>.
     Path-style /<bucket>/<key> on the regional endpoint answers
     403 SecondLevelDomainForbidden.
  2. CanonicalizedResource carries the bucket (/<bucket>/<key>) while the
     HTTP path never does (/<key>). Mixing them up = SignatureDoesNotMatch.
  3. Every x-oss-* request header must be prepended to the canonical resource
     as lowercased 'key:value' lines, sorted. Omitting them makes object PUTs
     fail on signature while header-free calls (like ?website) succeed.
  4. Subresources (?website, ?acl) stay in the canonical resource.

KNOWN GATE: a freshly created bucket has 阻止公共访问 ON, which rejects any
object PUT carrying x-oss-object-acl: public-read with
'AccessDenied: Put public object acl is not allowed' — even with a correct
signature and AliyunOSSFullAccess. The console must switch it off first
(data safety -> block public access). The ?website call below succeeds
regardless, which is the cheapest proof that credentials and signing are fine.
"""
import sys, json, base64, hmac, hashlib, mimetypes, urllib.request, urllib.error, email.utils
from pathlib import Path

AK = json.loads((Path.home() / ".hermes-secrets/aliyun-oss.json").read_text())
CT = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
      ".js": "application/javascript; charset=utf-8", ".xml": "application/xml",
      ".txt": "text/plain; charset=utf-8", ".png": "image/png", ".jpg": "image/jpeg",
      ".svg": "image/svg+xml", ".ico": "image/x-icon", ".json": "application/json"}


def call(verb, host, path, canonical, body=b"", ctype="", extra=None):
    date = email.utils.formatdate(usegmt=True)
    md5 = base64.b64encode(hashlib.md5(body).digest()).decode() if body else ""
    oss_hdrs = "".join(f"{k.lower()}:{v}\n" for k, v in sorted((extra or {}).items())
                       if k.lower().startswith("x-oss-"))
    to_sign = f"{verb}\n{md5}\n{ctype}\n{date}\n{oss_hdrs}{canonical}"
    sig = base64.b64encode(hmac.new(AK["access_key_secret"].encode(),
                                    to_sign.encode(), hashlib.sha1).digest()).decode()
    headers = {"Authorization": f"OSS {AK['access_key_id']}:{sig}", "Date": date}
    if ctype:
        headers["Content-Type"] = ctype
    if md5:
        headers["Content-MD5"] = md5
    if extra:
        headers.update(extra)
    req = urllib.request.Request(f"https://{host}{path}", data=(body or None),
                                 headers=headers, method=verb)
    try:
        r = urllib.request.urlopen(req, timeout=90)
        return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:240].decode(errors="replace").replace("\n", " ")


def main():
    site = Path(sys.argv[1]).expanduser().resolve()
    bucket = sys.argv[2]
    host = f"{bucket}.{sys.argv[3] if len(sys.argv) > 3 else 'oss-cn-hongkong.aliyuncs.com'}"

    files = [p for p in site.rglob("*") if p.is_file()
             and p.name not in ("README.md", "publish.py", "oss_publish.py")]
    ok = 0
    for p in sorted(files):
        rel = p.relative_to(site).as_posix()
        ctype = CT.get(p.suffix.lower()) or mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        code, err = call("PUT", host, f"/{rel}", f"/{bucket}/{rel}", p.read_bytes(), ctype,
                         {"x-oss-object-acl": "public-read"})
        print(f"{'OK ' if code == 200 else 'ERR'} {rel:28} {code} {err[:150]}")
        ok += code == 200

    xml = ('<?xml version="1.0" encoding="UTF-8"?><WebsiteConfiguration>'
           '<IndexDocument><Suffix>index.html</Suffix></IndexDocument>'
           '<ErrorDocument><Key>index.html</Key></ErrorDocument></WebsiteConfiguration>').encode()
    code, err = call("PUT", host, "/?website", f"/{bucket}/?website", xml, "application/xml")
    print(f"{'OK ' if code == 200 else 'ERR'} website-hosting               {code} {err[:150]}")

    code, body = call("GET", host, "/index.html", f"/{bucket}/index.html")
    print(f"{'OK ' if code == 200 else 'ERR'} verify GET /index.html        {code}")
    print(f"done {ok}/{len(files)} files; live check: https://{host}/index.html")


if __name__ == "__main__":
    main()
