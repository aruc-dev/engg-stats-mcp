# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Engineering Statistics MCP Servers
- GitHub MCP server for engineering activity analytics
- Jira MCP server for issue tracking analytics
- Confluence MCP server for documentation analytics
- FastMCP server implementation using official MCP SDK
- Comprehensive GitHub integration with PR cycle time analysis
- Review activity tracking and metrics
- Comment analysis across repositories
- Rate limiting and error handling for all API clients
- VS Code integration support
- Windsurf IDE compatibility
- Complete documentation and setup guides

### Features

#### GitHub Analytics
- PR authoring and merge tracking
- Cycle time calculation (creation to merge)
- Review activity analysis
- Comment tracking across pull requests
- Repository filtering support
- Date range queries

#### Jira Analytics (Planned)
- Issue assignment tracking
- Resolution time analysis
- Reopened issue metrics
- Lead time calculations
- Custom JQL query support

#### Confluence Analytics (Planned)
- Page creation tracking
- Update activity monitoring
- Comment analysis
- Space-based filtering

#### Technical Features
- Model Context Protocol (MCP) compliance
- HTTP transport with SSE support
- Pydantic data validation
- Comprehensive error handling
- Rate limiting respect
- Async/await support
- Type hints throughout
- Structured logging

### Documentation
- Complete README with setup instructions
- API documentation for all tools
- VS Code integration guide
- Troubleshooting section
- Contributing guidelines
- Security best practices

## [0.1.0] - 2025-11-16

### Added
- Initial project structure
- Basic MCP server framework
- GitHub API integration
- Core analytics functionality