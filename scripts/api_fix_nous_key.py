#!/usr/bin/env python3
"""Corrige a key Nous: AI_PROVIDER_KEY_UPDATE com apiKey como JSON string {baseUrl, apiKey}."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[fx] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

NOUS_KEY_ID = "aik_UmNW3ZTgwKtWK6sHwiTRv"
import json as _json
auth = _json.load(open(os.path.expanduser('~/.hermes/auth.json')))
key = (auth.get('providers', {}).get('nous', {}).get('agent_key') or '').strip()
# formato correto: apiKey é um JSON STRING aninhado com baseUrl + apiKey
api_key_json = _json.dumps({"baseUrl": "https://inference-api.nousresearch.com/v1", "apiKey": key})
log(f"apiKey json len={len(api_key_json)}")

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    js = """(apiKeyJson) => fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_UPDATE', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({keyId: 'KID', apiKey: apiKeyJson})
    }).then(r => r.text())""".replace("KID", NOUS_KEY_ID)
    try:
        result = page.evaluate(js, api_key_json)
        print("[fx] UPDATE:", result[:400])
    except Exception as e:
        log(f"evaluate: {e}")
    time.sleep(2)
    ctx.close()
log("fim")
