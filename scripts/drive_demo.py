#!/usr/bin/env python3
"""
Demo REAL do Catalog Intelligence Agent gravada no display :99 (Xvfb)
enquanto o ffmpeg x11grab captura a tela.

Fluxo (antes/depois, interativo):
  CENA 1 — Studio home (control plane)
  CENA 2 — Connections: nossa MCP "Catalog Enricher" plugada
  CENA 3 — Agent chat: cola URL da loja → agente chama analyze_url + enrich_product
  CENA 4 — Resultado do enrich (título/bullets/descrição/schema) ao vivo
  CENA 5 — Monitor/Audit (rastreabilidade de custo)
  CENA 6 — Produto real (antes) para contraste

Usar APÓS iniciar o ffmpeg:
  DISPLAY=:99 python3 scripts/drive_demo.py
"""

import os
import time

os.environ.setdefault("DISPLAY", ":99")

from camoufox.sync_api import Camoufox

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"
PROD_URL = "https://www.viadoterno.com.br/terno-slim-comfort-marrom-apricot-calca-c-regulagem-poliviscose-premium"


def log(msg: str) -> None:
    print(f"[demo] {msg}", flush=True)


def main() -> None:
    with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
        page = ctx.new_page()

        # ── CENA 1: Studio home ──────────────────────────────────────
        log("abrindo Deco Studio (control plane)...")
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
        time.sleep(7)
        page.screenshot(path="/tmp/shot_1_studio.png")
        log("Studio carregado")

        # ── CENA 2: Connections (MCP plugada) ────────────────────────
        log("abrindo Connections — nossa MCP Catalog Enricher")
        page.goto(f"{STUDIO}/ubuntu-local/settings/connections", wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        time.sleep(2)
        try:
            page.fill('input[placeholder*="Search" i]', "Catalog")
            time.sleep(2)
        except Exception:
            log("sem campo de busca visível")
        page.screenshot(path="/tmp/shot_2_connections.png")
        time.sleep(2)

        # ── CENA 3: Agent chat com URL ───────────────────────────────
        log("abrindo o agente Catalog Enricher no chat...")
        page.goto(f"{STUDIO}/ubuntu-local", wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        page.screenshot(path="/tmp/shot_3_agent.png")
        # tenta colar a URL no campo de chat
        try:
            page.keyboard.type(PROD_URL, delay=20)
            time.sleep(1)
            page.keyboard.press("Enter")
            log("URL enviada ao agente — aguardando enrich...")
            time.sleep(20)  # o agente chama analyze_url + enrich_product
        except Exception as e:
            log(f"chat type falhou: {e}")
        page.screenshot(path="/tmp/shot_4_enrich_result.png")
        time.sleep(4)

        # ── CENA 5: Monitor/Audit ────────────────────────────────────
        log("abrindo Monitor/Audit (rastreabilidade de custo)...")
        page.goto(f"{STUDIO}/ubuntu-local/settings/monitor?tab=audit&from=now-24h&to=now", wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        page.screenshot(path="/tmp/shot_5_monitor.png")
        time.sleep(3)

        # ── CENA 6: produto real (antes) ─────────────────────────────
        log("abrindo produto real (catálogo sujo de origem)...")
        page.goto(PROD_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(7)
        page.screenshot(path="/tmp/shot_6_produto.png")
        time.sleep(3)

        log("demo concluída")
        ctx.close()


if __name__ == "__main__":
    main()
