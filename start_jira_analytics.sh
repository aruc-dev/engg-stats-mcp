#!/bin/bash

# Start Jira Engineering Analytics MCP Server
echo "Starting Jira Engineering Analytics MCP Server..."

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
required_vars=("JIRA_BASE_URL" "JIRA_EMAIL" "JIRA_API_TOKEN")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var environment variable is required"
        exit 1
    fi
done

# Start the Jira analytics server
echo "Starting Jira Engineering Analytics server on port ${JIRA_ANALYTICS_PORT:-4012}"
echo "This server provides specialized engineering productivity metrics for Jira"
echo "Use alongside the official Atlassian MCP server for complete functionality"

export MCP_PORT=${JIRA_ANALYTICS_PORT:-4012}
python mcp_jira/analytics_server.py