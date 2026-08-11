#!/usr/bin/env python3
"""Roda enrich_product AO VIVO contra o MCP e imprime o JSON real (visível na gravação)."""
import json, urllib.request, time

MCP = "http://localhost:8791/mcp"
HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}

def rpc(method, params, id=1):
    body = json.dumps({"jsonrpc": "2.0", "id": id, "method": method, "params": params}).encode()
    req = urllib.request.Request(MCP, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def main():
    print(">>> Conectando ao Catalog Enricher MCP...", flush=True)
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "live", "version": "1"}})
    time.sleep(1)
    print(">>> Chamando enrich_product em produto REAL (viadoterno)...", flush=True)
    args = {"product": {
        "title": "Terno Slim Comfort Marrom Apricot Calça C Regulagem Poliviscose Premium",
        "brand": "Via do Terno",
        "category": "Roupa",
        "description": "Terno slim com calca de regulagem em poliviscose premium",
        "price": "499.90"
    }, "language": "pt-BR"}
    res = rpc("tools/call", {"name": "enrich_product", "arguments": args}, id=2)
    txt = res.get("result", {}).get("content", [{}])[0].get("text", "")
    print("\n=== RESULTADO DO ENRICH (AO VIVO) ===\n", flush=True)
    print(txt[:1500], flush=True)
    print("\n>>> Demo concluida. Pressione ENTER para sair.", flush=True)

if __name__ == "__main__":
    main()
