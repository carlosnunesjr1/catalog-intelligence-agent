/**
 * SEO de imagem — gera os metadados de imagem que o catálogo completo precisa:
 * alt text, filename otimizado, caption e keywords (SEO on-page de imagens).
 * Recebe o título do produto + análise da imagem (inclui metadados EXIF).
 */

export interface ImageSeo {
  alt_text: string;
  filename: string;
  caption: string;
  keywords: string[];
  /** metadados embutidos encontrados (EXIF) */
  embedded_metadata: Record<string, unknown>;
  /** avisos de SEO */
  warnings: string[];
}

export interface ImageSeoInput {
  title: string;
  brand?: string;
  image_analysis?: Record<string, unknown> | null;
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

function stopwordFree(text: string): string {
  const stop = new Set(['de', 'da', 'do', 'das', 'dos', 'e', 'com', 'para', 'em', 'um', 'uma', 'o', 'a']);
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .split(/[^a-z0-9]+/)
    .filter((w) => w.length > 2 && !stop.has(w))
    .join(' ');
}

export function generateImageSeo(input: ImageSeoInput): ImageSeo {
  const title = (input.title || 'produto').trim();
  const brand = (input.brand || '').trim();
  const analysis = input.image_analysis ?? null;
  const warnings: string[] = [];

  // Metadados embutidos encontrados (passa adiante, sem inventar)
  const meta = (analysis?.metadata as Record<string, unknown> | undefined) ?? {};
  const hasExif = meta.has_exif === true;
  if (!hasExif) warnings.push('Imagem sem metadados EXIF embutidos — adicionar descrição/autor/copyright via ferramenta de edição');

  // Alt text: descritivo, com marca, sem excesso (ideal 80-125 chars)
  let altText = title;
  if (brand) altText = `${title} — ${brand}`;
  if (altText.length < 80) altText = `${altText} — foto de produto para loja online`;
  altText = altText.slice(0, 125);

  // Filename otimizado (slug, sem espacos/sem acentos)
  const filename = `${slugify(`${brand ? `${brand} ` : ''}${title}`)}.jpg`.slice(0, 100);

  // Caption curto (contexto da vitrine)
  const caption = `Produto: ${title}${brand ? ` · Marca: ${brand}` : ''}. Foto com fundo tratado para catálogo online.`;

  // Keywords = palavras do título + categoria + complementos
  const baseWords = stopwordFree(title).split(' ').filter(Boolean);
  const seed = `${brand} ${baseWords.join(' ')}`.toLowerCase();
  const keywords = [...new Set([...seed.split(/[^a-z0-9]+/).filter((w) => w.length > 2), 'produto', 'comprar', 'loja online'].filter(Boolean))].slice(0, 8);

  return { alt_text: altText, filename, caption, keywords, embedded_metadata: meta, warnings };
}