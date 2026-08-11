#!/usr/bin/env python3
"""Screenshot do estado atual do chat do agente."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(AGENT_URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[ss] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 10:
                break
        except Exception:
            pass
    time.sleep(3)
    try:
        page.screenshot(path="/tmp/chat_state.png")
        print("[ss] screenshot ok")
    except Exception as e:
        print("[ss] fail:", e)
    # também capturar texto das mensagens
    try:
        txt = page.evaluate("""() => {
            const all = Array.from(document.querySelectorAll('*'));
            const msgs = all.filter(e => e.children.length === 0 && (e.textContent||'').trim().length > 3);
            const relevant = msgs.map(e => e.textContent.trim()).filter(t => /Bad Request|Unauthorized|FUNCIONANDO|Nenhuma resposta|erro/i.test(t));
            return relevant.slice(-10);
        }""")
        print("[ss] textos:", json.dumps(txt, ensure_ascii=False))
    except Exception as e:
        print("[ss] txt fail:", e)
    ctx.close()
print("[ss] fim")
