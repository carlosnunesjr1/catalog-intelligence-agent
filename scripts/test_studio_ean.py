#!/usr/bin/env python3
"""Teste no Deco Studio: agente recebe EAN que pertence a OUTRO produto (papel sulfite)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[tst] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception:
        return default

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
PEDIDO = "Oi! Preciso de ajuda com um terno slim azul marinho da minha loja. O código de barras dele é 7891173025074. Pode verificar se esse código está correto e enriquecer o produto?"

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
    try:
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO, delay=6)
        page.keyboard.press("Enter")
        log("pedido enviado — aguardando resposta...")
    except Exception as e:
        log(f"type: {e}")
    # monitora até 180s
    last = ""
    for i in range(20):
        time.sleep(9)
        txt = safe_eval(page, """() => {
            const msgs = Array.from(document.querySelectorAll('[class*=message], [class*=bubble]'));
            return msgs.map(m => (m.textContent||'').trim()).filter(t => t.length > 25).join(' ||| ').slice(-1400);
        }""", "")
        if txt and txt != last:
            last = txt
            log(f"t+{(i+1)*9}s: ...{txt[-200:]}")
        if "Unauthorized" in last or "Erro ocorreu" in last:
            log("ERRO")
            break
        if len(last) > 800 and "Raspando" not in last and "Preparando" not in last:
            log("resposta substancial")
            break
    try:
        page.screenshot(path="/tmp/tst_ean_studio.png")
    except Exception:
        pass
    print("[tst] RESPOSTA:", last[-800:] if last else "(vazia)")
    ctx.close()
log("fim")
