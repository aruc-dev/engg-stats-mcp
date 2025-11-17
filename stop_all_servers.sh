#!/bin/bash

# Stop All MCP Servers
echo "Stopping all Engineering Productivity MCP servers..."
cd "$(dirname "$0")"

if [ -f .server_pids ]; then
    while read pid; do
        if [ -n "$pid" ]; then
            echo "Stopping server with PID $pid..."
            kill $pid 2>/dev/null
        fi
    done < .server_pids
    
    # Wait a moment for graceful shutdown
    sleep 2
    
    # Force kill any remaining processes
    while read pid; do
        if [ -n "$pid" ]; then
            kill -9 $pid 2>/dev/null
        fi
    done < .server_pids
    
    rm -f .server_pids
    echo "All servers stopped."
else
    echo "No PID file found. Attempting to kill servers by port..."
    
    # Try to kill processes on the expected ports
    for port in 4001 4002 4003; do
        pid=$(lsof -t -i:$port 2>/dev/null)
        if [ -n "$pid" ]; then
            echo "Killing process on port $port (PID: $pid)"
            kill $pid
        fi
    done
fi