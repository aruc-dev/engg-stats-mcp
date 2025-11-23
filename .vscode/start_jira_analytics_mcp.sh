#!/bin/bash
cd "$(dirname "$0")/.."
source .env 2>/dev/null || true
source venv/bin/activate
export MCP_PORT=${MCP_PORT:-4012}
exec python mcp_jira/analytics_server.py