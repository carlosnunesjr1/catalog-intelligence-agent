#!/usr/bin/env python3
"""Aponta a key Nous do Studio para o proxy de interceptação (baseUrl 127.0.0.1:8998)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const out = {};
  try {
    const kr = await fetch('http://127.0.0.1:8999/key');
    const key = (await kr.text()).trim();
    const apiKeyJson = JSON.stringify({ baseUrl: 'http://127.0.0.1:8998/v1', apiKey: key });
    const r = await fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_UPDATE', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ keyId: 'aik_UmNW3ZTgwKtWK6sHwiTRv', apiKey: apiKeyJson })
    });
    out.update = {status: r.status, body: (await r.text()).slice(0,120)};
  } catch(e) { out.err = e.message; }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[px] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[px]", page.evaluate(JS))
    except Exception as e:
        print("[px] eval fail:", e)
    ctx.close()
print("[px] fim")
