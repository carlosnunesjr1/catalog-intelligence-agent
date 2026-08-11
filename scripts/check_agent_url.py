#!/usr/bin/env python3
"""Abre o chat do Catalog Enricher com URL correta e verifica qual agente carrega."""
import os, time, json, sys
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

URL = sys.argv[1] if len(sys.argv) > 1 else "https://deco-studio.173-249-43-230.sslip.io/ubuntu-local"

def log(m): print(f"[u] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception:
        return default

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    log(f"abrindo: {URL}")
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    for i in range(10):
        time.sleep(4)
        n = safe_eval(page, "document.querySelectorAll('button').length", 0)
        if n > 10:
            break
    time.sleep(2)
    info = safe_eval(page, """() => ({
        url: location.href.slice(0, 150),
        title: document.title.slice(0, 60),
        agentName: (document.querySelector('h2')||{}).textContent || '',
        hasCe: /Catalog Enricher/.test(document.body.textContent),
        hasSA: /Super Agent/.test(document.body.textContent)
    })""", {})
    print("[u] info:", json.dumps(info, ensure_ascii=False))
    page.screenshot(path="/tmp/url_check.png")
    ctx.close()
log("fim")
