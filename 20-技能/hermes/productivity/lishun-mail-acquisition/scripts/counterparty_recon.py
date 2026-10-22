#!/usr/bin/env python3
"""Aggregate mail_facts.jsonl into a counterparty table (customer-pool recon).

Outputs:
  - top counterparties by volume
  - dormant candidates (30-365 days since last contact)
  - CSV at ~/AI工作台/00-总控/STATE/customers.csv

No third-party deps. Reads only.
"""
import csv
import collections
import datetime
import json
import os
import sys

FACTS = os.path.expanduser('~/AI工作台/00-总控/STATE/mail_facts.jsonl')
OUT = os.path.expanduser('~/AI工作台/00-总控/STATE/customers.csv')

OWN = {
    'lslogistics.com.cn', 'cbloom.com.cn', 'wlnexus.com', 'mindaidata.com',
    'nva-ai.com', 'bytime.ai',
}
FREE = {
    '163.com', '126.com', 'qq.com', 'gmail.com', 'outlook.com', 'hotmail.com',
    'yahoo.com', 'foxmail.com', 'aliyun.com',
}
# Carriers / settlement platforms: operational, not customers.
PLATFORM = {'fedex.com', 'casslink2.iata.org', 'iata.org', 'dhl.com', 'ups.com'}


def parse_date(s):
    s = (s or '').strip()
    for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            d = datetime.datetime.strptime(s, fmt)
            return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
    return None


def main():
    if not os.path.exists(FACTS):
        sys.exit(f'no facts file: {FACTS}')
    now = datetime.datetime.now(datetime.timezone.utc)
    agg = collections.defaultdict(lambda: {
        'n': 0, 'last': None, 'first': None,
        'cats': collections.Counter(), 'subj': '', 'acct': collections.Counter(),
    })

    total = 0
    for line in open(FACTS, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        dom = (r.get('from_domain') or '').lower().strip()
        if not dom or dom in OWN or dom in FREE:
            continue
        a = agg[dom]
        a['n'] += 1
        a['acct'][r.get('account') or '?'] += 1
        a['cats'][r.get('category') or ''] += 1
        d = parse_date(r.get('date'))
        if d:
            if a['last'] is None or d > a['last']:
                a['last'] = d
                a['subj'] = (r.get('subject') or '')[:60]
            if a['first'] is None or d < a['first']:
                a['first'] = d

    rows = []
    for dom, a in agg.items():
        days = (now - a['last']).days if a['last'] else 9999
        kind = 'platform' if dom in PLATFORM else 'counterparty'
        rows.append({
            'domain': dom,
            'emails': a['n'],
            'days_since': days,
            'last_contact': a['last'].strftime('%Y-%m-%d') if a['last'] else '',
            'first_contact': a['first'].strftime('%Y-%m-%d') if a['first'] else '',
            'category': a['cats'].most_common(1)[0][0] if a['cats'] else '',
            'accounts': '/'.join(k for k, _ in a['acct'].most_common()),
            'last_subject': a['subj'].replace('\n', ' '),
            'kind': kind,
        })
    rows.sort(key=lambda x: (-x['emails'], x['days_since']))

    print(f'facts={total}  counterparties={sum(1 for r in rows if r["kind"] == "counterparty")}')
    print('\n=== top 15 ===')
    for r in rows[:15]:
        print(f"  {r['domain']:34s} {r['emails']:4d}  最近{r['days_since']:4d}d  "
              f"[{r['accounts']:10s}] {r['last_subject'][:48]}")

    dormant = [r for r in rows
               if r['kind'] == 'counterparty' and 30 <= r['days_since'] <= 365]
    print(f'\n=== dormant 30-365d: {len(dormant)} ===')
    for r in dormant[:20]:
        print(f"  {r['domain']:34s} {r['emails']:4d}  {r['days_since']:4d}d  {r['last_subject'][:50]}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ['domain'])
        w.writeheader()
        w.writerows(rows)
    print(f'\nCSV -> {OUT}  ({len(rows)} rows)')


if __name__ == '__main__':
    main()
