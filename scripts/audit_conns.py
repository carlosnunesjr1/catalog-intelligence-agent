#!/usr/bin/env python3
"""Audita: todas as connections + qual o agente usa + modelo real do tier."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"

JS = """async () => {
  const out = {};
  try {
    const r1 = await fetch('/api/ubuntu-local/tools/COLLECTION_CONNECTIONS_LIST', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    const d1 = await r1.json();
    const items = d1.items || d1.connections || [];
    out.connections = (Array.isArray(items)?items:[]).map(c => ({id:c.id, title:c.title, slug:c.slug, url:c.connection_url}));
  } catch(e) { out.connErr = e.message; }
  try {
    const r2 = await fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_GET', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id:'vir_DQ0xQ6tuzlqTQPZ2zKTJ-'})});
    const d2 = await r2.json();
    out.agentConnections = (d2.item||{}).connections;
  } catch(e) { out.agentErr = e.message; }
  try {
    const r3 = await fetch('/api/ubuntu-local/tools/ORGANIZATION_SETTINGS_GET', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    const d3 = await r3.json();
    out.tiers = (d3.simple_mode||{}).tiers;
  } catch(e) { out.tiersErr = e.message; }
  return JSON.stringify(out);
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[aud] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 5:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        out = page.evaluate(JS)
        print("[aud]", out)
    except Exception as e:
        print("[aud] eval fail:", e)
    ctx.close()
print("[aud] fim")
