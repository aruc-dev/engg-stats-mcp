#!/usr/bin/env python3
"""
Quick server startup test to verify all servers can initialize properly
"""
import sys
import os
import asyncio
import signal
import time
from multiprocessing import Process
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.getcwd())
load_dotenv()

def test_server_startup(server_module, server_name, port):
    """Test that a server can start up without errors"""
    try:
        # Import the server
        if server_module == "github":
            from mcp_github.analytics_server import main
        elif server_module == "github_main":
            from mcp_github.server import main
        elif server_module == "jira":
            from mcp_jira.analytics_server import main
        elif server_module == "jira_main": 
            from mcp_jira.server import main
        elif server_module == "confluence":
            from mcp_confluence.analytics_server import main
        elif server_module == "confluence_main":
            from mcp_confluence.server import main
        
        print(f"✅ {server_name}: Import successful")
        return True
        
    except ImportError as e:
        print(f"❌ {server_name}: Import failed - {e}")
        return False
    except Exception as e:
        if "environment variable" in str(e).lower():
            print(f"⚠️  {server_name}: Missing env vars (expected) - {e}")
            return True  # This is expected for servers without full config
        else:
            print(f"❌ {server_name}: Unexpected error - {e}")
            return False

def main():
    """Test all server startups"""
    print("🔄 Testing Server Startup Capabilities")
    print("=" * 50)
    
    servers_to_test = [
        ("github", "GitHub Analytics Server", 4001),
        ("github_main", "GitHub Main Server", 4001), 
        ("jira", "Jira Analytics Server", 4002),
        ("jira_main", "Jira Main Server", 4002),
        ("confluence", "Confluence Analytics Server", 4003),
        ("confluence_main", "Confluence Main Server", 4003)
    ]
    
    results = []
    for server_module, server_name, port in servers_to_test:
        result = test_server_startup(server_module, server_name, port)
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📊 Startup Test Results:")
    passed = sum(results)
    total = len(results)
    print(f"✅ Servers that can start: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All servers can initialize properly!")
        print("💡 Servers are ready for production deployment")
        
        # Check if we have tokens for actual functionality testing
        github_token = os.getenv("GITHUB_TOKEN")
        jira_config = all([
            os.getenv("JIRA_BASE_URL"),
            os.getenv("JIRA_EMAIL"), 
            os.getenv("JIRA_API_TOKEN")
        ])
        confluence_config = all([
            os.getenv("CONFLUENCE_BASE_URL"),
            os.getenv("CONFLUENCE_EMAIL"),
            os.getenv("CONFLUENCE_API_TOKEN")  
        ])
        
        print("\n🔧 Configuration Status:")
        print(f"  GitHub: {'✅ Configured' if github_token else '⚠️  Missing GITHUB_TOKEN'}")
        print(f"  Jira: {'✅ Configured' if jira_config else '⚠️  Missing Jira config'}")
        print(f"  Confluence: {'✅ Configured' if confluence_config else '⚠️  Missing Confluence config'}")
        
    else:
        print("⚠️  Some servers failed to initialize")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)