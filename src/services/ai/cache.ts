/**
 * Cache de respostas de IA — persistente em disco (JSON), TTL 24h.
 *
 * Objetivo de NEGÓCIO: enriquecer o mesmo produto/prompt NÃO deve consumir
 * tokens duas vezes. Primeiro hit → gasta; hits seguintes → cache (custo 0).
 * Expoe contadores p/ relatar economia no Monitor do Studio.
 *
 * Arquivo: <tmp>/catalog-agent-ai-cache.json (atômico, best-effort).
 */

import { createHash } from 'node:crypto';
import { promises as fs } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

interface CacheEntry {
  v: string; // resposta
  ts: number; // timestamp
}

const CACHE_FILE = path.join(os.tmpdir(), 'catalog-agent-ai-cache.json');
const TTL_MS = 24 * 60 * 60 * 1000;
const MAX_ENTRIES = 500;

let store: Record<string, CacheEntry> = {};
let loaded = false;
let hits = 0;
let misses = 0;

async function load(): Promise<void> {
  if (loaded) return;
  loaded = true;
  try {
    const raw = await fs.readFile(CACHE_FILE, 'utf-8');
    store = JSON.parse(raw) as Record<string, CacheEntry>;
  } catch {
    store = {};
  }
}

async function persist(): Promise<void> {
  try {
    // poda expirados + limita tamanho
    const now = Date.now();
    const keys = Object.keys(store);
    if (keys.length > MAX_ENTRIES) {
      const sorted = keys.sort((a, b) => (store[a]?.ts ?? 0) - (store[b]?.ts ?? 0));
      for (const k of sorted.slice(0, keys.length - MAX_ENTRIES)) delete store[k];
    }
    for (const k of Object.keys(store)) {
      if (now - (store[k]?.ts ?? 0) > TTL_MS) delete store[k];
    }
    const data = JSON.stringify(store);
    const tmp = `${CACHE_FILE}.${process.pid}.tmp`;
    await fs.writeFile(tmp, data, 'utf-8');
    await fs.rename(tmp, CACHE_FILE);
  } catch {
    /* cache é best-effort */
  }
}

/** Deriva chave estável do prompt + sistema + modelo. */
export function cacheKey(system: string | undefined, prompt: string, model: string): string {
  return createHash('sha256').update(`${model}|${system ?? ''}|${prompt}`).digest('hex').slice(0, 40);
}

/** Tenta obter do cache; registra hit/miss. */
export async function getCached(key: string): Promise<string | null> {
  await load();
  const e = store[key];
  if (!e) {
    misses++;
    return null;
  }
  if (Date.now() - e.ts > TTL_MS) {
    misses++;
    delete store[key];
    return null;
  }
  hits++;
  return e.v;
}

/** Guarda resposta no cache (best-effort). */
export async function putCached(key: string, value: string): Promise<void> {
  await load();
  store[key] = { v: value, ts: Date.now() };
  void persist();
}

/** Métricas de economia p/ relatório. */
export function cacheStats(): { hits: number; misses: number; hitRate: number; entries: number } {
  const total = hits + misses;
  return {
    hits,
    misses,
    hitRate: total > 0 ? Math.round((hits / total) * 100) : 0,
    entries: Object.keys(store).length,
  };
}

/** Limpa cache (p/ testes). */
export async function clearCache(): Promise<void> {
  store = {};
  hits = 0;
  misses = 0;
  try {
    await fs.rm(CACHE_FILE, { force: true });
  } catch {
    /* ok */
  }
}