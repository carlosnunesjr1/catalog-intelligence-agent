#!/usr/bin/env python3
"""Verifica baseUrl atual da key Nous no Studio."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const r = await fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_PREVIEW', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({keyId:'aik_UmNW3ZTgwKtWK6sHwiTRv'})});
  return JSON.stringify(await r.json());
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[bv] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[bv]", page.evaluate(JS))
    except Exception as e:
        print("[bv] eval fail:", e)
    ctx.close()
print("[bv] fim")
