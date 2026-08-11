#!/usr/bin/env python3
"""Testa o chat do agente Catalog Enricher com o novo modelo hy3 (Nous)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[ch] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception:
        return default

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
PEDIDO = "Oi! Tenho um produto da minha loja com cadastro fraco: um terno slim marrom, da Via do Terno. O link é https://www.viadoterno.com.br/terno-slim-comfort-marrom-apricot-calca-c-regulagem-poliviscose-premium. Pode deixar ele pronto pra publicar?"

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(AGENT_URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    for i in range(10):
        time.sleep(5)
        n = safe_eval(page, "document.querySelectorAll('button').length", 0)
        if n > 10:
            break
    time.sleep(2)
    # envia pedido no contenteditable
    try:
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO, delay=8)
        page.keyboard.press("Enter")
        log("pedido enviado — aguardando resposta...")
    except Exception as e:
        log(f"type: {e}")
    # monitora até 150s
    last = ""
    for i in range(18):
        time.sleep(8)
        txt = safe_eval(page, """() => {
            const msgs = Array.from(document.querySelectorAll('[class*=message], [class*=bubble]'));
            return msgs.map(m => (m.textContent||'').trim()).filter(t => t.length > 20).join(' ||| ').slice(-900);
        }""", "")
        if txt and txt != last:
            last = txt
            log(f"t+{(i+1)*8}s: ...{txt[-150:]}")
        if "Unauthorized" in last or "Erro ocorreu" in last:
            log("ERRO")
            break
        if len(last) > 500 and "Nenhuma resposta" not in last:
            log("resposta recebida")
            break
    try:
        page.screenshot(path="/tmp/chat_hy3.png")
    except Exception:
        pass
    print("[ch] RESPOSTA:", last[-600:] if last else "(vazia)")
    ctx.close()
log("fim")
