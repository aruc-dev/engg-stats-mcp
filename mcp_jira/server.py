"""Jira MCP Server for Engineering Activity Analytics"""
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
from shared.jira_client import JiraClient, JiraAPIError
from shared.date_utils import parse_iso_date

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class JiraEngineerActivityInput(BaseModel):
    """Input schema for Jira engineer activity tool"""
    user_email_or_account_id: str = Field(description="User email or Jira account ID")
    from_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    to_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    jql_extra: Optional[str] = Field(default=None, description="Extra JQL filter (project, labels, etc.)")


class JiraEngineerActivityOutput(BaseModel):
    """Output schema for Jira engineer activity tool"""
    user: str
    from_date: str = Field(alias="from")
    to_date: str = Field(alias="to")
    issues_assigned: int
    issues_resolved: int
    reopened_count: int
    avg_lead_time_hours: Optional[float]


class JiraMCPServer:
    """Jira MCP Server implementation"""
    
    def __init__(self):
        self.jira_base_url = os.getenv("JIRA_BASE_URL")
        self.jira_email = os.getenv("JIRA_EMAIL")
        self.jira_api_token = os.getenv("JIRA_API_TOKEN")
        
        # Validate required environment variables
        if not self.jira_base_url:
            logger.error("JIRA_BASE_URL environment variable is required")
            sys.exit(1)
        if not self.jira_email:
            logger.error("JIRA_EMAIL environment variable is required")
            sys.exit(1)
        if not self.jira_api_token:
            logger.error("JIRA_API_TOKEN environment variable is required")
            sys.exit(1)
        
        self.jira_client = JiraClient(self.jira_base_url, self.jira_email, self.jira_api_token)
        
        # Create MCP server
        self.server = McpServer(
            "jira-eng-activity",
            "0.1.0",
            notification_options=NotificationOptions()
        )
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.tool("jira_engineer_activity")
        async def jira_engineer_activity(
            user_email_or_account_id: str, 
            from_date: str, 
            to_date: str, 
            jql_extra: Optional[str] = None
        ) -> Dict[str, Any]:
            """Summarize Jira issue activity for a single engineer over a time range.
            
            Args:
                user_email_or_account_id: User email or Jira account ID
                from_date: ISO date string "YYYY-MM-DD" 
                to_date: ISO date string "YYYY-MM-DD"
                jql_extra: Optional extra JQL filter (project, labels, etc.)
            
            Returns:
                Dictionary with issue tracking and resolution metrics
            """
            try:
                # Validate inputs
                input_data = JiraEngineerActivityInput(
                    user_email_or_account_id=user_email_or_account_id,
                    from_date=from_date,
                    to_date=to_date,
                    jql_extra=jql_extra
                )
                
                logger.info(f"Fetching Jira activity for {user_email_or_account_id} from {from_date} to {to_date}")
                
                # Get issues assigned to user in date range
                assigned_issues = await self.jira_client.search_issues_assigned_to_user(
                    user_email_or_account_id, from_date, to_date, jql_extra
                )
                issues_assigned = len(assigned_issues)
                
                # Get issues resolved by user in date range
                resolved_issues = await self.jira_client.search_issues_resolved_by_user(
                    user_email_or_account_id, from_date, to_date, jql_extra
                )
                issues_resolved = len(resolved_issues)
                
                # Count reopened issues from assigned issues
                reopened_count = self.jira_client._count_reopened_issues(assigned_issues)
                
                # Calculate average lead time for resolved issues
                lead_times = self.jira_client._calculate_lead_times(resolved_issues)
                avg_lead_time_hours = None
                if lead_times:
                    avg_lead_time_hours = sum(lead_times) / len(lead_times)
                
                # Build result
                result = {
                    "user": user_email_or_account_id,
                    "from": from_date,
                    "to": to_date,
                    "issuesAssigned": issues_assigned,
                    "issuesResolved": issues_resolved,
                    "reopenedCount": reopened_count,
                    "avgLeadTimeHours": avg_lead_time_hours
                }
                
                logger.info(f"Jira activity analysis complete for {user_email_or_account_id}: {result}")
                
                return {
                    "structuredContent": result,
                    "content": [
                        {"type": "text", "text": json.dumps(result, indent=2)}
                    ]
                }
                
            except JiraAPIError as e:
                error_msg = f"Jira API error: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Failed to analyze Jira activity: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)


# FastAPI app for HTTP transport
app = FastAPI(title="Jira Engineering Activity MCP Server")
mcp_server = JiraMCPServer()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "jira-eng-activity", "version": "0.1.0"}


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
            
            if tool_name == "jira_engineer_activity":
                # Extract arguments
                user_email_or_account_id = arguments.get("user_email_or_account_id")
                from_date = arguments.get("from_date") 
                to_date = arguments.get("to_date")
                jql_extra = arguments.get("jql_extra")
                
                # Call the tool
                tool_func = getattr(mcp_server.server, "_tools")["jira_engineer_activity"]
                result = await tool_func(user_email_or_account_id, from_date, to_date, jql_extra)
                
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
                            "name": "jira_engineer_activity",
                            "description": "Summarize Jira issue activity for a single engineer over a time range",
                            "inputSchema": JiraEngineerActivityInput.model_json_schema()
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
    required_vars = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: The following environment variables are required: {', '.join(missing_vars)}")
        sys.exit(1)
    
    port = int(os.getenv("JIRA_MCP_PORT", 4002))
    
    logger.info(f"Starting Jira MCP server on port {port}")
    logger.info(f"Access the server at http://localhost:{port}/mcp")
    
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()