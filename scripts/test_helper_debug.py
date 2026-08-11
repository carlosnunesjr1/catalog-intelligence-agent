#!/usr/bin/env python3
"""Testa o helper TS mas capturando o stderr interno do subprocess python do Camoufox."""
import subprocess, os, json
env = {**os.environ, "DISPLAY": ":99", "LIBGL_ALWAYS_SOFTWARE": "1"}
code = """
// reimplementa o execFileP do helper para ver o stderr do python
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const execFileP = promisify(execFile);
const script = \`
import os, sys, json
os.environ.setdefault("DISPLAY", ":99")
url = sys.argv[1]
try:
    from camoufox.sync_api import Camoufox
except Exception as e:
    print(json.dumps({"error": f"import: {e}"})); sys.exit(0)
out = []
try:
    with Camoufox(headless=True, humanize=False, os=("linux",)) as browser:
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(8000)
        out = page.evaluate("() => { const seen=new Set(); const res=[]; document.querySelectorAll('img').forEach(i=>{ const s=i.currentSrc||i.src||''; if(/^(https?:)?\\\\/\\\\//.test(s)&&!/logo|icon|whatsapp|favicon|avatar|pixel|tracking/i.test(s)){ const f=s.startsWith('//')?'https:'+s:s; if(!seen.has(f)){seen.add(f);res.push(f);} } }); return res; }")
        ctx.close()
except Exception as e:
    print(json.dumps({"error": f"run: {e}"})); sys.exit(0)
print(json.dumps(out))
\`;
try {
  const { stdout, stderr } = await execFileP('python3', ['-c', script, 'https://www.viadoterno.com.br/terno-slim-comfort-cinza-escuro-semi-encerado-poliviscose-premium?inStock'], { timeout: 60000, maxBuffer: 4*1024*1024, env: { ...process.env, DISPLAY: ':99', LIBGL_ALWAYS_SOFTWARE: '1' } });
  console.log('STDOUT:', stdout.slice(0, 500));
  console.log('STDERR:', stderr.slice(-800));
} catch (e) { console.log('EXEC ERRO:', e.message.slice(0, 300)); }
"""
r = subprocess.run(["node", "--input-type=module", "-e", code], capture_output=True, text=True, timeout=100, cwd="/root/catalog-intelligence-agent", env=env)
print("rc:", r.returncode)
print(r.stdout[-1500:])
print("NODE STDERR:", r.stderr[-400:])
