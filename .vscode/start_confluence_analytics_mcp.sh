#!/bin/bash
cd "$(dirname "$0")/.."
source .env 2>/dev/null || true
source venv/bin/activate
export MCP_PORT=${MCP_PORT:-4013}
exec python mcp_confluence/analytics_server.py