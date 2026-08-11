#!/usr/bin/env python3
"""Verifica as mensagens da thread atual do agente (tamanho real)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const out = {};
  try {
    const r = await fetch('/api/ubuntu-local/tools/COLLECTION_THREADS_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    const d = await r.json();
    out.threads = (d.items||[]).map(t => ({id:t.id, title:(t.title||'').slice(0,40), vmcp:t.virtual_mcp_id}));
  } catch(e) { out.threadsErr = e.message; }
  // mensagens da thread do agente (a que tem vmcp vir_DQ0x)
  try {
    const r2 = await fetch('/api/ubuntu-local/tools/COLLECTION_THREADS_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    const d2 = await r2.json();
    const t = (d2.items||[]).find(x => x.virtual_mcp_id === 'vir_DQ0xQ6tuzlqTQPZ2zKTJ-');
    if (t) {
      const r3 = await fetch('/api/ubuntu-local/tools/COLLECTION_THREAD_MESSAGES_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({threadId: t.id})});
      const d3 = await r3.json();
      const msgs = d3.items || d3.messages || [];
      let total = 0;
      const roles = {};
      for (const m of msgs) {
        const c = JSON.stringify(m.content || m.message || '');
        total += c.length;
        roles[m.role || '?'] = (roles[m.role] || 0) + 1;
      }
      out.threadMsgs = {id: t.id, n: msgs.length, totalChars: total, roles};
    }
  } catch(e) { out.threadMsgsErr = e.message; }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[tm] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[tm]", page.evaluate(JS))
    except Exception as e:
        print("[tm] eval fail:", e)
    ctx.close()
print("[tm] fim")
