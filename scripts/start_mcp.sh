#!/usr/bin/env bash
# Sobe o MCP com o .env carregado de forma garantida
set -a
. /root/catalog-intelligence-agent/.env
set +a
cd /root/catalog-intelligence-agent
export PORT=8791
echo "[start] AI_API_KEYS set: $([ -n "$AI_API_KEYS" ] && echo SIM || echo NAO)" >> /tmp/mcp-opencode.log
exec node dist/http.js
