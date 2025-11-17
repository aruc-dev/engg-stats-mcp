#!/bin/bash

# Stop all Engineering Analytics MCP Servers
echo "Stopping all Engineering Analytics MCP Servers..."

# Find and kill processes by port
ports=(4001 4002 4003)
for port in "${ports[@]}"; do
    pid=$(lsof -ti:$port)
    if [ -n "$pid" ]; then
        echo "Stopping server on port $port (PID: $pid)"
        kill $pid
    else
        echo "No server found on port $port"
    fi
done

echo "All Analytics servers stopped."