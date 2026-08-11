#!/usr/bin/env python3
"""Atualiza a key Nous no Studio via AI_PROVIDER_KEY_UPDATE (key atual do auth.json)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[kr] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

NOUS_KEY_ID = "aik_UmNW3ZTgwKtWK6sHwiTRv"
# key atual
import json as _json
auth = _json.load(open(os.path.expanduser('~/.hermes/auth.json')))
key = (auth.get('providers', {}).get('nous', {}).get('agent_key') or '').strip()
log(f"key atual len={len(key)} fim=...{key[-4:]}")

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    # UPDATE da key Nous
    js = """(k) => fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_UPDATE', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({keyId: 'KID', apiKey: k})
    }).then(r => r.text())""".replace("KID", NOUS_KEY_ID)
    try:
        result = page.evaluate(js, key)
        print("[kr] UPDATE:", result[:400])
    except Exception as e:
        log(f"evaluate: {e}")
    time.sleep(2)
    ctx.close()
log("fim")
