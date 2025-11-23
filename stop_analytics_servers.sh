#!/bin/bash

# Stop all Engineering Analytics MCP Servers
echo "Stopping all Engineering Analytics MCP Servers..."

# Find and kill processes by port (analytics servers use ports 4011-4013)
ports=(4011 4012 4013)
for port in "${ports[@]}"; do
    pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "Stopping analytics server on port $port (PID: $pid)"
        kill $pid
    else
        echo "No analytics server found on port $port"
    fi
done

echo "All Analytics servers stopped."