#!/usr/bin/env python3
"""Teste final definitivo: nova conversa, pedido real, screenshot + texto após 30s."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[ok] {m}", flush=True)

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
PEDIDO = "Oi! teste: responda apenas FUNCIONANDO"

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
    # nova conversa real
    try:
        page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(x => /New chat|Nova conversa/i.test(x.textContent||''));
            if (b) { b.click(); return 'ok'; }
            return 'nao achei';
        }""")
        log("new chat")
        time.sleep(5)
    except Exception as e:
        log(f"new: {e}")
    try:
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO, delay=8)
        page.keyboard.press("Enter")
        log("enviado")
    except Exception as e:
        log(f"type: {e}")
    # monitorar 90s com snapshot de texto preciso
    last = ""
    for i in range(11):
        time.sleep(8)
        try:
            txt = page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('main *'));
                const leaves = els.filter(e => e.children.length === 0 && (e.textContent||'').trim().length > 1);
                return leaves.map(e => e.textContent.trim()).join(' | ').slice(-1000);
            }""")
        except Exception:
            txt = ""
        if txt and txt != last:
            last = txt
            log(f"t+{(i+1)*8}s: ...{last[-250:]}")
        if "Bad Request" in last or "Forbidden" in last:
            log("ERRO DETECTADO")
            break
        # resposta do agente = texto que NÃO é a pergunta nem erro, com FUNCIONANDO
        if "FUNCIONANDO" in last and "teste: responda" not in last.split('|')[-1]:
            log("RESPOSTA RECEBIDA")
            break
    try:
        page.screenshot(path="/tmp/chat_ok_final.png")
        log("screenshot ok")
    except Exception:
        pass
    print("[ok] FINAL:", last[-600:] if last else "(vazia)")
    ctx.close()
log("fim")
