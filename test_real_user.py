#!/usr/bin/env python3
"""
Test GitHub MCP Server with real user data
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_github.server_simple import GitHubMCPServer


async def test_real_user():
    """Test with a real active GitHub user"""
    print("🔍 Testing GitHub MCP with aruc-dev for last 4 weeks...")
    
    # Calculate dates for last 4 weeks
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    # Get date from 4 weeks ago
    four_weeks_ago = today - timedelta(weeks=4)
    
    from_date = four_weeks_ago.strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    print(f"📅 Date range: {from_date} to {to_date}")
    
    server = GitHubMCPServer()
    
    try:
        print(f"\n👤 Testing user: aruc-dev")
        result = await server.github_engineer_activity(
            login="aruc-dev",
            from_date=from_date,
            to_date=to_date
        )
        
        data = result['structuredContent']
        print(f"  📊 Activity for last 4 weeks:")
        print(f"     PRs authored: {data['prsAuthored']}")
        print(f"     PRs merged: {data['prsMerged']}")
        print(f"     Reviews given: {data['reviewsGiven']}")
        print(f"     Comments: {data['commentsWritten']}")
        
        if data['avgPrCycleHours']:
            print(f"     Avg cycle time: {data['avgPrCycleHours']:.1f} hours")
            
    except Exception as e:
        print(f"  ❌ Error testing aruc-dev: {e}")
    
    print(f"\n🎯 GitHub MCP server test completed!")


if __name__ == "__main__":
    asyncio.run(test_real_user())