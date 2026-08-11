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
import { sanitizeAiOutput, stripTechnicalLeaks } from '../utils/guardrails.js';
import { generateImageSeo } from '../services/images/seo.js';

/** Palavras que ficam minúsculas em Title Case (pt-BR) */
const SMALL_WORDS = new Set(['de', 'da', 'do', 'das', 'dos', 'e', 'com', 'para', 'em']);

/**
 * Repara JSON truncado (modelos free cortam no meio quando max_tokens estoura).
 * Estratégia: caminha o texto fechando strings não-terminadas e colchetes/chaves
 * abertos, até obter um JSON parseável. Retorna string reparada ou null.
 */
export function repairTruncatedJson(text: string): string | null {
  const t = text.trim();
  if (!t) return null;

  // Se já é parseável, devolve direto
  try {
    JSON.parse(t);
    return t;
  } catch {
    /* segue */
  }

  // Encontra o primeiro '{' e usa tudo a partir dele
  const start = t.indexOf('{');
  if (start === -1) return null;
  let s = t.slice(start);

  // Remove texto após o último '}' (lixo pós-JSON, ex.: explicações)
  const lastClose = s.lastIndexOf('}');
  if (lastClose !== -1) s = s.slice(0, lastClose + 1);

  // Fecha strings e estruturas pendentes, caractere a caractere
  const out: string[] = [];
  const stack: string[] = [];
  let inString = false;
  let escaped = false;
  let repaired = false;

  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (inString) {
      out.push(ch);
      if (escaped) {
        escaped = false;
      } else if (ch === '\\') {
        escaped = true;
      } else if (ch === '"') {
        inString = false;
      }
      continue;
    }
    if (ch === '"') {
      inString = true;
      out.push(ch);
      continue;
    }
    if (ch === '{' || ch === '[') {
      stack.push(ch === '{' ? '}' : ']');
      out.push(ch);
      continue;
    }
    if (ch === '}' || ch === ']') {
      if (stack.length && stack[stack.length - 1] === ch) {
        stack.pop();
      } else {
        repaired = true; // fecha extra — ignora
        continue;
      }
      out.push(ch);
      continue;
    }
    out.push(ch);
  }

  // Fecha string pendente
  if (inString) {
    out.push('"');
    repaired = true;
  }
  // Fecha estruturas pendentes (na ordem inversa)
  while (stack.length) {
    out.push(stack.pop()!);
    repaired = true;
  }

  const candidate = out.join('');
  try {
    JSON.parse(candidate);
    return repaired ? candidate : null;
  } catch {
    return null;
  }
}

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

/** Bullets determinísticos de fallback (sem IA) — extrai características reais do título. */
function fallbackBullets(title: string, brand: string): string[] {
  const t = toTitleCase(title);
  // extrai características do título: cor, material, modelo (palavras-chave reais)
  const words = title
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .split(/[^a-z0-9]+/)
    .filter((w) => w.length > 3 && !SMALL_WORDS.has(w) && !['produto', 'com', 'para', 'novo', 'original', 'premium', 'masculino', 'feminino', 'unissex'].includes(w));
  const feats = [...new Set(words)].slice(0, 3);
  const featsList = feats.length
    ? feats.map((f) => `Acabamento e material em destaque: ${f}.`).join(' ')
    : '';
  const brandText =
    brand && brand.toLowerCase() !== 'sem marca' && brand.toLowerCase() !== 'marca'
      ? toTitleCase(brand)
      : '';

  const bullets: string[] = [];
  if (feats.length) {
    bullets.push(`Material e acabamento cuidadosamente selecionados (${feats.join(', ')}).`);
  }
  if (brandText) {
    bullets.push(`Marca ${brandText} — produto original com procedência garantida.`);
  } else {
    bullets.push('Produto novo, original e com procedência garantida.');
  }
  bullets.push('Conforto e durabilidade para o uso no dia a dia.');
  bullets.push('Design versátil, combina com diferentes ocasiões e estilos.');
  if (featsList) bullets.push(featsList);
  return bullets.slice(0, 5);
}

function fallbackDescription(title: string, bullets: string[]): string {
  const items = bullets.map((b) => `<li>${b}</li>`).join('');
  return `<p>${toTitleCase(title)} — qualidade, durabilidade e acabamento pensados para o seu dia a dia.</p><ul>${items}</ul>`;
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

/** Remove emojis e símbolos decorativos (emojis em campos de produto trunca payload e reduz conversão). */
function stripEmojis(text: string): string {
  return text.replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2190}-\u{21FF}\u{2B00}-\u{2BFF}\u{FE0F}]/gu, '').replace(/\s{2,}/g, ' ').replace(/^[ .]+|[ .]+$/g, '').trim();
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
      price: product.price,
      attributes: product.attributes ?? {},
      locale,
      task: 'Gere um anúncio otimizado para LOJA PRÓPRIA (não marketplace). USE os atributos/descrição fornecidos para criar conteúdo ESPECÍFICO do produto (material, cor, modelo, medidas, uso) — NUNCA frases genéricas tipo "produto de qualidade" ou "marca X: confiança". Retorne: bullets (3-5, beneficiamentos concretos e específicos SEM emojis), description_html (parágrafos <p> mobile-first, específicos, sem emojis), meta_title (max 60 chars), meta_description (max 160 chars), seo_keywords (5-8). PROIBIDO emojis e frases genéricas.',
    });

    const ai = await generate(prompt, { system: sys, temperature: 0.5, maxTokens: 3000 });
    if (ai) {
      let jsonText = ai.trim();
      try {
        // Extrai JSON de resposta com fences markdown ```json ... ``` (modelos free o fazem)
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
        // Reparador de JSON truncado: modelos free às vezes cortam o JSON no meio
        // (max_tokens estourou). Tenta fechar strings/colchetes até o parse passar.
        try {
          const repaired = repairTruncatedJson(jsonText);
          if (repaired) {
            const clean = sanitizeAiOutput(JSON.parse(repaired));
            if (Array.isArray(clean.bullets)) bullets = clean.bullets.slice(0, 5);
            if (typeof clean.description_html === 'string') descriptionHtml = clean.description_html;
            if (typeof clean.meta_title === 'string') metaTitle = clean.meta_title.slice(0, 60);
            if (typeof clean.meta_description === 'string') metaDescription = clean.meta_description.slice(0, 160);
            if (Array.isArray(clean.seo_keywords)) seo = clean.seo_keywords.slice(0, 8);
            process.stderr.write(`[enricher] JSON reparado (truncado) — IA aproveitada\n`);
          } else {
            throw err;
          }
        } catch (err2) {
          warnings.push('IA retornou JSON inválido — fallback determinístico');
          process.stderr.write(`[enricher] JSON parse falhou: ${(err as Error).message}\n`);
        }
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

  // SANITIZA EMOJIS + VAZAMENTO TÉCNICO (práticas 2026: copy comercial p/ humanos)
  bullets = bullets.map(stripEmojis).map(stripTechnicalLeaks);
  descriptionHtml = stripTechnicalLeaks(stripEmojis(descriptionHtml));
  metaTitle = stripTechnicalLeaks(stripEmojis(metaTitle)).slice(0, 60);
  metaDescription = stripTechnicalLeaks(stripEmojis(metaDescription)).slice(0, 160);

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