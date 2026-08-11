#!/usr/bin/env python3
"""Verifica se LIST_MODELS funciona com a key Nous atualizada (formato correto)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const out = {};
  for (const kid of ['aik_UmNW3ZTgwKtWK6sHwiTRv','aik_brVFNnuzbFnw1cEO1mtLu']) {
    try {
      const r = await fetch('/api/ubuntu-local/tools/AI_PROVIDERS_LIST_MODELS', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({keyId: kid})});
      const txt = await r.text();
      let parsed = null;
      try { parsed = JSON.parse(txt); } catch(e) {}
      out[kid] = {status: r.status, models: parsed && parsed.models ? parsed.models.length : null, err: parsed && parsed.error ? String(parsed.error).slice(0,150) : (txt.slice(0,120))};
    } catch(e) { out[kid] = {fetchErr: e.message}; }
  }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[lm] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[lm]", page.evaluate(JS))
    except Exception as e:
        print("[lm] eval fail:", e)
    ctx.close()
print("[lm] fim")
