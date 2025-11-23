#!/bin/bash

# Start Confluence MCP Server
echo "Starting Confluence MCP server..."
cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Please copy .env.example to .env and configure your API tokens."
    exit 1
fi

# Load environment variables
source .env

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "WARNING: No virtual environment found. Please run install.sh first."
fi

# Start the Confluence server
python -m mcp_confluence.server