#!/usr/bin/env python3
"""Troca TODOS os cards para hy3 (Nous grátis) via busca do dialog — método validado com minimax."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[hy] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

MODELO = "hy3"
CARDS = ["Rápido", "Inteligente", "Reflexivo"]

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
    for card in CARDS:
        r = safe_eval(page, """() => {
            const rows = Array.from(document.querySelectorAll('div.flex.items-center.gap-3.px-4.py-4'));
            const row = rows.find(r => { const l = r.querySelector('div.text-sm.font-medium'); return l && l.textContent.trim() === 'CARD'; });
            if (!row) return 'row not found';
            const b = row.querySelector('button');
            if (b) { b.click(); return 'aberto'; }
            return 'sem botao';
        }""".replace("CARD", card))
        log(f"[{card}] abrir: {r}")
        time.sleep(4)
        try:
            page.fill('[role=dialog] input[placeholder]', MODELO)
            log(f"[{card}] digitou {MODELO}")
        except Exception as e:
            log(f"[{card}] fill: {e}")
        time.sleep(4)
        # descreve o que apareceu
        info = safe_eval(page, """() => {
            const dlg = document.querySelector('[role=dialog]');
            if (!dlg) return 'no dialog';
            const out = [];
            dlg.querySelectorAll('*').forEach(e => {
                const own = Array.from(e.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
                if (own && own.length < 60 && out.length < 20) out.push({tag: e.tagName, own});
            });
            return out;
        }""", [])
        # acha o item exato 'hy3' (não hy3-preview)
        r = safe_eval(page, """() => {
            const dlg = document.querySelector('[role=dialog]');
            if (!dlg) return 'no dialog';
            const els = Array.from(dlg.querySelectorAll('*'));
            const el = els.find(e => {
                const own = Array.from(e.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
                return own === 'hy3';
            });
            if (!el) return 'texto hy3 nao achado';
            let t = el;
            for (let i = 0; i < 6; i++) {
                if (t.getAttribute('role') === 'option' || t.tagName === 'BUTTON' || (t.className||'').toString().includes('cursor')) break;
                t = t.parentElement; if (!t) break;
            }
            t.click();
            return 'clicked: ' + t.tagName;
        }""")
        log(f"[{card}] clique hy3: {r}")
        time.sleep(5)
        st = safe_eval(page, """() => {
            const rows = Array.from(document.querySelectorAll('div.flex.items-center.gap-3.px-4.py-4'));
            const row = rows.find(r => { const l = r.querySelector('div.text-sm.font-medium'); return l && l.textContent.trim() === 'CARD'; });
            if (!row) return 'row sumiu';
            const b = row.querySelector('button');
            return b ? (b.textContent||'').trim() : 'sem botao';
        }""".replace("CARD", card))
        log(f"[{card}] agora: {st}")
    page.screenshot(path="/tmp/hy_final.png")
    ctx.close()
log("fim")
