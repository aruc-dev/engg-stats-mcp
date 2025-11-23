# VS Code Configuration for Engineering Stats MCP

This folder contains VS Code workspace configuration files to enable seamless development and integration with all MCP servers.

## 🚀 Quick Start

1. **Open this folder in VS Code**
2. **Install recommended extensions** when prompted
3. **Configure environment** by copying `.env.example` to `.env`
4. **Run setup**: Press `Ctrl+Shift+P` → "Tasks: Run Task" → "Install Dependencies"

## 📋 Configuration Files

### `mcp.json`
Configures all 6 MCP servers for VS Code integration:
- **Main Servers** (ports 4001-4003): GitHub, Jira, Confluence
- **Analytics Servers** (ports 4011-4013): Specialized productivity metrics

### `settings.json`
Workspace settings for Python development:
- Virtual environment detection
- Code formatting with Black
- Import organization
- Linting with Pylint

### `tasks.json`
Pre-configured tasks accessible via `Ctrl+Shift+P` → "Tasks: Run Task":
- **Start All Main Servers** - Launch GitHub, Jira, Confluence servers
- **Start Analytics Servers** - Launch analytics-focused servers
- **Stop All Servers** - Clean shutdown of main servers
- **Stop Analytics Servers** - Clean shutdown of analytics servers  
- **Test All Servers** - Validate all server functionality
- **Install Dependencies** - Run setup script
- **Validate Setup** - Check environment configuration

### `launch.json`
Debug configurations accessible via `F5` or Debug panel:
- Debug individual MCP servers
- Debug analytics servers
- Run test suites with debugging

### `extensions.json`
Recommended VS Code extensions for optimal development:
- Python development tools (Python, debugpy, Black, Pylint)
- GitHub Copilot integration
- JSON/YAML support
- Testing tools

## 🔧 Usage

### Starting Servers
```bash
# Via VS Code Tasks (Ctrl+Shift+P → Tasks: Run Task)
"Start All Main Servers"     # Ports 4001-4003
"Start Analytics Servers"    # Ports 4011-4013

# Via Terminal
./start_all_servers.sh       # Main servers
./start_analytics_servers.sh # Analytics servers
```

### Debugging
1. Set breakpoints in server code
2. Press `F5` or go to Debug panel
3. Select server configuration:
   - "Debug GitHub MCP Server"
   - "Debug Jira MCP Server" 
   - "Debug Confluence MCP Server"
   - "Debug [Platform] Analytics Server"

### Testing
```bash
# Via VS Code Tasks
"Test All Servers"      # Validate all functionality
"Validate Setup"        # Check environment

# Via Debug
"Run Tests"            # Debug test execution
```

## 🌐 MCP Server Endpoints

| Server | Port | Purpose | VS Code Config |
|--------|------|---------|----------------|
| GitHub MCP | 4001 | Main GitHub integration | `github-engineering` |
| Jira MCP | 4002 | Main Jira integration | `jira-engineering` |
| Confluence MCP | 4003 | Main Confluence integration | `confluence-engineering` |
| GitHub Analytics | 4011 | GitHub productivity metrics | `github-analytics` |
| Jira Analytics | 4012 | Jira productivity metrics | `jira-analytics` |
| Confluence Analytics | 4013 | Confluence productivity metrics | `confluence-analytics` |

## 🔑 Environment Setup

Ensure your `.env` file contains all required variables:

```bash
# GitHub
GITHUB_TOKEN=your_github_token

# Jira  
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your_email@company.com
JIRA_API_TOKEN=your_jira_token

# Confluence
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE_EMAIL=your_email@company.com  
CONFLUENCE_API_TOKEN=your_confluence_token
```

## 📊 Health Checks

All servers expose health check endpoints:
- Main servers: `http://localhost:400[1-3]/health`
- Analytics servers: `http://localhost:401[1-3]/health`

## 🛠️ Troubleshooting

### Common Issues

**"Error spawn python ENOENT" in VS Code MCP**
This error means VS Code can't find the Python interpreter. Solutions:

1. **Use the updated `mcp.json`** - The configuration now uses full Python paths
2. **Alternative: Use shell scripts** - Copy `mcp-shell.json` to `mcp.json` for shell-based startup
3. **Verify virtual environment**:
   ```bash
   ls -la venv/bin/python*
   ./venv/bin/python --version
   ```

**Virtual Environment Not Found**
```bash
# Run install script
./install.sh
# Or manually create
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Port Conflicts**
```bash
# Check what's using ports
lsof -ti:4001,4002,4003,4011,4012,4013

# Stop all servers
./stop_all_servers.sh
./stop_analytics_servers.sh
```

**Environment Variables Missing**
```bash
# Validate setup
python validate_setup.py

# Check environment file
ls -la .env
```

### Debug Logs
- Server logs appear in VS Code integrated terminal
- Enable debug mode by setting `DEBUG=true` in `.env`
- Use VS Code debugger to step through server code

## 🎯 Integration with GitHub Copilot

With the MCP servers running, GitHub Copilot can:
- Analyze engineering productivity metrics
- Query GitHub/Jira/Confluence data  
- Generate reports on team performance
- Suggest process improvements based on data

The analytics servers provide specialized tools that complement the main MCP functionality.