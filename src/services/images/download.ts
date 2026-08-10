/**
 * Download de imagens de produto — baixa até N imagens e devolve data-URLs
 * prontas para EXIBIÇÃO no chat (markdown `![alt](data:image/png;base64,...)`).
 *
 * O fluxo do cliente (ex.: no Deco Studio): pede "pegue as imagens deste
 * produto" → a tool baixa as imagens → o chat mostra a galeria.
 *
 * NUNCA lança — itens que falham viram entrada com error.
 */

import { promises as fs } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { isSafeImageUrl } from './process.js';

export interface DownloadedImage {
  index: number;
  url: string;
  data_url?: string;
  mime?: string;
  bytes?: number;
  local_path?: string;
  error?: string;
}

const CACHE_DIR = path.join(os.tmpdir(), 'catalog-agent-dl');

function mimeFromUrl(url: string): string {
  const clean = url.split('?')[0].toLowerCase();
  if (clean.endsWith('.png')) return 'image/png';
  if (clean.endsWith('.webp')) return 'image/webp';
  if (clean.endsWith('.gif')) return 'image/gif';
  if (clean.endsWith('.avif')) return 'image/avif';
  return 'image/jpeg';
}

async function downloadOne(url: string): Promise<DownloadedImage> {
  if (!isSafeImageUrl(url)) {
    return { index: -1, url, error: 'URL inválida/insegura' };
  }
  try {
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126' },
      signal: AbortSignal.timeout(10000),
      redirect: 'follow',
    });
    if (!res.ok) return { index: -1, url, error: `HTTP ${res.status}` };
    const buf = Buffer.from(await res.arrayBuffer());
    if (!buf.length || buf.length > 10 * 1024 * 1024) {
      return { index: -1, url, error: 'arquivo vazio ou >10MB' };
    }
    const mime = mimeFromUrl(url);
    return {
      index: -1,
      url,
      data_url: `data:${mime};base64,${buf.toString('base64')}`,
      mime,
      bytes: buf.length,
    };
  } catch (err) {
    return { index: -1, url, error: (err as Error).message };
  }
}

/**
 * Baixa até `limit` imagens em paralelo (concorrência 3).
 * Retorna array na MESMA ordem das URLs de entrada.
 */
export async function downloadImages(urls: string[], limit = 6): Promise<DownloadedImage[]> {
  const targets = urls.filter(Boolean).slice(0, limit);
  const results: DownloadedImage[] = [];
  const CONCURRENCY = 3;

  for (let i = 0; i < targets.length; i += CONCURRENCY) {
    const chunk = targets.slice(i, i + CONCURRENCY);
    const settled = await Promise.allSettled(chunk.map((u) => downloadOne(u)));
    settled.forEach((s) => {
      if (s.status === 'fulfilled') {
        results.push({ ...s.value, index: results.length });
      } else {
        results.push({ index: results.length, url: '', error: String(s.reason) });
      }
    });
  }

  // Persiste as que baixaram (p/ referência local opcional)
  try {
    await fs.mkdir(CACHE_DIR, { recursive: true });
    for (const r of results) {
      if (r.data_url) {
        const m = /^data:([^;]+);base64,(.*)$/.exec(r.data_url);
        if (m) {
          const ext = m[1].includes('png') ? 'png' : m[1].includes('webp') ? 'webp' : 'jpg';
          const fname = path.join(CACHE_DIR, `img-${r.index}.${ext}`);
          await fs.writeFile(fname, Buffer.from(m[2], 'base64')).catch(() => {});
          r.local_path = fname;
        }
      }
    }
  } catch {
    /* cache é opcional */
  }

  return results;
}