#!/usr/bin/env python3
"""Teste definitivo: conversa NOVA (0 histórico) + pedido simples + monitora resposta real."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[fin] {m}", flush=True)

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
PEDIDO = "Oi! só um teste rápido: responda apenas FUNCIONANDO"

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
    # garantir que é conversa nova
    try:
        page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(x => /New chat|Nova conversa/i.test(x.textContent||''));
            if (b) { b.click(); return 'ok'; }
            return 'sem botao new chat';
        }""")
        time.sleep(4)
    except Exception as e:
        log(f"new chat: {e}")
    try:
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO, delay=8)
        page.keyboard.press("Enter")
        log("enviado — aguardando resposta real...")
    except Exception as e:
        log(f"type: {e}")
    # monitorar com seletor mais preciso: pega texto das bubbles de MENSAGEM (não CSS)
    last = ""
    for i in range(30):
        time.sleep(8)
        try:
            txt = page.evaluate("""() => {
                const msgs = Array.from(document.querySelectorAll('[class*="message"], [class*="bubble"], [data-testid*="message"]'));
                return msgs.map(m => (m.textContent||'').trim()).filter(t => t.length > 2).join(' ||| ').slice(-900);
            }""")
        except Exception:
            txt = ""
        if txt and txt != last:
            last = txt
            log(f"t+{(i+1)*8}s: {last[-200:]}")
        if "FUNCIONANDO" in last and "teste rápido" not in last.split('|||')[-1]:
            log(">>> RESPOSTA DO AGENTE RECEBIDA <<<")
            break
        if "Bad Request" in last or "Forbidden" in last or "Unauthorized" in last:
            log(">>> ERRO LLM <<<")
            break
    try:
        page.screenshot(path="/tmp/chat_final_ok.png")
    except Exception:
        pass
    print("[fin] FINAL:", last[-500:] if last else "(vazia)")
    ctx.close()
log("fim")
