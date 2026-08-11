#!/usr/bin/env python3
"""
Demo REAL gravada no :99 (Xvfb) — browser Camoufox headful, sem slides.
Mostra:
  Aba 1: produto real (viadoterno) no browser
  Aba 2: chamada ao vivo do enrich_product no MCP, com JSON real renderizado
"""
import os, time, json, threading, urllib.request

os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

PROD_URL = "https://www.viadoterno.com.br/terno-slim-comfort-marrom-apricot-calca-c-regulagem-poliviscose-premium"
MCP = "http://localhost:8791/mcp"
HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}

def rpc(method, params, id=1):
    body = json.dumps({"jsonrpc": "2.0", "id": id, "method": method, "params": params}).encode()
    req = urllib.request.Request(MCP, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def build_result_html(txt):
    safe = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<html><head><meta charset=utf-8><style>
    body{{font-family:sans-serif;background:#0d1117;color:#e6edf3;padding:24px}}
    h1{{color:#58a6ff}} pre{{background:#161b22;padding:16px;border-radius:8px;white-space:pre-wrap;font-size:13px}}
    .badge{{background:#238636;color:#fff;padding:4px 10px;border-radius:12px;font-size:12px}}
    </style></head><body>
    <h1>🛠️ Catalog Enricher — Resultado AO VIVO</h1>
    <span class=badge>enrich_product ✅</span>
    <pre>{safe}</pre></body></html>"""

def main():
    with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")

        # Aba 1: produto real
        p1 = ctx.new_page()
        print("[real] abrindo produto real...", flush=True)
        try:
            p1.goto(PROD_URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"[real] goto: {e}", flush=True)
        time.sleep(10)
        for _ in range(4):
            p1.mouse.wheel(0, 250); time.sleep(1.2)

        # Aba 2: enrich ao vivo
        p2 = ctx.new_page()
        p2.set_content("<h1 style='font-family:sans-serif;padding:24px'>🔄 Chamando enrich_product no MCP Catalog Enricher...</h1>")
        p2.bring_to_front()
        print("[real] chamando MCP...", flush=True)
        try:
            rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "live", "version": "1"}})
            args = {"product": {
                "title": "Terno Slim Comfort Marrom Apricot Calça C Regulagem Poliviscose Premium",
                "brand": "Via do Terno", "category": "Roupa",
                "description": "Terno slim com calça de regulagem em poliviscose premium", "price": "499.90"},
                "language": "pt-BR"}
            res = rpc("tools/call", {"name": "enrich_product", "arguments": args}, id=2)
            txt = res.get("result", {}).get("content", [{}])[0].get("text", "sem resultado")
            p2.set_content(build_result_html(txt))
            print("[real] enrich OK — renderizado", flush=True)
        except Exception as e:
            p2.set_content(f"<h1>erro: {e}</h1>")
            print(f"[real] enrich erro: {e}", flush=True)

        # alterna entre as abas para a gravação
        for _ in range(20):
            p1.bring_to_front(); time.sleep(2.5)
            p2.bring_to_front(); time.sleep(2.5)

if __name__ == "__main__":
    main()
