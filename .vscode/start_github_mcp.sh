#!/bin/bash
cd "$(dirname "$0")"
source .env 2>/dev/null || true
source venv/bin/activate
exec python -m mcp_github.server