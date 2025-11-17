"""Confluence Engineering Analytics MCP Server - Focused on Metrics Only"""
import json
import logging
import os
import sys
from typing import Any, List, Optional, Dict
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# MCP SDK imports
from mcp.server import FastMCP

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from shared.confluence_client import ConfluenceClient, ConfluenceAPIError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ConfluenceEngineerActivityInput(BaseModel):
    """Input schema for Confluence engineer activity analytics"""
    user_email_or_account_id: str = Field(description="User email or Confluence account ID")
    from_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    to_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    space_key: Optional[str] = Field(default=None, description="Optional Confluence space key filter")


# Create FastMCP server focused on engineering analytics
app = FastMCP("Confluence Engineering Analytics")

# Initialize Confluence client
confluence_base_url = os.getenv("CONFLUENCE_BASE_URL")
confluence_email = os.getenv("CONFLUENCE_EMAIL")
confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")

# Validate required environment variables
required_vars = ["CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

confluence_client = ConfluenceClient(confluence_base_url, confluence_email, confluence_api_token)
logger.info("Confluence Engineering Analytics MCP Server initialized")


@app.tool("confluence_engineer_activity")
async def confluence_engineer_activity(
    user_email_or_account_id: str,
    from_date: str,
    to_date: str,
    space_key: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate comprehensive engineering activity metrics for a Confluence user.
    
    This tool provides specialized analytics not available in the official Atlassian MCP server:
    - Content creation and update tracking
    - Comment activity analysis
    - Space-filtered metrics
    - Documentation productivity insights
    
    Use the official Atlassian MCP server for basic page CRUD operations, space management,
    and content searches. Use this tool for engineering documentation productivity insights.
    
    Args:
        user_email_or_account_id: User email or Confluence account ID
        from_date: ISO date string "YYYY-MM-DD"
        to_date: ISO date string "YYYY-MM-DD"
        space_key: Optional Confluence space key filter
    
    Returns:
        Dictionary with comprehensive Confluence activity metrics
    """
    try:
        # Validate inputs
        input_data = ConfluenceEngineerActivityInput(
            user_email_or_account_id=user_email_or_account_id,
            from_date=from_date,
            to_date=to_date,
            space_key=space_key
        )
        
        logger.info(f"Calculating Confluence engineering metrics for {user_email_or_account_id} from {from_date} to {to_date}")
        
        # Get pages created by user
        created_pages = await confluence_client.search_content_by_creator(
            user_email_or_account_id, from_date, to_date, space_key, "page"
        )
        pages_created = len(created_pages)
        
        # Get pages updated by user (excluding those they created)
        updated_pages = await confluence_client.search_updated_content_by_user(
            user_email_or_account_id, from_date, to_date, space_key
        )
        
        # Filter out pages that were created by the same user (to avoid double counting)
        created_page_ids = {page.get("id") for page in created_pages}
        updated_only_pages = [
            page for page in updated_pages 
            if page.get("id") not in created_page_ids
        ]
        pages_updated = len(updated_only_pages)
        
        # Get comments written by user
        comments = await confluence_client.search_comments_by_user(
            user_email_or_account_id, from_date, to_date, space_key
        )
        comments_written = len(comments)
        
        # Analyze content types and spaces
        spaces_activity = {}
        content_types = {"page": pages_created, "blog": 0}  # Default tracking
        
        # Track space distribution
        for page in created_pages + updated_only_pages:
            space_name = page.get('space', {}).get('name', 'Unknown')
            if space_name not in spaces_activity:
                spaces_activity[space_name] = {"created": 0, "updated": 0}
            
            if page.get("id") in created_page_ids:
                spaces_activity[space_name]["created"] += 1
            else:
                spaces_activity[space_name]["updated"] += 1
        
        # Calculate content velocity (pages per week)
        from datetime import datetime, timedelta
        start_date = datetime.fromisoformat(from_date)
        end_date = datetime.fromisoformat(to_date)
        days_period = (end_date - start_date).days
        
        # Ensure weeks_period is always > 0 to prevent division by zero
        # For same-day queries or very short periods, default to 1 week
        weeks_period = max(days_period / 7, 1) if days_period >= 0 else 1
        
        # Build comprehensive metrics result
        result = {
            "user": user_email_or_account_id,
            "from": from_date,
            "to": to_date,
            "space_filter": space_key,
            "period_days": days_period,
            "metrics": {
                "content": {
                    "pages_created": pages_created,
                    "pages_updated": pages_updated,
                    "total_content_activity": pages_created + pages_updated,
                    "creation_rate": round(pages_created / weeks_period, 1),
                    "update_rate": round(pages_updated / weeks_period, 1)
                },
                "engagement": {
                    "comments_written": comments_written,
                    "comment_rate": round(comments_written / weeks_period, 1),
                    "engagement_ratio": round(comments_written / (pages_created + pages_updated), 1) if (pages_created + pages_updated) > 0 else 0
                },
                "distribution": {
                    "spaces_active": len(spaces_activity),
                    "spaces_breakdown": spaces_activity,
                    "content_types": content_types
                }
            }
        }
        
        logger.info(f"Confluence engineering analytics complete for {user_email_or_account_id}")
        
        return result
        
    except ConfluenceAPIError as e:
        error_msg = f"Confluence API error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to calculate Confluence engineering metrics: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def main():
    """Main entry point for Confluence Engineering Analytics MCP Server"""
    # Validate environment variables
    required_vars = ["CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: The following environment variables are required: {', '.join(missing_vars)}")
        sys.exit(1)
    
    port = int(os.getenv("CONFLUENCE_MCP_PORT", 4003))
    
    logger.info(f"Starting Confluence Engineering Analytics MCP server on port {port}")
    logger.info("This server provides engineering documentation productivity metrics")
    logger.info("Use alongside the official Atlassian MCP server for complete functionality")
    
    # Use SSE transport for compatibility
    import uvicorn
    sse_app = app.sse_app
    uvicorn.run(sse_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()