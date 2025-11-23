#!/bin/bash

# Start GitHub Engineering Analytics MCP Server
echo "Starting GitHub Engineering Analytics MCP Server..."

cd "$(dirname "$0")"

# Check if .env exists and load it
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Please copy .env.example to .env and configure your API tokens."
    exit 1
fi
source .env

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "ERROR: No virtual environment found. Please run install.sh first."
    exit 1
fi

# Check for required environment variables
if [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: GITHUB_TOKEN environment variable is required"
    exit 1
fi

# Start the GitHub analytics server
echo "Starting GitHub Engineering Analytics server on port ${GITHUB_ANALYTICS_PORT:-4011}"
echo "This server provides specialized engineering productivity metrics"
echo "Use alongside the official GitHub MCP server for complete functionality"

export MCP_PORT=${GITHUB_ANALYTICS_PORT:-4011}
python mcp_github/analytics_server.py