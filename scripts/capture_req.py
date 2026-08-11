#!/usr/bin/env python3
"""Testa o chat do agente e captura o request REAL via network (log do processo)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[net] {m}", flush=True)

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
PEDIDO = "Responda apenas: FUNCIONANDO"

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    # capturar requests para a API de chat
    captured = []
    def on_request(req):
        u = req.url
        if 'chat/completions' in u or 'inference-api' in u or 'opencode' in u or 'nousresearch' in u:
            try:
                body = req.post_data or ''
                captured.append({'url': u[:120], 'body_len': len(body), 'body_head': body[:400]})
            except Exception:
                pass
    page.on("request", on_request)
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
    # limpar capturas do carregamento
    captured.clear()
    try:
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO, delay=8)
        page.keyboard.press("Enter")
        log("pedido enviado")
    except Exception as e:
        log(f"type: {e}")
    time.sleep(20)
    for i, c in enumerate(captured):
        log(f"REQ {i}: {c['url']}")
        log(f"  body({c['body_len']}): {c['body_head'][:300]}")
    if not captured:
        log("NENHUM request de chat capturado")
    ctx.close()
log("fim")
