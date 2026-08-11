#!/usr/bin/env python3
"""Conta TODAS as imagens reais do produto na página renderizada (via Camoufox)."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

def log(m): print(f"[img] {m}", flush=True)

def safe_eval(page, js, default=None):
    try:
        return page.evaluate(js)
    except Exception as e:
        log(f"eval fail: {str(e)[:60]}")
        return default

URL = "https://www.viadoterno.com.br/terno-slim-comfort-cinza-escuro-semi-encerado-poliviscose-premium?inStock#derivacao=85"

with Camoufox(headless=False, humanize=True, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        log(f"goto: {e}")
    time.sleep(12)  # deixa a galeria JS carregar
    # todas as imagens visíveis com URL de produto
    imgs = safe_eval(page, """() => {
        const out = [];
        document.querySelectorAll('img').forEach(i => {
            const src = i.currentSrc || i.src || '';
            if (/cdn\.magazord\.com\.br\/img/.test(src) && !/logo|icon|whatsapp|favicon/i.test(src)) {
                const r = i.getBoundingClientRect();
                out.push({src: src.slice(0,120), w: Math.round(r.width), h: Math.round(r.height), visible: r.width > 40});
            }
        });
        return out;
    }""", [])
    print("[img] imagens de produto na página renderizada:", len(imgs))
    seen = set()
    for i in imgs:
        key = i['src'].split('/').slice(-1)[0][:30]
        if key in seen: continue
        seen.add(key)
        print(f"  - {i['src'][:100]} | {i['w']}x{i['h']} visivel={i['visible']}")
    page.screenshot(path="/tmp/viadoterno_gallery.png")
    ctx.close()
log("fim")
