#!/usr/bin/env python3
"""Reverte baseUrl da key Nous para a API direta + deleta todas as threads do agente."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const out = {};
  // 1. reverter key para Nous direta
  try {
    const kr = await fetch('http://127.0.0.1:8999/key');
    const key = (await kr.text()).trim();
    const apiKeyJson = JSON.stringify({ baseUrl: 'https://inference-api.nousresearch.com/v1', apiKey: key });
    const r = await fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_UPDATE', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ keyId: 'aik_UmNW3ZTgwKtWK6sHwiTRv', apiKey: apiKeyJson })
    });
    out.revert = r.status;
  } catch(e) { out.revertErr = e.message; }
  // 2. listar threads
  try {
    const r2 = await fetch('/api/ubuntu-local/tools/COLLECTION_THREADS_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    const d2 = await r2.json();
    out.threads = (d2.items||[]).map(t => ({id:t.id, title:(t.title||'').slice(0,40), vmcp:t.virtual_mcp_id}));
  } catch(e) { out.threadsErr = e.message; }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[rv] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        print("[rv]", page.evaluate(JS))
    except Exception as e:
        print("[rv] eval fail:", e)
    ctx.close()
print("[rv] fim")
