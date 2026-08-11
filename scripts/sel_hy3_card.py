#!/usr/bin/env python3
"""Seleciona hy3: busca, fecha popover de detalhes, clica no role=option exato."""
import os, time, json, sys
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

CARD = sys.argv[1] if len(sys.argv) > 1 else "Rápido"

def log(m): print(f"[h3] {m}", flush=True)

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
    # abre o card
    safe_eval(page, """() => {
        const rows = Array.from(document.querySelectorAll('div.flex.items-center.gap-3.px-4.py-4'));
        const row = rows.find(r => { const l = r.querySelector('div.text-sm.font-medium'); return l && l.textContent.trim() === 'CARD'; });
        if (row) { const b = row.querySelector('button'); if (b) b.click(); }
    }""".replace("CARD", CARD))
    time.sleep(4)
    # busca hy3
    try:
        page.fill('[role=dialog] input[placeholder]', 'hy3')
    except Exception as e:
        log(f"fill: {e}")
    time.sleep(4)
    # fecha popover de detalhes se abrir (botão Close)
    safe_eval(page, """() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const b = btns.find(x => /^Close$/i.test((x.textContent||'').trim()) && x.offsetParent !== null);
        if (b) { b.click(); return 'closed'; }
        return 'no popover';
    }""")
    time.sleep(1)
    # clica no role=option com texto exatamente 'hy3' (não hy3-preview)
    r = safe_eval(page, """() => {
        const dlg = document.querySelector('[role=dialog]');
        if (!dlg) return 'no dialog';
        const opts = Array.from(dlg.querySelectorAll('[role=option]'));
        const el = opts.find(o => (o.textContent||'').trim() === 'hy3');
        if (el) { el.click(); return 'clicked option hy3'; }
        // fallback: texto próprio
        const els = Array.from(dlg.querySelectorAll('*'));
        const el2 = els.find(e => {
            const own = Array.from(e.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
            return own === 'hy3';
        });
        if (el2) {
            let t = el2;
            for (let i = 0; i < 6; i++) {
                if (t.getAttribute('role') === 'option' || t.tagName === 'BUTTON' || (t.className||'').toString().includes('cursor')) break;
                t = t.parentElement; if (!t) break;
            }
            t.click();
            return 'clicked via texto: ' + t.tagName;
        }
        return 'nao achou; opts=' + opts.map(o=>(o.textContent||'').trim().slice(0,20)).join('|');
    }""")
    log(f"clique: {r}")
    time.sleep(5)
    st = safe_eval(page, """() => {
        const rows = Array.from(document.querySelectorAll('div.flex.items-center.gap-3.px-4.py-4'));
        const row = rows.find(r => { const l = r.querySelector('div.text-sm.font-medium'); return l && l.textContent.trim() === 'CARD'; });
        if (!row) return 'row sumiu';
        const b = row.querySelector('button');
        return b ? (b.textContent||'').trim() : 'sem botao';
    }""".replace("CARD", CARD))
    log(f"card {CARD} agora: {st}")
    page.screenshot(path=f"/tmp/hy3_{CARD}.png")
    ctx.close()
log("fim")
