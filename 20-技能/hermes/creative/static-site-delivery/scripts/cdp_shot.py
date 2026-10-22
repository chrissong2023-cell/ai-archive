#!/usr/bin/env python3
"""Full-page + real-mobile screenshots and DOM assertions over CDP.

Why this exists: `chrome --headless --screenshot` clamps --window-size to a
500px minimum and captures the viewport only, so it cannot prove a 390px
layout or a whole long page. This drives CDP instead: device-metrics
emulation + captureBeyondViewport with a clip from Page.getLayoutMetrics.

Usage:
    python3 cdp_shot.py jobs.json
    python3 cdp_shot.py '[{"url":"http://127.0.0.1:8781/","out":"/tmp/a.png",
                          "width":1440,"height":900}]'
    python3 cdp_shot.py '[{"url":"http://127.0.0.1:8781/","out":"/tmp/m.png",
                          "width":390,"height":844,"mobile":true,
                          "eval":["document.title",
                                  "document.documentElement.scrollWidth - window.innerWidth"]}]'

Job fields: url, out, width (1280), height (900), mobile (false), full (true),
            wait (1.6s), clear (true = clear origin storage before load), eval ([]).

Jobs run SEQUENTIALLY on one tab: parallel jobs on one target capture the same
frame. Each job gets a fresh target and cleared origin storage, because
localStorage is per-profile and will otherwise leak language/theme state
between jobs and mislead the review.

Requires: python3 -m pip install websockets
"""
import asyncio
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

import websockets

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
]
DEFAULT_PORT = int(os.environ.get("CDP_PORT", "9333"))


def http_json(path, port, method="GET"):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method)
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read().decode("utf-8", "replace")
    return json.loads(body) if body.strip() else {}


def ensure_chrome(port):
    try:
        return http_json("/json/version", port)
    except Exception:
        pass
    binary = next((c for c in CHROME_CANDIDATES if os.path.exists(c) or c in ("google-chrome", "chromium")), None)
    if not binary:
        sys.exit("no Chrome/Chromium binary found; set one in CHROME_CANDIDATES")
    profile = "/tmp/chrome-cdp-profile"  # own profile: a running desktop Chrome holding the real one is irrelevant
    subprocess.Popen(
        [binary, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         f"--remote-debugging-port={port}", f"--user-data-dir={profile}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        time.sleep(0.5)
        try:
            return http_json("/json/version", port)
        except Exception:
            continue
    sys.exit(f"headless Chrome did not open a CDP port on {port}")


class Session:
    def __init__(self, ws):
        self.ws = ws
        self.id = 0
        self.exceptions = []

    async def call(self, method, **params):
        self.id += 1
        mid = self.id
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("method") == "Runtime.exceptionThrown":
                d = msg["params"]["exceptionDetails"]
                self.exceptions.append(d.get("text", "exception"))
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    async def evaluate(self, expr):
        r = await self.call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        res = r.get("result", {})
        return res.get("value", res.get("description"))


async def run_job(job, port):
    url = job["url"]
    out = job["out"]
    width = int(job.get("width", 1280))
    height = int(job.get("height", 900))
    mobile = bool(job.get("mobile", False))
    full = bool(job.get("full", True))
    wait = float(job.get("wait", 1.6))
    evals = job.get("eval", [])

    target = http_json("/json/new?about:blank", port, method="PUT")
    async with websockets.connect(target["webSocketDebuggerUrl"], max_size=2 ** 26) as ws:
        s = Session(ws)
        await s.call("Page.enable")
        await s.call("Runtime.enable")
        await s.call("Emulation.setDeviceMetricsOverride",
                     width=width, height=height, deviceScaleFactor=1, mobile=mobile)
        if mobile:
            await s.call("Emulation.setUserAgentOverride",
                         userAgent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                                    "Mobile/15E148 Safari/604.1"),
                         platform="iPhone")
        if job.get("clear", True):
            try:
                await s.call("Storage.clearDataForOrigin", origin=job.get("origin", url),
                             storageTypes="local_storage")
            except Exception:
                pass
        await s.call("Page.navigate", url=url)
        await asyncio.sleep(wait)

        if full:
            m = await s.call("Page.getLayoutMetrics")
            css = m.get("cssContentSize") or m.get("contentSize")
            w, h = int(css["width"]), int(css["height"])
            shot = await s.call("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                                clip={"x": 0, "y": 0, "width": w, "height": h, "scale": 1})
        else:
            w, h = width, height
            shot = await s.call("Page.captureScreenshot", format="png")
        with open(out, "wb") as f:
            f.write(base64.b64decode(shot["data"]))

        print(f"{out}  {w}x{h}  mobile={mobile}  {url}")
        for expr in evals:
            try:
                print(f"  eval[{expr[:60]}]: {await s.evaluate(expr)}")
            except Exception as e:
                print(f"  eval[{expr[:60]}]: ERROR {e}")
        if s.exceptions:
            print(f"  exceptions: {s.exceptions}")
    try:
        http_json(f"/json/close/{target['id']}", port)
    except Exception:
        pass


async def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    raw = argv[1]
    if os.path.exists(raw):
        raw = open(raw, encoding="utf-8").read()
    jobs = json.loads(raw)
    port = int(argv[2]) if len(argv) > 2 else DEFAULT_PORT
    ensure_chrome(port)
    for job in jobs:  # sequential on purpose
        await run_job(job, port)


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
