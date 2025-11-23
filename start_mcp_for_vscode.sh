#!/bin/bash

# VS Code MCP Server Startup Script for GitHub Engineering Activity
# This script starts the GitHub MCP server for VS Code integration

# Change to the project directory
cd "$(dirname "$0")"

# Check if .env exists and load it
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Please copy .env.example to .env and configure your GitHub token."
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

# Set default port for VS Code (can be overridden)
export GITHUB_MCP_PORT=${GITHUB_MCP_PORT:-4006}

# Start the MCP server for VS Code
exec python mcp_github/server.py