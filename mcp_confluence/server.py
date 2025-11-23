"""Confluence MCP Server for Engineering Activity Analytics - Using FastMCP"""
import json
import logging
import os
import sys
from typing import Any, List, Optional, Dict
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# MCP SDK imports
from mcp.server import FastMCP

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from shared.confluence_client import ConfluenceClient
from shared.date_utils import parse_iso_date
from shared.errors import (
    ConfluenceAPIError, ValidationError, ConfigurationError,
    handle_mcp_error, log_and_raise_error
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ConfluenceEngineerActivityInput(BaseModel):
    """Input schema for Confluence engineer activity tool"""
    user_email_or_account_id: str = Field(description="User email or Confluence account ID")
    from_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    to_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    space_key: Optional[str] = Field(default=None, description="Optional Confluence space key filter")


# Create FastMCP server
app = FastMCP("Confluence Engineering Activity Analytics")

# Initialize Confluence client
confluence_base_url = os.getenv("CONFLUENCE_BASE_URL")
confluence_email = os.getenv("CONFLUENCE_EMAIL")
confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")

# Validate required environment variables
required_vars = ["CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
    logger.error(error_msg)
    raise ConfigurationError(error_msg, missing_config=missing_vars[0])

try:
    confluence_client = ConfluenceClient(confluence_base_url, confluence_email, confluence_api_token)
    logger.info("Confluence MCP Server initialized successfully")
except Exception as e:
    log_and_raise_error(ConfigurationError(f"Failed to initialize Confluence client: {str(e)}"), "Confluence Server Init")


@app.tool("confluence_engineer_activity")
async def confluence_engineer_activity(
    user_email_or_account_id: str,
    from_date: str,
    to_date: str,
    space_key: Optional[str] = None
) -> Dict[str, Any]:
    """Summarize Confluence activity for a single user over a time range.
    
    Args:
        user_email_or_account_id: User email or Confluence account ID
        from_date: ISO date string "YYYY-MM-DD"
        to_date: ISO date string "YYYY-MM-DD"
        space_key: Optional Confluence space key filter
    
    Returns:
        Dictionary with Confluence activity metrics
    """
    try:
        # Validate inputs
        try:
            input_data = ConfluenceEngineerActivityInput(
                user_email_or_account_id=user_email_or_account_id,
                from_date=from_date,
                to_date=to_date,
                space_key=space_key
            )
        except Exception as e:
            raise ValidationError(f"Invalid input parameters: {str(e)}")
        
        logger.info(f"Fetching Confluence activity for {user_email_or_account_id} from {from_date} to {to_date}")
        
        # Get pages created by user
        try:
            created_pages = await confluence_client.search_content_by_creator(
                user_email_or_account_id, from_date, to_date, space_key, "page"
            )
        except ConfluenceAPIError as e:
            log_and_raise_error(e, f"Fetching created pages for {user_email_or_account_id}")
            
        pages_created = len(created_pages)
        
        # Get pages updated by user
        try:
            updated_pages = await confluence_client.search_updated_content_by_user(
                user_email_or_account_id, from_date, to_date, space_key
            )
        except ConfluenceAPIError as e:
            log_and_raise_error(e, f"Fetching updated pages for {user_email_or_account_id}")
        
        # Filter out pages that were created by the same user (to avoid double counting)
        created_page_ids = {page.get("id") for page in created_pages}
        updated_only_pages = [
            page for page in updated_pages 
            if page.get("id") not in created_page_ids
        ]
        pages_updated = len(updated_only_pages)
        
        # Get comments written by user
        try:
            comments = await confluence_client.search_comments_by_user(
                user_email_or_account_id, from_date, to_date, space_key
            )
        except ConfluenceAPIError as e:
            log_and_raise_error(e, f"Fetching comments for {user_email_or_account_id}")
            
        comments_written = len(comments)
        
        # Build result
        result = {
            "user": user_email_or_account_id,
            "from": from_date,
            "to": to_date,
            "pagesCreated": pages_created,
            "pagesUpdated": pages_updated,
            "commentsWritten": comments_written
        }
        
        logger.info(f"Confluence activity analysis complete for {user_email_or_account_id}: {result}")
        
        return result
        
    except (ConfluenceAPIError, ValidationError, ConfigurationError) as e:
        # Re-raise known errors
        raise e
    except Exception as e:
        # Wrap unexpected errors
        error_msg = f"Failed to analyze Confluence activity: {str(e)}"
        logger.error(error_msg)
        log_and_raise_error(ConfluenceAPIError(error_msg), "Confluence Activity Analysis")


def main():
    """Main entry point"""
    # Validate environment variables
    required_vars = ["CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"The following environment variables are required: {', '.join(missing_vars)}"
        print(f"ERROR: {error_msg}")
        raise ConfigurationError(error_msg, missing_config=missing_vars[0])
    
    port = int(os.getenv("CONFLUENCE_MCP_PORT", 4003))
    
    logger.info(f"Starting Confluence MCP server on port {port}")
    logger.info("Using FastMCP with SSE transport")
    
    try:
        # Use SSE transport for compatibility
        import uvicorn
        sse_app = app.sse_app
        uvicorn.run(sse_app, host="0.0.0.0", port=port)
    except Exception as e:
        log_and_raise_error(
            ConfigurationError(f"Failed to start server: {str(e)}"),
            "Confluence Server Startup"
        )


if __name__ == "__main__":
    main()