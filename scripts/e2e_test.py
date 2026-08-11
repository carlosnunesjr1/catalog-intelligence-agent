#!/usr/bin/env python3
"""
Teste E2E dos 2 fluxos de usuário no chat do Catalog Enricher (Deco Studio):
  CENÁRIO A: link de concorrente → análise → melhoria
  CENÁRIO B: produto novo (foto + descrição) → cadastro completo
Monitora a resposta do agente e salva screenshots.
"""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[e2e] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception:
        return default

AGENT_URL = "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local/795287d0-d73e-4070-99f9-58963451ef76?virtualmcpid=vir_DQ0xQ6tuzlqTQPZ2zKTJ-"

# CENÁRIO A: análise de concorrente (link)
PEDIDO_A = ("Oi! Preciso de uma análise de um concorrente. "
            "Este é o link de um produto da loja Via do Terno: "
            "https://www.viadoterno.com.br/terno-slim-comfort-marrom-apricot-calca-c-regulagem-poliviscose-premium. "
            "Pode analisar a página e me dizer o que dá pra melhorar no meu cadastro?")

# CENÁRIO B: produto novo (foto + descrição)
PEDIDO_B = ("Oi! Preciso criar o cadastro de um produto novo na minha loja. "
            "É uma camisa social masculina, azul, manga longa, da minha marca própria. "
            "Tenho a foto aqui e a descrição: tecido de algodão pima, caimento slim, botões de madrepérola. "
            "Pode criar o título, os bullets e a descrição pronta pra publicar?")

def monitor(page, label, timeout_loops=30):
    """Monitora o chat até resposta substancial ou erro. Retorna o texto final."""
    last = ""
    for i in range(timeout_loops):
        time.sleep(8)
        txt = safe_eval(page, """() => {
            const body = document.body.textContent || '';
            // procura blocos de resposta do agente (depois do último pedido do usuário)
            const parts = body.split('Pode ');
            return parts.slice(-2).join(' Pode ').slice(-1200);
        }""", "")
        if txt and txt != last:
            last = txt
            log(f"[{label}] t+{(i+1)*8}s: ...{txt[-180:]}")
        if "Unauthorized" in last or "Erro ocorreu" in last:
            log(f"[{label}] ERRO detectado")
            break
        if len(last) > 700:
            log(f"[{label}] resposta substancial")
            break
    return last

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
    time.sleep(4)

    # ── CENÁRIO A ──
    log("=== CENÁRIO A: análise de concorrente (link) ===")
    try:
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO_A, delay=6)
        page.keyboard.press("Enter")
        log("A: pedido enviado")
    except Exception as e:
        log(f"A: type: {e}")
    resp_a = monitor(page, "A")
    try:
        page.screenshot(path="/tmp/e2e_cenarioA.png")
    except Exception:
        pass
    print("[e2e] RESPOSTA A:", resp_a[-600:] if resp_a else "(vazia)")

    # ── CENÁRIO B ──
    log("=== CENÁRIO B: produto novo (foto + descrição) ===")
    try:
        page.click('[contenteditable="true"]', timeout=5000)
        time.sleep(1)
        page.keyboard.type(PEDIDO_B, delay=6)
        page.keyboard.press("Enter")
        log("B: pedido enviado")
    except Exception as e:
        log(f"B: type: {e}")
    resp_b = monitor(page, "B")
    try:
        page.screenshot(path="/tmp/e2e_cenarioB.png")
    except Exception:
        pass
    print("[e2e] RESPOSTA B:", resp_b[-600:] if resp_b else "(vazia)")

    ctx.close()
log("fim")
