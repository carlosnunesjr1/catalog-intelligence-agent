#!/usr/bin/env python3
"""Teste final: conversa limpa (threads deletadas) no Catalog Enricher."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[clean] {m}", flush=True)

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
PEDIDO = "Responda apenas: FUNCIONANDO"

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
    try:
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO, delay=8)
        page.keyboard.press("Enter")
        log("pedido enviado — aguardando...")
    except Exception as e:
        log(f"type: {e}")
    last = ""
    for i in range(30):
        time.sleep(8)
        try:
            txt = page.evaluate("""() => {
                const msgs = Array.from(document.querySelectorAll('[class*=message], [class*=bubble]'));
                return msgs.map(m => (m.textContent||'').trim()).filter(t => t.length > 2).join(' ||| ').slice(-800);
            }""")
        except Exception:
            txt = ""
        if txt and txt != last:
            last = txt
            log(f"t+{(i+1)*8}s: ...{last[-160:]}")
        if "Unauthorized" in last or "Bad Request" in last:
            log("ERRO_LLM")
            break
        if "FUNCIONANDO" in last:
            log("RESPOSTA OK")
            break
    try:
        page.screenshot(path="/tmp/chat_clean.png")
    except Exception:
        pass
    print("[clean] RESPOSTA:", last[-400:] if last else "(vazia)")
    ctx.close()
log("fim")
