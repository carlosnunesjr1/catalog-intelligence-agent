# Catalog Intelligence Agent

**Agente MCP de enriquecimento autônomo de catálogo para STOREFRONTS (lojas próprias).**
Trilha *Catalog & Content* — Hackathon [Agents for Commerce](https://hackathon.decocms.com/agents-for-commerce) (Deco, 01–09/08/2026).

> Recebe **dados brutos de ERP** (título em CAIXA ALTA, sem descrição, marca genérica, sem imagem)
> e devolve o **produto pronto para publicar na loja própria do lojista** — com título SEO,
> bullets de benefícios, descrição HTML mobile-first, slug/meta, **schema.org JSON-LD** e imagem.

Não é integrador de marketplace: foca no motor central de higienização que qualquer storefront
(deco.cx, VTEX, Shopify, Nuvemshop…) consome via um agente de IA.

---

## Ferramentas MCP (5)

| Tool | O que faz |
|---|---|
| `lookup_ean` | Dados de referência por EAN/GTIN (valida dígito verificador + cascade: Bluesoft Cosmos BR → Open Food Facts → EAN-Search) |
| `search_images` | URLs de imagem candidatas por EAN **ou título** (marca própria sem EAN → Unsplash/Pexels) |
| `enrich_product` | Pipeline completo: higieniza título → bullets → descrição HTML → SEO → schema.org JSON-LD → imagem (rembg fundo branco) → análise visual → SEO da imagem (alt/filename/caption) |
| `validate_listing` | Score 0–100 de completeza p/ loja própria (SEO on-page, dados, schema.org, imagem, **regras de moda**: grade/composição/cor/medidas) + issues |
| `enrich_batch` | Orquestra lote de até 50 produtos → relatório consolidado |
| `analyze_url` | Raspa e diagnostica a página de um produto na loja do cliente (título, preço, marca, SKU, imagens, EAN) |
| `analyze_image` | Analisa a imagem: resolução, proporção, fundo, nitidez, **metadados EXIF** + prontidão p/ loja |
| `fetch_product_images` | Baixa até 10 imagens e exibe **galeria no chat** (data-URLs) ou retorna caminhos locais |
| `prepare_shopify_payload` | Converte o produto enriquecido no **payload GraphQL productCreate** (publicação automática na loja, sem copiar/colar) |

## Impacto financeiro (pitch)

- Operação de **5.000 SKUs** gasta ~**200 h/mês** de equipe de catálogo → **R$ 5.000/mês** em horas (R$25/h)
- Concorrência (PIMs + IA): US$600–1.000/mês para 500 SKUs — **nosso custo ≈ R$0–50/lote**
- Demo inteira roda em free tiers (~R$0)

## Execução

```bash
npm install
npm run build        # tsc → dist/
npm run dev          # modo dev (tsx watch) — MCP server stdio
npm start            # node dist/server.js — MCP server stdio
npm test             # testes unitários (9): EAN, validate, schema
npm run smoke        # smoke end-to-end do protocolo MCP (6 checks, stdio)
```

### Conectar em um cliente MCP

**Claude Desktop / Cursor / CLI:**
```json
{ "mcpServers": { "catalog-intelligence": { "command": "node", "args": ["/caminho/para/dist/server.js"] } } }
```

**deco Studio (Custom Connection):** rode o servidor HTTP e aponte a Connection para o endpoint:

```bash
PORT=8788 node dist/http.js     # Streamable HTTP em http://localhost:8788/mcp
```

No Studio: *Agent → Settings → Connections → Add Connection → Custom Connection* →
cole a URL → selecione as tools do agente.

### Teste com MCP Inspector

```bash
npx @modelcontextprotocol/inspector node dist/server.js
```

---

## Exemplo

**Entrada (ERP):**
```json
{ "ean": "7891234567890", "title": "FURADEIRA IMPACTO 750W 110V", "brand": "SEM MARCA" }
```

**Saída (storefront):**
```json
{
  "title": "Furadeira de Impacto 750W 110V",
  "slug": "furadeira-de-impacto-750w-110v",
  "meta_title": "Furadeira de Impacto 750W 110V — Compre Online",
  "bullets": ["✅ Potência de 750W...", "✅ Mandril 13mm...", "✅ Ideal para uso doméstico e profissional..."],
  "description_html": "<p>Furadeira de impacto profissional...</p>",
  "seo_keywords": ["furadeira", "furadeira de impacto", "750w"],
  "schema_org": { "@type": "Product", "name": "Furadeira de Impacto 750W 110V", "sku": "7891234567890", "brand": {"@type":"Brand","name":"..."} },
  "image_url": "https://...",
  "warnings": []
}
```

## Stack

- TypeScript ESM (Node 22+)
- `@modelcontextprotocol/sdk` (MCP) + `zod` (schemas)
- Transportes: **stdio** (dev) + **Streamable HTTP** (deco Studio)
- IA: qualquer endpoint OpenAI-compatível via env (`AI_ENDPOINT`, `AI_MODEL`, `AI_API_KEY`) — **sem key, o agente funciona 100% determinístico**
- Zero dependências proprietárias — sem regras de marketplace, sem pricing engine

## Env vars

| Var | Uso | Obrigatória |
|---|---|---|
| `AI_ENDPOINT` | Endpoint OpenAI-compatível (default: Nous inference) | não |
| `AI_MODEL` | Modelo (default: `deepseek-v4-flash`) | não |
| `AI_API_KEY` | Key da IA (sem ela → fallback determinístico) | não |
| `COSMOS_TOKEN` | Bluesoft Cosmos BR (opcional, 1ª fonte EAN) | não |
| `EAN_SEARCH_TOKEN` | EAN-Search.org (opcional, 3ª fonte) | não |
| `PORT` | Porta do Streamable HTTP (default 8788) | não |

## Integração com deco Studio

O servidor é um **MCP server padrão** — pluga como *Connection* customizada no Studio
(control plane de agentes da Deco). A demo mostra o agente rodando **dentro do Studio**:
conectar → chamar `enrich_product` → ver trace/custo no Monitor.

## Author

Carlos Nunes — ClickPim (consultor Amazon BR / automação de catálogo).
Submissão individual, hackathon Agents for Commerce — trilha Catalog & Content.