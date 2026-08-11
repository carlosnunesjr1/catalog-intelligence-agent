/**
 * Extrai a galeria completa de imagens de um produto usando Camoufox (browser
 * headless) quando o HTML estático não expõe todas as imagens.
 *
 * Motivação (Carlos, 10/08): lojas Magazord (ex.: Viadoterno) carregam a
 * galeria via JS — o HTML estático tem só og:image, mas o browser renderiza
 * 10+ imagens (fotos + tabela de medidas). O scrape estático perde quase tudo.
 *
 * Apenas usado quando o HTML estático tem <3 imagens de produto — assim o
 * path rápido (sem browser) continua para a maioria dos sites.
 */

import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileP = promisify(execFile);

const CAMOUFOX_SCRIPT = `
import os, sys, json
os.environ.setdefault("DISPLAY", ":99")
url = sys.argv[1]
try:
    from camoufox.sync_api import Camoufox
except Exception as e:
    print(json.dumps({"error": f"camoufox import: {e}"})); sys.exit(0)
out = []
try:
    with Camoufox(headless=True, humanize=False, os=("linux",)) as browser:
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(8000)
        out = page.evaluate("""() => {
            const seen = new Set();
            const res = [];
            document.querySelectorAll("img").forEach(i => {
                const src = i.currentSrc || i.src || "";
                if (/^(https?:)?\\/\\//.test(src) && !/logo|icon|whatsapp|favicon|avatar|pixel|tracking/i.test(src)) {
                    const full = src.startsWith("//") ? "https:" + src : src;
                    if (!seen.has(full)) { seen.add(full); res.push(full); }
                }
            });
            return res;
        }""")
        ctx.close()
except Exception as e:
    print(json.dumps({"error": f"run: {e}"})); sys.exit(0)
print(json.dumps(out))
`;

/**
 * Renderiza a página via Camoufox headless e devolve TODAS as URLs de imagem.
 * Retorna [] em falha (nunca lança).
 */
export async function extractGalleryWithBrowser(url: string): Promise<string[]> {
  try {
    const { stdout } = await execFileP('python3', ['-c', CAMOUFOX_SCRIPT, url], {
      timeout: 60000,
      maxBuffer: 4 * 1024 * 1024,
      env: {
        ...process.env,
        DISPLAY: ':99',
        LIBGL_ALWAYS_SOFTWARE: '1',
      },
    });
    const data = JSON.parse(stdout);
    if (Array.isArray(data)) {
      // filtra: só http(s), sem extensões de não-imagem óbvias, dedup
      const seen = new Set<string>();
      const out: string[] = [];
      for (const u of data) {
        if (typeof u !== 'string' || !/^https?:/i.test(u)) continue;
        if (/\.(css|js|svg|json|txt)(\?|$)/i.test(u)) continue;
        if (seen.has(u)) continue;
        seen.add(u);
        out.push(u);
      }
      return out;
    }
    return [];
  } catch (err) {
    process.stderr.write(
      `[scrape/browser] galeria via browser falhou: ${(err as Error).message}\n`
    );
    return [];
  }
}
