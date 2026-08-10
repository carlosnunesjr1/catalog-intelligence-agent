/**
 * Pipeline de enriquecimento de produto — STOREFRONT (loja própria).
 * Entrada: produto bruto de ERP → Saída: produto pronto para a loja.
 *
 * Sem AI_API_KEY o pipeline roda 100% determinístico (demo offline).
 */

import type { EnrichedProduct, EnrichOptions, RawProduct } from '../types.js';
import { generate } from '../services/ai/client.js';
import { searchImages } from '../services/images/search.js';
import { DEFAULT_LOCALE } from '../types.js';
import { sanitizeAiOutput } from '../utils/guardrails.js';
import { generateImageSeo } from '../services/images/seo.js';

/** Palavras que ficam minúsculas em Title Case (pt-BR) */
const SMALL_WORDS = new Set(['de', 'da', 'do', 'das', 'dos', 'e', 'com', 'para', 'em']);

/** Expande abreviações comuns do catálogo bruto. */
const ABBREVIATIONS: Record<string, string> = {
  'cf/': 'com',
  'c/': 'com',
  'p/': 'para',
  's/': 'sem',
  'und': 'unidade',
  'pct': 'pacote',
  'cx': 'caixa',
  'cxs': 'caixas',
  'ref': 'referencia',
  'tam': 'tamanho',
  'volt': 'voltagem',
};

const NOISE_PATTERNS = [
  /^produto\s*/i,
  /^novo\s*/i,
  /^promo[cç][aã]o\s*/i,
  /\s+-\s*$/,
  /^\s*[-–—]\s*/,
  /\s{2,}/g,
];

function cleanRawTitle(raw: string): string {
  let t = raw.trim().toLowerCase();
  for (const re of NOISE_PATTERNS) t = t.replace(re, '');
  // Troca abreviações
  const words = t.split(/\s+/).filter(Boolean);
  const expanded = words.map((w) => ABBREVIATIONS[w.toLowerCase()] ?? w);
  return expanded.join(' ');
}

function toTitleCase(text: string): string {
  const words = text.split(/\s+/).filter(Boolean);
  return words
    .map((w, i) => {
      const lower = w.toLowerCase();
      if (i > 0 && SMALL_WORDS.has(lower)) return lower;
      return lower.charAt(0).toUpperCase() + lower.slice(1);
    })
    .join(' ');
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);
}

function buildSchemaOrg(p: {
  title: string;
  brand: string;
  ean: string | null;
  description: string;
  image_url: string | null;
}): Record<string, unknown> {
  const schema: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: p.title,
    brand: { '@type': 'Brand', name: p.brand || 'Marca' },
    description: p.description,
  };
  if (p.ean) {
    schema.sku = p.ean;
    schema.gtin13 = p.ean;
  }
  if (p.image_url) schema.image = p.image_url;
  return schema;
}

/** Bullets determinísticos de fallback (sem IA). */
function fallbackBullets(title: string, brand: string): string[] {
  return [
    `${toTitleCase(title)} — produto de qualidade com garantia do fabricante.`,
    brand && brand.toLowerCase() !== 'sem marca'
      ? `Marca ${toTitleCase(brand)}: confiança e procedência.`
      : 'Produto novo, original e com procedência garantida.',
    'Ideal para uso doméstico e profissional.',
  ];
}

function fallbackDescription(title: string, bullets: string[]): string {
  const items = bullets.map((b) => `<li>${b}</li>`).join('');
  return `<p>${toTitleCase(title)} — a escolha certa para quem busca qualidade e performance.</p><ul>${items}</ul>`;
}

/** Extrai keywords determinísticas do título (5-8 palavras-chave). */
function seoKeywords(title: string): string[] {
  const words = title
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .split(/[^a-z0-9]+/)
    .filter((w) => w.length > 2 && !SMALL_WORDS.has(w));
  const uniq = [...new Set(words)];
  return uniq.slice(0, 8).length >= 5 ? uniq.slice(0, 8) : [...uniq, 'comprar', 'online', 'loja'].slice(0, 8);
}

function cleanBrand(brand: string | null | undefined): string {
  const b = (brand ?? '').trim();
  if (/^sem marca$/i.test(b) || /^generi[coa]$/i.test(b) || /^marca$/i.test(b) || !b) {
    return 'Marca';
  }
  return toTitleCase(b);
}

export async function enrichProduct(
  product: RawProduct,
  options?: EnrichOptions
): Promise<EnrichedProduct> {
  const withImages = options?.with_images ?? true;
  const withAi = options?.with_ai ?? true;
  const locale = options?.locale ?? DEFAULT_LOCALE;

  const ean = product.ean?.replace(/\D/g, '') || null;
  const rawTitle = product.title?.trim() || (ean ? `Produto ${ean}` : 'Produto sem título');
  const cleanTitle = cleanRawTitle(rawTitle);
  const title = toTitleCase(cleanTitle);
  const brand = cleanBrand(product.brand);
  const warnings: string[] = [];

  // ── IA (opcional) ──────────────────────────────────────────────────
  let bullets: string[] = [];
  let descriptionHtml = '';
  let metaTitle = '';
  let metaDescription = '';
  let seo: string[] = [];

  if (withAi) {
    const sys = locale === 'pt-BR'
      ? 'Você é especialista em e-commerce (storefront/loja própria). Responda SOMENTE JSON válido.'
      : 'You are an e-commerce (storefront) expert. Reply ONLY with valid JSON.';

    const prompt = JSON.stringify({
      title: rawTitle,
      brand: product.brand,
      description: product.description,
      locale,
      task: 'Gere um anúncio otimizado para LOJA PRÓPRIA (não marketplace). Retorne: bullets (3-5, beneficiamentos com emoji), description_html (parágrafos <p> mobile-first), meta_title (max 60 chars), meta_description (max 160 chars), seo_keywords (5-8).',
    });

    const ai = await generate(prompt, { system: sys, temperature: 0.5, maxTokens: 3000 });
    if (ai) {
      try {
        // Extrai JSON de resposta com fences markdown ```json ... ``` (modelos free o fazem)
        let jsonText = ai.trim();
        const fence = jsonText.match(/```(?:json)?\s*([\s\S]*?)```/);
        if (fence) jsonText = fence[1].trim();
        // fallback: pega o primeiro {...} balanceado
        if (!jsonText.startsWith('{')) {
          const start = jsonText.indexOf('{');
          const end = jsonText.lastIndexOf('}');
          if (start !== -1 && end > start) jsonText = jsonText.slice(start, end + 1);
        }
        const parsed = JSON.parse(jsonText);
        const clean = sanitizeAiOutput(parsed);
        if (Array.isArray(clean.bullets)) bullets = clean.bullets.slice(0, 5);
        if (typeof clean.description_html === 'string') descriptionHtml = clean.description_html;
        if (typeof clean.meta_title === 'string') metaTitle = clean.meta_title.slice(0, 60);
        if (typeof clean.meta_description === 'string') metaDescription = clean.meta_description.slice(0, 160);
        if (Array.isArray(clean.seo_keywords)) seo = clean.seo_keywords.slice(0, 8);
      } catch (err) {
        warnings.push('IA retornou JSON inválido — fallback determinístico');
        process.stderr.write(`[enricher] JSON parse falhou: ${(err as Error).message}\n`);
      }
    } else {
      warnings.push('IA indisponível (sem AI_API_KEY) — modo determinístico');
    }
  } else {
    warnings.push('with_ai=false — modo determinístico');
  }

  // Fallback determinístico
  if (bullets.length === 0) bullets = fallbackBullets(title, brand);
  if (!descriptionHtml) descriptionHtml = fallbackDescription(title, bullets);
  if (!metaTitle) metaTitle = `${title} — Compre Online`;
  if (!metaDescription) metaDescription = `${title}. ${bullets[0] ?? ''}`.slice(0, 160);
  if (seo.length === 0) seo = seoKeywords(cleanTitle);

  // ── Imagem (opcional) ──────────────────────────────────────────────
  let imageUrl: string | null = null;
  let imageProcessed = false;
  let imageAnalysis: Record<string, unknown> | null = null;
  if (withImages) {
    const own = product.image_urls?.find((u) => /^https?:\/\//.test(u));
    const candidate = own ?? (ean ? (await searchImages({ ean, title: cleanTitle, limit: 1 }))[0]?.url ?? null : null);
    if (candidate) {
      // Analisa primeiro (diagnóstico visual), depois processa fundo branco
      try {
        const { analyzeImageUrl } = await import('../services/images/analyze.js');
        const analysis = await analyzeImageUrl(candidate);
        if (analysis && !analysis.error) {
          imageAnalysis = analysis as unknown as Record<string, unknown>;
          if (analysis.issues?.length) warnings.push(`Imagem: ${analysis.issues.join('; ')}`);
        }
      } catch {
        /* análise não é bloqueio */
      }
      try {
        const { processImage } = await import('../services/images/process.js');
        const { processed } = await processImage(candidate);
        imageUrl = processed.url;
        imageProcessed = processed.background_removed;
        if (processed.warning) warnings.push(`Imagem: ${processed.warning}`);
        if (processed.background_removed) warnings.push('Fundo da imagem removido → fundo branco (compliance storefront)');
      } catch {
        imageUrl = candidate; // fallback: URL original
      }
    } else {
      warnings.push('Imagem não encontrada — adicionar manualmente antes de publicar');
    }
  }

  const slug = slugify(title);
  const attributes: Record<string, string | number | null> = {
    ...(product.attributes ?? {}),
    brand,
  };

  // SEO da imagem: alt text, filename, caption, keywords (se houver imagem)
  let imageSeo: Record<string, unknown> | null = null;
  if (imageUrl || imageAnalysis) {
    try {
      imageSeo = generateImageSeo({
        title,
        brand: brand === 'Marca' ? undefined : brand,
        image_analysis: imageAnalysis,
      }) as unknown as Record<string, unknown>;
    } catch {
      /* SEO de imagem é enriquecimento, nunca bloqueio */
    }
  }

  return {
    ean,
    title,
    slug,
    meta_title: metaTitle,
    meta_description: metaDescription,
    brand,
    bullets,
    description_html: descriptionHtml,
    seo_keywords: seo,
    image_url: imageUrl,
    schema_org: buildSchemaOrg({ title, brand, ean, description: descriptionHtml, image_url: imageUrl }),
    attributes,
    source_ean: ean,
    warnings,
    image_processed: imageProcessed,
    image_analysis: imageAnalysis,
    image_seo: imageSeo,
  };
}