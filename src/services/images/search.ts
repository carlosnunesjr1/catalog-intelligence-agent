/**
 * Busca de imagens determinística para storefronts.
 *
 * Estratégia (sem API key obrigatória):
 *  1. EAN → Open Food Facts (imagem de referência por código de barras)
 *  2. Título (marca própria / sem EAN) → Unsplash Source (sem key) + Pexels (se PEXELS_KEY)
 *
 * NUNCA lança — erros são registrados no stderr e retorna [].
 */

import type { EanLookupResult, ImageCandidate } from '../../types.js';
import { isValidEan } from '../lookup/ean.js';

export interface SearchImagesOptions {
  ean?: string;
  title?: string;
  limit?: number;
}

/** Open Food Facts — imagem pública por EAN (7/2/2/1 dígitos). */
function offImageUrl(ean: string): string | null {
  if (!isValidEan(ean)) return null;
  return `https://static.openfoodfacts.org/images/products/${ean.slice(0, 7)}/${ean.slice(7, 9)}/${ean.slice(9, 11)}/${ean}/front.jpg`;
}

/** Gera query slug-safe para busca textual (sem acentos, + separador). */
function titleQuery(title: string): string {
  const clean = title
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9 ]+/g, ' ')
    .trim();
  return clean.split(/\s+/).filter((w) => w.length > 2).slice(0, 4).join('+') || clean || 'produto';
}

/** Unsplash Source — URL direta de imagem por query (sem key). */
function unsplashSourceUrl(query: string): string {
  const encoded = encodeURIComponent(query.replace(/\+/g, ','));
  return `https://source.unsplash.com/800x800/?${encoded}`;
}

/** Pexels — API oficial; exige PEXELS_KEY (opcional). */
async function pexelsImages(query: string, limit: number): Promise<string[]> {
  const key = process.env.PEXELS_KEY;
  if (!key) return [];
  try {
    const res = await fetch(
      `https://api.pexels.com/v1/search?query=${encodeURIComponent(query.replace(/\+/g, ' '))}&per_page=${Math.min(limit, 10)}`,
      { headers: { Authorization: key }, signal: AbortSignal.timeout(8000) }
    );
    if (!res.ok) return [];
    const data = (await res.json()) as { photos?: Array<{ src?: { large?: string } }> };
    return (data.photos ?? []).map((p) => p.src?.large ?? '').filter(Boolean);
  } catch (err) {
    process.stderr.write(`[images/search] Pexels falhou: ${(err as Error).message}\n`);
    return [];
  }
}

export async function searchImages(options: SearchImagesOptions): Promise<ImageCandidate[]> {
  const limit = Math.max(1, Math.min(options.limit ?? 3, 10));
  const results: ImageCandidate[] = [];

  // 1. EAN via Open Food Facts (prioritário — identidade real do produto)
  if (options.ean) {
    const url = offImageUrl(options.ean);
    if (url) results.push({ url, source: 'openfoodfacts', score: 0.95 });
  }

  // 2. Título: busca textual como fallback (marca própria / moda sem EAN)
  if (results.length < limit && options.title) {
    const query = titleQuery(options.title);
    if (query) {
      const needed = limit - results.length;

      // 2a. Unsplash Source (sem key)
      results.push({ url: unsplashSourceUrl(query), source: 'unsplash', score: 0.8 });

      // 2b. Pexels (se key configurada)
      if (results.length < limit) {
        const pexels = await pexelsImages(query, Math.max(needed, 3));
        for (const p of pexels) {
          if (results.length < limit && !results.some((r) => r.url === p)) {
            results.push({ url: p, source: 'pexels', score: 0.7 });
          }
        }
      }
    }
  }

  return results.slice(0, limit);
}

export type { EanLookupResult };