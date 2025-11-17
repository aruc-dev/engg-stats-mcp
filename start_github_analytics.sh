#!/bin/bash

# Start GitHub Engineering Analytics MCP Server
echo "Starting GitHub Engineering Analytics MCP Server..."

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check for required environment variables
if [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: GITHUB_TOKEN environment variable is required"
    exit 1
fi

# Start the GitHub analytics server
echo "Starting GitHub Engineering Analytics server on port ${GITHUB_MCP_PORT:-4001}"
echo "This server provides specialized engineering productivity metrics"
echo "Use alongside the official GitHub MCP server for complete functionality"

python mcp_github/analytics_server.py