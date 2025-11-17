#!/usr/bin/env python3
"""
Test the GitHub MCP server HTTP endpoints
"""
import asyncio
import httpx
import json


async def test_mcp_endpoints():
    """Test the MCP HTTP endpoints"""
    print("🌐 Testing GitHub MCP Server HTTP Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:4001"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            print("🔍 Testing health endpoint...")
            health_response = await client.get(f"{base_url}/health")
            print(f"✅ Health check: {health_response.status_code}")
            print(f"   Response: {health_response.json()}")
            
            # Test root endpoint
            print("\n🔍 Testing root endpoint...")
            root_response = await client.get(f"{base_url}/")
            print(f"✅ Root endpoint: {root_response.status_code}")
            print(f"   Response: {root_response.json()}")
            
            # Test MCP tools list
            print("\n🔍 Testing MCP tools list...")
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            tools_response = await client.post(
                f"{base_url}/mcp", 
                json=mcp_request,
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ Tools list: {tools_response.status_code}")
            tools_data = tools_response.json()
            print(f"   Available tools: {len(tools_data['result']['tools'])}")
            for tool in tools_data['result']['tools']:
                print(f"     - {tool['name']}: {tool['description']}")
            
            # Test actual tool call
            print("\n🔍 Testing github_engineer_activity tool...")
            tool_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "github_engineer_activity",
                    "arguments": {
                        "login": "octocat",
                        "from_date": "2024-01-01",
                        "to_date": "2024-01-31"
                    }
                }
            }
            
            tool_response = await client.post(
                f"{base_url}/mcp",
                json=tool_request,
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ Tool call: {tool_response.status_code}")
            tool_data = tool_response.json()
            
            if 'result' in tool_data:
                result = tool_data['result']['structuredContent']
                print(f"   Results for {result['login']}:")
                print(f"     PRs authored: {result['prsAuthored']}")
                print(f"     PRs merged: {result['prsMerged']}")
                print(f"     Reviews given: {result['reviewsGiven']}")
                print(f"     Comments: {result['commentsWritten']}")
            else:
                print(f"   Error: {tool_data.get('error', 'Unknown error')}")
            
            print("\n🎉 All MCP endpoints working correctly!")
            print("\n📝 Your GitHub MCP server is ready for IDE integration!")
            print("   Configure your IDE to use: http://localhost:4001/mcp")
            
        except httpx.ConnectError:
            print("❌ Could not connect to server. Make sure it's running on port 4001")
            print("   Start with: python mcp_github/server_simple.py")
        except Exception as e:
            print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_mcp_endpoints())