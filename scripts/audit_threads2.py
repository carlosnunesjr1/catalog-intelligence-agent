#!/usr/bin/env python3
"""Audita threads + prefs + tenta achar override de modelo do agente."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const out = {};
  try {
    const r = await fetch('/api/ubuntu-local/tools/COLLECTION_THREADS_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    const d = await r.json();
    out.threads = (d.items||[]).map(t => ({id:t.id, title:(t.title||'').slice(0,40), status:t.status, vmcp:t.virtual_mcp_id, updated:t.updated_at}));
  } catch(e) { out.threadsErr = e.message; }
  try {
    const r2 = await fetch('/api/ubuntu-local/tools/USER_MODEL_PREFERENCES_GET', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    out.prefs = await r2.json();
  } catch(e) { out.prefsErr = e.message; }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[thr2] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[thr2]", page.evaluate(JS))
    except Exception as e:
        print("[thr2] eval fail:", e)
    ctx.close()
print("[thr2] fim")
