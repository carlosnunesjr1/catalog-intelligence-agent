/**
 * OCR de print/imagem de página de produto (via tesseract, worker Python).
 * Modo 3 do PRD: "cliente manda print da loja/concorrente → OCR extrai texto".
 *
 * NUNCA lança — em falha retorna objeto com error.
 */

import { spawn } from 'node:child_process';
import path from 'node:path';
import { isSafeImageUrl } from './process.js';

export interface OcrResult {
  ok: boolean;
  full_text: string;
  lines: string[];
  word_count: number;
  error?: string;
}

const VENV_PYTHON = path.join(process.cwd(), '.venv-rembg', 'bin', 'python');
const HELPER = path.join(process.cwd(), 'scripts', 'ocr_worker.py');

async function download(url: string): Promise<Buffer | null> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(10000), redirect: 'follow' });
    if (!res.ok) return null;
    const buf = Buffer.from(await res.arrayBuffer());
    if (!buf.length || buf.length > 15 * 1024 * 1024) return null;
    return buf;
  } catch {
    return null;
  }
}

function runOcr(input: Buffer): Promise<OcrResult> {
  return new Promise((resolve) => {
    try {
      const child = spawn(VENV_PYTHON, [HELPER], { stdio: ['pipe', 'pipe', 'pipe'] });
      const out: Buffer[] = [];
      child.stdout.on('data', (d) => out.push(Buffer.from(d)));
      child.on('error', () => resolve({ ok: false, full_text: '', lines: [], word_count: 0, error: 'spawn falhou' }));
      child.on('close', (code) => {
        if (code === 0 && out.length > 0) {
          try {
            const parsed = JSON.parse(Buffer.concat(out).toString()) as OcrResult;
            resolve({ ...parsed, error: undefined });
          } catch {
            resolve({ ok: false, full_text: '', lines: [], word_count: 0, error: 'resposta inválida do worker' });
          }
        } else {
          resolve({ ok: false, full_text: '', lines: [], word_count: 0, error: `worker exit ${code}` });
        }
      });
      child.stdin.on('error', () => {});
      child.stdin.end(input);
    } catch (err) {
      resolve({ ok: false, full_text: '', lines: [], word_count: 0, error: (err as Error).message });
    }
  });
}

/** OCR de imagem por URL (download + tesseract). */
export async function ocrImageUrl(url: string): Promise<OcrResult> {
  if (!isSafeImageUrl(url)) {
    return { ok: false, full_text: '', lines: [], word_count: 0, error: 'URL de imagem inválida/insegura' };
  }
  try {
    const buf = await download(url);
    if (!buf) return { ok: false, full_text: '', lines: [], word_count: 0, error: 'download falhou' };
    return await runOcr(buf);
  } catch (err) {
    return { ok: false, full_text: '', lines: [], word_count: 0, error: (err as Error).message };
  }
}

/** OCR de bytes (imagem local). */
export async function ocrImageBuffer(buf: Buffer): Promise<OcrResult> {
  return runOcr(buf);
}