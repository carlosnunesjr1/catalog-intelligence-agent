/**
 * Cliente mínimo OpenAI-compatible usando fetch nativo (Node 22+).
 *
 * Lê configuração via environment variables:
 *  - AI_ENDPOINT  (default: https://inference-api.nousresearch.com/v1)
 *  - AI_MODEL     (default: deepseek-v4-flash)
 *  - AI_API_KEY   (obrigatório — sem key, generate() retorna null)
 *
 * generate() NUNCA lança exceção: retorna `null` em qualquer falha
 * (key ausente, erro de rede, timeout de 30s).
 */

const AI_ENDPOINT = process.env.AI_ENDPOINT || 'https://inference-api.nousresearch.com/v1';
const AI_MODEL = process.env.AI_MODEL || 'deepseek-v4-flash';
const AI_API_KEY = process.env.AI_API_KEY;

const TIMEOUT_MS = 30_000;

// Cache de respostas (economia de tokens): mesma chave → mesmo resultado, custo 0
import { getCached, putCached, cacheKey } from './cache.js';

export interface GenerateOptions {
  system?: string;
  temperature?: number;
  maxTokens?: number;
}

/**
 * Envia um prompt para o endpoint de chat completions.
 * Retorna o conteúdo da resposta como string, ou `null` se:
 *  - AI_API_KEY não estiver definida
 *  - a requisição falhar por qualquer motivo (network, HTTP, parse, timeout)
 */
export async function generate(
  prompt: string,
  opts?: GenerateOptions
): Promise<string | null> {
  if (!AI_API_KEY) {
    process.stderr.write('[ai/client] AI_API_KEY não definida — modo determinístico\n');
    return null;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    // 1. Cache hit? (mesmo prompt+modelo → resposta igual, sem gastar tokens)
    const key = cacheKey(opts?.system, prompt, AI_MODEL);
    const cached = await getCached(key);
    if (cached) {
      process.stderr.write('[ai/client] cache HIT — resposta servida sem chamada de IA\n');
      return cached;
    }

    const messages: Array<{ role: 'system' | 'user'; content: string }> = [];
    if (opts?.system) {
      messages.push({ role: 'system', content: opts.system });
    }
    messages.push({ role: 'user', content: prompt });

    const body = {
      model: AI_MODEL,
      messages,
      temperature: opts?.temperature ?? 0.7,
      // IMPORTANTE: stepfun free corta em 'length' com max_tokens baixo e
      // devolve content:null — manter padrão alto (2048+) para respostas longas.
      max_tokens: opts?.maxTokens ?? 2048,
    };

    const res = await fetch(`${AI_ENDPOINT}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${AI_API_KEY}`,
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!res.ok) {
      process.stderr.write(
        `[ai/client] HTTP ${res.status} ${res.statusText} — fallback determinístico\n`
      );
      return null;
    }

    const data = (await res.json()) as {
      choices?: Array<{ message?: { content?: string | null } }>;
    };

    const content = data.choices?.[0]?.message?.content;
    if (typeof content === 'string') {
      // 2. Guarda no cache (best-effort)
      void putCached(key, content);
      return content;
    }
    return null;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    process.stderr.write(`[ai/client] Erro: ${msg} — fallback determinístico\n`);
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}
