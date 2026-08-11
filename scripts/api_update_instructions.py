#!/usr/bin/env python3
"""Atualiza instructions do Catalog Enricher: usar ONLY tools MCP, nunca Run Command/sandbox."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[up] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
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
    res = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_UPDATE', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                id: 'AID',
                metadata: {instructions: 'INS'}
            })});
        return {status: r.status, body: await r.text()};
    }""".replace("AID", AGENT_ID).replace("INS", NEW_INSTRUCTIONS.replace("'", "\\'")), None)
    print("[up] UPDATE:", json.dumps(res, ensure_ascii=False, default=str)[:600])
    time.sleep(2)
    # verifica GET
    res2 = safe_eval(page, """async () => {
        const r = await fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_GET', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: 'AID'})});
        return await r.json();
    }""".replace("AID", AGENT_ID), None)
    if res2 and 'item' in res2:
        ins = res2['item'].get('metadata', {}).get('instructions', '')
        print("[up] instructions atualizadas:", ins[:80], "... len:", len(ins))
        print("[up] contem 'NUNCA use Run Command':", "Run Command" in ins)
    ctx.close()
log("fim")
