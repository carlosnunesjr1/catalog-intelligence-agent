#!/usr/bin/env python3
"""Tenta setar stepfun/step-3.7-flash:free nos tiers via ORGANIZATION_SETTINGS_UPDATE."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[st2] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

NOUS_KEY_ID = "aik_UmNW3ZTgwKtWK6sHwiTRv"
MODEL = "stepfun/step-3.7-flash:free"

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    js = """() => fetch('/api/ubuntu-local/tools/ORGANIZATION_SETTINGS_UPDATE', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            organizationId: 'GShn2ZDUQucdGifMjSjxmSPdO2Ap0Dev',
            simple_mode: {
                tiers: {
                    fast: {keyId: 'KID', modelId: 'MODEL', title: 'MODEL'},
                    smart: {keyId: 'KID', modelId: 'MODEL', title: 'MODEL'},
                    thinking: {keyId: 'KID', modelId: 'MODEL', title: 'MODEL'},
                    image: null, web_search: null, deep_research: null
                }
            }
        })
    }).then(r => r.text())""".replace("KID", NOUS_KEY_ID).replace("MODEL", MODEL)
    try:
        result = page.evaluate(js)
        print("[st2] UPDATE:", result[:400])
    except Exception as e:
        log(f"evaluate: {e}")
    time.sleep(2)
    # verifica
    try:
        cur = page.evaluate("""() => fetch('/api/ubuntu-local/tools/ORGANIZATION_SETTINGS_GET', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}).then(r => r.json())""")
        tiers = cur.get('simple_mode', {}).get('tiers', {})
        print("[st2] tiers:", json.dumps({k: v.get('modelId') if v else None for k, v in tiers.items()}, ensure_ascii=False))
    except Exception as e:
        log(f"verifica: {e}")
    ctx.close()
log("fim")
