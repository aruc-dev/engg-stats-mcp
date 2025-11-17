# Contributing to Engineering Statistics MCP Servers

Thank you for considering contributing to this project! 🎉

## Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API tokens
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Create a feature branch**: `git checkout -b feature/your-feature-name`
5. **Make your changes** and test them
6. **Submit a pull request**

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings for all functions and classes
- Keep functions focused and small

### Testing
- Test your changes with the included test scripts:
  ```bash
  python test_mcp_sdk_server.py
  python test_github.py
  ```
- Add new tests for new functionality
- Ensure all existing tests pass

### Commit Messages
- Use clear, descriptive commit messages
- Format: `type(scope): description`
- Examples:
  - `feat(github): add PR cycle time calculation`
  - `fix(jira): handle missing issue fields`
  - `docs: update API documentation`

## Adding New Features

### New MCP Tools
1. Add the tool function to the appropriate server (e.g., `mcp_github/server.py`)
2. Update the shared client if needed (e.g., `shared/github_client.py`)
3. Add input/output schemas using Pydantic
4. Add comprehensive error handling
5. Update documentation and tests

### New API Integrations
1. Create a new client in `shared/` (e.g., `shared/slack_client.py`)
2. Follow the existing patterns for authentication and pagination
3. Add comprehensive error handling and rate limiting
4. Create corresponding MCP server in `mcp_slack/`

## Pull Request Process

1. **Update documentation** if you're changing behavior
2. **Add tests** for new functionality
3. **Update README.md** if adding new features or changing setup
4. **Ensure CI passes** (when set up)
5. **Request review** from maintainers

## Reporting Issues

### Bug Reports
Include:
- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Error logs (sanitized of tokens)
- API versions if relevant

### Feature Requests
Include:
- Use case description
- Proposed API design
- Examples of usage
- Why existing functionality doesn't work

## Security

- **Never commit API tokens or secrets**
- Use `.env` files for configuration
- Report security issues privately to maintainers
- Follow secure coding practices for API clients

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn and contribute
- Assume good intentions

## Questions?

Feel free to open an issue for questions about:
- How to implement a feature
- Understanding the codebase
- Best practices for MCP servers
- API integration patterns

Thanks for contributing! 🚀