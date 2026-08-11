#!/usr/bin/env python3
"""Pós-restart: verifica connection + keys + tiers, e testa chat."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[pr] {m}", flush=True)

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
PEDIDO = "Responda apenas: FUNCIONANDO"

JS = """async () => {
  const out = {};
  try {
    const r = await fetch('/api/ubuntu-local/tools/COLLECTION_CONNECTIONS_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    const d = await r.json();
    out.conns = (d.items||[]).map(c => ({id:c.id, title:c.title, slug:c.slug})).filter(c => /catalog/i.test(c.title+c.slug));
  } catch(e) { out.connsErr = e.message; }
  try {
    const r2 = await fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    const d2 = await r2.json();
    out.keys = (d2.keys||[]).map(k => ({id:k.id, label:k.label}));
  } catch(e) { out.keysErr = e.message; }
  try {
    const r3 = await fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_PREVIEW', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({keyId:'aik_UmNW3ZTgwKtWK6sHwiTRv'})});
    out.preview = await r3.json();
  } catch(e) { out.previewErr = e.message; }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io", wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    for i in range(15):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        log("STATE: " + str(page.evaluate(JS)))
    except Exception as e:
        log(f"state fail: {e}")
    # ir para o chat do agente e testar
    try:
        page.goto(AGENT_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO, delay=8)
        page.keyboard.press("Enter")
        log("pedido enviado")
    except Exception as e:
        log(f"chat: {e}")
    last = ""
    for i in range(25):
        time.sleep(8)
        try:
            txt = page.evaluate("""() => {
                const msgs = Array.from(document.querySelectorAll('[class*=message], [class*=bubble]'));
                return msgs.map(m => (m.textContent||'').trim()).filter(t => t.length > 2).join(' ||| ').slice(-600);
            }""")
        except Exception:
            txt = ""
        if txt and txt != last:
            last = txt
            log(f"t+{(i+1)*8}s: ...{last[-130:]}")
        if "FUNCIONANDO" in last:
            log("RESPOSTA OK")
            break
        if "Bad Request" in last or "Unauthorized" in last:
            log("ERRO")
            break
    print("[pr] RESPOSTA:", last[-300:] if last else "(vazia)")
    ctx.close()
log("fim")
