#!/usr/bin/env python3
"""Verifica qual modelo o chat do agente está usando (tier picker) e se aceita upload."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[tp] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception:
        return default

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(AGENT_URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    for i in range(10):
        time.sleep(4)
        n = safe_eval(page, "document.querySelectorAll('button').length", 0)
        if n > 10:
            break
    time.sleep(3)
    # procura o tier picker (Fast/Smart/Thinking) e o modelo atual
    info = safe_eval(page, """() => {
        const out = {buttons: []};
        document.querySelectorAll('button, [role=combobox]').forEach(b => {
            const t = (b.textContent||'').trim().replace(/\\s+/g,' ');
            if (/Fast|Smart|Thinking|Rápido|Inteligente|Reflexivo|deepseek|hy3|stepfun|minimax/i.test(t) && t.length < 60) {
                out.buttons.push(t.slice(0,50));
            }
        });
        // procura input de upload
        out.hasFileInput = !!document.querySelector('input[type=file]');
        return out;
    }""", {})
    print("[tp] tier picker/modelo:", json.dumps(info, ensure_ascii=False)[:600])
    page.screenshot(path="/tmp/tier_picker.png")
    ctx.close()
log("fim")
