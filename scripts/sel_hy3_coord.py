#!/usr/bin/env python3
"""Seleciona hy3 clicando por coordenadas do item na lista."""
import os, time, json, sys
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

CARD = sys.argv[1] if len(sys.argv) > 1 else "Rápido"

def log(m): print(f"[c3] {m}", flush=True)

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
    for i in range(10):
        time.sleep(4)
        n = safe_eval(page, "document.querySelectorAll('button').length", 0)
        if n >= 10:
            break
    time.sleep(2)
    safe_eval(page, """() => {
        const rows = Array.from(document.querySelectorAll('div.flex.items-center.gap-3.px-4.py-4'));
        const row = rows.find(r => { const l = r.querySelector('div.text-sm.font-medium'); return l && l.textContent.trim() === 'CARD'; });
        if (row) { const b = row.querySelector('button'); if (b) b.click(); }
    }""".replace("CARD", CARD))
    time.sleep(4)
    try:
        page.fill('[role=dialog] input[placeholder]', 'hy3')
    except Exception as e:
        log(f"fill: {e}")
    time.sleep(4)
    # pega coordenadas do item hy3 (o que tem texto próprio exato, ou span com texto)
    coords = safe_eval(page, """() => {
        const dlg = document.querySelector('[role=dialog]');
        if (!dlg) return null;
        // procura o span com texto hy3 (o primeiro, nao hy3-preview)
        const spans = Array.from(dlg.querySelectorAll('span, div'));
        const el = spans.find(s => {
            const own = Array.from(s.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
            return own === 'hy3';
        }) || spans.find(s => (s.textContent||'').trim() === 'hy3' && s.offsetParent !== null);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), tag: el.tagName};
    }""", None)
    log(f"coords hy3: {json.dumps(coords, ensure_ascii=False)}")
    if coords:
        page.mouse.click(coords['x'], coords['y'])
        log(f"click em ({coords['x']}, {coords['y']})")
        time.sleep(5)
    st = safe_eval(page, """() => {
        const rows = Array.from(document.querySelectorAll('div.flex.items-center.gap-3.px-4.py-4'));
        const row = rows.find(r => { const l = r.querySelector('div.text-sm.font-medium'); return l && l.textContent.trim() === 'CARD'; });
        if (!row) return 'row sumiu';
        const b = row.querySelector('button');
        return b ? (b.textContent||'').trim() : 'sem botao';
    }""".replace("CARD", CARD))
    log(f"card {CARD} agora: {st}")
    page.screenshot(path=f"/tmp/c3_{CARD}.png")
    ctx.close()
log("fim")
