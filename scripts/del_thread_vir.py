#!/usr/bin/env python3
"""Deleta thread do agente + lista threads restantes."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async (tid) => {
  const out = {};
  try {
    const r = await fetch('/api/ubuntu-local/tools/COLLECTION_THREADS_DELETE', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({id: tid})});
    out.del = r.status;
  } catch(e) { out.delErr = e.message; }
  try {
    const r2 = await fetch('/api/ubuntu-local/tools/COLLECTION_THREADS_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    const d2 = await r2.json();
    out.restantes = (d2.items||[]).map(t => ({id:t.id, title:(t.title||'').slice(0,40), vmcp:t.virtual_mcp_id}));
  } catch(e) { out.listErr = e.message; }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[dt] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[dt]", page.evaluate(JS, "30a72083-a608-4353-b7dd-99baa6f44b9c"))
    except Exception as e:
        print("[dt] eval fail:", e)
    ctx.close()
print("[dt] fim")
