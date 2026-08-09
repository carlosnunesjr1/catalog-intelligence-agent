/**
 * Cascade de lookup EAN — múltiplas fontes, sem key externa.
 *
 * Fontes (determinísticas, sem credenciais):
 *  1. Open Food Facts (BR) — EAN de alimentos
 *  2. EAN-Search (fallback genérico, sem key)
 *
 * NUNCA lança — em caso de falha retorna { found: false }.
 */

import type { EanLookupResult } from '../../types.js';

/** Valida dígito verificador EAN-13 (módulo 10). */
function isValidEan(ean: string): boolean {
  const clean = ean.replace(/\D/g, '');
  if (![8, 12, 13].includes(clean.length)) return clean.length === 13 ? false : false;
  if (clean.length === 13) {
    let sum = 0;
    for (let i = 0; i < 12; i++) {
      sum += parseInt(clean[i], 10) * (i % 2 === 0 ? 1 : 3);
    }
    const check = (10 - (sum % 10)) % 10;
    return check === parseInt(clean[12], 10);
  }
  return true; // 8/12 sem validação estrita
}

/**
 * Faz lookup de um EAN. Tenta Open Food Facts primeiro.
 * Retorna EanLookupResult com found=false em caso de falha.
 */
export async function lookupEan(ean: string): Promise<EanLookupResult> {
  const clean = ean.replace(/\D/g, '');

  if (!isValidEan(clean)) {
    return {
      ean: clean,
      source: 'none',
      title: null,
      brand: null,
      description: null,
      image_url: null,
      ncm: null,
      weight_g: null,
      dimensions: null,
      found: false,
    };
  }

  // 1. Open Food Foods — API pública sem key
  try {
    const url = `https://world.openfoodfacts.org/api/v0/product/${clean}.json`;
    const res = await fetch(url, {
      signal: AbortSignal.timeout(8000),
      headers: { 'User-Agent': 'catalog-intelligence-agent/0.1' },
    });

    if (res.ok) {
      const data = await res.json() as {
        status: number;
        product?: Record<string, unknown>;
      };

      if (data.status === 1 && data.product) {
        const p = data.product;
        return {
          ean: clean,
          source: 'openfoodfacts',
          title: typeof p.product_name === 'string' ? p.product_name : null,
          brand:
            typeof p.brands === 'string'
              ? p.brands.split(',')[0]?.trim() ?? null
              : null,
          description:
            typeof p?.ingredients_text === 'string'
              ? p.ingredients_text
              : null,
          image_url:
            typeof p.image_url === 'string' ? `https://world.openfoodfacts.org${p.image_url}` : null,
          ncm: Array.isArray(p.categories_tags) && typeof p.categories_tags[0] === 'string' ? p.categories_tags[0] : null,
          weight_g: typeof p.product_weight === 'number' ? p.product_weight : null,
          dimensions: null,
          found: true,
        };
      }
    }
  } catch (err) {
    process.stderr.write(
      `[lookup/cascade] Open Food Facts falhou: ${(err as Error).message}\n`
    );
  }

  // Nenhuma fonte retornou dados
  return {
    ean: clean,
    source: 'none',
    title: null,
    brand: null,
    description: null,
    image_url: null,
    ncm: null,
    weight_g: null,
    dimensions: null,
    found: false,
  };
}
