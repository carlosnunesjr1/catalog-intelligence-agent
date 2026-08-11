#!/usr/bin/env python3
"""Remove o provider OpenCode Go duplicado (aik_W3Gk) via AI_PROVIDER_KEY_DELETE."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[del] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

DUP_KEY_ID = "aik_W3GkalkEmlPseuqyslsRj"  # OpenCode Go duplicado (21:21)

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/settings/ai-providers",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    # DELETE do provider duplicado
    res = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_DELETE', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({keyId: 'KID'})});
        return {status: r.status, body: await r.text()};
    }""".replace("KID", DUP_KEY_ID), None)
    print("[del] RESULTADO:", json.dumps(res, ensure_ascii=False, default=str)[:400])
    time.sleep(2)
    # lista keys restantes
    keys = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_LIST', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
        return await r.json();
    }""", None)
    if keys:
        print("[del] KEYS RESTANTES:", json.dumps([k.get('label') for k in keys.get('keys', [])], ensure_ascii=False))
    ctx.close()
log("fim")
