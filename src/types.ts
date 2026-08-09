/**
 * Contratos compartilhados do Catalog Intelligence Agent.
 * Foco: storefronts (lojas próprias) — NÃO marketplaces.
 */

/** Produto bruto vindo do ERP/distribuidor */
export interface RawProduct {
  /** EAN/GTIN quando disponível */
  ean?: string | null;
  /** Título bruto (pode ser CAIXA ALTA, com ruído) */
  title?: string | null;
  /** Marca informada no ERP (pode ser genérica/errada) */
  brand?: string | null;
  /** Descrição bruta (pode ser vazia ou copiada do ERP) */
  description?: string | null;
  /** URLs de imagem brutas (podem ser ruins) */
  image_urls?: string[];
  /** Atributos adicionais livre */
  attributes?: Record<string, string | number | null>;
}

/** Dados de referência encontrados no lookup EAN */
export interface EanLookupResult {
  ean: string;
  source: string;
  title?: string | null;
  brand?: string | null;
  description?: string | null;
  image_url?: string | null;
  ncm?: string | null;
  weight_g?: number | null;
  dimensions?: { height_cm?: number; width_cm?: number; length_cm?: number } | null;
  found: boolean;
}

/** Imagem candidata retornada pelo search_images */
export interface ImageCandidate {
  url: string;
  source: string;
  width?: number;
  height?: number;
  score?: number;
}

/** Produto enriquecido (saída final de enrich_product) */
export interface EnrichedProduct {
  ean?: string | null;
  title: string;
  slug: string;
  meta_title: string;
  meta_description: string;
  brand: string;
  bullets: string[];
  description_html: string;
  seo_keywords: string[];
  image_url: string | null;
  /** JSON-LD schema.org Product pronto para a storefront */
  schema_org: Record<string, unknown>;
  attributes: Record<string, string | number | null>;
  source_ean?: string | null;
  warnings: string[];
}

/** Resultado da validação de completeza p/ loja própria */
export interface ValidationIssue {
  field: string;
  severity: 'error' | 'warning';
  message: string;
}

export interface ValidationResult {
  score: number; // 0-100
  issues: ValidationIssue[];
  ready: boolean; // score >= threshold (default 70)
}

/** Config de execução do enriquecimento */
export interface EnrichOptions {
  /** Forçar busca de imagem (padrão: true) */
  with_images?: boolean;
  /** Forçar geração IA (padrão: true; se false usa fallback determinístico) */
  with_ai?: boolean;
  /** Idioma do conteúdo gerado (padrão: 'pt-BR') */
  locale?: string;
  /** Modelo de IA (padrão: variável de ambiente AI_MODEL) */
  model?: string;
}

export interface LookupService {
  lookup(ean: string): Promise<EanLookupResult>;
}

export const VALIDATION_THRESHOLD = 70;
export const DEFAULT_LOCALE = 'pt-BR';