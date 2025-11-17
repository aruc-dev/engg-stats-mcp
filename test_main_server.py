#!/usr/bin/env python3
"""Test script to validate the main GitHub MCP server"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

async def test_server():
    """Test the main GitHub server functionality"""
    print("Testing main GitHub MCP server...")
    
    # Check if we have a token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment")
        print("💡 Create a .env file with your GitHub token to test")
        return False
    
    try:
        # Import and test the server
        from mcp_github.server import GitHubMCPServer
        
        # Create server instance
        server = GitHubMCPServer()
        print("✅ Server initialized successfully")
        
        # Test with a simple request
        print("🔍 Testing with octocat user...")
        result = await server.github_engineer_activity(
            login="octocat",
            from_date="2024-01-01",
            to_date="2024-12-31"
        )
        
        print("✅ Test request completed successfully")
        print(f"📊 Result structure: {list(result.keys())}")
        
        # Check if structured content exists
        if "structuredContent" in result:
            data = result["structuredContent"]
            print(f"👤 User: {data.get('login')}")
            print(f"📅 Period: {data.get('from')} to {data.get('to')}")
            print(f"📝 PRs authored: {data.get('prsAuthored')}")
            print(f"✅ PRs merged: {data.get('prsMerged')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    if success:
        print("\n🎉 Main server.py is working correctly!")
    else:
        print("\n💥 Server test failed")
        sys.exit(1)