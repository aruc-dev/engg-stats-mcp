# Engineering Productivity MCP Servers - Hybrid Architecture

A set of **specialized engineering analytics MCP servers** designed to work alongside official GitHub and Atlassian MCP servers. This hybrid approach provides both comprehensive platform functionality through official servers and specialized engineering productivity metrics through custom analytics servers.

## 🏗️ Hybrid Architecture

This project now follows a **hybrid architecture** that combines:

### Official MCP Servers (for comprehensive platform access):
- **[GitHub's Official MCP Server](https://github.com/github/github-mcp-server)**: Repository management, issues, PRs, workflows, and more
- **[Atlassian's Official MCP Server](https://github.com/atlassian/atlassian-mcp-server)**: Secure OAuth access to Jira and Confluence

### Custom Analytics Servers (for engineering productivity insights):
- **GitHub Analytics**: PR cycle times, review metrics, contribution analysis
- **Jira Analytics**: Issue lead times, resolution tracking, quality metrics  
- **Confluence Analytics**: Documentation productivity, content engagement

## Features

### 📊 GitHub Engineering Analytics
- **PR Metrics**: Authoring rates, merge statistics, cycle time analysis
- **Review Activity**: Code review participation, comment engagement
- **Repository Filtering**: Focus analytics on specific repositories
- **Quality Indicators**: Merge rates, review participation ratios

### 📋 Jira Engineering Analytics  
- **Issue Tracking**: Assignment rates, resolution velocity, reopened analysis
- **Lead Time Calculation**: Average issue lifecycle duration
- **Quality Metrics**: Resolution rates, defect analysis
- **JQL Filtering**: Custom project and label-based analytics

### 📝 Confluence Engineering Analytics
- **Content Productivity**: Page creation and update rates
- **Engagement Metrics**: Comment activity, collaboration indicators
- **Space Analytics**: Cross-space content distribution
- **Documentation Velocity**: Content creation trends over time

## Quick Start

### 1. Prerequisites

- Python 3.10+
- VS Code 1.101+ (for remote MCP servers)
- Node.js 18+ (for Atlassian server)
- API access to GitHub, Jira, and/or Confluence
- Virtual environment (recommended)

### 2. Installation

```bash
# Clone or navigate to project
cd engg-stats-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. VS Code Workspace Setup (Recommended)

This repository includes a complete VS Code workspace configuration for seamless development:

```bash
# Open the workspace in VS Code
code engineering-stats-mcp.code-workspace

# Or open the folder directly
code .
```

The `.vscode/` folder contains:
- **`mcp.json`**: All 6 MCP servers pre-configured
- **`tasks.json`**: One-click server management via Command Palette
- **`launch.json`**: Debug configurations for all servers
- **`settings.json`**: Python development optimizations
- **`extensions.json`**: Recommended extensions

**Quick VS Code Setup:**
1. Open workspace → Install recommended extensions when prompted
2. Run task: `Ctrl+Shift+P` → "Tasks: Run Task" → "Install Dependencies"
3. Run task: "Start All Main Servers" to launch GitHub/Jira/Confluence servers
4. Run task: "Start Analytics Servers" for specialized metrics servers

### 4. Manual Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API credentials
nano .env
```

Required environment variables:

```env
# GitHub (for analytics server)
GITHUB_TOKEN=your_github_personal_access_token_here

# Jira (for analytics server)
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token_here

# Confluence (for analytics server)
CONFLUENCE_BASE_URL=https://your-org.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_confluence_api_token_here

# Optional
LOG_LEVEL=INFO
```

### 4. Setup Hybrid MCP Configuration

#### Option 1: Use Pre-configured Setup
Copy the hybrid configuration to your VS Code settings:

```bash
cp vscode-mcp-hybrid-config.json ~/.config/vscode/mcp.json
```

#### Option 2: Manual Configuration
Add to your VS Code MCP configuration file:

```json
{
  "mcp": {
    "servers": {
      "github-official": {
        "type": "http",
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": {
          "Authorization": "Bearer ${input:github_mcp_pat}"
        }
      },
      "atlassian-official": {
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
      },
      "github-engineering-analytics": {
        "command": "python",
        "args": ["./mcp_github/analytics_server.py"],
        "cwd": "/path/to/engg-stats-mcp",
        "env": {
          "PATH": "/path/to/engg-stats-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin"
        }
      },
      "jira-engineering-analytics": {
        "command": "python", 
        "args": ["./mcp_jira/analytics_server.py"],
        "cwd": "/path/to/engg-stats-mcp"
      },
      "confluence-engineering-analytics": {
        "command": "python",
        "args": ["./mcp_confluence/analytics_server.py"], 
        "cwd": "/path/to/engg-stats-mcp"
      }
    },
    "inputs": [
      {
        "type": "promptString",
        "id": "github_mcp_pat",
        "description": "GitHub Personal Access Token for Official MCP Server",
        "password": true
      }
    ]
  }
}
```

### 5. Start Analytics Servers

```bash
# Start all main servers (ports 4001-4003)
./start_all_servers.sh

# Start all analytics servers (ports 4011-4013)
./start_analytics_servers.sh

# Or start individual servers
./start_github_server.sh        # Port 4001
./start_jira_server.sh          # Port 4002
./start_confluence_server.sh    # Port 4003
./start_github_analytics.sh     # Port 4011
./start_jira_analytics.sh       # Port 4012
./start_confluence_analytics.sh # Port 4013

# Stop servers
./stop_all_servers.sh          # Stop main servers
./stop_analytics_servers.sh    # Stop analytics servers
```

**Server Ports:**
| Server | Port | Type |
|--------|------|------|
| GitHub MCP | 4001 | Main |
| Jira MCP | 4002 | Main |
| Confluence MCP | 4003 | Main |
| GitHub Analytics | 4011 | Analytics |
| Jira Analytics | 4012 | Analytics |
| Confluence Analytics | 4013 | Analytics |

### 6. Complete Setup

1. **GitHub Official Server**: Will use OAuth or the PAT you configured
2. **Atlassian Official Server**: Run OAuth flow when first connecting
3. **Analytics Servers**: Will automatically use environment variables

## Usage Examples

### GitHub Analytics
```
"Analyze GitHub engineering metrics for alice from 2025-11-01 to 2025-11-15 in the backend repos"
```

### Combined Workflow
```
"First, get the open issues from project BACKEND (official server), then analyze alice's Jira productivity this month (analytics server)"
```

### Documentation Analysis  
```
"Show confluence activity for bob in the TECH space, plus create a summary page of his contributions (using both servers)"
```

## Technical Architecture

### 🏗️ FastMCP Framework
All custom analytics servers are built using the **FastMCP** framework:
- **Consistent Implementation**: Standardized server pattern across all 6 MCP servers
- **SSE Transport**: Server-Sent Events for real-time communication
- **Tool Decorators**: Simple, declarative tool definitions
- **Type Safety**: Pydantic models for input validation and serialization

### 🛡️ Comprehensive Error Handling
Robust error management system with specific exception types:
- **Hierarchical Error System**: Base `MCPServerError` with platform-specific errors
- **API Error Types**: `GitHubAPIError`, `JiraAPIError`, `ConfluenceAPIError`
- **Validation Errors**: Input validation with detailed error messages
- **Rate Limiting**: Automatic retry logic with exponential backoff
- **Network Resilience**: Timeout handling and connection error management

### 🔌 VS Code Integration
Complete development environment configuration:
- **MCP Server Configuration**: Pre-configured for all 6 servers
- **Debug Support**: Full debugging with breakpoints for all servers
- **Task Automation**: One-click server management via Command Palette
- **Shell Scripts**: Alternative startup scripts with proper environment activation
- **Troubleshooting**: Built-in connectivity tests and error diagnostics

## Architecture Benefits

### 🔧 Official Servers Provide:
- **Robust API Access**: Full platform functionality with official support
- **Security**: OAuth 2.0 authentication, rate limiting, security updates
- **Comprehensive Tools**: Complete CRUD operations, advanced features
- **Maintenance**: Automatically updated and maintained by platform vendors

### 📊 Custom Analytics Provide:
- **Specialized Metrics**: Engineering productivity insights not available elsewhere
- **Custom Business Logic**: Tailored calculations for your specific needs  
- **Focused Functionality**: Lightweight, purpose-built analytics tools
- **Enhanced Insights**: Deeper analysis of engineering team performance

### 💡 Combined Benefits:
- **No Functionality Gaps**: Complete platform access plus specialized analytics
- **Reduced Maintenance**: Official servers handle complex API management
- **Focused Development**: Custom servers only need to maintain analytics logic
- **Best of Both Worlds**: Platform reliability + custom insights

## Troubleshooting

### VS Code MCP Connection Issues

**"Error spawn python ENOENT"**: VS Code can't find the Python interpreter.
- **Solution**: The `.vscode/mcp.json` uses full virtual environment paths
- **Alternative**: Use shell-based configuration: `cp .vscode/mcp-shell.json .vscode/mcp.json`
- **Test**: Run `python .vscode/test_mcp_connectivity.py` to validate setup
- **Restart**: Restart VS Code after configuration changes

**"Waiting for server to respond to initialize request"**: Server started but not responding.
- **Check Ports**: Kill processes on ports 4001-4003, 4011-4013
- **Kill Command**: `lsof -ti:4001,4002,4003,4011,4012,4013 | xargs kill -9`
- **Verify Setup**: Run `./stop_all_servers.sh && ./stop_analytics_servers.sh` before starting
- **Check Logs**: Look at VS Code Output panel → MCP server logs

### Official Servers
- **GitHub**: Follow [official GitHub MCP setup guide](https://github.com/github/github-mcp-server)
- **Atlassian**: Follow [official Atlassian MCP setup guide](https://github.com/atlassian/atlassian-mcp-server)

### Analytics Servers
- **Rate Limits**: Official servers handle API rate limiting automatically
- **Authentication**: Verify environment variables are set correctly in `.env`
- **Logs**: Check server logs for detailed error information with error types
- **Testing**: Use provided test scripts: `test_startup.py`, `test_comprehensive.py`

### Common Issues
- **Port Conflicts**: Main servers use 4001-4003, analytics use 4011-4013
- **Environment Variables**: Ensure all required variables are set in `.env`
- **Virtual Environment**: Always activate venv before running analytics servers
- **Python Path**: VS Code MCP configuration uses `${workspaceFolder}/venv/bin/python`

## Migration Guide

If upgrading from the previous standalone implementation:

1. **Install Official Servers**: Follow setup guides for GitHub and Atlassian servers
2. **Update Configuration**: Use the new hybrid MCP configuration
3. **Test Functionality**: Verify both official and analytics servers work together
4. **Remove Old Scripts**: The old `start_all_servers.sh` is replaced by the new hybrid approach

## Project Structure

```
engg-stats-mcp/
├── .vscode/                    # VS Code workspace configuration
│   ├── mcp.json               # MCP server configuration
│   ├── mcp-shell.json         # Alternative shell-based config
│   ├── tasks.json             # Task definitions for server management
│   ├── launch.json            # Debug configurations
│   ├── settings.json          # Python workspace settings
│   ├── start_*_mcp.sh         # Individual server startup scripts
│   └── test_mcp_connectivity.py # MCP setup validation
├── mcp_github/                 # GitHub MCP servers
│   ├── server.py              # Main GitHub MCP server (FastMCP)
│   └── analytics_server.py    # GitHub analytics server (FastMCP)
├── mcp_jira/                   # Jira MCP servers
│   ├── server.py              # Main Jira MCP server (FastMCP)
│   └── analytics_server.py    # Jira analytics server (FastMCP)
├── mcp_confluence/             # Confluence MCP servers
│   ├── server.py              # Main Confluence MCP server (FastMCP)
│   └── analytics_server.py    # Confluence analytics server (FastMCP)
├── shared/                     # Shared utilities
│   ├── errors.py              # Comprehensive error handling
│   ├── github_client.py       # GitHub API client with retry logic
│   ├── jira_client.py         # Jira API client with error handling
│   ├── confluence_client.py   # Confluence API client
│   └── date_utils.py          # Date/time utilities
├── test_startup.py             # Server startup validation
├── test_comprehensive.py       # Full functionality tests
├── test_vscode_config.py       # VS Code configuration tests
├── start_*.sh                  # Server startup scripts
├── stop_*.sh                   # Server shutdown scripts
├── engineering-stats-mcp.code-workspace  # VS Code workspace file
└── README.md                   # This file
```

## Testing

Run the included test suites to validate your setup:

```bash
# Test server startup
python test_startup.py

# Test comprehensive functionality
python test_comprehensive.py

# Test VS Code configuration
python test_vscode_config.py

# Test MCP connectivity
python .vscode/test_mcp_connectivity.py
```

## Contributing

1. Fork the repository
2. Focus contributions on engineering analytics functionality
3. Official server issues should be reported to respective official repositories
4. Add tests for new analytics features
5. Update documentation as needed
6. Submit pull requests

## License

MIT License - see LICENSE file for details.

## Engineering Analytics Tools

The custom analytics servers provide specialized tools that complement the official MCP servers:

### GitHub Engineering Analytics

#### Tool: `github_engineer_activity`

Calculates comprehensive engineering productivity metrics for a GitHub user.

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
  "repositories_analyzed": ["owner/repo1", "owner/repo2"],
  "metrics": {
    "pull_requests": {
      "authored": 12,
      "merged": 10,
      "merge_rate": 0.83
    },
    "cycle_times": {
      "average_hours": 48.5,
      "average_days": 2.0,
      "total_merged": 10
    },
    "code_review": {
      "reviews_given": 8,
      "comments_written": 23,
      "review_participation": 0.7
    }
  }
}
```

### Jira Engineering Analytics

#### Tool: `jira_engineer_activity`

Analyzes Jira issue activity and productivity metrics for a user.

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
  "jql_filter": "project = PROJ AND labels = backend",
  "metrics": {
    "issues": {
      "assigned": 15,
      "resolved": 12,
      "resolution_rate": 0.8,
      "reopened": 2,
      "quality_score": 0.83
    },
    "lead_times": {
      "average_hours": 72.3,
      "average_days": 3.0,
      "resolved_count": 12
    },
    "issue_distribution": {
      "types": {"Story": 8, "Bug": 4, "Task": 3},
      "priorities": {"High": 5, "Medium": 8, "Low": 2}
    }
  }
}
```

### Confluence Engineering Analytics

#### Tool: `confluence_engineer_activity`

Analyzes Confluence content activity and documentation productivity.

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
  "space_filter": "TECH",
  "period_days": 14,
  "metrics": {
    "content": {
      "pages_created": 3,
      "pages_updated": 7,
      "total_content_activity": 10,
      "creation_rate": 1.5,
      "update_rate": 3.5
    },
    "engagement": {
      "comments_written": 12,
      "comment_rate": 6.0,
      "engagement_ratio": 1.2
    },
    "distribution": {
      "spaces_active": 2,
      "spaces_breakdown": {"TECH": {"created": 2, "updated": 5}, "DOC": {"created": 1, "updated": 2}},
      "content_types": {"page": 3, "blog": 0}
    }
  }
}
```

## IDE Integration Examples

Once configured with the hybrid setup, you can use natural language prompts that leverage both official servers and analytics:

### Basic Operations (Official Servers)
- *"Show me the open issues in the backend project"* (Atlassian official)
- *"Create a new issue for the login bug"* (Atlassian official)  
- *"List recent commits in the main branch"* (GitHub official)
- *"Show workflow runs for the CI pipeline"* (GitHub official)

### Engineering Analytics (Custom Servers)
- *"Analyze GitHub activity for alice from 2025-11-01 to 2025-11-15"*
- *"Compare Jira productivity for alice and bob this month"*
- *"Show Confluence documentation metrics for the team this quarter"*

### Combined Workflows (Both Server Types)
- *"Get the backend project issues (official), then analyze alice's resolution metrics (analytics)"*
- *"Show recent PRs (official) and calculate team review participation (analytics)"*
- *"Create a sprint report combining Jira issue data (official) and team productivity metrics (analytics)"*

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

**Note**: For the official Atlassian MCP server, OAuth 2.0 authentication is handled automatically through the browser flow.

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


## Contributing

1. Fork the repository
2. Create feature branches for new tools or improvements
3. Add tests for new functionality
4. Update documentation as needed
5. Submit pull requests

## License

MIT License - see LICENSE file for details.