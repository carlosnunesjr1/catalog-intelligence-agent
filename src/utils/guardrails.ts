/**
 * Guardrails de propósito do agente — protege contra "fuga de escopo":
 * (1) lucro/instruções conflitantes (prompt injection) na entrada,
 * (2) resposta da IA fora do contrato (campos desconhecidos),
 * (3) volume excessivo.
 */

export interface InjectionRisk {
  detected: boolean;
  matched: string[];
}

/** Padrões de prompt injection / fuga de escopo em entradas de produto. */
const INJECTION_PATTERNS = [
  /ignor[ae] (as )?(suas )?(instru|regras|system)/i,
  /(ignore|disregard).{0,20}(instruction|prompt|rules|system)/i,
  /act as|pretend (to be|you are)/i,
  /voc[eê] (é|e|éste|agora)/i,
  /(reveal|expose|mostre).{0,20}(prompt|instruction|system|segred)/i,
  /da te (o|a|uma) resposta (direta|completa).{0,30}(sem|ignorand)/i,
  /(esqueça|ignore).{0,20}(o que te|as instru)/i,
  /you are now|override/gi,
  /\batue como|\baja como|\bvire (um|uma)\b/i,
  /sem (regras|limites|restrições)/i,
  /(responda|agora) (sem|fora|ignorando)/i,
];

/** Verifica se um texto de entrada contém tentativa de injeção. */
export function checkInjection(...texts: Array<string | null | undefined>): InjectionRisk {
  const matched: string[] = [];
  for (const t of texts) {
    if (!t) continue;
    for (const re of INJECTION_PATTERNS) {
      if (re.test(t)) matched.push(re.source);
    }
  }
  return { detected: matched.length > 0, matched: [...new Set(matched)] };
}

/** Campos permitidos no JSON que a IA pode retornar (allowlist de contrato). */
const ALLOWED_AI_FIELDS = new Set([
  'bullets',
  'description_html',
  'meta_title',
  'meta_description',
  'seo_keywords',
]);

/** Padrões de vazamento técnico que nunca devem aparecer em copy comercial. */
const TECHNICAL_LEAKS = [
  /\bRGB\s*[:(]\s*[0-9.,\s]*\)?/gi,
  /\b(?:mean|border)_?rgb\b[^;.!?]*/gi,
  /\b\d{2,3}(?:\.\d+)?\s*,\s*\d{2,3}(?:\.\d+)?\s*,\s*\d{2,3}(?:\.\d+)?\b/g,
  /\b\d{2,4}\s*x\s*\d{2,4}\s*pixels?\b/gi,
  /\b(?:sharpness|border_stddev|aspect_ratio|stddev)\b[^;.!?]*/gi,
];

/** Remove vazamentos técnicos de texto destinado a humanos. */
export function stripTechnicalLeaks(text: string): string {
  let out = text;
  for (const re of TECHNICAL_LEAKS) out = out.replace(re, '');
  return out.replace(/\s{2,}/g, ' ').replace(/[.,;]\s*[.,;]/g, ';').trim();
}

/**
 * Filtra o objeto retornado pela IA para SOMENTE os campos do contrato.
 * Remove chaves desconhecidas, nulls e strings excessivamente longas,
 * e coage arrays a máx. 8 itens.
 */
export function sanitizeAiOutput(input: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const key of Object.keys(input)) {
    if (!ALLOWED_AI_FIELDS.has(key)) continue;
    const v = input[key];
    if (v == null) continue;
    if (Array.isArray(v)) {
      const arr = v.filter((x) => typeof x === 'string').slice(0, 8);
      if (arr.length) out[key] = arr;
    } else if (typeof v === 'string') {
      if (key === 'meta_title' && v.length > 120) out[key] = v.slice(0, 120);
      else if (key === 'meta_description' && v.length > 320) out[key] = v.slice(0, 320);
      else if (v.length <= 20000) out[key] = v;
    }
  }
  return out;
}

/** Volume máximo de produtos por chamada de batch (já aplicado via zod, reforço). */
export const BATCH_MAX = 50;

/** Sanitiza texto bruto de entrada (remove null bytes e controle). */
export function sanitizeText(t: string | null | undefined): string {
  if (!t) return '';
  return t.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, ' ').trim();
}