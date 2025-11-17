#!/bin/bash

# Start Confluence Engineering Analytics MCP Server
echo "Starting Confluence Engineering Analytics MCP Server..."

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check for required environment variables
required_vars=("CONFLUENCE_BASE_URL" "CONFLUENCE_EMAIL" "CONFLUENCE_API_TOKEN")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var environment variable is required"
        exit 1
    fi
done

# Start the Confluence analytics server
echo "Starting Confluence Engineering Analytics server on port ${CONFLUENCE_MCP_PORT:-4003}"
echo "This server provides specialized documentation productivity metrics"
echo "Use alongside the official Atlassian MCP server for complete functionality"

python mcp_confluence/analytics_server.py