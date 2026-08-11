/**
 * Fallback: busca WEB por EAN quando as bases gratuitas não têm o produto.
 *
 * Motivação (Carlos, 10/08): EAN de produto brasileiro de marca própria (ex:
 * moda) NÃO existe em Open Food Facts — mas o produto EXISTE e aparece em
 * lojas/marketplaces. Em vez de devolver "não encontrado", busca na web e
 * retorna candidatos para o lojista validar.
 *
 * Implementação: usa o pacote Python `ddgs` (DuckDuckGo) via subprocess —
 * mesmo backend que o Hermes usa; o fetch Node direto é bloqueado (HTTP 202
 * anti-bot), mas o ddgs funciona.
 *
 * NUNCA lança — retorna lista vazia em falha.
 */

import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileP = promisify(execFile);

export interface WebEanCandidate {
  title: string;
  url: string;
  snippet?: string;
  source: string;
}

const DDGS_SCRIPT = `
import json, sys
try:
    from ddgs import DDGS
except Exception as e:
    print(json.dumps({"error": f"import: {e}"})); sys.exit(0)
query = sys.argv[1]
out = []
try:
    with DDGS() as d:
        for r in d.text(query, max_results=6):
            out.append({"title": r.get("title",""), "url": r.get("href",""), "snippet": r.get("body","")})
except Exception as e:
    print(json.dumps({"error": f"search: {e}"})); sys.exit(0)
print(json.dumps(out))
`;

/**
 * Busca na web o EAN + termo de produto via ddgs (DuckDuckGo, sem key).
 * Retorna candidatos com título, URL e snippet.
 */
export async function webSearchEan(
  ean: string,
  productHint?: string,
): Promise<WebEanCandidate[]> {
  // PITFALL (Carlos, 10/08): buscar EAN + product_hint juntos PODE associar o
  // EAN a um produto errado (o buscador casa o hint e ignora o EAN). Ex: EAN de
  // papel sulfite + hint "terno" → retorna terno (falso). CORRETO: buscar
  // PRIMEIRO o EAN nu (mostra o que o código realmente é) e só usar o hint como
  // segunda query, separado e com prioridade menor.
  const queries = [`"${ean}"`, productHint ? `"${ean}" ${productHint}` : ''].filter(Boolean);
  const seen = new Set<string>();
  const out: WebEanCandidate[] = [];

  for (const q of queries) {
    try {
      const { stdout } = await execFileP('python3', ['-c', DDGS_SCRIPT, q], {
        timeout: 20000,
        maxBuffer: 2 * 1024 * 1024,
      });
      const data = JSON.parse(stdout);
      if (Array.isArray(data)) {
        for (const r of data) {
          const url = r.url || '';
          const title = (r.title || '').trim();
          if (!title || title.length < 4) continue;
          // filtra lixo (barcode lookups genéricos, agregadores de busca)
          if (/barcode|upc|ean-lookup|ean-search|lookup/i.test(url) && !/mercadolivre|amazon|com\.br/i.test(url)) {
            continue;
          }
          if (seen.has(url)) continue;
          seen.add(url);
          out.push({ title, url, snippet: r.snippet, source: 'web' });
        }
      }
    } catch (err) {
      process.stderr.write(
        `[lookup/web] query '${q}' falhou: ${(err as Error).message}\n`
      );
    }
    // se o EAN nu já achou algo, NÃO contamina com o hint
    if (q === `"${ean}"` && out.length > 0) break;
  }

  return out;
}
