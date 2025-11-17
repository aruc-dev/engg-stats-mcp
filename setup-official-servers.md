# Setting Up Official MCP Servers

This guide explains how to integrate the official GitHub and Atlassian MCP servers alongside your custom engineering analytics servers.

## Official GitHub MCP Server Setup

### Option 1: Remote Server (Recommended)
Add to your VS Code MCP configuration (`vscode-mcp-config.json`):

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
      "github-engineering-activity": {
        "command": "python",
        "args": ["/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp/mcp_github/server.py"],
        "cwd": "/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp",
        "env": {
          "PATH": "/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin",
          "GITHUB_MCP_PORT": "4006"
        }
      }
    },
    "inputs": [
      {
        "type": "promptString",
        "id": "github_mcp_pat",
        "description": "GitHub Personal Access Token",
        "password": true
      }
    ]
  }
}
```

### Option 2: Local Docker Server
Add to your VS Code MCP configuration:

```json
{
  "mcp": {
    "servers": {
      "github-official": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "-e",
          "GITHUB_PERSONAL_ACCESS_TOKEN",
          "ghcr.io/github/github-mcp-server"
        ],
        "env": {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
        }
      },
      "github-engineering-activity": {
        "command": "python",
        "args": ["/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp/mcp_github/server.py"],
        "cwd": "/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp",
        "env": {
          "PATH": "/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin",
          "GITHUB_MCP_PORT": "4006"
        }
      }
    },
    "inputs": [
      {
        "type": "promptString",
        "id": "github_token",
        "description": "GitHub Personal Access Token",
        "password": true
      }
    ]
  }
}
```

## Official Atlassian MCP Server Setup

Add to your VS Code MCP configuration:

```json
{
  "mcp": {
    "servers": {
      "atlassian-official": {
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
      },
      "jira-engineering-activity": {
        "command": "python",
        "args": ["/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp/mcp_jira/server.py"],
        "cwd": "/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp",
        "env": {
          "PATH": "/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin"
        }
      },
      "confluence-engineering-activity": {
        "command": "python",
        "args": ["/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp/mcp_confluence/server.py"],
        "cwd": "/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp",
        "env": {
          "PATH": "/Users/arunbabuchandrababu/Documents/code/engg-stats-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin"
        }
      }
    }
  }
}
```

## Authentication Setup

### GitHub PAT Setup
You'll need a GitHub Personal Access Token with the following scopes:
- `repo` (for repository access)
- `read:user` (for user information)
- `read:org` (for organization access)

### Atlassian OAuth Setup
The official Atlassian server uses OAuth 2.0:
1. Run the `npx mcp-remote` command
2. A browser window will open for authentication
3. Log in with your Atlassian credentials
4. Approve the required permissions

## Benefits of This Hybrid Approach

### Official Servers Handle:
- **GitHub**: Repository management, issues, PRs, workflows, code security
- **Atlassian**: Secure OAuth access, real-time data, comprehensive CRUD operations

### Custom Servers Provide:
- **Engineering Analytics**: Specialized metrics and calculations
- **Custom Business Logic**: Tailored to your specific needs
- **Focused Functionality**: Lightweight, purpose-built tools

## Next Steps

1. Update your existing VS Code MCP configuration
2. Test the official servers work correctly
3. Refactor custom servers to remove overlapping functionality
4. Update documentation and scripts

This hybrid approach gives you the best of both worlds: robust, maintained official APIs plus your specialized engineering analytics.