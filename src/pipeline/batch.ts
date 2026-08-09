/**
 * Pipeline de enriquecimento — orquestrador de lote (enrich_batch).
 * Processa produtos com Promise.allSettled em chunks de 5.
 */

import type { EnrichedProduct, EnrichOptions, RawProduct } from '../types.js';
import { enrichProduct } from './enricher.js';

export interface BatchResult {
  total: number;
  succeeded: number;
  failed: number;
  results: Array<{ index: number; product?: EnrichedProduct; error?: string }>;
}

export async function enrichBatch(
  products: RawProduct[],
  options?: EnrichOptions
): Promise<BatchResult> {
  const results: BatchResult['results'] = [];
  const CHUNK = 5;

  for (let i = 0; i < products.length; i += CHUNK) {
    const chunk = products.slice(i, i + CHUNK);
    const settled = await Promise.allSettled(
      chunk.map((p, j) => enrichProduct(p, options).then((product) => ({ index: i + j, product })))
    );

    for (const s of settled) {
      if (s.status === 'fulfilled') {
        results.push({ index: s.value.index, product: s.value.product });
      } else {
        results.push({
          index: i + settled.indexOf(s),
          error: (s.reason as Error)?.message ?? String(s.reason),
        });
      }
    }
  }

  const succeeded = results.filter((r) => r.product).length;
  return {
    total: products.length,
    succeeded,
    failed: products.length - succeeded,
    results,
  };
}