#!/usr/bin/env python3
"""Testa scrapeProductUrl com env correto (simula o fluxo real sem MCP)."""
import subprocess, os
env = {**os.environ, "DISPLAY": ":99", "LIBGL_ALWAYS_SOFTWARE": "1"}
code = """
import('./dist/services/scrape/product.js').then(async m => {
  const r = await m.scrapeProductUrl('https://www.viadoterno.com.br/terno-slim-comfort-cinza-escuro-semi-encerado-poliviscose-premium?inStock');
  const urls = r.image_urls || [];
  console.log('image_urls:', urls.length);
  urls.forEach(u => console.log('IMG:' + u.split('/').pop().slice(0,50)));
}).catch(e => console.log('ERRO: ' + e.message));
"""
r = subprocess.run(["node", "--input-type=module", "-e", code], capture_output=True, text=True, timeout=120, cwd="/root/catalog-intelligence-agent", env=env)
print("rc:", r.returncode)
print(r.stdout[-1200:])
print("STDERR:", r.stderr[-400:])
