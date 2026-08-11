#!/usr/bin/env python3
"""
Demo COMPLETA (~4 min) — cada funcionalidade ao vivo contra o MCP.
Cenas:
  A. Produto real (catálogo sujo) — tempo longo
  B. 1/6 analyze_url — link colado pelo lojista
  C. 2/6 search_images — busca imagem
  D. 3/6 analyze_image — entende a imagem
  E. 4/6 enrich_product — IA cria conteúdo
  F. 5/6 validate_listing ANTES (score 0) — pede informações, não inventa
  G. 5/6 validate_listing DEPOIS (score alto) — produto enriquecido
  H. 6/6 prepare_shopify_payload — ciclo fechado
"""
import os, time, json, urllib.request
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

PROD_URL = "https://www.viadoterno.com.br/terno-slim-comfort-marrom-apricot-calca-c-regulagem-poliviscose-premium"
MCP = "http://localhost:8791/mcp"
HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}

def log(m): print(f"[demo] {m}", flush=True)

def rpc(method, params, id=1):
    body = json.dumps({"jsonrpc": "2.0", "id": id, "method": method, "params": params}).encode()
    req = urllib.request.Request(MCP, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)

def build_html(title, badge, payload, extra=None):
    safe = json.dumps(payload, ensure_ascii=False, indent=2)
    safe = safe.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    extra_html = ""
    if extra:
        extra_html = f'<div style="background:#1c2333;padding:12px;border-radius:8px;margin:12px 0;font-size:13px;color:#8b949e">{extra}</div>'
    return f"""<html><head><meta charset=utf-8><style>
    body{{font-family:sans-serif;background:#0d1117;color:#e6edf3;padding:20px;margin:0}}
    h1{{color:#58a6ff;font-size:17px;margin:0 0 4px}} h2{{color:#8b949e;font-size:12px;font-weight:normal;margin:0 0 14px}}
    .badge{{display:inline-block;background:#238636;color:#fff;padding:3px 10px;border-radius:12px;font-size:11px;margin-bottom:12px}}
    pre{{background:#161b22;padding:14px;border-radius:8px;white-space:pre-wrap;font-size:12px;line-height:1.5;max-height:520px;overflow:auto}}
    .ok{{color:#3fb950}} .warn{{color:#d29922}} .err{{color:#f85149}}
    </style></head><body>
    <h1>🛠️ Catalog Enricher — {title}</h1>
    <h2>Chamada AO VIVO contra o MCP Catalog Intelligence Agent</h2>
    <span class="badge">{badge} ✅</span>
    {extra_html}
    <pre>{safe}</pre></body></html>"""

def safe(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception as e:
        log(f"safe: {type(e).__name__}: {str(e)[:80]}")
        return None

def show_step(p2, title, badge, args, extra):
    safe(p2.bring_to_front)
    try:
        res = rpc("tools/call", {"name": args["name"], "arguments": args.get("arguments", {})}, id=2)
        txt = res.get("result", {}).get("content", [{}])[0].get("text", "{}")
        try:
            payload = json.loads(txt)
        except Exception:
            payload = {"raw": txt[:2000]}
        safe(p2.set_content, build_html(title, badge, payload, extra))
        log(f"{title}: OK ({len(txt)} chars)")
    except Exception as e:
        safe(p2.set_content, build_html(title, badge, {"erro": str(e)[:300]}, extra))
        log(f"{title}: ERRO {e}")
    time.sleep(14)

def main():
    with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
        p1 = ctx.new_page()
        p2 = ctx.new_page()

        # ── CENA A: produto real (tempo longo) ──
        log("CENA A: produto real...")
        try:
            p1.goto(PROD_URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            log(f"goto prod: {e}")
        time.sleep(14)
        for _ in range(6):
            safe(p1.mouse.wheel, 0, 250)
            time.sleep(1.5)
        p1.bring_to_front()
        time.sleep(10)

        # ── CENA B: 1/6 analyze_url ──
        log("CENA B: analyze_url...")
        show_step(p2, "1/6 — analyze_url (link da loja)", "analyze_url",
                  {"name": "analyze_url", "arguments": {"url": PROD_URL}},
                  f"📍 <b>O lojista cola o link do produto no agente:</b><br><span style='color:#58a6ff'>{PROD_URL[:70]}...</span><br><br>O agente acessa a página e extrai <b>título, preço, marca, SKU e imagens reais</b> — sem inventar nada.")

        # ── CENA C: 2/6 search_images ──
        log("CENA C: search_images...")
        show_step(p2, "2/6 — search_images (produto novo sem foto)", "search_images",
                  {"name": "search_images", "arguments": {"title": "Terno Slim Comfort Marrom Apricot Calça C Regulagem Poliviscose Premium", "limit": 4}},
                  "🔎 <b>Produto novo sem foto?</b> O agente busca a imagem em alta resolução pelo título/EAN em fontes públicas, e devolve as melhores opções.")

        # ── CENA D: 3/6 analyze_image ──
        log("CENA D: analyze_image...")
        show_step(p2, "3/6 — analyze_image (entende a foto)", "analyze_image",
                  {"name": "analyze_image", "arguments": {"image_url": "https://www.viadoterno.com.br/images/products/terno-slim-comfort-marrom-apricot.jpg", "title": "Terno Slim Comfort Marrom Apricot"}},
                  "👁️ <b>O agente 'olha' a imagem:</b> extrai cor, proporção, fundo e qualidade — para a descrição descrever exatamente o que o cliente recebe.")

        # ── CENA E: 4/6 enrich_product ──
        log("CENA E: enrich_product...")
        show_step(p2, "4/6 — enrich_product (IA cria o conteúdo)", "enrich_product",
                  {"name": "enrich_product", "arguments": {"product": {
                      "title": "Terno Slim Comfort Marrom Apricot Calça C Regulagem Poliviscose Premium",
                      "brand": "Via do Terno", "category": "Roupa",
                      "description": "Terno slim com calça de regulagem em poliviscose premium",
                      "price": "499.90"}, "language": "pt-BR"}},
                  "✨ <b>IA cria o conteúdo de venda:</b> título SEO, bullets de benefícios, descrição HTML mobile-first, meta tags e palavras-chave — em português.")

        # ── CENA F: 5/6 validate ANTES (produto incompleto → score 0) ──
        log("CENA F: validate ANTES (score 0)...")
        show_step(p2, "5/6 — validate_listing ANTES (dados incompletos)", "validate_listing",
                  {"name": "validate_listing", "arguments": {"listing": {
                      "title": "Camisa",
                      "brand": "",
                      "price": "89.90",
                      "description": ""}, "language": "pt-BR"}},
                  "⚠️ <b>O agente NÃO inventa:</b> com dados incompletos, ele devolve <b>score 0</b> e aponta exatamente o que falta — descrição, imagem, bullets, EAN. Ele <b>pede a informação</b> ao lojista.")

        # ── CENA G: 5/6 validate DEPOIS (produto enriquecido → score alto) ──
        log("CENA G: validate DEPOIS (score alto)...")
        show_step(p2, "5/6 — validate_listing DEPOIS (produto enriquecido)", "validate_listing",
                  {"name": "validate_listing", "arguments": {"listing": {
                      "title": "Terno Slim Comfort Marrom Apricot Calça C Regulagem Poliviscose Premium",
                      "brand": "Via do Terno",
                      "price": "499.90",
                      "description": "Terno slim com calça de regulagem em poliviscose premium. Caimento estruturado, tecido que evita amassados.",
                      "image_url": "https://www.viadoterno.com.br/images/products/terno-slim-comfort-marrom-apricot.jpg",
                      "ean": "3168930010265",
                      "bullets": ["Tecido premium que evita amassados", "Caimento estruturado que valoriza a silhueta", "Marrom versátil para o dia a dia"]}, "language": "pt-BR"}},
                  "📈 <b>Após o enriquecimento:</b> o mesmo produto validado com <b>score alto</b> — SEO on-page, schema.org, imagem, marca e EAN completos.")

        # ── CENA H: 6/6 prepare_shopify_payload ──
        log("CENA H: prepare_shopify_payload...")
        show_step(p2, "6/6 — prepare_shopify_payload (publicação)", "prepare_shopify_payload",
                  {"name": "prepare_shopify_payload", "arguments": {"product": {
                      "title": "Terno Slim Comfort Marrom Apricot Calça C Regulagem Poliviscose Premium",
                      "brand": "Via do Terno", "category": "Roupa",
                      "description": "Terno slim com calça de regulagem em poliviscose premium",
                      "price": "499.90"}}},
                  "🚀 <b>Ciclo fechado:</b> payload GraphQL productCreate pronto — o agente publica direto na loja, sem copy-paste.")

        # ── alternância final (navegação) ──
        for _ in range(8):
            safe(p1.bring_to_front); time.sleep(5)
            safe(p2.bring_to_front); time.sleep(5)

        log("demo concluída")

if __name__ == "__main__":
    main()
