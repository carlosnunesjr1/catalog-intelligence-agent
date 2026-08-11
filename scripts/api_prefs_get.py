#!/usr/bin/env python3
"""Testa USER_MODEL_PREFERENCES_UPDATE via API direta (fetch mesma origem)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[api] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

NOUS_KEY_ID = "aik_UmNW3ZTgwKtWK6sHwiTRv"

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/settings/ai-providers",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    # 1. GET atual
    cur = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/USER_MODEL_PREFERENCES_GET', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
        return await r.json();
    }""", None)
    print("[api] GET atual:", json.dumps(cur, ensure_ascii=False, default=str)[:800])
    ctx.close()
log("fim")
