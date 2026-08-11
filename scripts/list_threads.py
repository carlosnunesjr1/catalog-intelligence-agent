#!/usr/bin/env python3
"""Lista conversas/threads do agente Catalog Enricher."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const out = {};
  const eps = ['COLLECTION_CHAT_THREADS_LIST','COLLECTION_THREADS_LIST','THREAD_LIST','COLLECTION_CHATS_LIST'];
  for (const ep of eps) {
    try {
      const r = await fetch('/api/ubuntu-local/tools/'+ep, {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
      const txt = await r.text();
      out[ep] = {status: r.status, body: txt.slice(0,600)};
    } catch(e) { out[ep] = {err: e.message}; }
  }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[thr] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[thr]", page.evaluate(JS))
    except Exception as e:
        print("[thr] eval fail:", e)
    ctx.close()
print("[thr] fim")
