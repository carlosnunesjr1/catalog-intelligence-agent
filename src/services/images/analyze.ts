/**
 * Análise determinística de imagem de produto (storefront).
 * Usa o helper Python (PIL) para extrair: dimensões, proporção, fundo,
 * nitidez e "prontidão para a loja". Sem dependência de LLM com visão.
 *
 * NUNCA lança — em falha retorna objeto com error e análise vazia.
 */

import { spawn } from 'node:child_process';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { isSafeImageUrl } from './process.js';

export interface ImageAnalysis {
  width?: number;
  height?: number;
  aspect_ratio?: number | null;
  format?: string;
  size_bytes?: number;
  background?: 'uniform' | 'noisy';
  border_stddev?: number;
  mean_rgb?: number[];
  sharpness?: number;
  ready_for_store?: boolean;
  issues: string[];
  error?: string;
  /**
   * Resumo COMERCIAL para o agente usar na resposta ao lojista.
   * SEMPRE usar este campo em texto destinado a humanos — nunca os campos técnicos
   * (mean_rgb, border_stddev, sharpness, width/height) que são diagnóstico interno.
   */
  human_summary?: string;
}

const VENV_PYTHON = path.join(process.cwd(), '.venv-rembg', 'bin', 'python');
const HELPER = path.join(process.cwd(), 'scripts', 'imginfo_worker.py');

async function download(url: string): Promise<Buffer | null> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
    if (!res.ok) return null;
    const buf = Buffer.from(await res.arrayBuffer());
    if (!buf.length || buf.length > 15 * 1024 * 1024) return null;
    return buf;
  } catch {
    return null;
  }
}

function runHelper(input: Buffer): Promise<ImageAnalysis> {
  return new Promise((resolve) => {
    try {
      const child = spawn(VENV_PYTHON, [HELPER], { stdio: ['pipe', 'pipe', 'pipe'] });
      const out: Buffer[] = [];
      child.stdout.on('data', (d) => out.push(Buffer.from(d)));
      child.on('error', () => resolve({ issues: [], error: 'spawn falhou' }));
      child.on('close', (code) => {
        if (code === 0 && out.length > 0) {
          try {
            const parsed = JSON.parse(Buffer.concat(out).toString()) as ImageAnalysis;
                    const result: ImageAnalysis = { ...parsed, issues: parsed.issues ?? [] };
                    // Gera resumo COMERCIAL automático (nunca expor números técnicos ao lojista)
                    if (!result.error) {
                      const parts: string[] = [];
                      if (result.ready_for_store === true) {
                        parts.push('Foto do produto em boas condições para a loja.');
                      } else {
                        parts.push('A foto do produto precisa de ajustes antes de publicar:');
                        for (const issue of result.issues ?? []) parts.push(`• ${issue}`);
                      }
                      if (result.background === 'noisy') {
                        parts.push('Recomendação: aplicar fundo branco para padrão de catálogo.');
                      }
                      result.human_summary = parts.join(' ');
                    }
                    resolve(result);
          } catch {
            resolve({ issues: [], error: 'resposta inválida do helper' });
          }
        } else {
          resolve({ issues: [], error: `helper exit ${code}` });
        }
      });
      child.stdin.on('error', () => {});
      child.stdin.end(input);
    } catch (err) {
      resolve({ issues: [], error: (err as Error).message });
    }
  });
}

/** Analisa uma imagem por URL (download + PIL). */
export async function analyzeImageUrl(url: string): Promise<ImageAnalysis> {
  if (!isSafeImageUrl(url)) {
    return { issues: ['URL de imagem inválida/insegura'], error: 'URL inválida' };
  }
  try {
    const buf = await download(url);
    if (!buf) return { issues: ['download falhou'], error: 'download falhou' };
    return await runHelper(buf);
  } catch (err) {
    return { issues: [], error: (err as Error).message };
  }
}

/** Analisa bytes de imagem (já baixada). */
export async function analyzeImageBuffer(buf: Buffer): Promise<ImageAnalysis> {
  return runHelper(buf);
}

export async function analyzeImageBytesAvailable(): Promise<boolean> {
  try {
    await fs.access(VENV_PYTHON);
    await fs.access(HELPER);
    return true;
  } catch {
    return false;
  }
}