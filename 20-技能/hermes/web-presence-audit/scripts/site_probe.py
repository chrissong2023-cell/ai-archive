#!/usr/bin/env python3
"""Probe a list of domains: DNS, HTTP/HTTPS status, body size, title, SPA-shell hint.

Usage: python3 site_probe.py a.com b.com [--json out.json] [--ports]
  --ports  also test 22/80/443 on the resolved IP (single-IP triage)

Stdlib only. Read-only GETs, 15s timeout, one request per scheme/site.
"""
import json
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/155.0 Safari/537.36')
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def resolve(host):
    try:
        return sorted({ai[4][0] for ai in socket.getaddrinfo(host, None)})
    except socket.gaierror:
        return []


def port_open(ip, port, timeout=4):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            raw = r.read()
            return r.status, len(raw), raw.decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, 0, ''
    except Exception as e:  # noqa: BLE001 - report, do not crash the batch
        return 0, 0, f'ERR:{type(e).__name__}:{str(e)[:50]}'


def probe(host, check_ports=False):
    ips = resolve(host)
    out = {'domain': host, 'ips': ips, 'schemes': {}, 'ports': {}}
    for scheme in ('http', 'https'):
        code, size, body = fetch(f'{scheme}://{host}/')
        title = ''
        if body and not body.startswith('ERR:'):
            m = re.search(r'<title[^>]*>(.*?)</title>', body, re.S | re.I)
            title = re.sub(r'\s+', ' ', m.group(1)).strip()[:90] if m else ''
        shell = bool(code == 200 and 0 < size < 2048 and '<script' in body.lower())
        out['schemes'][scheme] = {'status': code, 'bytes': size,
                                  'title': title, 'spa_shell': shell,
                                  'err': body if body.startswith('ERR:') else ''}
    if check_ports and ips:
        ip = ips[0]
        out['ports'] = {p: port_open(ip, p) for p in (22, 80, 443)}
    return out


def verdict(r):
    h, s = r['schemes'].get('http', {}), r['schemes'].get('https', {})
    ports, ips = r.get('ports') or {}, r['ips']
    if not ips:
        return 'DNS 解析失败'
    if ports and not any(ports.values()):
        return '机器/防火墙不可达（端口全关）'
    if s.get('status') in (502, 503, 504):
        return 'Web 服务挂了（端口通、上游 502）→ 重启 nginx/应用'
    if s.get('status') == 200 and h.get('status') == 200 and h.get('bytes', 0) > 0 and s.get('bytes', 0) == 0:
        return 'HTTPS 不通（443/证书未配）'
    if s.get('status') == 200 and s.get('spa_shell'):
        return f'JS 壳：HTML 仅 {s["bytes"]}B，爬虫读不到内容'
    if s.get('status') == 200:
        return '正常'
    if h.get('status') == 200:
        return '只有 HTTP 可用'
    return '不可用'


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    check_ports = '--ports' in sys.argv
    jpath = None
    if '--json' in sys.argv:
        jpath = sys.argv[sys.argv.index('--json') + 1]
        args = [a for a in args if a != jpath]

    results = []
    for host in args:
        r = probe(host, check_ports)
        r['verdict'] = verdict(r)
        results.append(r)
        h, s = r['schemes']['http'], r['schemes']['https']
        print(f"{host:28s} http={h['status']:<4d}{h['bytes']:>7d}B  "
              f"https={s['status']:<4d}{s['bytes']:>7d}B  {r['verdict']}")
        if s.get('title'):
            print(f"{'':28s} title: {s['title']}")
        if r['ports']:
            print(f"{'':28s} ip={r['ips'][0]} ports="
                  f"{ {p: ('open' if v else 'closed') for p, v in r['ports'].items()} }")

    if jpath:
        with open(jpath, 'w', encoding='utf-8') as fh:
            json.dump(results, fh, ensure_ascii=False, indent=2)
        print(f'\njson -> {jpath}')

    shared = {tuple(r['ips']): [x['domain'] for x in results if r['ips']] for r in results}
    for ips, doms in shared.items():
        if len(doms) > 1:
            print(f"\n⚠️ 同 IP 单点故障 {ips[0]}: {', '.join(doms)}")


if __name__ == '__main__':
    main()
