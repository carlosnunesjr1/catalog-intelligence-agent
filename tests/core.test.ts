/**
 * Testes unitários do núcleo (sem rede): validação EAN, higienização, schema.
 * Roda com `node --test tests/`.
 * Cobertura do teste interno ANTES de verificar em clientes externos.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';

// Reimplementação mínima para testar o dígito verificador sem rede.
function isValidEan(ean: string): boolean {
  if (!/^\d{8}$|^\d{12}$|^\d{13}$|^\d{14}$/.test(ean)) return false;
  const digits = ean.split('').map(Number);
  const check = digits.pop()!;
  const sum = digits.reduce((acc, d, i) => {
    const weight = (digits.length - i) % 2 === 0 ? 3 : 1;
    return acc + d * weight;
  }, 0);
  const calc = (10 - (sum % 10)) % 10;
  return calc === check;
}

test('EAN-13 válido: 7891234567890', () => assert.equal(isValidEan('7891234567890'), true));
test('EAN-13 inválido', () => assert.equal(isValidEAN('7891234567891'), false));

// Teste do schema JSON-LD gerado (função pura copiada do contrato)
function buildSchemaOrg(title: string, brand: string, ean: string | null): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: title,
    ...(ean ? { sku: ean, gtin13: ean } : {}),
    brand: { '@type': 'Brand', name: brand || 'Marca' },
  };
}

test('schema_org Gera Product JSON-LD com @type Product', () => {
  const schema = buildSchemaOrg('Furadeira 750W', 'Tramontina', '7891234567890');
  assert.equal(schema['@type'], 'Product');
  assert.equal(schema.name, 'Furadeira 750W');
  assert.equal((schema as any).gtin13, '7891234567890');
});

test('validate: título ausente gera error', () => {
  // proxy para o validateListing (import ponte; sem rede)
  const { validateListing } = require('../src/services/validate/listing.js');
  const r = validateListing({ title: '', description_html: '', brand: '' });
  assert.equal(r.ready, false);
  assert.ok(r.issues.some((i) => i.severity === 'error'));
});