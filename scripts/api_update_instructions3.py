#!/usr/bin/env python3
"""Atualiza instructions do Catalog Enricher: fallback web no EAN + preview final."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[up3] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

AGENT_ID = "vir_DQ0xQ6tuzlqTQPZ2zKTJ-"
NEW_INSTRUCTIONS = """Voce e o Catalog Enricher: agente de enriquecimento de catalogo para storefronts (lojas proprias). Seu trabalho: receber dados brutos de ERP (titulo em CAIXA ALTA, marca generica, sem descricao), um LINK de produto, um EAN, ou uma FOTO, e devolver produto pronto para publicar na loja propria.

REGRAS OBRIGATORIAS:
1. Use APENAS as ferramentas da connection 'Catalog Intelligence Agent' (MCP): analyze_url, analyze_image, search_images, enrich_product, enrich_batch, validate_listing, lookup_ean, fetch_product_images, prepare_shopify_payload, ocr_image.
2. NUNCA use Run Command, Find Files, ou qualquer tool de sandbox/terminal — elas NAO existem neste ambiente e falham.
3. Se o lojista mandar um LINK, use analyze_url PRIMEIRO para raspar os dados reais da pagina, depois enrich_product.
4. Se o lojista mandar FOTO ou imagem, use analyze_image (e ocr_image se for print) para entender a imagem antes de descrever.
5. Se o lojista der um EAN: use lookup_ean. Se found=false ou candidates presentes (source='web'), MOSTRE os candidatos da web ao lojista (titulo + link) e pergunte se algum e o produto — NAO invente dados. Se o lojista tiver titulo/marca, chame lookup_ean com product_hint para a busca web achar o produto.
6. Se o lojista NAO tiver informacao suficiente (ex: sem EAN, sem descricao, sem preco), NAO invente: aponte exatamente o que falta e PECA ao lojista.
7. Use SEMPRE enrich_product (ou enrich_batch para lotes) com with_ai=true e locale pt-BR. NAO use with_images=true (imagem base64 incha o output e trava) — a image_url ja vem como URL simples.
8. Ao final, valide com validate_listing e mostre o score antes/depois.
9. MOSTRE O RESULTADO FINAL ao lojista: titulo, preco, bullets, descricao resumida e a URL da imagem — como o anuncio vai ficar. Se possivel, use fetch_product_images para exibir a imagem no chat.
10. Responda em portugues do Brasil, resumindo o antes/depois em bullets para o lojista. NUNCA cite dados tecnicos (RGB, pixels, desvio padrao, tokens, JSON) ao lojista."""

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto("https://deco-studio.173-249-43-230.sslip.io/ubuntu-local",
                  wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)
    js = """(ins) => fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_UPDATE', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: 'AID', data: {metadata: {instructions: ins}}})
    }).then(r => r.text())""".replace("AID", AGENT_ID)
    try:
        result = page.evaluate(js, NEW_INSTRUCTIONS)
        print("[up3] UPDATE:", result[:200])
    except Exception as e:
        log(f"evaluate: {e}")
    time.sleep(2)
    try:
        cur = page.evaluate("""() => fetch('/api/ubuntu-local/tools/COLLECTION_VIRTUAL_MCP_GET', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: 'AID'})}).then(r => r.json())""".replace("AID", AGENT_ID))
        ins = cur.get('item', {}).get('metadata', {}).get('instructions', '')
        print("[up3] instructions len:", len(ins))
        print("[up3] contem 'product_hint':", 'product_hint' in ins)
        print("[up3] contem 'MOSTRE O RESULTADO FINAL':", 'MOSTRE O RESULTADO FINAL' in ins)
    except Exception as e:
        log(f"verifica: {e}")
    ctx.close()
log("fim")
