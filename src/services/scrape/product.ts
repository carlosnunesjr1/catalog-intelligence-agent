/**
 * Raspagem estruturada de página de produto (storefront do cliente).
 * Extrai: título, preço, descrição, meta description, imagens (og:image),
 * marca, schema.org JSON-LD (Product), EAN/GTIN quando no schema.
 *
 * NUNCA lança — em falha retorna um objeto com erro e campos vazios.
 */

import { isValidEan } from '../lookup/ean.js';
import { promises as fs } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const SCRAPE_CACHE = path.join(os.tmpdir(), 'catalog-agent-scrape-cache.json');
const SCRAPE_TTL_MS = 6 * 60 * 60 * 1000;

export interface ScrapedProduct {
  url: string;
  title: string;
  price?: number | null;
  price_text?: string | null;
  description: string;
  meta_description: string;
  image_url?: string | null;
  image_urls: string[];
  brand?: string | null;
  ean?: string | null;
  sku?: string | null;
  currency?: string | null;
  schema_org: Record<string, unknown> | null;
  found: boolean;
  error?: string;
}

const UA =
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36';

/** Valida se a URL é http(s) e parece de produto/loja (sem travas locais). */
export function isSafeUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return u.protocol === 'http:' || u.protocol === 'https:';
  } catch {
    return false;
  }
}

function clean(s: string): string {
  return s.replace(/\s+/g, ' ').trim();
}

function unescapeHtml(s: string): string {
  return s
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&nbsp;/g, ' ');
}

/** Extrai o primeiro JSON-LD com @type Product (ou Offer/ItemPage com product). */
function extractSchemaLd(html: string): Record<string, unknown> | null {
  const re = /<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(html)) !== null) {
    try {
      const data = JSON.parse(unescapeHtml(m[1]));
      const arr = Array.isArray(data) ? data : [data];
      for (const item of arr) {
        const type = Array.isArray(item['@type']) ? item['@type'].join(',') : String(item['@type'] || '');
        if (/Product/i.test(type)) return item as Record<string, unknown>;
      }
    } catch {
      /* JSON-LD inválido — ignora e segue p/ próxima tag */
    }
  }
  return null;
}

/** Extrai EAN/GTIN (13 dígitos) do HTML e do schema. */
function extractEan(html: string, schema: Record<string, unknown> | null): string | null {
  const candidates: unknown[] = [];
  if (schema) {
    for (const k of ['gtin', 'gtin13', 'gtin14', 'ean', 'mpn']) {
      const v = schema[k];
      if (v) candidates.push(v);
    }
    // dentro de offers/itemIdentifiers
    const offers = schema.offers as Record<string, unknown> | undefined;
    if (offers) for (const k of ['gtin', 'gtin13', 'ean']) if (offers[k]) candidates.push(offers[k]);
  }
  const re = /\b(\d{13}|\d{14})\b/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(html)) !== null) {
    candidates.push(m[1]);
  }
  for (const c of candidates) {
    const s = String(c).replace(/\D/g, '');
    // valida dígito verificador GS1 (reusa ean.ts) — ignora placeholders tipo 5..9
    if ((s.length === 13 || s.length === 14) && isValidEan(s)) return s;
  }
  return null;
}

/** Import da validação GS1 (mesma usada no lookup). */
function extractPrice(html: string, schema: Record<string, unknown> | null): { price?: number; price_text?: string; currency?: string } {
  if (schema) {
    const offers = schema.offers as Record<string, unknown> | undefined;
    const priceRaw = offers?.price ?? offers?.['lowPrice'] ?? null;
    if (priceRaw != null) {
      const p = Number(priceRaw);
      if (!Number.isNaN(p)) {
        return { price: p, price_text: String(priceRaw), currency: String(offers?.priceCurrency || 'BRL') };
      }
    }
  }
  // Padrão brasileiro: R$ 899,00 / R$1.234,56
  const m = /R\$\s?([0-9][0-9.]*,[0-9]{2})/.exec(html);
  if (m) {
    const texto = m[1].replace(/\./g, '').replace(',', '.');
    return { price: Number(texto), price_text: `R$ ${m[1]}`, currency: 'BRL' };
  }
  // Alternativo: preço em JSON "price":"1234.56"
  const m2 = /"price"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)"?/.exec(html);
  if (m2) return { price: Number(m2[1]), price_text: m2[1], currency: 'BRL' };
  return {};
}

async function scrapeCacheGet(url: string): Promise<ScrapedProduct | null> {
  try {
    const raw = await fs.readFile(SCRAPE_CACHE, 'utf-8');
    const obj = JSON.parse(raw) as Record<string, { v: ScrapedProduct; ts: number }>;
    const e = obj[url];
    if (e && Date.now() - e.ts < SCRAPE_TTL_MS) return e.v;
  } catch {
    /* sem cache */
  }
  return null;
}

async function scrapeCachePut(url: string, result: ScrapedProduct): Promise<void> {
  try {
    let obj: Record<string, { v: ScrapedProduct; ts: number }> = {};
    try {
      obj = JSON.parse(await fs.readFile(SCRAPE_CACHE, 'utf-8'));
    } catch {
      obj = {};
    }
    obj[url] = { v: result, ts: Date.now() };
    // limita tamanho (100 entradas)
    const keys = Object.keys(obj);
    if (keys.length > 100) {
      for (const k of keys.slice(0, keys.length - 100)) delete obj[k];
    }
    const tmp = `${SCRAPE_CACHE}.${process.pid}.tmp`;
    await fs.writeFile(tmp, JSON.stringify(obj), 'utf-8');
    await fs.rename(tmp, SCRAPE_CACHE);
  } catch {
    /* best-effort */
  }
}

/**
 * Faz a raspagem de uma URL de produto.
 * Timeout 12s, máximo 2MB. Em falha: { found: false, error }.
 * Usa cache por URL (TTL 6h): mesma página não é raspada duas vezes.
 */
export async function scrapeProductUrl(url: string): Promise<ScrapedProduct> {
  const cached = await scrapeCacheGet(url);
  if (cached) {
    process.stderr.write('[scrape] cache HIT — página servida sem raspagem\n');
    return cached;
  }
  const result = await scrapeProductUrlUncached(url);
  if (result.found) void scrapeCachePut(url, result);
  return result;
}

async function scrapeProductUrlUncached(url: string): Promise<ScrapedProduct> {
  const base: ScrapedProduct = {
    url,
    title: '',
    description: '',
    meta_description: '',
    image_url: null,
    image_urls: [],
    brand: null,
    ean: null,
    sku: null,
    schema_org: null,
    found: false,
  };

  if (!isSafeUrl(url)) {
    return { ...base, error: 'URL inválida (apenas http/https)' };
  }

  try {
    const res = await fetch(url, {
      headers: { 'User-Agent': UA, Accept: 'text/html,application/xhtml+xml' },
      signal: AbortSignal.timeout(12000),
      redirect: 'follow',
    });
    if (!res.ok) {
      return { ...base, error: `HTTP ${res.status}` };
    }
    const html = (await res.text()).slice(0, 2 * 1024 * 1024);
    if (!html || html.length < 200) {
      return { ...base, error: 'HTML vazio ou muito curto (possível JS-only)' };
    }

    const mTitle = /<title>(.*?)<\/title>/i.exec(html);
    const mDesc = /<meta[^>]+name=["']description["'][^>]+content=["'](.*?)["']/i.exec(html);
    const mBrand = /<meta[^>]+property=["'](?:product:brand|og:site_name)["'][^>]+content=["'](.*?)["']/i.exec(html);
    const mImage = /<meta[^>]+property=["']og:image["'][^>]+content=["'](.*?)["']/i.exec(html);
    const mSku = /<meta[^>]+property=["']product:retailer_item_id["'][^>]+content=["'](.*?)["']/i.exec(html);

    const schema = extractSchemaLd(html);
    const ean = extractEan(html, schema);
    const { price, price_text, currency } = extractPrice(html, schema);

    // Todas as imagens grandes do produto (og + data-src de galeria, dedup)
    const allImages: string[] = [];
    if (mImage) allImages.push(unescapeHtml(mImage[1]));
    const gallery = html.match(/https?:\/\/[^"'\s]+\.(?:png|jpe?g|webp)(?:\?[^"'\s]*)?/gi) || [];
    for (const img of gallery) {
      if (!allImages.includes(img) && allImages.length < 6) allImages.push(img);
    }

    // Descrição: prefere meta; senão trecho de texto da página (limpo)
    let description = mDesc ? unescapeHtml(mDesc[1]) : '';
    if (!description) {
      const body = html.replace(/<script[\s\S]*?<\/script>/gi, ' ').replace(/<style[\s\S]*?<\/style>/gi, ' ');
      const text = clean(body.replace(/<[^>]+>/g, ' '));
      description = text.slice(0, 400);
    }

    return {
      url,
      title: unescapeHtml(clean(mTitle ? mTitle[1].split(/\s*[|–-]\s*/)[0].trim() : (mDesc ? mDesc[1] : ''))).slice(0, 200) || 'Produto',
      price: price ?? null,
      price_text: price_text ?? null,
      description: clean(description).slice(0, 800),
      meta_description: clean(mDesc ? unescapeHtml(mDesc[1]) : ''),
      image_url: mImage ? unescapeHtml(mImage[1]) : allImages[0] || null,
      image_urls: allImages,
      brand: mBrand ? unescapeHtml(mBrand[1]) : null,
      ean,
      sku: (mSku ? unescapeHtml(mSku[1]) : null) || (schema?.sku ? String(schema.sku) : null),
      currency: currency ?? null,
      schema_org: schema,
      found: true,
    };
  } catch (err) {
    return { ...base, error: (err as Error).message };
  }
}