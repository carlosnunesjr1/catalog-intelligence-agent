#!/usr/bin/env node
/**
 * Verificação end-to-end local do MCP server (stdio).
 * Prova #1 — "é funcional internamente" ANTES de testar em clientes externos.
 *
 * Uso: node scripts/smoke-mcp.mjs
 * Fluxo: initialize → tools/list → tools/call lookup_ean (EAN inválido, sem rede)
 *        → tools/call enrich_product (fallback determinístico, sem rede)
 */
import { spawn } from 'node:child_process';
import { once } from 'node:events';

const SERVER = process.env.SERVER ?? 'dist/server.js';
const child = spawn('node', [SERVER], {
  stdio: ['pipe', 'pipe', 'inherit'],
});

let buf = '';
const pending = new Map();
let nextId = 1;

child.stdout.on('data', (d) => {
  buf += d.toString();
  let idx;
  while ((idx = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, idx).trim();
    buf = buf.slice(idx + 1);
    if (!line) continue;
    let msg;
    try {
      msg = JSON.parse(line);
    } catch {
      console.error('[smoke] linha não-JSON (ignorada):', line.slice(0, 120));
      continue;
    }
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  }
});

function rpc(method, params = {}) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`timeout ${method}`)), 15000);
    pending.set(id, (msg) => {
      clearTimeout(timer);
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg.result);
    });
    child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
  });
}

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok, detail });
  console.log(`${ok ? '✅' : '❌'} ${name}${detail ? ' — ' + detail : ''}`);
}

try {
  // 1. Initialize
  const init = await rpc('initialize', {
    protocolVersion: '2025-03-26',
    capabilities: {},
    clientInfo: { name: 'smoke-test', version: '0.0.1' },
  });
  check('initialize', init.serverInfo?.name === 'catalog-intelligence-agent',
    `server=${init.serverInfo?.name} proto=${init.protocolVersion}`);

  // 2. tools/list — 5 ferramentas
  const tools = await rpc('tools/list');
  const names = (tools.tools ?? []).map((t) => t.name);
  const expected = ['lookup_ean', 'search_images', 'enrich_product', 'validate_listing', 'enrich_batch'];
  check('tools/list 5 tools', expected.every((n) => names.includes(n)),
    `${names.length} tools: ${names.join(', ')}`);

  // 3. lookup_ean EAN inválido (sem rede, valida dígito)
  const lk = await rpc('tools/call', {
    name: 'lookup_ean',
    arguments: { ean: '1234567890123' },
  });
  const lkTxt = lk.content?.map((c) => c.text).join('');
  check('lookup_ean inválido sem rede', lkTxt.includes('"found": false'),
    lkTxt?.slice(0, 100));

  // 4. enrich_product (determinístico, sem IA)
  const en = await rpc('tools/call', {
    name: 'enrich_product',
    arguments: {
      product: {
        ean: '7891234567890',
        title: 'FURADEIRA DE IMPACTO 750W 110V',
        brand: 'SEM MARCA',
      },
      options: { with_ai: false, with_images: false },
    },
  });
  const enTxt = en.content?.map((c) => c.text).join('');
  const enObj = JSON.parse(enTxt);
  check('enrich_product determinístico', enObj.title && enObj.slug && enObj.schema_org?.['@type'] === 'Product',
    `title="${enObj.title?.slice(0, 40)}" slug="${enObj.slug}"`);

  // 5. validate_listing
  const va = await rpc('tools/call', {
    name: 'validate_listing',
    arguments: { listing: { title: '', description_html: '', brand: 'sem marca' } },
  });
  const vaTxt = va.content?.map((c) => c.text).join('');
  const vaObj = JSON.parse(vaTxt);
  check('validate_listing score baixo', vaObj.score < 70 && vaObj.ready === false,
    `score=${vaObj.score}, issues=${vaObj.issues?.length}`);

  // 6. enrich_batch
  const ba = await rpc('tools/call', {
    name: 'enrich_batch',
    arguments: {
      products: [
        { ean: '7891234567890', title: 'FURADEIRA DE IMPACTO 750W 110V', brand: 'SEM MARCA' },
        { ean: '7891234567890', title: 'CHAVE DE FENDA 6MM', brand: '' },
      ],
      options: { with_ai: false, with_images: false },
    },
  });
  const baTxt = ba.content?.map((c) => c.text).join('');
  const baObj = JSON.parse(baTxt);
  check('enrich_batch 2 produtos', baObj.total === 2 && typeof baObj.succeeded === 'number',
    `total=${baObj.total} ok=${baObj.succeeded} fail=${baObj.failed}`);
} catch (err) {
  check('fluxo completo', false, err.message);
}

child.kill();
const passed = results.filter((r) => r.ok).length;
console.log(`\n${passed}/${results.length} passaram.`);
process.exit(passed === results.length ? 0 : 1);