#!/bin/bash

# Start Jira Engineering Analytics MCP Server
echo "Starting Jira Engineering Analytics MCP Server..."

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check for required environment variables
required_vars=("JIRA_BASE_URL" "JIRA_EMAIL" "JIRA_API_TOKEN")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var environment variable is required"
        exit 1
    fi
done

# Start the Jira analytics server
echo "Starting Jira Engineering Analytics server on port ${JIRA_MCP_PORT:-4002}"
echo "This server provides specialized engineering productivity metrics for Jira"
echo "Use alongside the official Atlassian MCP server for complete functionality"

python mcp_jira/analytics_server.py