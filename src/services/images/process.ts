/**
 * Processamento de imagem p/ storefront (fundo branco).
 *
 * rembg e PIL são Python — este módulo Node chama o venv python via subprocess
 * (stack híbrida de propósito: Node = MCP/HTTP, Python = visão).
 *
 * Comando usado: .venv-rembg/bin/python scripts/rembg_worker.py <input.desc>
 * (input por tempfile; output PNG puro em stdout).
 *
 * Fallback determinístico: sem python/rembg → devolve URL original (imagem é
 * enriquecimento, nunca bloqueio).
 */

import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { promises as fs } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

export interface ProcessedImage {
  url: string;
  background_removed: boolean;
  bytes?: number;
  local_path?: string;
  warning?: string;
}

const CACHE_DIR = path.join(os.tmpdir(), 'catalog-agent-img');
const VENV_PYTHON = path.join(process.cwd(), '.venv-rembg', 'bin', 'python');
const HELPER = path.join(process.cwd(), 'scripts', 'rembg_worker.py');

/** Valida se uma URL de imagem parece segura (http/https, extensão de imagem). */
export function isSafeImageUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return (u.protocol === 'http:' || u.protocol === 'https:') && /\.(png|jpe?g|webp|gif|avif)(\?|$)/i.test(u.pathname);
  } catch {
    return false;
  }
}

/** Baixa imagem (8s timeout, máx 15MB). */
async function downloadImage(url: string): Promise<Buffer | null> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
    if (!res.ok) return null;
    const buf = Buffer.from(await res.arrayBuffer());
    if (buf.length === 0 || buf.length > 15 * 1024 * 1024) return null;
    return buf;
  } catch {
    return null;
  }
}

/** Chama o helper Python (rembg + fundo branco) via subprocess. */
async function removeBackgroundWithPython(input: Buffer): Promise<Buffer | null> {
  try {
    await fs.access(VENV_PYTHON);
    await fs.access(HELPER);
  } catch {
    process.stderr.write('[images/process] venv rembg não encontrado — fallback original\n');
    return null;
  }

  return new Promise((resolve) => {
    const child = spawn(VENV_PYTHON, [HELPER], { stdio: ['pipe', 'pipe', 'pipe'] });
    const out: Buffer[] = [];
    const err: Buffer[] = [];

    child.stdout.on('data', (d) => out.push(Buffer.from(d)));
    child.stderr.on('data', (d) => err.push(Buffer.from(d)));
    child.on('error', (e) => {
      process.stderr.write(`[images/process] spawn erro: ${e.message}\n`);
      resolve(null);
    });
    child.on('close', (code) => {
      if (code === 0 && out.length > 0) {
        resolve(Buffer.concat(out));
      } else {
        process.stderr.write(`[images/process] helper exit ${code}: ${Buffer.concat(err).toString().slice(0, 200)}\n`);
        resolve(null);
      }
    });
    child.stdin.on('error', () => {});
    child.stdin.end(input);
  });
}

/**
 * Pipeline: download → rembg (fundo branco) → data-URL.
 * Sempre retorna objeto; nunca lança.
 */
export async function processImage(url: string): Promise<{ processed: ProcessedImage }> {
  if (!isSafeImageUrl(url)) {
    return { processed: { url, background_removed: false, warning: 'URL de imagem inválida/insegura' } };
  }

  try {
    const hash = createHash('sha256').update(url).digest('hex').slice(0, 16);
    const cached = path.join(CACHE_DIR, `${hash}.png`);
    await fs.mkdir(CACHE_DIR, { recursive: true });

    // Cache hit?
    try {
      const cachedBuf = await fs.readFile(cached);
      return {
        processed: {
          url: `data:image/png;base64,${cachedBuf.toString('base64')}`,
          background_removed: true,
          bytes: cachedBuf.length,
          local_path: cached,
        },
      };
    } catch {
      /* miss */
    }

    const input = await downloadImage(url);
    if (!input) {
      return { processed: { url, background_removed: false, warning: 'download falhou' } };
    }

    const removed = await removeBackgroundWithPython(input);
    if (!removed) {
      return { processed: { url, background_removed: false, warning: 'rembg indisponível (imagem original)' } };
    }

    await fs.writeFile(cached, removed).catch(() => {});
    return {
      processed: {
        url: `data:image/png;base64,${removed.toString('base64')}`,
        background_removed: true,
        bytes: removed.length,
        local_path: cached,
      },
    };
  } catch (err) {
    return { processed: { url, background_removed: false, warning: (err as Error).message } };
  }
}