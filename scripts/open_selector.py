#!/usr/bin/env python3
"""Abre o seletor de modelo do chat do agente e mostra o modelo ativo."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[sel] {m}", flush=True)

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(AGENT_URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 10:
                break
        except Exception:
            pass
    time.sleep(2)
    # clicar no botão do tier (Inteligente) para abrir o seletor
    try:
        r = page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(x => /Inteligente|Smart/i.test(x.textContent||''));
            if (b) { b.click(); return 'clicado: ' + b.textContent.trim(); }
            return 'nao achei';
        }""")
        log("tier: " + str(r))
    except Exception as e:
        log(f"click tier: {e}")
    time.sleep(5)
    # descrever o dialog/seletor
    try:
        info = page.evaluate("""() => {
            const dlg = document.querySelector('[role=dialog]');
            if (!dlg) return 'sem dialog';
            const texts = [];
            dlg.querySelectorAll('*').forEach(e => {
                const own = Array.from(e.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
                if (own && own.length < 80 && texts.length < 25) texts.push(own);
            });
            return texts;
        }""")
        log("dialog: " + str(info))
    except Exception as e:
        log(f"dialog: {e}")
    try:
        page.screenshot(path="/tmp/model_sel.png")
    except Exception:
        pass
    ctx.close()
log("fim")
