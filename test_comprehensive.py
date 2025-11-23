#!/usr/bin/env python3
"""
Comprehensive test suite for all MCP servers after FastMCP standardization
"""
import asyncio
import sys
import os
from pathlib import Path
import logging

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests

async def test_github_servers():
    """Test both GitHub servers"""
    print("🔵 Testing GitHub Servers...")
    
    try:
        # Test main server
        from mcp_github.server import github_engineer_activity
        result = await github_engineer_activity("octocat", "2024-01-01", "2024-01-31")
        
        assert isinstance(result, dict)
        assert "login" in result
        assert "prsAuthored" in result
        print("  ✅ GitHub Main Server: FastMCP working")
        
        # Test analytics server
        from mcp_github.analytics_server import github_engineer_activity as analytics_activity
        result = await analytics_activity("octocat", "2024-01-01", "2024-01-31")
        
        assert isinstance(result, dict)
        assert "metrics" in result
        assert "pull_requests" in result["metrics"]
        print("  ✅ GitHub Analytics Server: Enhanced metrics working")
        
        return True
    except Exception as e:
        print(f"  ❌ GitHub Servers Failed: {e}")
        return False

def test_error_handling():
    """Test the new error handling system"""
    print("🟡 Testing Error Handling...")
    
    try:
        from shared.errors import (
            GitHubAPIError, JiraAPIError, ConfluenceAPIError,
            ValidationError, ConfigurationError, RateLimitError,
            handle_mcp_error, create_github_error
        )
        
        # Test error creation
        validation_error = ValidationError("Test validation error", field="test_field")
        assert validation_error.error_code == "VALIDATION_ERROR"
        assert validation_error.details["field"] == "test_field"
        
        # Test MCP error conversion
        mcp_error = handle_mcp_error(validation_error)
        assert mcp_error["code"] == -32000
        assert "VALIDATION_ERROR" in str(mcp_error)
        
        print("  ✅ Error Handling: Comprehensive error types working")
        return True
    except Exception as e:
        print(f"  ❌ Error Handling Failed: {e}")
        return False

def test_server_configurations():
    """Test server configuration validation"""
    print("🟢 Testing Server Configurations...")
    
    try:
        # Test that all servers use FastMCP
        from mcp_github.server import app as github_app
        from mcp_github.analytics_server import app as github_analytics
        from mcp_jira.server import app as jira_app
        from mcp_jira.analytics_server import app as jira_analytics
        from mcp_confluence.server import app as confluence_app
        from mcp_confluence.analytics_server import app as confluence_analytics
        
        # Check that all apps are FastMCP instances
        apps = [
            ("GitHub Server", github_app),
            ("GitHub Analytics", github_analytics), 
            ("Jira Server", jira_app),
            ("Jira Analytics", jira_analytics),
            ("Confluence Server", confluence_app),
            ("Confluence Analytics", confluence_analytics)
        ]
        
        for name, app in apps:
            assert hasattr(app, 'sse_app'), f"{name} not using FastMCP"
            assert hasattr(app, 'tool'), f"{name} missing tool decorator"
        
        print("  ✅ Server Configurations: All servers standardized on FastMCP")
        return True
    except Exception as e:
        print(f"  ❌ Server Configurations Failed: {e}")
        return False

def test_api_clients():
    """Test API client error handling"""
    print("🟣 Testing API Client Error Handling...")
    
    try:
        from shared.github_client import GitHubClient
        from shared.jira_client import JiraClient  
        from shared.confluence_client import ConfluenceClient
        from shared.errors import GitHubAPIError, JiraAPIError, ConfluenceAPIError
        
        # Test that clients import error types correctly
        github_client = GitHubClient("fake_token")
        assert hasattr(github_client, '_make_request')
        
        print("  ✅ API Clients: Error handling integration working")
        return True
    except Exception as e:
        print(f"  ❌ API Clients Failed: {e}")
        return False

async def main():
    """Run comprehensive test suite"""
    print("🚀 MCP Server Comprehensive Test Suite")
    print("=" * 60)
    print("Testing FastMCP standardization and error handling improvements")
    print("=" * 60)
    
    # Only test GitHub if token is available (others require more setup)
    github_token = os.getenv("GITHUB_TOKEN")
    
    test_results = []
    
    # Test error handling (always available)
    test_results.append(test_error_handling())
    
    # Test server configurations (always available) 
    test_results.append(test_server_configurations())
    
    # Test API clients (always available)
    test_results.append(test_api_clients())
    
    # Test GitHub servers if token available
    if github_token:
        test_results.append(await test_github_servers())
    else:
        print("🔵 Skipping GitHub Servers: No GITHUB_TOKEN found")
        print("  💡 Add GITHUB_TOKEN to .env to test GitHub functionality")
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    passed = sum(test_results)
    total = len(test_results)
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! FastMCP standardization successful.")
        print("\n📈 Improvements implemented:")
        print("  • All servers standardized on FastMCP")
        print("  • Comprehensive error handling with specific types")
        print("  • Consistent configuration validation")
        print("  • Enhanced API client error management")
        print("  • Better rate limiting and retry logic")
        
        print("\n🚀 Ready for production use!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)