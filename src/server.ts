/**
 * Catalog Intelligence Agent — MCP server.
 * Enriquecimento autônomo de catálogo para STOREFRONTS (lojas próprias).
 * Trilha: Catalog & Content — Hackathon Deco Agents for Commerce.
 *
 * Transportes: stdio (dev/local) + Streamable HTTP (deco Studio).
 * Usa a API high-level `McpServer` do @modelcontextprotocol/sdk (v1.30).
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

import { lookupEan } from './services/lookup/cascade.js';
import { searchImages } from './services/images/search.js';
import { enrichProduct } from './pipeline/enricher.js';
import { validateListing } from './services/validate/listing.js';
import { enrichBatch } from './pipeline/batch.js';
import { scrapeProductUrl } from './services/scrape/product.js';
import { analyzeImageUrl } from './services/images/analyze.js';
import { downloadImages } from './services/images/download.js';
import { ocrImageUrl, ocrImageBuffer } from './services/images/ocr.js';
import { checkInjection, sanitizeAiOutput } from './utils/guardrails.js';

export function makeServer(): McpServer {
  const server = new McpServer({
    name: 'catalog-intelligence-agent',
    version: '0.1.0',
    description:
      'Agente de enriquecimento de catálogo para storefronts: recebe dados brutos de ERP ' +
      '(EAN, título sujo, marca genérica) e devolve produto pronto para publicar na loja própria ' +
      '(título SEO, bullets, descrição HTML, schema.org JSON-LD, imagem). Ferramentas: ' +
      'lookup_ean, search_images, enrich_product, validate_listing, enrich_batch.',
  });

  // ── Tool 1: lookup_ean ────────────────────────────────────────────
  server.tool(
    'lookup_ean',
    'Busca dados de referência de um produto pelo código EAN/GTIN em múltiplas fontes ' +
      '(Open Food Facts, EAN-Search). Valida o dígito verificador antes da requisição. ' +
      'Retorna título, marca, descrição, imagem e dimensões quando encontrados.',
    { ean: z.string().describe('Código EAN/GTIN de 8, 12, 13 ou 14 dígitos') },
    async ({ ean }) => {
      try {
        const injection = checkInjection(ean);
        if (injection.detected) {
          return {
            content: [{ type: 'text', text: JSON.stringify({ error: 'Entrada rejeitada por segurança (padrão de injeção detectado)', matched: injection.matched }) }],
            isError: true,
          };
        }
        const result = await lookupEan(ean);
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Erro no lookup: ${(err as Error).message}` }],
          isError: true,
        };
      }
    }
  );

  // ── Tool 2: search_images ─────────────────────────────────────────
  server.tool(
    'search_images',
    'Busca imagens candidatas de um produto por EAN/GTIN. Retorna até N URLs de imagem ' +
      'com fonte e score. Usa Open Food Facts (sem key) e URLs já informadas no ERP.',
    {
      ean: z.string().optional().describe('EAN/GTIN do produto'),
      title: z.string().optional().describe('Título do produto (reservado)'),
      limit: z.number().int().min(1).max(10).default(3).describe('Quantidade máxima de imagens'),
    },
    async ({ ean, limit }) => {
      try {
        const images = await searchImages({ ean, limit: limit ?? 3 });
        return { content: [{ type: 'text', text: JSON.stringify({ images }, null, 2) }] };
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Erro na busca de imagens: ${(err as Error).message}` }],
          isError: true,
        };
      }
    }
  );

  // ── Tool 3: enrich_product ────────────────────────────────────────
  server.tool(
    'enrich_product',
    'Pipeline completo de enriquecimento: higieniza título (Title Case, remove ruído), gera ' +
      'bullets de benefícios, descrição HTML mobile-first, SEO (slug/meta/keywords), schema.org ' +
      'JSON-LD, busca imagem por EAN e normaliza atributos. Entrada = produto bruto de ERP; ' +
      'saída = produto pronto para a loja própria (storefront).',
    {
      product: z.object({
        ean: z.string().optional().nullable(),
        title: z.string().optional().nullable(),
        brand: z.string().optional().nullable(),
        description: z.string().optional().nullable(),
        image_urls: z.array(z.string()).optional(),
        attributes: z.record(z.string(), z.unknown()).optional(),
      }),
      options: z
        .object({
          with_images: z.boolean().default(true),
          with_ai: z.boolean().default(true),
          locale: z.string().default('pt-BR'),
        })
        .optional(),
    },
    async ({ product, options }) => {
      try {
        const enriched = await enrichProduct(product as never, options);
        return { content: [{ type: 'text', text: JSON.stringify(enriched, null, 2) }] };
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Erro no enriquecimento: ${(err as Error).message}` }],
          isError: true,
        };
      }
    }
  );

  // ── Tool 4: validate_listing ──────────────────────────────────────
  server.tool(
    'validate_listing',
    'Valida a completeza de um produto/listing para publicação em storefront: título, descrição, ' +
      'imagem, atributos obrigatórios, schema.org JSON-LD e SEO on-page. Retorna score 0-100, ' +
      'lista de issues (error/warning) e pronto-para-publicar (score >= 70).',
    {
      listing: z.record(z.string(), z.unknown()).describe('Objeto do produto/listing a validar'),
      rules: z
        .object({
          require_schema_org: z.boolean().default(true),
          require_image: z.boolean().default(true),
        })
        .optional(),
    },
    async ({ listing, rules }) => {
      try {
        const result = validateListing(listing, rules);
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Erro na validação: ${(err as Error).message}` }],
          isError: true,
        };
      }
    }
  );

  // ── Tool 5: enrich_batch ──────────────────────────────────────────
  server.tool(
    'enrich_batch',
    'Orquestrador de lote: aplica o pipeline de enriquecimento a uma lista de produtos brutos, ' +
      'um a um, e devolve relatório consolidado (produtos enriquecidos, falhas, warnings) pronto ' +
      'para importação na storefront.',
    {
      products: z
        .array(
          z.object({
            ean: z.string().optional().nullable(),
            title: z.string().optional().nullable(),
            brand: z.string().optional().nullable(),
            description: z.string().optional().nullable(),
            image_urls: z.array(z.string()).optional(),
            attributes: z.record(z.string(), z.unknown()).optional(),
                        })
                      )
                      .min(1)
                      .max(50),
      options: z
        .object({
          with_images: z.boolean().default(true),
          with_ai: z.boolean().default(true),
          locale: z.string().default('pt-BR'),
        })
        .optional(),
    },
    async ({ products, options }) => {
      try {
        const report = await enrichBatch(products as never, options);
        return { content: [{ type: 'text', text: JSON.stringify(report, null, 2) }] };
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Erro no lote: ${(err as Error).message}` }],
          isError: true,
        };
      }
    }
  );

  // ── Tool 6: analyze_url ───────────────────────────────────────────
  server.tool(
    'analyze_url',
    'Raspa e diagnostica a página de um produto na loja própria do cliente (storefront). ' +
      'Extrai título, preço, descrição, imagem, marca, schema.org e EAN; retorna um diagnóstico ' +
      'de prontidão por seção. Ideal para: o lojista cola o link do produto e o agente audita.',
    {
      url: z.string().url().describe('URL do produto na loja (http/https)'),
    },
    async ({ url }) => {
      try {
        const injection = checkInjection(url);
        if (injection.detected) {
          return {
            content: [{ type: 'text', text: JSON.stringify({ error: 'Entrada rejeitada por segurança', matched: injection.matched }) }],
            isError: true,
          };
        }
        const scraped = await scrapeProductUrl(url);
        return { content: [{ type: 'text', text: JSON.stringify(scraped, null, 2) }] };
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Erro ao analisar URL: ${(err as Error).message}` }],
          isError: true,
        };
      }
    }
  );

  // ── Tool 7: analyze_image ─────────────────────────────────────────
  server.tool(
    'analyze_image',
    'Analisa a imagem de um produto (por URL): resolução, proporção, fundo (uniforme/ruidoso), ' +
      'nitidez e prontidão para a loja. Sugere rembg (fundo branco) quando o fundo não é uniforme.',
    {
      image_url: z.string().describe('URL da imagem do produto (http/https)'),
    },
    async ({ image_url }) => {
      try {
        const analysis = await analyzeImageUrl(image_url);
        return { content: [{ type: 'text', text: JSON.stringify(analysis, null, 2) }] };
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Erro ao analisar imagem: ${(err as Error).message}` }],
          isError: true,
        };
      }
    }
  );

  // ── Tool 8: fetch_product_images ──────────────────────────────────
  server.tool(
    'fetch_product_images',
    'Baixa as imagens de um produto para EXIBIÇÃO no chat. Aceita: (a) URL da página ' +
      '(raspa e baixa todas as imagens do produto), ou (b) lista direta de URLs. ' +
      'Retorna data-URLs (renderizáveis no markdown) + caminhos locais.',
    {
      product_url: z.string().url().optional().describe('URL da página do produto (raspa as imagens)'),
      image_urls: z.array(z.string()).optional().describe('Lista direta de URLs de imagem'),
      limit: z.number().int().min(1).max(10).default(6).describe('Máx de imagens (default 6)'),
    },
    async ({ product_url, image_urls, limit }) => {
      try {
        let urls: string[] = image_urls ?? [];
        if (product_url) {
          const scraped = await scrapeProductUrl(product_url);
          if (!scraped.found) {
            return {
              content: [{ type: 'text', text: JSON.stringify({ error: scraped.error || 'Não foi possível raspar a página' }) }],
              isError: true,
            };
          }
          urls = scraped.image_urls.length ? scraped.image_urls : (scraped.image_url ? [scraped.image_url] : []);
        }
        if (!urls.length) {
          return {
            content: [{ type: 'text', text: JSON.stringify({ images: [], message: 'Nenhuma imagem encontrada' }) }],
          };
        }
        const images = await downloadImages(urls, limit ?? 6);
        // monta markdown renderizável para o chat (data-URLs)
        const gallery = images
          .filter((i) => i.data_url)
          .map((i) => `![produto-${i.index}](${i.data_url})`)
          .join('\n\n');
        const summary = images.map((i) => ({
          index: i.index,
          url: i.url,
          bytes: i.bytes,
          local_path: i.local_path,
          error: i.error,
        }));
        const text = gallery
          ? `**${images.filter((i) => i.data_url).length} imagens baixadas:**\n\n${gallery}\n\n\`\`\`json\n${JSON.stringify(summary, null, 2)}\n\`\`\``
          : JSON.stringify({ images: summary, message: 'Nenhuma imagem baixada' }, null, 2);
        return { content: [{ type: 'text', text }] };
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Erro ao baixar imagens: ${(err as Error).message}` }],
          isError: true,
        };
      }
    }
  );

  // ── Tool 9: prepare_shopify_payload ───────────────────────────────
  server.tool(
    'prepare_shopify_payload',
    'Converte um produto enriquecido (saída de enrich_product) no payload pronto da Shopify ' +
      'Admin GraphQL (productCreate) para PUBLICAÇÃO AUTOMÁTICA na loja, sem copiar/colar. ' +
      'Retorna a query GraphQL e o payload JSON com title, descriptionHtml, handle, vendor, ' +
      'tags (SEO), metafields (gtin, meta_title, meta_description) e imagem.',
    {
      product: z
        .object({
          title: z.string().optional(),
          description_html: z.string().optional(),
          seo_keywords: z.array(z.string()).optional(),
          brand: z.string().optional(),
          ean: z.string().optional().nullable(),
          image_url: z.string().optional().nullable(),
          meta_title: z.string().optional(),
          meta_description: z.string().optional(),
          bullets: z.array(z.string()).optional(),
          attributes: z.record(z.string(), z.unknown()).optional(),
        })
        .partial(),
      handle: z.string().optional().describe('Slug da URL (opcional; gerado do título se ausente)'),
    },
    async ({ product, handle }) => {
      try {
        const title = product.title?.trim() || 'Produto sem título';
        const slug = (handle || title).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80);
        const bullets = product.bullets ?? [];
        const descriptionHtml = product.description_html || `<p>${title}</p>${bullets.map((b) => `<li>${b}</li>`).join('')}`;
        const tags = (product.seo_keywords ?? []).slice(0, 6);
        const vendor = product.brand || 'Marca';

        const metafields = [];
        if (product.ean) metafields.push({ key: 'gtin', value: product.ean, type: 'single_line_text_field', namespace: 'custom' });
        if (product.meta_title) metafields.push({ key: 'meta_title', value: product.meta_title, type: 'single_line_text_field', namespace: 'custom' });
        if (product.meta_description) metafields.push({ key: 'meta_description', value: product.meta_description, type: 'multi_line_text_field', namespace: 'custom' });

        const shopify_payload = {
          input: {
            title,
            descriptionHtml,
            handle: slug,
            vendor,
            tags,
            productType: '',
            ...(product.image_url ? { media: [{ mediaContentType: 'IMAGE', originalSource: product.image_url }] } : {}),
            metafields,
            redirectNewUrls: true,
          },
          media: product.image_url ? [{ originalSource: product.image_url, mediaContentType: 'IMAGE' }] : [],
        };

        const result = {
          shopify_mutation_name: 'productCreate',
          shopify_query:
            'mutation productCreate($input: ProductInput!, $media: [CreateMediaInput!]) { productCreate(input: $input, media: $media) { product { id title handle vendor } userErrors { field message } } }',
          shopify_payload,
          summary: {
            title,
            handle: slug,
            vendor,
            tags,
            gtin: product.ean ?? null,
            image: product.image_url ?? null,
          },
        };
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Erro ao preparar payload Shopify: ${(err as Error).message}` }],
          isError: true,
        };
      }
    }
  );

  // ── Tool 10: ocr_image ────────────────────────────────────────────
  server.tool(
    'ocr_image',
    'Extrai texto de um PRINT/foto da página de produto (tesseract OCR, pt-BR). ' +
      'Ideal quando o lojista manda um print da loja própria ou do concorrente em vez de link: ' +
      'o agente lê o título, preço e marca direto da imagem.',
    {
      image_url: z.string().describe('URL da imagem (print/foto) para OCR'),
    },
    async ({ image_url }) => {
      try {
        const result = await ocrImageUrl(image_url);
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Erro no OCR: ${(err as Error).message}` }],
          isError: true,
        };
      }
    }
  );

  return server;
}

// ── Transporte stdio (dev) ──────────────────────────────────────────
async function main() {
  const server = makeServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write('[catalog-intelligence-agent] MCP server (stdio) pronto\n');
}

main().catch((err) => {
  process.stderr.write(`[catalog-intelligence-agent] Fatal: ${err.stack || err}\n`);
  process.exit(1);
});

