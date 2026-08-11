#!/usr/bin/env python3
"""Testa o helper TS extractGalleryWithBrowser (via node) — precisa LIBGL_ALWAYS_SOFTWARE."""
import subprocess, os, json
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"
os.environ["DISPLAY"] = ":99"
code = """
import('./dist/services/scrape/browser_gallery.js').then(async m => {
  const imgs = await m.extractGalleryWithBrowser('https://www.viadoterno.com.br/terno-slim-comfort-cinza-escuro-semi-encerado-poliviscose-premium?inStock');
  console.log(JSON.stringify({count: imgs.length, imgs: imgs.slice(0,15)}));
}).catch(e => console.log('ERRO: ' + e.message));
"""
r = subprocess.run(["node", "--input-type=module", "-e", code], capture_output=True, text=True, timeout=100, cwd="/root/catalog-intelligence-agent")
print("rc:", r.returncode)
print("stdout:", r.stdout[-1500:])
print("stderr:", r.stderr[-500:])
