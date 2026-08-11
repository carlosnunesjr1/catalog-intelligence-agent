#!/usr/bin/env python3
"""Verifica os cards Rápido/Inteligente/Reflexivo do agente (modelos por card)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"

JS = """() => {
  const cards = [];
  const lines = Array.from(document.querySelectorAll('div.flex.items-center.gap-3, div.flex.items-center.gap-2'));
  for (const l of lines) {
    const label = l.querySelector('div.text-sm.font-medium, div.text-xs.font-medium');
    const btn = l.querySelector('button');
    if (label && btn) {
      cards.push({label: label.textContent.trim().slice(0,30), btn: btn.textContent.trim().slice(0,60)});
    }
  }
  return JSON.stringify(cards.slice(0,12));
}"""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(AGENT_URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("[cards] goto:", e)
    for i in range(12):
        time.sleep(5)
        try:
            if page.evaluate("document.querySelectorAll('button').length") > 10:
                break
        except Exception:
            pass
    time.sleep(2)
    # procurar no painel do agente (pode precisar rolar para Settings)
    try:
        # vai para aba Settings se existir
        page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const s = btns.find(b => /Settings|Configurações/i.test(b.textContent||''));
            if (s) s.click();
        }""")
        time.sleep(3)
    except Exception:
        pass
    try:
        print("[cards]", page.evaluate(JS))
    except Exception as e:
        print("[cards] eval fail:", e)
    # screenshot
    try:
        page.screenshot(path="/tmp/cards.png")
    except Exception:
        pass
    ctx.close()
print("[cards] fim")
