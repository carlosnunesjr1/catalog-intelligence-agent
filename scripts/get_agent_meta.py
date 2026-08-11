#!/usr/bin/env python3
"""Verifica metadata completa do agente (model override) + cria conversa nova."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const out = {};
  try {
    const r = await fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_GET', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id:'vir_DQ0xQ6tuzlqTQPZ2zKTJ-'})});
    const d = await r.json();
    const it = d.item || {};
    out.metadata = it.metadata;
    out.runtime = it.runtime;
  } catch(e) { out.err = e.message; }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[meta] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[meta]", page.evaluate(JS))
    except Exception as e:
        print("[meta] eval fail:", e)
    ctx.close()
print("[meta] fim")
