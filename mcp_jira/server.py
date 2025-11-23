"""Jira MCP Server for Engineering Activity Analytics - Using FastMCP"""
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

from shared.jira_client import JiraClient
from shared.date_utils import parse_iso_date
from shared.errors import (
    JiraAPIError, ValidationError, ConfigurationError,
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


class JiraEngineerActivityInput(BaseModel):
    """Input schema for Jira engineer activity tool"""
    user_email_or_account_id: str = Field(description="User email or Jira account ID")
    from_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    to_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    jql_extra: Optional[str] = Field(default=None, description="Extra JQL filter (project, labels, etc.)")


# Create FastMCP server
app = FastMCP("Jira Engineering Activity Analytics")

# Initialize Jira client
jira_base_url = os.getenv("JIRA_BASE_URL")
jira_email = os.getenv("JIRA_EMAIL")
jira_api_token = os.getenv("JIRA_API_TOKEN")

# Validate required environment variables
required_vars = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
    logger.error(error_msg)
    raise ConfigurationError(error_msg, missing_config=missing_vars[0])

try:
    jira_client = JiraClient(jira_base_url, jira_email, jira_api_token)
    logger.info("Jira MCP Server initialized successfully")
except Exception as e:
    log_and_raise_error(ConfigurationError(f"Failed to initialize Jira client: {str(e)}"), "Jira Server Init")
@app.tool("jira_engineer_activity")
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
        try:
            input_data = JiraEngineerActivityInput(
                user_email_or_account_id=user_email_or_account_id,
                from_date=from_date,
                to_date=to_date,
                jql_extra=jql_extra
            )
        except Exception as e:
            raise ValidationError(f"Invalid input parameters: {str(e)}")
        
        logger.info(f"Fetching Jira activity for {user_email_or_account_id} from {from_date} to {to_date}")
        
        # Get issues assigned to user in date range
        try:
            assigned_issues = await jira_client.search_issues_assigned_to_user(
                user_email_or_account_id, from_date, to_date, jql_extra
            )
        except JiraAPIError as e:
            log_and_raise_error(e, f"Fetching assigned issues for {user_email_or_account_id}")
            
        issues_assigned = len(assigned_issues)
        
        # Get issues resolved by user in date range
        try:
            resolved_issues = await jira_client.search_issues_resolved_by_user(
                user_email_or_account_id, from_date, to_date, jql_extra
            )
        except JiraAPIError as e:
            log_and_raise_error(e, f"Fetching resolved issues for {user_email_or_account_id}")
            
        issues_resolved = len(resolved_issues)
        
        # Count reopened issues from assigned issues
        try:
            reopened_count = jira_client._count_reopened_issues(assigned_issues)
        except Exception as e:
            logger.warning(f"Failed to count reopened issues: {e}")
            reopened_count = 0
        
        # Calculate average lead time for resolved issues
        try:
            lead_times = jira_client._calculate_lead_times(resolved_issues)
            avg_lead_time_hours = None
            if lead_times:
                avg_lead_time_hours = sum(lead_times) / len(lead_times)
        except Exception as e:
            logger.warning(f"Failed to calculate lead times: {e}")
            avg_lead_time_hours = None
        
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
        
        return result
        
    except (JiraAPIError, ValidationError, ConfigurationError) as e:
        # Re-raise known errors
        raise e
    except Exception as e:
        # Wrap unexpected errors
        error_msg = f"Failed to analyze Jira activity: {str(e)}"
        logger.error(error_msg)
        log_and_raise_error(JiraAPIError(error_msg), "Jira Activity Analysis")


def main():
    """Main entry point"""
    # Validate environment variables
    required_vars = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"The following environment variables are required: {', '.join(missing_vars)}"
        print(f"ERROR: {error_msg}")
        raise ConfigurationError(error_msg, missing_config=missing_vars[0])
    
    port = int(os.getenv("JIRA_MCP_PORT", 4002))
    
    logger.info(f"Starting Jira MCP server on port {port}")
    logger.info("Using FastMCP with SSE transport")
    
    try:
        # Use SSE transport for compatibility
        import uvicorn
        sse_app = app.sse_app
        uvicorn.run(sse_app, host="0.0.0.0", port=port)
    except Exception as e:
        log_and_raise_error(
            ConfigurationError(f"Failed to start server: {str(e)}"),
            "Jira Server Startup"
        )


if __name__ == "__main__":
    main()