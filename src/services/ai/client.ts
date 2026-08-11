/**
 * Cliente OpenAI-compatible com POOL DE CHAVES e failover em cascata.
 *
 * Estratégia:
 *  - OpenCode é o TIER 0 (PRIMÁRIO): várias chaves em pool, round-robin por saúde.
 *  - Nous / Zen / outros são TIER 1 (FALLBACK): só entram se o pool OpenCode
 *    estiver todo em cooldown (todas as chaves 429/401).
 *  - Cada chave tem cooldown独立: 429 → 60s, 401 → 1h (chave morta/inválida).
 *  - NUNCA lança exceção: se tudo falhar, retorna null (modo determinístico).
 *
 * Configuração via env:
 *  - AI_ENDPOINT          (default OpenCode: https://gateway.opencode.ai/v1)
 *  - AI_MODEL             (modelo OpenCode, ex: "sonic")
 *  - AI_API_KEYS          (PRIMÁRIO pool OpenCode: chaves separadas por vírgula)
 *  - AI_FALLBACK_KEYS     (FALLBACK pool: Nous/Zen/etc, separadas por vírgula)
 *  - AI_FALLBACK_ENDPOINT (default Nous: https://inference-api.nousresearch.com/v1)
 *  - AI_FALLBACK_MODEL    (default: poolside/laguna-s-2.1:free)
 */

const PRIMARY_ENDPOINT = process.env.AI_ENDPOINT || 'https://opencode.ai/zen/go/v1';
const PRIMARY_MODEL = process.env.AI_MODEL || 'deepseek-v4-flash';
const PRIMARY_KEYS = (process.env.AI_API_KEYS || process.env.AI_API_KEY || '')
  .split(',')
  .map((k) => k.trim())
  .filter(Boolean);

const FALLBACK_ENDPOINT =
  process.env.AI_FALLBACK_ENDPOINT || 'https://inference-api.nousresearch.com/v1';
const FALLBACK_MODEL = process.env.AI_FALLBACK_MODEL || 'poolside/laguna-s-2.1:free';
const FALLBACK_KEYS = (process.env.AI_FALLBACK_KEYS || '')
  .split(',')
  .map((k) => k.trim())
  .filter(Boolean);

const TIMEOUT_MS = 30_000;
const COOLDOWN_429_MS = 60_000; // rate limit: pausa 60s
const COOLDOWN_401_MS = 3_600_000; // chave inválida: pausa 1h

import { getCached, putCached, cacheKey } from './cache.js';

// Estado de saúde por chave (em memória, por processo)
interface KeyState {
  key: string;
  endpoint: string;
  model: string;
  cooldownUntil: number; // epoch ms; 0 = saudável
  tier: 'primary' | 'fallback';
}

const keyStates: KeyState[] = [
  ...PRIMARY_KEYS.map((k) => ({
    key: k,
    endpoint: PRIMARY_ENDPOINT,
    model: PRIMARY_MODEL,
    cooldownUntil: 0,
    tier: 'primary' as const,
  })),
  ...FALLBACK_KEYS.map((k) => ({
    key: k,
    endpoint: FALLBACK_ENDPOINT,
    model: FALLBACK_MODEL,
    cooldownUntil: 0,
    tier: 'fallback' as const,
  })),
];

function isHealthy(ks: KeyState, now: number): boolean {
  return ks.cooldownUntil <= now;
}

function markCooldown(ks: KeyState, httpStatus: number, now: number): void {
  if (httpStatus === 401) {
    ks.cooldownUntil = now + COOLDOWN_401_MS;
    process.stderr.write(`[ai/client] chave ${ks.tier} 401 — cooldown 1h\n`);
  } else if (httpStatus === 429) {
    ks.cooldownUntil = now + COOLDOWN_429_MS;
    process.stderr.write(`[ai/client] chave ${ks.tier} 429 — cooldown 60s\n`);
  }
}

export interface GenerateOptions {
  system?: string;
  temperature?: number;
  maxTokens?: number;
}

export async function generate(
  prompt: string,
  opts?: GenerateOptions
): Promise<string | null> {
  if (keyStates.length === 0) {
    process.stderr.write('[ai/client] Nenhuma chave de IA definida — modo determinístico\n');
    return null;
  }

  const now = Date.now();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const messages: Array<{ role: 'system' | 'user'; content: string }> = [];
    if (opts?.system) messages.push({ role: 'system', content: opts.system });
    messages.push({ role: 'user', content: prompt });

    // Ordem: primárias saudáveis primeiro, depois fallback saudável
    const ordered = keyStates
      .filter((ks) => isHealthy(ks, now))
      .sort((a, b) => (a.tier === b.tier ? 0 : a.tier === 'primary' ? -1 : 1));

    if (ordered.length === 0) {
      process.stderr.write('[ai/client] todas as chaves em cooldown — modo determinístico\n');
      return null;
    }

    for (const ks of ordered) {
      const cacheModel = `${ks.tier}:${ks.model}`;
      const key = cacheKey(opts?.system, prompt, cacheModel);
      const cached = await getCached(key);
      if (cached) {
        process.stderr.write(`[ai/client] cache HIT (${cacheModel})\n`);
        return cached;
      }

      const body = {
        model: ks.model,
        messages,
        temperature: opts?.temperature ?? 0.7,
        max_tokens: opts?.maxTokens ?? 2048,
      };

      try {
        const res = await fetch(`${ks.endpoint}/chat/completions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${ks.key}`,
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        // OpenCode Go retorna 200 com {type:error, error:{type:GoUsageLimitError}}
        // quando a chave atingiu limite — tratar como cooldown (não erro fatal)
        if (res.ok) {
          const text = await res.text();
          try {
            const parsed = JSON.parse(text);
            if (parsed?.type === 'error' && parsed?.error?.type === 'GoUsageLimitError') {
              markCooldown(ks, 429, Date.now()); // reusa cooldown de rate limit
              process.stderr.write(
                `[ai/client] OpenCode GoUsageLimitError em ${ks.tier} — próxima chave\n`
              );
              continue;
            }
            const data = parsed as {
              choices?: Array<{ message?: { content?: string | null } }>;
            };
            const content = data.choices?.[0]?.message?.content;
            if (typeof content === 'string') {
              void putCached(key, content);
              return content;
            }
            process.stderr.write(`[ai/client] conteúdo vazio de ${ks.tier}\n`);
            continue;
          } catch {
            process.stderr.write(`[ai/client] JSON inválido de ${ks.tier}\n`);
            continue;
          }
        }

        // resposta não-OK (401/429/5xx)
        let status = res.status;
        if (res.status === 200) {
          // body já lido acima; não deve chegar aqui, mas por segurança:
          status = 429;
        }
        markCooldown(ks, status, Date.now());
        process.stderr.write(
          `[ai/client] HTTP ${res.status} ${ks.tier} — tentando próxima chave\n`
        );
        continue;
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        process.stderr.write(`[ai/client] Erro ${ks.tier}: ${msg} — próxima chave\n`);
        continue;
      }
    }
    return null; // todas as chaves falharam
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    process.stderr.write(`[ai/client] Erro: ${msg} — modo determinístico\n`);
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}
