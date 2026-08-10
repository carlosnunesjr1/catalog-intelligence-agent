#!/usr/bin/env python3
"""
Grava a demo REAL no Deco Studio: abre o browser headful no display :99,
dirige a demo com cliques reais (abrir agent, colar URL, mostrar tools,
Monitor/Audit) — enquanto ffmpeg x11grab captura o display inteiro.

Uso (disparado após o ffmpeg iniciar a gravação):
  DISPLAY=:99 python3 scripts/drive_demo.py
"""

import os
import re
import subprocess
import sys
import time

os.environ.setdefault("DISPLAY", ":99")

from camoufox.sync_api import Camoufox  # noqa: E402

STUDIO = "https://deco-studio.173-249-43-230.sslip.io"
MCP_URL = "https://catalog-mcp.173-249-43-230.sslip.io/mcp"
PROD_URL = "https://www.viadoterno.com.br/terno-slim-comfort-marrom-apricot-calca-c-regulagem-poliviscose-premium"


def log(msg: str) -> None:
    print(f"[demo] {msg}", flush=True)


def wait_network(page, timeout=15000) -> None:
    page.wait_for_load_state("networkidle", timeout=timeout)


def main() -> None:
    with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
        page = ctx.new_page()

        # ── CENA 1: Studio home ──────────────────────────────────────
        log("abrindo Studio...")
        page.goto(STUDIO, wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        wait_network(page, timeout=20000)
        log("Studio carregado")

        # ── CENA 2: conexão / tools ──────────────────────────────────
        log("indo para Connections...")
        page.goto(f"{STUDIO}/ubuntu-local/settings/connections", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        time.sleep(2)
        log("connections visível")

        # Tool card da nossa connection — usa pesquisa
        try:
            page.fill('input[placeholder*="Search" i]', "Catalog")
            time.sleep(2)
        except Exception:
            log("sem campo de busca visível")
        page.screenshot(path="/tmp/video_shot_connections.png")
        time.sleep(2)

        # ── CENA 3: Agent / chat com URL do produto ──────────────────
        log("abrindo o agent Catalog Enricher (chat)...")
        # navega direto para o app do agent (reutiliza sessão do perfil)
        page.goto(f"{STUDIO}/ubuntu-local", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        page.screenshot(path="/tmp/video_shot_agent.png")
        time.sleep(2)

        # ── CENA 4: Monitor/Audit ────────────────────────────────────
        log("abrindo Monitor/Audit...")
        page.goto(f"{STUDIO}/ubuntu-local/settings/monitor?tab=audit&from=now-24h&to=now", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        page.screenshot(path="/tmp/video_shot_monitor.png")
        time.sleep(3)

        # ── CENA 5: página do produto real (para Google/YT thumb) ────
        log("abrindo produto real...")
        page.goto(PROD_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        page.screenshot(path="/tmp/video_shot_product.png")
        time.sleep(3)

        log("demo dirigida — finalizando")
        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()