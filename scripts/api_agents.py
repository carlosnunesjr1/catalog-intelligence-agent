#!/usr/bin/env python3
"""Lista agentes da org via API para achar o Catalog Enricher."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[ag] {m}", flush=True)

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
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/settings/agents",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    # lista de agentes via API (tenta endpoint conhecido)
    agents = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/AGENT_LIST', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
        return {status: r.status, body: await r.text()};
    }""", None)
    print("[ag] AGENT_LIST:", json.dumps(agents, ensure_ascii=False, default=str)[:1500])
    ctx.close()
log("fim")
