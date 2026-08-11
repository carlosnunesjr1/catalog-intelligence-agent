#!/usr/bin/env python3
"""Aplica melhorias: stepfun nos tiers + description pt-BR."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[imp] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

NOUS_KEY_ID = "aik_UmNW3ZTgwKtWK6sHwiTRv"
AGENT_ID = "vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
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

    # 1. Tiers → stepfun (Nous grátis, visão)
    r1 = safe_eval(page, """() => fetch('/api/ubuntu-local/tools/ORGANIZATION_SETTINGS_UPDATE', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            organizationId: 'GShn2ZDUQucdGifMjSjxmSPdO2Ap0Dev',
            simple_mode: { tiers: {
                fast: {keyId: 'KID', modelId: 'MODEL', title: 'MODEL'},
                smart: {keyId: 'KID', modelId: 'MODEL', title: 'MODEL'},
                thinking: {keyId: 'KID', modelId: 'MODEL', title: 'MODEL'},
                image: null, web_search: null, deep_research: null
            }}
        })}).then(r => r.text())""".replace("KID", NOUS_KEY_ID).replace("MODEL", MODEL), None)
    print("[imp] tiers update:", "stepfun" in str(r1))

    # 2. Description pt-BR
    r2 = safe_eval(page, """() => fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_UPDATE', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: 'AID', data: {
            description: 'Agente de enriquecimento de catálogo para lojas próprias. Recebe dados brutos do ERP, link, EAN ou foto e devolve o produto pronto para publicar (título SEO, bullets, descrição, validação).',
            icon: 'icon://Tag?color=blue'
        }})}).then(r => r.text())""".replace("AID", AGENT_ID), None)
    print("[imp] description update:", "enriquecimento" in str(r2))

    time.sleep(2)
    # verifica
    org = safe_eval(page, """() => fetch('/api/ubuntu-local/tools/ORGANIZATION_SETTINGS_GET', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}).then(r => r.json())""", None)
    if org:
        tiers = org.get('simple_mode', {}).get('tiers', {})
        print("[imp] tiers agora:", {k: (v.get('modelId') if v else None) for k, v in tiers.items()})
    agent = safe_eval(page, """() => fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_GET', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: 'AID'})}).then(r => r.json())""".replace("AID", AGENT_ID), None)
    if agent and 'item' in agent:
        print("[imp] description agora:", str(agent['item'].get('description'))[:80])
        print("[imp] icon agora:", agent['item'].get('icon'))
    ctx.close()
log("fim")
