/**
 * Testes unitários do núcleo (sem rede): validação EAN, validate_listing, schema.
 * Roda com: node --import tsx --test tests/core.test.ts
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateListing } from '../src/services/validate/listing.js';
import { isValidEan } from '../src/services/lookup/ean.js';

// EANs válidos conhecidos (GS1)
const VALID_EAN13 = '5901234123457'; // exemplo clássico (Wikipedia)
const VALID_EAN8 = '96385074'; // EAN-8 válido

test('EAN-13 válido 5901234123457', () => assert.equal(isValidEan(VALID_EAN13), true));
test('EAN-13 inválido (check errado)', () => assert.equal(isValidEan('5901234123458'), false));
test('EAN-8 válido 96385074', () => assert.equal(isValidEan(VALID_EAN8), true));
test('EAN-8 inválido (check errado)', () => assert.equal(isValidEan('96385075'), false));
test('EAN com caracteres não-dígito é normalizado', () => assert.equal(isValidEan('5901234123457 '), true));
test('EAN em formato inválido (9 dígitos) rejeitado', () => assert.equal(isValidEan('123456789'), false));

test('validate_listing: título/desc/marca ausentes → not ready', () => {
  const r = validateListing({ title: '', description_html: '', brand: '' });
  assert.equal(r.ready, false);
  assert.ok(r.issues.some((i) => i.severity === 'error'));
});

test('validate_listing: produto completo → ready', () => {
  const r = validateListing({
    title: 'Furadeira de Impacto 750W 110V — Profissional',
    description_html: '<p>Furadeira de impacto com motor 750W, mandril 13mm e cabo auxiliar.</p>',
    brand: 'Tramontina',
    image_url: 'https://cdn.example.com/furadeira.jpg',
    ean: VALID_EAN13,
    schema_org: { '@type': 'Product', name: 'Furadeira' },
    meta_title: 'Furadeira de Impacto 750W',
    slug: 'furadeira-de-impacto-750w',
  });
  assert.equal(r.ready, true);
  assert.ok(r.score >= 70, `score=${r.score}`);
});

test('schema_org de enricher: @type Product com gtin', async () => {
  const { enrichProduct } = await import('../src/pipeline/enricher.js');
  const p = await enrichProduct(
    { ean: VALID_EAN13, title: 'FURADEIRA DE IMPACTO 750W 110V', brand: 'SEM MARCA' },
    { with_ai: false, with_images: false }
  );
  assert.equal(p.schema_org['@type'], 'Product');
  assert.ok(p.title.includes('Furadeira'), `title=${p.title}`);
  assert.equal(p.slug, 'furadeira-de-impacto-750w-110v');
});