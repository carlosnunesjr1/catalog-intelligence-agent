#!/usr/bin/env python3
"""Verifica se poolside/laguna-s-2.1:free está no catálogo de modelos da key Nous via API."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const r = await fetch('/api/ubuntu-local/tools/AI_PROVIDERS_LIST_MODELS', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({keyId:'aik_UmNW3ZTgwKtWK6sHwiTRv'})});
  const d = await r.json();
  const models = d.models || [];
  const wanted = models.filter(m => /poolside|laguna|stepfun|hy3/i.test(m.modelId));
  return JSON.stringify(wanted.map(m => ({modelId: m.modelId, ctx: m.limits && m.limits.contextWindow, out: m.limits && m.limits.maxOutputTokens})));
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[cat] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[cat]", page.evaluate(JS))
    except Exception as e:
        print("[cat] eval fail:", e)
    ctx.close()
print("[cat] fim")
