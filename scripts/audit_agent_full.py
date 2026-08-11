#!/usr/bin/env python3
"""Auditoria completa do agente Catalog Enricher via API — para identificar melhorias."""
import os, time, json, re
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[aud] {m}", flush=True)

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

    # 1. config do agente
    agent = safe_eval(page, """() => fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_GET', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: 'AID'})}).then(r => r.json())""".replace("AID", AGENT_ID), None)
    if agent and 'item' in agent:
        it = agent['item']
        print("[aud] AGENTE:")
        print("  title:", it.get('title'))
        print("  description:", str(it.get('description'))[:60])
        print("  icon:", it.get('icon'))
        print("  status:", it.get('status'))
        print("  connections:", len(it.get('connections') or []))
        for c in (it.get('connections') or []):
            print("    - conn:", c.get('connection_id'), "| selected_tools:", c.get('selected_tools') or "TODAS")
        ins = (it.get('metadata') or {}).get('instructions', '')
        print("  instructions len:", len(ins))
        print("  instructions (primeiros 200):", ins[:200].replace("\n", " "))
        runtime = (it.get('metadata') or {}).get('runtime') or {}
        print("  runtime env vars:", len(runtime.get('env') or []))

    # 2. org settings (modelos)
    org = safe_eval(page, """() => fetch('/api/ubuntu-local/tools/ORGANIZATION_SETTINGS_GET', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}).then(r => r.json())""", None)
    if org:
        tiers = org.get('simple_mode', {}).get('tiers', {})
        print("[aud] MODELOS (org):")
        for k, v in tiers.items():
            print(f"  {k}: {v.get('modelId') if v else 'null'}")

    # 3. keys
    keys = safe_eval(page, """() => fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_LIST', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}).then(r => r.json())""", None)
    if keys:
        print("[aud] KEYS:")
        for k in keys.get('keys', []):
            print(f"  {k.get('label')} ({k.get('id','')[:8]}...) provider={k.get('providerId')}")

    ctx.close()
log("fim")
