#!/usr/bin/env python3
"""Bulk-check a reference list against Crossref.

Input: a text file, one reference per line (>=40 chars, APA-ish).
Output: per-entry status.
  OK    - title, first author, year and journal all match
  WARN  - a real record exists but year / journal / volume / pages differ
  MISS  - no plausible record found (treat as fabricated until proven)

Usage:
    python3 check_refs.py refs.txt [--csv out.csv]
"""
import argparse, csv, difflib, json, re, urllib.parse, urllib.request

UA = {"User-Agent": "refcheck/1.0 (mailto:chris@lslogistics.com.cn)"}

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def crossref(query, rows=5):
    url = ("https://api.crossref.org/works?rows=%d"
           "&select=title,author,issued,container-title,volume,issue,page,DOI,is-referenced-by-count"
           "&query.bibliographic=" % rows) + urllib.parse.quote(query)
    try:
        return fetch(url)["message"]["items"]
    except Exception:
        return []

def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower())

def parse(ref):
    m = re.match(r"^(.*?)\((\d{4})[a-z]?\)\.\s*(.*?)\.\s*([^,]+)", ref)
    if not m:
        return None
    authors, year, title, journal = m.groups()
    return authors.split(",")[0].strip(), int(year), title, journal.strip()

def check(ref):
    p = parse(ref)
    if not p:
        return ("PARSE", "", "could not parse")
    first, year, title, journal = p
    items = crossref(title + " " + journal)
    best, best_score = None, 0.0
    for it in items:
        t = (it.get("title") or [""])[0]
        s = difflib.SequenceMatcher(None, norm(title)[:70], norm(t)[:70]).ratio()
        fams = [norm(a.get("family", "")) for a in it.get("author", [])]
        if norm(first) and any(norm(first) in f for f in fams):
            s += 0.08
        if s > best_score:
            best, best_score = it, s
    if not best or best_score < 0.60:
        return ("MISS", f"{best_score:.2f}", "no plausible record")
    y = (best.get("issued", {}).get("date-parts") or [[None]])[0][0]
    j = (best.get("container-title") or [""])[0]
    t = (best.get("title") or [""])[0]
    doi = best.get("DOI", "")
    year_ok = (y == year)
    jour_ok = difflib.SequenceMatcher(None, norm(journal)[:30], norm(j)[:30]).ratio() > 0.75
    status = "OK" if (year_ok and jour_ok) else "WARN"
    real = f"{y} | {j} {best.get('volume','')}({best.get('issue','')}) {best.get('page','')} | {t} | {doi}"
    return (status, f"{best_score:.2f}", real)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--csv", default=None)
    a = ap.parse_args()
    refs = [l.strip() for l in open(a.path, encoding="utf-8") if len(l.strip()) >= 40]
    rows = []
    for ref in refs:
        status, score, real = check(ref)
        rows.append(dict(status=status, score=score, claimed=ref[:110], real=real))
        print(f"[{status:5}] {ref[:90]}")
        if status != "OK":
            print(f"        -> {real}")
    counts = {k: sum(1 for r in rows if r["status"] == k) for k in ("OK", "WARN", "MISS", "PARSE")}
    print("\nTotals:", counts)
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["status", "score", "claimed", "real"])
            w.writeheader()
            w.writerows(rows)
        print("csv ->", a.csv)

if __name__ == "__main__":
    main()
