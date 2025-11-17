# Engineering Productivity MCP Servers

A set of **Model Context Protocol (MCP) servers** in Python that provide engineering activity analytics for GitHub, Jira, and Confluence. These servers expose engineer activity metrics as tools that can be consumed by AI agents in VS Code, Windsurf, or other MCP-compatible environments.

## Features

- **GitHub Analytics**: PR authoring, merge metrics, review activity, and code contribution analysis
- **Jira Analytics**: Issue assignment, resolution tracking, reopened issues, and lead time calculations
- **Confluence Analytics**: Page creation, updates, and commenting activity
- **Real-time Metrics**: All analytics computed on-the-fly from external APIs (no database required)
- **MCP Protocol**: Standards-compliant MCP servers with HTTP transport
- **Robust Error Handling**: Rate limiting detection, authentication validation, and graceful failure modes

## Architecture

```
engg-stats-mcp/
├── mcp_github/          # GitHub MCP server
├── mcp_jira/            # Jira MCP server  
├── mcp_confluence/      # Confluence MCP server
├── shared/              # Shared API clients and utilities
├── requirements.txt     # Python dependencies
├── .env.example        # Environment configuration template
└── *.sh                # Startup/shutdown scripts
```

## Quick Start

### 1. Prerequisites

- Python 3.10+
- API access to GitHub, Jira, and/or Confluence
- Virtual environment (recommended)

### 2. Installation

```bash
# Clone or create the project
cd engg-stats-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API credentials
nano .env
```

Required environment variables:

```env
# GitHub (required for GitHub server)
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_MCP_PORT=4001

# Jira (required for Jira server)
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token_here
JIRA_MCP_PORT=4002

# Confluence (required for Confluence server)
CONFLUENCE_BASE_URL=https://your-org.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_confluence_api_token_here
CONFLUENCE_MCP_PORT=4003

# Optional
LOG_LEVEL=INFO
```

### 4. Start Servers

```bash
# Start all servers
./start_all_servers.sh

# Or start individual servers
./start_github_server.sh
./start_jira_server.sh
./start_confluence_server.sh

# Stop all servers
./stop_all_servers.sh
```

### 5. Verify Installation

Check that servers are running:

```bash
# Health checks
curl http://localhost:4001/health  # GitHub
curl http://localhost:4002/health  # Jira
curl http://localhost:4003/health  # Confluence

# List available tools
curl -X POST http://localhost:4001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

## API Documentation

### GitHub MCP Server

**Endpoint**: `http://localhost:4001/mcp`

#### Tool: `github_engineer_activity`

Analyzes GitHub activity for a user over a date range.

**Input**:
```json
{
  "login": "alice",
  "from_date": "2025-11-01", 
  "to_date": "2025-11-15",
  "repos": ["owner/repo1", "owner/repo2"]  // Optional
}
```

**Output**:
```json
{
  "login": "alice",
  "from": "2025-11-01",
  "to": "2025-11-15", 
  "prsAuthored": 12,
  "prsMerged": 10,
  "avgPrCycleHours": 48.5,
  "reviewsGiven": 8,
  "commentsWritten": 23
}
```

### Jira MCP Server

**Endpoint**: `http://localhost:4002/mcp`

#### Tool: `jira_engineer_activity`

Analyzes Jira issue activity for a user over a date range.

**Input**:
```json
{
  "user_email_or_account_id": "alice@company.com",
  "from_date": "2025-11-01",
  "to_date": "2025-11-15", 
  "jql_extra": "project = PROJ AND labels = backend"  // Optional
}
```

**Output**:
```json
{
  "user": "alice@company.com",
  "from": "2025-11-01",
  "to": "2025-11-15",
  "issuesAssigned": 15,
  "issuesResolved": 12, 
  "reopenedCount": 2,
  "avgLeadTimeHours": 72.3
}
```

### Confluence MCP Server

**Endpoint**: `http://localhost:4003/mcp`

#### Tool: `confluence_engineer_activity`

Analyzes Confluence content activity for a user over a date range.

**Input**:
```json
{
  "user_email_or_account_id": "alice@company.com",
  "from_date": "2025-11-01", 
  "to_date": "2025-11-15",
  "space_key": "TECH"  // Optional
}
```

**Output**:
```json
{
  "user": "alice@company.com",
  "from": "2025-11-01",
  "to": "2025-11-15",
  "pagesCreated": 3,
  "pagesUpdated": 7,
  "commentsWritten": 12
}
```

## IDE Integration

### VS Code / Windsurf Configuration

Configure your IDE's MCP client to connect to the servers:

```json
{
  "mcp": {
    "servers": {
      "github-eng-activity": {
        "command": "curl",
        "args": ["-X", "POST", "http://localhost:4001/mcp"],
        "transport": "http"
      },
      "jira-eng-activity": {
        "command": "curl", 
        "args": ["-X", "POST", "http://localhost:4002/mcp"],
        "transport": "http"
      },
      "confluence-eng-activity": {
        "command": "curl",
        "args": ["-X", "POST", "http://localhost:4003/mcp"], 
        "transport": "http"
      }
    }
  }
}
```

### Usage Examples

Once configured, you can use natural language prompts with your AI agent:

- *"Get GitHub activity for alice from 2025-11-01 to 2025-11-15"*
- *"Compare Jira activity for alice@company.com and bob@company.com in the last 2 weeks"*  
- *"Summarize Confluence contributions for alice this month in the TECH space"*
- *"Show me engineering productivity metrics for the backend team this sprint"*

## API Token Setup

### GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with scopes:
   - `repo` (for private repos) or `public_repo` (for public only)
   - `read:user`
   - `read:org` (if analyzing org repos)

### Jira Cloud API Token

1. Go to [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create API token
3. Use your Atlassian account email as `JIRA_EMAIL`

### Confluence Cloud API Token

1. Same as Jira (can reuse the same token and email)
2. Ensure your account has appropriate space permissions

## Troubleshooting

### Common Issues

**"Rate limit exceeded"**: APIs return 429 status codes when rate limited. The servers will return readable error messages. Wait before retrying.

**Authentication errors**: Verify your API tokens and URLs in `.env`. Check token permissions and expiration.

**Import errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`

**Port conflicts**: Change port numbers in `.env` if defaults (4001-4003) are in use.

### Debugging

Enable debug logging:
```bash
echo "LOG_LEVEL=DEBUG" >> .env
```

Check server logs for detailed API request/response information.

### Testing Individual Tools

Test tools directly via curl:

```bash
# Test GitHub tool
curl -X POST http://localhost:4001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "github_engineer_activity",
      "arguments": {
        "login": "octocat",
        "from_date": "2025-11-01", 
        "to_date": "2025-11-15"
      }
    }
  }'
```

## Architecture Notes

- **No Database**: All metrics computed on-demand from external APIs
- **Stateless**: Servers don't maintain session state between requests
- **Concurrent**: Multiple requests can be handled simultaneously
- **Error Resilient**: Individual API failures don't crash servers
- **Extensible**: Easy to add new tools or modify existing metrics

## Contributing

1. Fork the repository
2. Create feature branches for new tools or improvements
3. Add tests for new functionality
4. Update documentation as needed
5. Submit pull requests

## License

MIT License - see LICENSE file for details.