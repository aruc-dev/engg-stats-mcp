"""Jira Engineering Analytics MCP Server - Focused on Metrics Only"""
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
    """Input schema for Jira engineer activity analytics"""
    user_email_or_account_id: str = Field(description="User email or Jira account ID")
    from_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    to_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    jql_extra: Optional[str] = Field(default=None, description="Extra JQL filter (project, labels, etc.)")


# Create FastMCP server focused on engineering analytics
app = FastMCP("Jira Engineering Analytics")

# Initialize Jira client
jira_base_url = os.getenv("JIRA_BASE_URL")
jira_email = os.getenv("JIRA_EMAIL")
jira_api_token = os.getenv("JIRA_API_TOKEN")

# Validate required environment variables
required_vars = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

jira_client = JiraClient(jira_base_url, jira_email, jira_api_token)
logger.info("Jira Engineering Analytics MCP Server initialized")


@app.tool("jira_engineer_activity")
async def jira_engineer_activity(
    user_email_or_account_id: str, 
    from_date: str, 
    to_date: str, 
    jql_extra: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate comprehensive engineering activity metrics for a Jira user.
    
    This tool provides specialized analytics not available in the official Atlassian MCP server:
    - Issue assignment and resolution tracking
    - Lead time calculations
    - Reopened issue analysis  
    - Custom JQL-filtered metrics
    
    Use the official Atlassian MCP server for basic issue CRUD operations, project management,
    and workflow operations. Use this tool for engineering productivity insights.
    
    Args:
        user_email_or_account_id: User email or Jira account ID
        from_date: ISO date string "YYYY-MM-DD" 
        to_date: ISO date string "YYYY-MM-DD"
        jql_extra: Optional extra JQL filter (project, labels, etc.)
    
    Returns:
        Dictionary with comprehensive Jira activity metrics
    """
    try:
        # Validate inputs
        input_data = JiraEngineerActivityInput(
            user_email_or_account_id=user_email_or_account_id,
            from_date=from_date,
            to_date=to_date,
            jql_extra=jql_extra
        )
        
        logger.info(f"Calculating Jira engineering metrics for {user_email_or_account_id} from {from_date} to {to_date}")
        
        # Get issues assigned to user in date range
        assigned_issues = await jira_client.search_issues_assigned_to_user(
            user_email_or_account_id, from_date, to_date, jql_extra
        )
        issues_assigned = len(assigned_issues)
        
        # Get issues resolved by user in date range
        resolved_issues = await jira_client.search_issues_resolved_by_user(
            user_email_or_account_id, from_date, to_date, jql_extra
        )
        issues_resolved = len(resolved_issues)
        
        # Count reopened issues from assigned issues
        # Use the public method to preserve encapsulation (see JiraClient)
        reopened_count = jira_client.count_reopened_issues(assigned_issues)
        
        # Calculate lead times for resolved issues
        lead_times = jira_client._calculate_lead_times(resolved_issues)
        avg_lead_time_hours = None
        if lead_times:
            avg_lead_time_hours = sum(lead_times) / len(lead_times)
        
        # Analyze issue types and priorities
        issue_types = {}
        priorities = {}
        
        for issue in assigned_issues:
            # Track issue types
            issue_type = issue.get('fields', {}).get('issuetype', {}).get('name', 'Unknown')
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
            
            # Track priorities
            priority = issue.get('fields', {}).get('priority', {}).get('name', 'Unknown')
            priorities[priority] = priorities.get(priority, 0) + 1
        
        # Build comprehensive metrics result
        result = {
            "user": user_email_or_account_id,
            "from": from_date,
            "to": to_date,
            "jql_filter": jql_extra,
            "metrics": {
                "issues": {
                    "assigned": issues_assigned,
                    "resolved": issues_resolved,
                    "resolution_rate": round(issues_resolved / issues_assigned, 2) if issues_assigned > 0 else 0,
                    "reopened": reopened_count,
                    "quality_score": round((issues_resolved - reopened_count) / issues_resolved, 2) if issues_resolved > 0 else 0
                },
                "lead_times": {
                    "average_hours": round(avg_lead_time_hours, 1) if avg_lead_time_hours else None,
                    "average_days": round(avg_lead_time_hours / 24, 1) if avg_lead_time_hours else None,
                    "resolved_count": len(lead_times)
                },
                "issue_distribution": {
                    "types": issue_types,
                    "priorities": priorities
                }
            }
        }
        
        logger.info(f"Jira engineering analytics complete for {user_email_or_account_id}")
        
        return result
        
    except JiraAPIError as e:
        error_msg = f"Jira API error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to calculate Jira engineering metrics: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def main():
    """Main entry point for Jira Engineering Analytics MCP Server"""
    # Validate environment variables
    required_vars = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: The following environment variables are required: {', '.join(missing_vars)}")
        sys.exit(1)
    
    port = int(os.getenv("JIRA_MCP_PORT", 4002))
    
    logger.info(f"Starting Jira Engineering Analytics MCP server on port {port}")
    logger.info("This server provides engineering productivity metrics for Jira")
    logger.info("Use alongside the official Atlassian MCP server for complete functionality")
    
    # Use SSE transport for compatibility
    import uvicorn
    sse_app = app.sse_app
    uvicorn.run(sse_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()