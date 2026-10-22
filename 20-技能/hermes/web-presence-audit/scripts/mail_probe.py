#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mail_probe.py — 域名邮箱就绪度探针

做三件事：
  1. 查 A / MX / NS / SPF / DMARC（多解析器 + 权威 NS 复验）
  2. 查域名注册状态（whois Creation Date / Expiry）
  3. 用授权码去撞候选 IMAP 端点，靠错误串判定服务商

用法：
  python3 mail_probe.py example.com user@example.com
  python3 mail_probe.py example.com user@example.com --vault ~/.hermes-secrets/mail.json
  # vault 为 JSON，含 {"auth_code": "..."} 或 {"password": "..."}
  # 不给 --vault 且未设 MAIL_PROBE_CODE 环境变量时，只做 DNS/注册检查

输出最后的「该补哪些记录」表，可直接贴给用户。
"""
import argparse, json, os, re, socket, ssl, subprocess, sys, imaplib

HOSTS = [
    ("imap.qiye.aliyun.com", "阿里云企业邮"),
    ("imap.aliyun.com", "阿里云邮箱"),
    ("imap.mxhichina.com", "万网/阿里云"),
    ("imap.exmail.qq.com", "腾讯企业邮"),
    ("imap.qiye.163.com", "网易企业邮"),
]

PROVIDER_DNS = {
    "阿里云企业邮": {"mx": [("mx1.qiye.aliyun.com", 10), ("mx2.qiye.aliyun.com", 20)],
                 "spf": "v=spf1 include:spf.qiye.aliyun.com ~all"},
    "腾讯企业邮": {"mx": [("mxbiz1.qq.com", 5), ("mxbiz2.qq.com", 10)],
                "spf": "v=spf1 include:spf.mail.qq.com ~all"},
    "网易企业邮": {"mx": [("hzmx01.mxmail.netease.com", 5), ("hzmx02.mxmail.netease.com", 10)],
                "spf": "v=spf1 include:spf.163.com ~all"},
}


def dig(domain, rtype, server=None):
    cmd = ["dig", "+short", domain, rtype] + ([f"@{server}"] if server else [])
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
        return [l.strip() for l in out.splitlines() if l.strip()]
    except Exception:
        return []


def section(t):
    print("\n" + "=" * 62 + f"\n  {t}\n" + "=" * 62)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domain")
    ap.add_argument("address", nargs="?")
    ap.add_argument("--vault")
    a = ap.parse_args()
    d = a.domain.strip().lower()

    section(f"1. 解析  {d}")
    a_rec = dig(d, "A")
    ns = dig(d, "NS")
    mx = dig(d, "MX")
    spf = [t for t in dig(d, "TXT") if "spf" in t.lower()]
    dmarc = dig("_dmarc." + d, "TXT")
    print(f"  NS   : {', '.join(ns) or '（空）'}")
    print(f"  A    : {', '.join(a_rec) or '（空 → 网站不存在）'}")
    print(f"  MX   : {', '.join(mx) or '（空 → 外部邮件收不进来）'}")
    print(f"  SPF  : {', '.join(spf) or '（未配置）'}")
    print(f"  DMARC: {', '.join(dmarc) or '（未配置）'}")

    if not mx:
        print("  复验（排除缓存）：")
        for srv in ("119.29.29.29", "8.8.8.8", "1.1.1.1"):
            print(f"    @{srv:14s} MX = {', '.join(dig(d, 'MX', srv)) or '空'}")
        if ns:
            print(f"    @{ns[0]:14s} MX = {', '.join(dig(d, 'MX', ns[0].rstrip('.'))) or '空'}  ← 权威")

    section("2. 注册状态")
    try:
        w = subprocess.run(["whois", d], capture_output=True, text=True, timeout=20).stdout
        for k in ("Creation Date", "Registry Expiry", "Registrar:", "Domain Status"):
            for line in w.splitlines():
                if k.lower() in line.lower():
                    print("  " + line.strip()[:100]); break
    except Exception as e:
        print("  whois 不可用：", e)

    section("3. 服务商指纹（IMAP 登录试探）")
    code = os.environ.get("MAIL_PROBE_CODE")
    if a.vault and os.path.exists(os.path.expanduser(a.vault)):
        v = json.load(open(os.path.expanduser(a.vault)))
        code = v.get("auth_code") or v.get("password") or code
    if not a.address or not code:
        print("  跳过：需要 --vault（含 auth_code）或 MAIL_PROBE_CODE + 邮箱地址")
        provider = None
    else:
        provider = None
        for host, name in HOSTS:
            try:
                socket.create_connection((host, 993), timeout=8).close()
            except Exception:
                continue
            try:
                M = imaplib.IMAP4_SSL(host, 993, ssl_context=ssl.create_default_context())
                M.login(a.address, code)
                typ, _ = M.select("INBOX", readonly=True)
                n = len(M.search(None, "ALL")[1][0].split())
                print(f"  ✅ {host:26s} 登录成功 · INBOX {n} 封")
                M.logout(); provider = name; break
            except Exception as e:
                msg = str(e)[:90]
                print(f"  ✗  {host:26s} {msg}")
                if "LOGIN failed" in msg or "AUTHENTICATIONFAILED" in msg.upper():
                    provider = name  # 端点认这个域，只是凭据/开关不对
        if provider:
            print(f"\n  → 判定服务商：{provider}")
            print("  → 若登录被拒：先在后台开启 IMAP/SMTP 客户端服务，再生成『客户端专用密码』；")
            print("    用登录密码撞 IMAP 一定失败。")

    section("4. 该补的记录")
    rec = PROVIDER_DNS.get(provider or "")
    if not mx:
        if rec:
            for h, p in rec["mx"]:
                print(f"  MX   @  →  {h}  (优先级 {p})")
        else:
            print("  MX   @  →  <服务商 MX，先确认是哪家>")
    if not spf and rec:
        print(f"  TXT  @  →  {rec['spf']}")
    print("  TXT  default._domainkey  →  服务商后台生成的 DKIM")
    print(f"  TXT  _dmarc  →  v=DMARC1; p=none; rua=mailto:postmaster@{d}")
    if not a_rec:
        print("  A/CNAME www  →  官网主机")
    print("\n提醒：一个域名别开一堆独立收件箱；只留本人 + 自动化两个，其余转发。")


if __name__ == "__main__":
    main()
