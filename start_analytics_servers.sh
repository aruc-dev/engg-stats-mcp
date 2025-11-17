#!/bin/bash

# Start all Engineering Analytics MCP Servers
echo "Starting all Engineering Analytics MCP Servers..."

cd "$(dirname "$0")"

# Start servers in background
echo "Starting GitHub Engineering Analytics server..."
./start_github_analytics.sh &
GITHUB_PID=$!

echo "Starting Jira Engineering Analytics server..."  
./start_jira_analytics.sh &
JIRA_PID=$!

echo "Starting Confluence Engineering Analytics server..."
./start_confluence_analytics.sh &
CONFLUENCE_PID=$!

echo ""
echo "All Engineering Analytics servers started:"
echo "  - GitHub Analytics (PID: $GITHUB_PID) on port ${GITHUB_MCP_PORT:-4001}"
echo "  - Jira Analytics (PID: $JIRA_PID) on port ${JIRA_MCP_PORT:-4002}" 
echo "  - Confluence Analytics (PID: $CONFLUENCE_PID) on port ${CONFLUENCE_MCP_PORT:-4003}"
echo ""
echo "Use these servers alongside the official GitHub and Atlassian MCP servers"
echo "for comprehensive GitHub/Jira/Confluence functionality plus engineering analytics."
echo ""
echo "To stop all servers, run: ./stop_analytics_servers.sh"

# Wait for all background processes
wait