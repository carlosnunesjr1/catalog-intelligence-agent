/**
 * Validação de dígito verificador EAN-8/12/13/14 (GS1, módulo 10).
 * Exposta separadamente p/ reuso (lookup, images, validate, testes).
 *
 * Regra GS1: pesos alternam 3/1 a partir da DIREITA (dígito mais à direita
 * dos dados tem peso 3). Soma ponderada mod 10 → dígito verificador.
 */

/** Valida formato e dígito verificador de um EAN/GTIN. */
export function isValidEan(ean: string): boolean {
  const clean = ean.replace(/\D/g, '');
  if (![8, 12, 13, 14].includes(clean.length)) return false;

  const digits = clean.split('').map(Number);
  const check = digits.pop()!;
  const n = digits.length;

  let sum = 0;
  for (let i = 0; i < n; i++) {
    // último dígito de dados (i = n-1) tem peso 3; alterna da direita
    const weight = (n - 1 - i) % 2 === 0 ? 3 : 1;
    sum += digits[i] * weight;
  }
  const calc = (10 - (sum % 10)) % 10;
  return calc === check;
}

/** Normaliza string para apenas dígitos (retorna null se não tiver EAN). */
export function normalizeEan(raw: string | null | undefined): string | null {
  if (!raw) return null;
  const clean = String(raw).replace(/\D/g, '');
  return clean.length > 0 ? clean : null;
}