#!/usr/bin/env python3
"""Configura os 3 default models para tencent/hy3:free (Nous) via ORGANIZATION_SETTINGS_UPDATE."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[upd] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

NOUS_KEY_ID = "aik_UmNW3ZTgwKtWK6sHwiTRv"
MODEL = "tencent/hy3:free"

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/settings/ai-providers",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    # UPDATE com os 3 tiers = hy3 via key Nous
    res = safe_eval(page, """async () => {
        const payload = {
            organizationId: 'GShn2ZDUQucdGifMjSjxmSPdO2Ap0Dev',
            simple_mode: {
                tiers: {
                    fast: {keyId: 'KID', modelId: 'MODEL', title: 'MODEL'},
                    smart: {keyId: 'KID', modelId: 'MODEL', title: 'MODEL'},
                    thinking: {keyId: 'KID', modelId: 'MODEL', title: 'MODEL'},
                    image: null,
                    web_search: null,
                    deep_research: null
                }
            }
        };
        const r = await fetch('/api/ubuntu-local/tools/ORGANIZATION_SETTINGS_UPDATE', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)});
        return {status: r.status, body: await r.text()};
    }""".replace("KID", NOUS_KEY_ID).replace("MODEL", MODEL), None)
    print("[upd] RESULTADO:", json.dumps(res, ensure_ascii=False, default=str)[:800])
    time.sleep(2)
    # verifica com GET
    cur = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/ORGANIZATION_SETTINGS_GET', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
        return await r.json();
    }""", None)
    if cur and 'simple_mode' in cur:
        print("[upd] VERIFICAÇÃO:", json.dumps(cur['simple_mode'], ensure_ascii=False, default=str)[:600])
    ctx.close()
log("fim")
