#!/usr/bin/env python3
"""Nova conversa limpa no Catalog Enricher + pedido + monitora até resposta final."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[nc] {m}", flush=True)

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
    # clica em nova conversa (botão New chat)
    nc = safe_eval(page, """() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const b = btns.find(x => /New chat|Nova conversa|Novo chat/i.test(x.textContent||'') || (x.getAttribute('aria-label')||'').match(/new|nova/i));
        return b ? b.textContent.trim().slice(0,30) : null;
    }""", None)
    log(f"botão nova conversa: {nc}")
    if nc:
        try:
            page.click('button:has-text("New chat"), button:has-text("Nova conversa"), button[aria-label*="new" i], button[aria-label*="nova" i]', timeout=3000)
            log("nova conversa clicada")
            time.sleep(3)
        except Exception as e:
            log(f"click new: {e}")
    # envia pedido
    try:
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO, delay=8)
        page.keyboard.press("Enter")
        log("pedido enviado — aguardando resposta completa...")
    except Exception as e:
        log(f"type: {e}")
    # monitora até 240s (analyze_url + enrich + validate demoram)
    last = ""
    for i in range(30):
        time.sleep(8)
        txt = safe_eval(page, """() => {
            const body = document.body.textContent || '';
            // pega os últimos blocos de mensagem
            const msgs = Array.from(document.querySelectorAll('[class*=message], [class*=bubble]'));
            return msgs.map(m => (m.textContent||'').trim()).filter(t => t.length > 25).join(' ||| ').slice(-1500);
        }""", "")
        if txt and txt != last:
            last = txt
            log(f"t+{(i+1)*8}s: ...{txt[-200:]}")
        # detecta erro grave ou resposta final longa
        if "Unauthorized" in last or "Erro ocorreu" in last:
            log("ERRO detectado")
            break
        if len(last) > 800 and "Raspando" not in last and "Preparando" not in last:
            log("resposta substancial — provavelmente final")
            break
    try:
        page.screenshot(path="/tmp/nc_final.png")
    except Exception:
        pass
    print("[nc] RESPOSTA:", last[-800:] if last else "(vazia)")
    ctx.close()
log("fim")
