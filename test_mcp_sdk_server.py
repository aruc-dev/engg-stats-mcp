#!/usr/bin/env python3
"""Test script for the MCP SDK GitHub server"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

async def test_mcp_sdk_server():
    """Test the MCP SDK server functionality"""
    print("🧪 Testing MCP SDK GitHub server...")
    
    # Check if we have a token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment")
        print("💡 Create a .env file with your GitHub token to test")
        return False
    
    try:
        # Import and test the server
        from mcp_github.server import app, github_engineer_activity
        
        print("✅ MCP SDK server imports successful")
        print(f"📡 Server type: {type(app)}")
        
        # Test the tool function directly
        print("🔍 Testing tool function directly...")
        result = await github_engineer_activity(
            login="octocat",
            from_date="2024-01-01",
            to_date="2024-12-31"
        )
        
        print("✅ Tool function test completed")
        print(f"📊 Result keys: {list(result.keys())}")
        
        if "login" in result:
            print(f"👤 User: {result.get('login')}")
            print(f"📝 PRs authored: {result.get('prsAuthored', 0)}")
            print(f"✅ PRs merged: {result.get('prsMerged', 0)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_sdk_server())
    if success:
        print("\n🎉 MCP SDK server is working correctly!")
        print("🚀 You can now use the server with:")
        print("   python mcp_github/server.py")
    else:
        print("\n💥 MCP SDK server test failed")
        sys.exit(1)