#!/usr/bin/env python3
"""Atualiza a key Nous no Studio (key fresca do key_server) + verifica preview."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const out = {};
  try {
    const kr = await fetch('http://127.0.0.1:8999/key');
    const key = (await kr.text()).trim();
    const apiKeyJson = JSON.stringify({ baseUrl: 'https://inference-api.nousresearch.com/v1', apiKey: key });
    const r = await fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_UPDATE', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ keyId: 'aik_UmNW3ZTgwKtWK6sHwiTRv', apiKey: apiKeyJson })
    });
    out.update = {status: r.status, body: (await r.text()).slice(0,150)};
  } catch(e) { out.updateErr = e.message; }
  try {
    const r2 = await fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_PREVIEW', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({keyId:'aik_UmNW3ZTgwKtWK6sHwiTRv'})});
    out.preview = await r2.json();
  } catch(e) { out.previewErr = e.message; }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[upd] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[upd]", page.evaluate(JS))
    except Exception as e:
        print("[upd] eval fail:", e)
    ctx.close()
print("[upd] fim")
