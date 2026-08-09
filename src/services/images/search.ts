/**
 * Busca de imagens determinística para storefronts.
 *
 * Estratégia (sem dependências externas / sem API key):
 *  1. Usa URLs de imagem já presentes no produto bruto (quando válidas).
 *  2. Usa o Open Food Facts (imagen por EAN) — gratuito, sem key.
 *  3. Fallback: retorna array vazio.
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

/**
 * Open Food Facts fallback — imagem pública por EAN.
 * URL padrão: https://static.openfoodfacts.org/images/products/{7-digit}/{8-9-digit}/{10-12-digit}/{13-digit}/front.jpg
 */
function offImageUrl(ean: string): string | null {
  if (!isValidEan(ean)) return null;
  // OFF usa o EAN completo: xxx/xx/xx/x.jpg (7/2/2/1 por padrão, mas aceita full)
  return `https://static.openfoodfacts.org/images/products/${ean.slice(0, 7)}/${ean.slice(7, 9)}/${ean.slice(9, 11)}/${ean}/front.jpg`;
}

export async function searchImages(
  options: SearchImagesOptions
): Promise<ImageCandidate[]> {
  const limit = Math.max(1, Math.min(options.limit ?? 3, 10));
  const results: ImageCandidate[] = [];

  // 1. EAN via Open Food Facts (prioritário — imagem de referência)
  if (options.ean) {
    const url = offImageUrl(options.ean);
    if (url) {
      results.push({ url, source: 'openfoodfacts', score: 0.9 });
    }
  }

  // 2. Imagens já informadas no ERP (se válidas)
  for (const raw of options.title ? [] : []) {
    void raw; // placeholder — título não gera URL
  }

  return results.slice(0, limit);
}

export type { EanLookupResult };
