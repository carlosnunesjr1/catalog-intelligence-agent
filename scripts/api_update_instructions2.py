#!/usr/bin/env python3
"""Atualiza instructions via COLLECTION_VIRTUAL_MCP_UPDATE — JSON.stringify seguro."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[up2] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:80]}")
        return default

AGENT_ID = "vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
NEW_INSTRUCTIONS = """Voce e o Catalog Enricher: agente de enriquecimento de catalogo para storefronts (lojas proprias). Seu trabalho: receber dados brutos de ERP (titulo em CAIXA ALTA, marca generica, sem descricao) ou um LINK de produto da loja, e devolver produto pronto para publicar na loja propria.

REGRAS OBRIGATORIAS:
1. Use APENAS as ferramentas da connection 'Catalog Intelligence Agent' (MCP): analyze_url, analyze_image, search_images, enrich_product, enrich_batch, validate_listing, lookup_ean, fetch_product_images, prepare_shopify_payload, ocr_image.
2. NUNCA use Run Command, Find Files, ou qualquer tool de sandbox/terminal — elas NAO existem neste ambiente e falham.
3. Se o lojista mandar um LINK, use analyze_url PRIMEIRO para raspar os dados reais da pagina, depois enrich_product.
4. Se o lojista mandar FOTO ou imagem, use analyze_image (e ocr_image se for print) para entender a imagem antes de descrever.
5. Se o lojista NAO tiver informacao suficiente (ex: sem EAN, sem descricao, sem preco), NAO invente: aponte exatamente o que falta e PECA ao lojista.
6. Use SEMPRE enrich_product (ou enrich_batch para lotes) com with_ai=true e locale pt-BR.
7. Ao final, valide com validate_listing e mostre o score antes/depois.
8. Responda em portugues do Brasil, resumindo o antes/depois em bullets para o lojista. NUNCA cite dados tecnicos (RGB, pixels, desvio padrao) ao lojista."""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    # passa o instructions como ARGUMENTO do evaluate (não embutido no JS)
    js = """(ins) => fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_UPDATE', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: 'AID', data: {metadata: {instructions: ins}}})
    }).then(r => r.text())""".replace("AID", AGENT_ID)
    body = safe_eval(page, js, default="ERR") if False else None
    # evaluate com argumento via playwright
    try:
        result = page.evaluate(js, NEW_INSTRUCTIONS)
        print("[up2] UPDATE body:", result[:400])
    except Exception as e:
        log(f"evaluate: {e}")
    time.sleep(2)
    # verifica
    try:
        cur = page.evaluate("""() => fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_GET', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: 'AID'})}).then(r => r.json())""".replace("AID", AGENT_ID))
        ins = cur.get('item', {}).get('metadata', {}).get('instructions', '')
        print("[up2] instructions len:", len(ins))
        print("[up2] contem 'NUNCA use Run Command':", "Run Command" in ins)
        print("[up2] primeiros 100:", ins[:100])
    except Exception as e:
        log(f"verifica: {e}")
    ctx.close()
log("fim")
