#!/usr/bin/env python3
"""Troca os tiers do Studio para poolside/laguna-s-2.1:free (estável) via fetch mesma-origem."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const r = await fetch('/api/ubuntu-local/tools/ORGANIZATION_SETTINGS_UPDATE', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      organizationId: 'GShn2ZDUQucdGifMjSjxmSPdO2Ap0Dev',
      simple_mode: { tiers: {
        fast:     { keyId: 'aik_UmNW3ZTgwKtWK6sHwiTRv', modelId: 'poolside/laguna-s-2.1:free', title: 'poolside/laguna-s-2.1:free' },
        smart:    { keyId: 'aik_UmNW3ZTgwKtWK6sHwiTRv', modelId: 'poolside/laguna-s-2.1:free', title: 'poolside/laguna-s-2.1:free' },
        thinking: { keyId: 'aik_UmNW3ZTgwKtWK6sHwiTRv', modelId: 'poolside/laguna-s-2.1:free', title: 'poolside/laguna-s-2.1:free' },
        image: null, web_search: null, deep_research: null
      }}
    })
  });
  const d = await r.json();
  return JSON.stringify({status:r.status, body: JSON.stringify(d).slice(0,300)});
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[tiers] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            n = page.evaluate("document.querySelectorAll('button').length")
            if n > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        out = page.evaluate(JS)
        print("[tiers] RESULT:", out)
    except Exception as e:
        print("[tiers] eval fail:", e)
    ctx.close()
print("[tiers] fim")
