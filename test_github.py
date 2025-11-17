#!/usr/bin/env python3
"""
Test script for GitHub MCP Server
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_github.server_simple import GitHubMCPServer


async def test_github_server():
    """Test the GitHub MCP server functionality"""
    print("🧪 Testing GitHub MCP Server")
    print("=" * 40)
    
    try:
        # Initialize the server
        print("📡 Initializing GitHub MCP server...")
        server = GitHubMCPServer()
        print("✅ Server initialized successfully")
        
        # Test with a simple GitHub user - using 'octocat' which is GitHub's mascot
        print("\n🔍 Testing with GitHub user 'octocat'...")
        result = await server.github_engineer_activity(
            login="octocat",
            from_date="2024-01-01",
            to_date="2024-12-31"
        )
        
        print("✅ GitHub API call successful!")
        print("\n📊 Results:")
        print(f"  User: {result['structuredContent']['login']}")
        print(f"  Date range: {result['structuredContent']['from']} to {result['structuredContent']['to']}")
        print(f"  PRs authored: {result['structuredContent']['prsAuthored']}")
        print(f"  PRs merged: {result['structuredContent']['prsMerged']}")
        print(f"  Reviews given: {result['structuredContent']['reviewsGiven']}")
        print(f"  Comments written: {result['structuredContent']['commentsWritten']}")
        
        if result['structuredContent']['avgPrCycleHours'] is not None:
            print(f"  Avg PR cycle time: {result['structuredContent']['avgPrCycleHours']:.1f} hours")
        else:
            print("  Avg PR cycle time: No merged PRs in period")
        
        print("\n🎉 GitHub MCP server test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_connectivity():
    """Test basic API connectivity"""
    print("\n🌐 Testing GitHub API connectivity...")
    
    try:
        from shared.github_client import GitHubClient
        from dotenv import load_dotenv
        
        load_dotenv()
        token = os.getenv("GITHUB_TOKEN")
        
        if not token:
            print("❌ GITHUB_TOKEN not found in environment")
            return False
        
        client = GitHubClient(token)
        
        # Simple API test - search for a single PR
        print("🔍 Making test API call to GitHub...")
        prs = await client.search_prs_by_author("octocat", "2024-01-01", "2024-01-31")
        print(f"✅ API call successful! Found {len(prs)} PRs for octocat in January 2024")
        
        return True
        
    except Exception as e:
        print(f"❌ API connectivity test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 GitHub MCP Server Test Suite")
    print("=" * 50)
    
    # Test API connectivity first
    api_ok = await test_api_connectivity()
    
    if not api_ok:
        print("\n❌ API connectivity test failed. Please check your GITHUB_TOKEN.")
        return
    
    # Test the full server functionality
    server_ok = await test_github_server()
    
    print("\n" + "=" * 50)
    if server_ok:
        print("🎯 All tests passed! Your GitHub MCP server is working correctly.")
        print("\n📝 Next steps:")
        print("   1. Start the server: python mcp_github/server_simple.py")
        print("   2. Test with curl: curl http://localhost:4001/health")
        print("   3. Use the MCP endpoint: http://localhost:4001/mcp")
    else:
        print("❌ Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())