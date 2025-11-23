# Start Scripts Reference

## 🚀 Quick VS Code Setup

**Fastest way to get started:**
```bash
# Open the pre-configured workspace
code engineering-stats-mcp.code-workspace

# Use Command Palette (Ctrl+Shift+P)
"Tasks: Run Task" → "Start All Main Servers"
"Tasks: Run Task" → "Start Analytics Servers"
```

## Server Organization

This repository contains **6 MCP servers** organized into two groups:

### Main MCP Servers (Ports 4001-4003)
- **GitHub MCP Server** (Port 4001): Full GitHub integration with engineering activity tracking
- **Jira MCP Server** (Port 4002): Full Jira integration with engineering activity tracking  
- **Confluence MCP Server** (Port 4003): Full Confluence integration with engineering activity tracking

### Analytics MCP Servers (Ports 4011-4013)
- **GitHub Analytics Server** (Port 4011): Specialized engineering productivity metrics for GitHub
- **Jira Analytics Server** (Port 4012): Specialized engineering productivity metrics for Jira
- **Confluence Analytics Server** (Port 4013): Specialized documentation productivity metrics for Confluence

## Start Scripts

### Individual Server Scripts
1. **`start_github_server.sh`** - Start GitHub MCP server (port 4001)
2. **`start_jira_server.sh`** - Start Jira MCP server (port 4002)
3. **`start_confluence_server.sh`** - Start Confluence MCP server (port 4003)
4. **`start_github_analytics.sh`** - Start GitHub analytics server (port 4011)
5. **`start_jira_analytics.sh`** - Start Jira analytics server (port 4012)
6. **`start_confluence_analytics.sh`** - Start Confluence analytics server (port 4013)

### Group Launcher Scripts
7. **`start_all_servers.sh`** - Start all main MCP servers (ports 4001-4003)
8. **`start_analytics_servers.sh`** - Start all analytics servers (ports 4011-4013)

### Special Purpose Scripts
9. **`start_mcp_for_vscode.sh`** - Start GitHub MCP server configured for VS Code integration (port 4006)

## Stop Scripts

1. **`stop_all_servers.sh`** - Stop all main MCP servers (ports 4001-4003)
2. **`stop_analytics_servers.sh`** - Stop all analytics servers (ports 4011-4013)

## Usage Patterns

### Development Usage
```bash
# Start all main servers for full functionality
./start_all_servers.sh

# Start analytics servers for specialized metrics
./start_analytics_servers.sh

# Start VS Code integration
./start_mcp_for_vscode.sh
```

### Individual Server Usage
```bash
# Start only GitHub functionality
./start_github_server.sh

# Start only analytics
./start_github_analytics.sh
```

### Cleanup
```bash
# Stop main servers
./stop_all_servers.sh

# Stop analytics servers  
./stop_analytics_servers.sh
```

## Script Features

All scripts include:
- ✅ Environment file validation (`.env` required)
- ✅ Virtual environment detection (`.venv` or `venv`)
- ✅ Environment variable validation
- ✅ Consistent error handling
- ✅ Proper port assignment
- ✅ Clear status messages

## Port Allocation

| Service | Port | Purpose |
|---------|------|---------|
| GitHub MCP | 4001 | Main GitHub server |
| Jira MCP | 4002 | Main Jira server |
| Confluence MCP | 4003 | Main Confluence server |
| GitHub Analytics | 4011 | GitHub metrics server |
| Jira Analytics | 4012 | Jira metrics server |
| Confluence Analytics | 4013 | Confluence metrics server |
| VS Code GitHub | 4006 | GitHub server for VS Code |

## Architecture

All servers use:
- **FastMCP framework** for consistent MCP protocol implementation
- **Comprehensive error handling** with specific exception types
- **Environment-based configuration** via `.env` files
- **Modular design** with shared utilities in `shared/` directory