#!/bin/bash

# Start All Main MCP Servers
echo "Starting all Engineering Productivity MCP servers..."
cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Please copy .env.example to .env and configure your API tokens."
    exit 1
fi

# Load environment variables
source .env

# Function to start a server in background
start_server() {
    local server_name=$1
    local script_name=$2
    echo "Starting $server_name server..."
    ./$script_name &
    local pid=$!
    echo "$server_name server started with PID $pid"
    echo $pid >> .server_pids
}

# Clean up any existing PID file
rm -f .server_pids

# Start all servers
start_server "GitHub" "start_github_server.sh"
start_server "Jira" "start_jira_server.sh" 
start_server "Confluence" "start_confluence_server.sh"

echo ""
echo "All servers started! PIDs saved in .server_pids"
echo ""
echo "Server endpoints:"
echo "  GitHub MCP:      http://localhost:4001/mcp"
echo "  Jira MCP:        http://localhost:4002/mcp"
echo "  Confluence MCP:  http://localhost:4003/mcp"
echo ""
echo "Health check endpoints:"
echo "  GitHub:      http://localhost:4001/health"
echo "  Jira:        http://localhost:4002/health"
echo "  Confluence:  http://localhost:4003/health"
echo ""
echo "To stop all servers, run: ./stop_all_servers.sh"