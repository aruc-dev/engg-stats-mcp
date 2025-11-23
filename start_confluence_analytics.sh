#!/bin/bash

# Start Confluence Engineering Analytics MCP Server
echo "Starting Confluence Engineering Analytics MCP Server..."

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
required_vars=("CONFLUENCE_BASE_URL" "CONFLUENCE_EMAIL" "CONFLUENCE_API_TOKEN")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var environment variable is required"
        exit 1
    fi
done

# Start the Confluence analytics server
echo "Starting Confluence Engineering Analytics server on port ${CONFLUENCE_ANALYTICS_PORT:-4013}"
echo "This server provides specialized documentation productivity metrics"
echo "Use alongside the official Atlassian MCP server for complete functionality"

export MCP_PORT=${CONFLUENCE_ANALYTICS_PORT:-4013}
python mcp_confluence/analytics_server.py