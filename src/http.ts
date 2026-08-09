/**
 * Entrada HTTP (Streamable HTTP) para conexão com o deco Studio.
 * Usa WebStandardStreamableHTTPServerTransport (Fetch API, Node 22+, sem Express).
 * Stateless: um server + transport NOVO por request (padrão SDK — cada
 * conexão HTTP é um Protocol instance; o Studio mantém a sessão via header).
 *
 * Uso: PORT=8788 node dist/http.js
 * Studio: Settings → Connections → Custom Connection → http://localhost:8788/mcp
 */

import { createServer } from 'node:http';
import { WebStandardStreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js';
import { makeServer } from './server.js';

const httpServer = createServer(async (req, res) => {
  // CORS para o Studio (roda em outra origem)
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'content-type, mcp-session-id, authorization, accept');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  try {
    const body = await readBody(req);
    const request = new Request(`http://localhost${req.url ?? '/'}`, {
      method: req.method,
      headers: req.headers as Record<string, string>,
      body: body.length > 0 ? new Uint8Array(body) : undefined,
    });

    // Novo server + transport por request (stateless)
    const server = makeServer();
    const transport = new WebStandardStreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
      enableJsonResponse: true,
    });
    await server.connect(transport);

    const response = await transport.handleRequest(request);
    res.writeHead(response.status, Object.fromEntries(response.headers.entries()));
    const buf = Buffer.from(await response.arrayBuffer());
    res.end(buf);
  } catch (err) {
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: (err as Error).message }));
  }
});

function readBody(req: import('node:http').IncomingMessage): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on('data', (c) => chunks.push(Buffer.from(c)));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

const port = parseInt(process.env.PORT ?? '8788', 10);
httpServer.listen(port, () => {
  process.stderr.write(`[catalog-intelligence-agent] Streamable HTTP em http://localhost:${port}/mcp\n`);
});