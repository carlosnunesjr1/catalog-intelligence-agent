#!/usr/bin/env python3
"""Configura o agente Catalog Enricher p/ stepfun/step-3.7-flash:free (Nous, visão grátis)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[sf] {m}", flush=True)

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
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    # 1. confirma que stepfun está no catálogo da key Nous
    models = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/AI_PROVIDERS_LIST_MODELS', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({keyId: 'KID'})});
        const d = await r.json();
        const ids = (d.models||[]).map(m => m.modelId);
        return {hasStepfun: ids.some(i => i.includes('stepfun')), ids: ids.slice(0, 40)};
    }""".replace("KID", NOUS_KEY_ID), None)
    print("[sf] modelos Nous:", json.dumps(models, ensure_ascii=False)[:500])
    ctx.close()
log("fim")
