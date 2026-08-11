#!/usr/bin/env python3
"""
Demo no DECO STUDIO: agente Catalog Enricher em ação no chat.
Mostra: pedido natural do lojista com LINK → agente chama analyze_url →
enrich_product → validate_listing (tool calls ao vivo) → resposta final.

Gravado no :99 com ffmpeg x11grab.
"""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[ds] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception:
        return default

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
PEDIDO = ("Oi! Tenho um produto da minha loja com cadastro fraco: um terno slim marrom, da Via do Terno. "
          "O link é https://www.viadoterno.com.br/terno-slim-comfort-marrom-apricot-calca-c-regulagem-poliviscose-premium. "
          "Pode deixar ele pronto pra publicar?")

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    log("abrindo Catalog Enricher...")
    try:
        page.goto(AGENT_URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    # espera o app carregar (12s de tela do Studio)
    for i in range(8):
        time.sleep(3)
        n = safe_eval(page, "document.querySelectorAll('button').length", 0)
        if n > 10:
            break
    time.sleep(6)
    log("Studio carregado — cena inicial")

    # digita o pedido natural (mostra a digitação na gravação)
    try:
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO, delay=12)  # delay = visível na gravação
        log("pedido digitado")
        time.sleep(2)
        page.screenshot(path="/tmp/ds_typed.png")
        page.keyboard.press("Enter")
        log("Enter — agente processando...")
    except Exception as e:
        log(f"type: {e}")

    # deixa o agente trabalhar (analyze_url → enrich → validate) — tempo longo p/ gravação
    for i in range(24):
        time.sleep(10)
        # loga o que está visível na tela (texto do chat)
        txt = safe_eval(page, """() => (document.body.textContent || '').match(/Raspando|Enrich|enrich|Preparando|validat|Analisando|Bullets|título|bullet|score|pronto/i) ? (document.body.textContent.match(/Raspando[^\\n]{0,60}|Enrich[^\\n]{0,60}|Preparando[^\\n]{0,60}|validat[^\\n]{0,60}|Analisando[^\\n]{0,60}|Score[^\\n]{0,60}/g) || []).slice(-3).join(' | ') : '(processando...)'
        """, "(processando...)")
        log(f"t+{(i+1)*10}s: {txt[:150]}")
        if i == 8:
            page.screenshot(path="/tmp/ds_mid.png")

    page.screenshot(path="/tmp/ds_final.png")
    log("demo concluída")
    ctx.close()
log("fim")
