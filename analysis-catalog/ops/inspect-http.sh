#!/usr/bin/env bash
set -euo pipefail

CLIENT_PORT="${CLIENT_PORT:-6275}"
SERVER_PORT="${SERVER_PORT:-6278}"
MCP_HTTP_PORT="${MCP_HTTP_PORT:-8000}"

pkill -f "modelcontextprotocol/inspector|mcp-inspector|euclid_catalog_mcp.server" >/dev/null 2>&1 || true

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

./.venv/bin/python -m euclid_catalog_mcp.server >/tmp/euclid-mcp-http.stdout.log 2>/tmp/euclid-mcp-http.stderr.log &
SERVER_PID=$!

sleep 1

echo "Started MCP server PID=${SERVER_PID}"
echo "MCP endpoint: http://127.0.0.1:${MCP_HTTP_PORT}/mcp"
echo "Inspector URL: http://127.0.0.1:${CLIENT_PORT}"
echo "Inspector proxy: http://127.0.0.1:${SERVER_PORT}"
echo
echo "In Inspector UI set:"
echo "  Transport     = streamable-http"
echo "  URL           = http://127.0.0.1:${MCP_HTTP_PORT}/mcp"
echo "  Proxy Address = http://127.0.0.1:${SERVER_PORT}"
echo

CLIENT_PORT="${CLIENT_PORT}" SERVER_PORT="${SERVER_PORT}" DANGEROUSLY_OMIT_AUTH=true \
  npx @modelcontextprotocol/inspector
