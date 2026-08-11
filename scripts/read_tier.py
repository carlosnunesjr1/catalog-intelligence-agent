#!/usr/bin/env python3
"""Lê o modelo ativo no chat do agente (tier picker) + manda pedido de teste."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[tp] {m}", flush=True)

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
    # achar o botão do tier picker (Smart/Fast/Thinking) e o modelo ao lado
    try:
        info = page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const res = [];
            for (const b of btns) {
                const t = (b.textContent||'').trim();
                if (/Smart|Fast|Thinking|Rápido|Inteligente|Reflexivo/i.test(t) || /poolside|laguna|stepfun|hy3|deepseek|model/i.test(t)) {
                    res.push({text: t.slice(0,80), cls: (b.className||'').toString().slice(0,50)});
                }
            }
            return JSON.stringify(res.slice(0,10));
        }""")
        log("tiers: " + str(info))
    except Exception as e:
        log(f"tier read: {e}")
    # screenshot do chat
    try:
        page.screenshot(path="/tmp/tier_picker.png")
    except Exception:
        pass
    ctx.close()
log("fim")
