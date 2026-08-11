#!/usr/bin/env python3
"""Deleta as threads grandes do Catalog Enricher (zera contexto) e testa chat novo."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"
THREADS = ["96674168-d7b7-4c88-a100-54d20f122b69", "32155bf9-1196-4a33-8213-ae9745550506"]

JS_DEL = """async (tid) => {
  const r = await fetch('/api/ubuntu-local/tools/COLLECTION_THREAD_DELETE', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({id: tid})});
  return {status: r.status, body: (await r.text()).slice(0,200)};
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[del] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    for tid in THREADS:
        try:
            out = page.evaluate(JS_DEL, tid)
            print("[del]", tid, "->", out)
        except Exception as e:
            print("[del]", tid, "eval fail:", e)
    # lista threads restantes
    try:
        out = page.evaluate("""async () => {
          const r = await fetch('/api/ubuntu-local/tools/COLLECTION_THREADS_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
          const d = await r.json();
          return (d.items||[]).map(t => ({id:t.id, title:(t.title||'').slice(0,40), vmcp:t.virtual_mcp_id}));
        }""")
        print("[del] restantes:", json.dumps(out, ensure_ascii=False))
    except Exception as e:
        print("[del] list fail:", e)
    ctx.close()
print("[del] fim")
