#!/usr/bin/env python3
"""GET do agente Catalog Enricher — ver config atual."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[get] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

AGENT_ID = "vir_DQ0xQ6tuzlqTQPZ2zKTJ-"

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    res = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_GET', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: 'AID'})});
        return {status: r.status, body: await r.text()};
    }""".replace("AID", AGENT_ID), None)
    body = res.get('body','') if isinstance(res, dict) else str(res)
    # mascara e mostra trechos-chave
    import re
    body_masked = re.sub(r'(sk-[A-Za-z0-9]{6})[A-Za-z0-9]+', r'\\1...', body)
    print("[get] STATUS:", res.get('status') if isinstance(res, dict) else '?')
    print("[get] BODY (primeiros 1500):", body_masked[:1500])
    ctx.close()
log("fim")
