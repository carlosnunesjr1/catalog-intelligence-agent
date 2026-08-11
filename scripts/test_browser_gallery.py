#!/usr/bin/env python3
"""Testa o extractGalleryWithBrowser (mesmo código do helper TS) na Viadoterno."""
import os, time, json
os.environ.setdefault("DISPLAY", ":99")
from camoufox.sync_api import Camoufox

URL = "https://www.viadoterno.com.br/terno-slim-comfort-cinza-escuro-semi-encerado-poliviscose-premium?inStock"

with Camoufox(headless=True, humanize=False, os=("linux",)) as browser:
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    page = ctx.new_page()
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(8000)
        imgs = page.evaluate("""() => {
            const seen = new Set();
            const res = [];
            document.querySelectorAll('img').forEach(i => {
                const src = i.currentSrc || i.src || '';
                if (/^(https?:)?\\/\\//.test(src) && !/logo|icon|whatsapp|favicon|avatar|pixel|tracking/i.test(src)) {
                    const full = src.startsWith('//') ? 'https:' + src : src;
                    if (!seen.has(full)) { seen.add(full); res.push(full); }
                }
            });
            return res;
        }""")
        print("imagens headless:", len(imgs))
        for i in imgs:
            print("  -", i[:110])
    except Exception as e:
        print("ERRO:", str(e)[:150])
    ctx.close()
