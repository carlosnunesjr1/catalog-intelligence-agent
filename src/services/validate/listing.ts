/**
 * Validação de completeza para storefronts (lojas próprias).
 *
 * Calcula um score 0-100 baseado na presença de campos críticos
 * (título, descrição, imagem, SKU/EAN, schema.org) e retorna issues.
 *
 * Regra de corte: score >= 70 → ready.
 */

import type { ValidationIssue, ValidationResult } from '../../types.js';

interface ValidateRules {
  require_schema_org?: boolean;
  require_image?: boolean;
}

export function validateListing(
  listing: Record<string, unknown>,
  rules?: ValidateRules
): ValidationResult {
  const issues: ValidationIssue[] = [];
  let score = 100;

  const r = {
    require_schema_org: rules?.require_schema_org ?? true,
    require_image: rules?.require_image ?? true,
  };

  // Título
  const title = listing.title;
  if (!title || typeof title !== 'string' || title.trim().length < 5) {
    issues.push({ field: 'title', severity: 'error', message: 'Título ausente ou muito curto' });
    score -= 25;
  } else if (title.trim().length < 20) {
    issues.push({ field: 'title', severity: 'warning', message: 'Título curto — considere expandir' });
    score -= 5;
  }

  // Descrição
  const desc = listing.description_html ?? listing.description;
  if (!desc || typeof desc !== 'string' || desc.trim().length < 20) {
    issues.push({ field: 'description_html', severity: 'error', message: 'Descrição ausente ou insuficiente' });
    score -= 20;
  }

  // Imagem
  if (r.require_image) {
    const img = listing.image_url;
    if (!img || typeof img !== 'string') {
      issues.push({ field: 'image_url', severity: 'error', message: 'Imagem de produto ausente' });
      score -= 15;
    }
  }

  // Bullets
  const bullets = listing.bullets;
  if (!Array.isArray(bullets) || bullets.length < 3) {
    issues.push({ field: 'bullets', severity: 'warning', message: 'Poucos bullets (mínimo 3)' });
    score -= 10;
  }

  // SKU / EAN
  const ean = listing.ean;
  if (!ean && !listing.sku) {
    issues.push({ field: 'ean', severity: 'warning', message: 'EAN/SKU ausente' });
    score -= 5;
  }

  // SEO
  if (!listing.meta_title || typeof listing.meta_title !== 'string' || listing.meta_title.length > 60) {
    issues.push({ field: 'meta_title', severity: 'warning', message: 'meta_title ausente ou > 60 chars' });
    score -= 5;
  }
  if (!listing.meta_description || typeof listing.meta_description !== 'string' || listing.meta_description.length > 160) {
    issues.push({ field: 'meta_description', severity: 'warning', message: 'meta_description ausente ou > 160 chars' });
    score -= 5;
  }

  // Schema.org
  if (r.require_schema_org) {
    const schema = listing.schema_org;
    if (!schema || typeof schema !== 'object' || !(schema as Record<string, unknown>)['@type']) {
      issues.push({ field: 'schema_org', severity: 'error', message: 'schema.org JSON-LD ausente' });
      score -= 20;
    }
  }

  // Keywords SEO
  const kw = listing.seo_keywords;
  if (!Array.isArray(kw) || kw.length < 3) {
    issues.push({ field: 'seo_keywords', severity: 'warning', message: 'seo_keywords insuficiente (mínimo 3)' });
    score -= 5;
  }

  // ── Regras de MODA (vestuário) ─────────────────────────────────────
  if (isFashion(listing)) {
    const attrs = (listing.attributes ?? {}) as Record<string, unknown>;
    // Grade de tamanhos
    const hasSize = attrs['tamanhos'] || attrs['size_guide'] || attrs['grade'] || listing.size_guide;
    if (!hasSize) {
      issues.push({ field: 'size_guide', severity: 'warning', message: 'Grade de tamanhos ausente — essencial p/ moda (P/M/G ou numérica)' });
      score -= 5;
    }
    // Composição/tecido
    const hasFabric = attrs['composicao'] || attrs['tecido'] || attrs['material'] || listing.composicao;
    if (!hasFabric) {
      issues.push({ field: 'composicao', severity: 'warning', message: 'Composição/tecido ausente — obrigatório p/ moda (ex.: 60% algodão, 40% poliéster)' });
      score -= 5;
    }
    // Cor
    const hasColor = attrs['cor'] || attrs['color'] || listing.cor;
    if (!hasColor) {
      issues.push({ field: 'cor', severity: 'warning', message: 'Cor não informada — ajuda filtros da loja' });
      score -= 5;
    }
    // Guia de medidas
    const hasGuide = attrs['guia_medidas'] || attrs['measurements'] || listing.medidas;
    if (!hasGuide) {
      issues.push({ field: 'medidas', severity: 'warning', message: 'Guia de medidas ausente — reduz trocas/devoluções em vestuário' });
      score -= 5;
    }
  }

  score = Math.max(0, Math.min(100, score));

  return {
    score,
    issues,
    ready: score >= 70,
  };
}

/** Detecta segmento moda/vestuário por campos, attributes ou categoria. */
export function isFashion(listing: Record<string, unknown>): boolean {
  const attrs = (listing.attributes ?? {}) as Record<string, unknown>;
  const category = String(listing.category ?? listing.categoria ?? attrs['categoria'] ?? '').toLowerCase();
  const title = String(listing.title ?? '').toLowerCase();
  const hay = `${category} ${title} ${Object.keys(attrs).join(' ')} ${Object.values(attrs).join(' ')}`.toLowerCase();
  const FASHION_TERMS = [
    'moda', 'roupa', 'vestuário', 'fashion', 'terno', 'blusa', 'calça', 'calca', 'vestido',
    'camisa', 'camiseta', 'moletom', 'jaqueta', 'saia', 'short', 'bermuda', 'casaco',
    'tamanho', 'tamanhos', 'composicao', 'tecido', 'size_guide', 'cor',
  ];
  return FASHION_TERMS.some((t) => hay.includes(t));
}

export type { ValidateRules };
