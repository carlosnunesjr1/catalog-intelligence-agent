#!/usr/bin/env python3
"""Extrai id/title dos agentes (foco: Catalog Enricher e Super Agent)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[vm2] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    res = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_LIST', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
        const d = await r.json();
        const items = d.items || [];
        return items.map(i => ({id: i.id, title: i.title, status: i.status, conns: (i.connections||[]).length}));
    }""", None)
    if res:
        print("[vm2] agentes:")
        for a in res:
            mark = " <<<" if "Catalog" in (a.get('title') or '') or "Super" in (a.get('title') or '') else ""
            print(f"  {a['title']} | {a['id']} | status={a['status']} | conns={a['conns']}{mark}")
    ctx.close()
log("fim")
