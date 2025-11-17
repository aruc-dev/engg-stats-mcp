"""Confluence MCP Server for Engineering Activity Analytics"""
import json
import logging
import os
import sys
from typing import Any, List, Optional, Dict
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from mcp import McpServer, Tool
from mcp.server.stdio import stdio_server
from mcp.server import NotificationOptions
from shared.confluence_client import ConfluenceClient, ConfluenceAPIError
from shared.date_utils import parse_iso_date

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


class ConfluenceEngineerActivityOutput(BaseModel):
    """Output schema for Confluence engineer activity tool"""
    user: str
    from_date: str = Field(alias="from")
    to_date: str = Field(alias="to")
    pages_created: int
    pages_updated: int
    comments_written: int


class ConfluenceMCPServer:
    """Confluence MCP Server implementation"""
    
    def __init__(self):
        self.confluence_base_url = os.getenv("CONFLUENCE_BASE_URL")
        self.confluence_email = os.getenv("CONFLUENCE_EMAIL")
        self.confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")
        
        # Validate required environment variables
        if not self.confluence_base_url:
            logger.error("CONFLUENCE_BASE_URL environment variable is required")
            sys.exit(1)
        if not self.confluence_email:
            logger.error("CONFLUENCE_EMAIL environment variable is required")
            sys.exit(1)
        if not self.confluence_api_token:
            logger.error("CONFLUENCE_API_TOKEN environment variable is required")
            sys.exit(1)
        
        self.confluence_client = ConfluenceClient(
            self.confluence_base_url, 
            self.confluence_email, 
            self.confluence_api_token
        )
        
        # Create MCP server
        self.server = McpServer(
            "confluence-eng-activity",
            "0.1.0",
            notification_options=NotificationOptions()
        )
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.tool("confluence_engineer_activity")
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
                input_data = ConfluenceEngineerActivityInput(
                    user_email_or_account_id=user_email_or_account_id,
                    from_date=from_date,
                    to_date=to_date,
                    space_key=space_key
                )
                
                logger.info(f"Fetching Confluence activity for {user_email_or_account_id} from {from_date} to {to_date}")
                
                # Get pages created by user
                created_pages = await self.confluence_client.search_content_by_creator(
                    user_email_or_account_id, from_date, to_date, space_key, "page"
                )
                pages_created = len(created_pages)
                
                # Get pages updated by user
                updated_pages = await self.confluence_client.search_updated_content_by_user(
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
                comments = await self.confluence_client.search_comments_by_user(
                    user_email_or_account_id, from_date, to_date, space_key
                )
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
                
                return {
                    "structuredContent": result,
                    "content": [
                        {"type": "text", "text": json.dumps(result, indent=2)}
                    ]
                }
                
            except ConfluenceAPIError as e:
                error_msg = f"Confluence API error: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Failed to analyze Confluence activity: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)


# FastAPI app for HTTP transport
app = FastAPI(title="Confluence Engineering Activity MCP Server")
mcp_server = ConfluenceMCPServer()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "confluence-eng-activity", "version": "0.1.0"}


@app.post("/mcp")
async def mcp_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """MCP HTTP endpoint"""
    try:
        # Handle the MCP request through the server
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "confluence_engineer_activity":
                # Extract arguments
                user_email_or_account_id = arguments.get("user_email_or_account_id")
                from_date = arguments.get("from_date")
                to_date = arguments.get("to_date")
                space_key = arguments.get("space_key")
                
                # Call the tool
                tool_func = getattr(mcp_server.server, "_tools")["confluence_engineer_activity"]
                result = await tool_func(user_email_or_account_id, from_date, to_date, space_key)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": result
                }
            else:
                raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "confluence_engineer_activity",
                            "description": "Summarize Confluence activity for a single user over a time range",
                            "inputSchema": ConfluenceEngineerActivityInput.model_json_schema()
                        }
                    ]
                }
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
    
    except Exception as e:
        logger.error(f"MCP endpoint error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }


def main():
    """Main entry point"""
    # Validate environment variables
    required_vars = ["CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: The following environment variables are required: {', '.join(missing_vars)}")
        sys.exit(1)
    
    port = int(os.getenv("CONFLUENCE_MCP_PORT", 4003))
    
    logger.info(f"Starting Confluence MCP server on port {port}")
    logger.info(f"Access the server at http://localhost:{port}/mcp")
    
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()