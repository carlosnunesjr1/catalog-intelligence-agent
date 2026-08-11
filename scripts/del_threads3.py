#!/usr/bin/env python3
"""Deleta threads do agente de verdade — testa parâmetros corretos."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"
THREADS = ["ffce8de5-7639-492f-847a-26b94ebd7761", "30a72083-a608-4353-b7dd-99baa6f44b9c"]

JS = """async (tid) => {
  const out = {};
  const bodies = [{id: tid}, {threadId: tid}, {thread_id: tid}];
  for (let i = 0; i < bodies.length; i++) {
    try {
      const r = await fetch('/api/ubuntu-local/tools/COLLECTION_THREADS_DELETE', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify(bodies[i])});
      out['try'+i] = {status: r.status, body: (await r.text()).slice(0,80)};
    } catch(e) { out['try'+i] = {err: e.message}; }
  }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[d3] goto:", e)
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
            print("[d3]", tid, "->", page.evaluate(JS, tid))
        except Exception as e:
            print("[d3]", tid, "fail:", e)
    try:
        out = page.evaluate("""async () => {
          const r = await fetch('/api/ubuntu-local/tools/COLLECTION_THREADS_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
          const d = await r.json();
          return (d.items||[]).map(t => ({id:t.id, title:(t.title||'').slice(0,40), vmcp:t.virtual_mcp_id, status:t.status}));
        }""")
        print("[d3] restantes:", json.dumps(out, ensure_ascii=False))
    except Exception as e:
        print("[d3] list fail:", e)
    ctx.close()
print("[d3] fim")
