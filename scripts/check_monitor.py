#!/usr/bin/env python3
"""Verifica o Monitor do Studio — estatísticas de tool calls da connection."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[mon] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/settings/monitor?tab=overview&from=now-24h&to=now",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    info = safe_eval(page, """() => {
        const body = document.body.textContent || '';
        // procura números de tool calls / connections
        return {
            hasCatalog: /Catalog Intelligence Agent/.test(body),
            hasToolCalls: /Chamadas de ferramenta|Tool Calls|tool calls/i.test(body),
            sample: body.replace(/\\s+/g,' ').match(/.{0,60}(?:Catalog Intelligence Agent|Tool Calls|Chamadas de ferramenta|Latency|Tokens).{0,80}/gi) || []
        };
    }""", {})
    print("[mon] Catalog no monitor:", info.get('hasCatalog'))
    print("[mon] tem tool calls:", info.get('hasToolCalls'))
    print("[mon] amostras:", json.dumps(info.get('sample', [])[:6], ensure_ascii=False)[:900])
    page.screenshot(path="/tmp/monitor.png")
    ctx.close()
log("fim")
