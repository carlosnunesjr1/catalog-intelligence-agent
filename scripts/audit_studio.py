#!/usr/bin/env python3
"""Auditoria final do Studio: cards de modelo + providers conectados via API."""
import os, time, json, re
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[aud] {m}", flush=True)

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
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/settings/ai-providers",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    # cards de modelo
    cards = safe_eval(page, """() => {
        const rows = Array.from(document.querySelectorAll('div.flex.items-center.gap-3.px-4.py-4'));
        return rows.filter(r => {
            const l = r.querySelector('div.text-sm.font-medium');
            return l && /Rápido|Inteligente|Reflexivo/.test(l.textContent);
        }).map(r => {
            const l = r.querySelector('div.text-sm.font-medium');
            const b = r.querySelector('button');
            return {card: l.textContent.trim(), model: b ? b.textContent.trim() : ''};
        });
    }""", [])
    print("[aud] CARDS:", json.dumps(cards, ensure_ascii=False))
    # keys conectadas via API
    keys = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/AI_PROVIDER_KEY_LIST', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
        return await r.json();
    }""", None)
    if keys:
        klist = keys.get('keys', [])
        print("[aud] KEYS:", json.dumps([{'id': k.get('id','')[:8], 'label': k.get('label'), 'createdAt': k.get('createdAt','')[:16]} for k in klist], ensure_ascii=False))
    ctx.close()
log("fim")
