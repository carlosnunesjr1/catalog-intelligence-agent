#!/usr/bin/env python3
"""Teste final v3: aba Chat + New chat correto + pedido."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[v3] {m}", flush=True)

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
    # garantir aba Chat ativa
    try:
        page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const c = btns.find(b => b.textContent.trim() === 'Chat');
            if (c) { c.click(); return 'chat tab'; }
            return 'sem tab chat';
        }""")
        time.sleep(3)
    except Exception as e:
        log(f"tab: {e}")
    # New chat DENTRO da área do chat (botão com ícone +, perto do topo)
    try:
        r = page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            // New chat costuma ser o botão com SVG plus no header do chat
            const candidates = btns.filter(b => {
                const t = (b.textContent||'').trim();
                const hasSvg = !!b.querySelector('svg');
                return hasSvg && (t.length < 15) && /New|Nova|novo/i.test(t);
            });
            const exact = btns.find(b => /New chat|Nova conversa|Novo chat/i.test(b.textContent||''));
            if (exact) { exact.click(); return 'exact: ' + exact.textContent.trim(); }
            if (candidates.length) { candidates[0].click(); return 'cand: ' + candidates.length; }
            return 'nenhum';
        }""")
        log("new chat: " + str(r))
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
    last = ""
    for i in range(12):
        time.sleep(8)
        try:
            txt = page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('main *'));
                const leaves = els.filter(e => e.children.length === 0 && (e.textContent||'').trim().length > 1);
                return leaves.map(e => e.textContent.trim()).join(' | ').slice(-900);
            }""")
        except Exception:
            txt = ""
        if txt and txt != last:
            last = txt
            log(f"t+{(i+1)*8}s: {last[-220:]}")
        if "Bad Request" in last or "Forbidden" in last:
            log("ERRO")
            break
        if "FUNCIONANDO" in last and "teste: responda" not in last.split('|')[-1]:
            log("RESPOSTA")
            break
    try:
        page.screenshot(path="/tmp/chat_v3.png")
    except Exception:
        pass
    print("[v3] FINAL:", last[-500:] if last else "(vazia)")
    ctx.close()
log("fim")
