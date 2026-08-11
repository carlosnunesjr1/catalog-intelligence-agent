#!/usr/bin/env python3
"""Roda o helper TS com stderr capturado para ver o erro real."""
import subprocess, os, json
env = {**os.environ, "DISPLAY": ":99", "LIBGL_ALWAYS_SOFTWARE": "1"}
code = """
import('./dist/services/scrape/browser_gallery.js').then(async m => {
  const imgs = await m.extractGalleryWithBrowser('https://www.viadoterno.com.br/terno-slim-comfort-cinza-escuro-semi-encerado-poliviscose-premium?inStock');
  console.log('COUNT:' + imgs.length);
  imgs.forEach(i => console.log('IMG:' + i.slice(0,100)));
}).catch(e => console.log('ERRO: ' + e.message));
"""
r = subprocess.run(["node", "--input-type=module", "-e", code], capture_output=True, text=True, timeout=100, cwd="/root/catalog-intelligence-agent", env=env)
print("rc:", r.returncode)
print("=== STDOUT (fim) ===")
print(r.stdout[-1200:])
print("=== STDERR (fim) ===")
print(r.stderr[-800:])
