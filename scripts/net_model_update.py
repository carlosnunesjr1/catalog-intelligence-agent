#!/usr/bin/env python3
"""Captura requests de rede ao selecionar modelo (minimax-m3) para descobrir o endpoint de update."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[net] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

captured = []
def on_request(req):
    url = req.url
    if "/api/" in url and any(k in url for k in ['MODEL', 'model', 'PROVIDER', 'provider']):
        try:
            captured.append({"m": req.method, "u": url.replace("https://deco-studio.173-249-43-230.sslip.io", ""), "b": (req.post_data or "")[:300]})
        except Exception:
            pass

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    page.on("request", on_request)
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
    # abre card Reflexivo (está em minimax-m3 — vamos trocar p/ hy3 e capturar o endpoint)
    safe_eval(page, """() => {
        const rows = Array.from(document.querySelectorAll('div.flex.items-center.gap-3.px-4.py-4'));
        const row = rows.find(r => { const l = r.querySelector('div.text-sm.font-medium'); return l && l.textContent.trim() === 'Reflexivo'; });
        if (row) { const b = row.querySelector('button'); if (b) b.click(); }
    }""")
    time.sleep(4)
    try:
        page.fill('[role=dialog] input[placeholder]', 'hy3')
    except Exception as e:
        log(f"fill: {e}")
    time.sleep(4)
    # tenta clicar no item hy3 (qualquer elemento com texto hy3, sem popover)
    r = safe_eval(page, """() => {
        const dlg = document.querySelector('[role=dialog]');
        if (!dlg) return 'no dialog';
        // procura o item da lista: div com role=option ou botão contendo texto hy3
        const candidates = Array.from(dlg.querySelectorAll('[role=option], button, div[class*=cursor], div[class*=item]'));
        const el = candidates.find(o => /^hy3$/.test((o.textContent||'').trim()) || ((o.textContent||'').trim() === 'hy3'));
        if (el) { el.click(); return 'clicked: ' + el.tagName; }
        return 'nao achou; cands=' + candidates.map(c=>(c.textContent||'').trim().slice(0,15)).join('|').slice(-150);
    }""")
    log(f"clique: {r}")
    time.sleep(6)
    ctx.close()
print("[net] CAPTURED:")
for c in captured:
    print("  ", json.dumps(c, ensure_ascii=False)[:350])
log("fim")
