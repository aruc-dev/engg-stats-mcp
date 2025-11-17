"""GitHub Engineering Analytics MCP Server - Focused on Metrics Only"""
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

from shared.github_client import GitHubClient, GitHubAPIError
from shared.date_utils import parse_iso_date, calculate_hours_between

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GitHubEngineerActivityInput(BaseModel):
    """Input schema for GitHub engineer activity analytics"""
    login: str = Field(description="GitHub username, e.g. 'alice'")
    from_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    to_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    repos: Optional[List[str]] = Field(default=None, description="Optional list of 'owner/repo' strings to filter")


# Create FastMCP server focused on engineering analytics
app = FastMCP("GitHub Engineering Analytics")

# Initialize GitHub client
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    logger.error("GITHUB_TOKEN environment variable is required")
    sys.exit(1)

github_client = GitHubClient(github_token)
logger.info("GitHub Engineering Analytics MCP Server initialized")


@app.tool("github_engineer_activity")
async def github_engineer_activity(
    login: str, 
    from_date: str, 
    to_date: str, 
    repos: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Calculate comprehensive engineering activity metrics for a GitHub user.
    
    This tool provides specialized analytics not available in the official GitHub MCP server:
    - PR authoring and merge statistics
    - Average PR cycle time calculations  
    - Code review activity metrics
    - Repository-filtered analytics
    
    Use the official GitHub MCP server for basic repository operations, issue management, 
    and workflow monitoring. Use this tool for engineering productivity insights.
    
    Args:
        login: GitHub username, e.g. "alice"
        from_date: ISO date string "YYYY-MM-DD"
        to_date: ISO date string "YYYY-MM-DD"
        repos: Optional list of "owner/repo" strings to filter analysis
    
    Returns:
        Dictionary with comprehensive engineering activity metrics
    """
    try:
        # Validate inputs
        GitHubEngineerActivityInput(
            login=login,
            from_date=from_date,
            to_date=to_date,
            repos=repos
        )
        
        logger.info(f"Calculating GitHub engineering metrics for {login} from {from_date} to {to_date}")
        
        # Fetch PRs authored by user
        prs = await github_client.search_prs_by_author(
            login, from_date, to_date, repos
        )
        
        prs_authored = len(prs)
        prs_merged = 0
        cycle_times = []
        
        # Analyze PR details for merge status and cycle times
        for pr in prs:
            if pr.get("pull_request"):
                # Get detailed PR info to check merge status
                repo_url = pr["repository_url"]
                repo_parts = repo_url.split("/")
                repo_owner, repo_name = repo_parts[-2], repo_parts[-1]
                
                try:
                    pr_details = await github_client.get_pr_details(
                        repo_owner, repo_name, pr["number"]
                    )
                    
                    if pr_details.get("merged_at"):
                        prs_merged += 1
                        
                        # Calculate cycle time
                        created_at = parse_iso_date(pr_details["created_at"])
                        merged_at = parse_iso_date(pr_details["merged_at"])
                        cycle_hours = calculate_hours_between(created_at, merged_at)
                        cycle_times.append(cycle_hours)
                        
                except GitHubAPIError as e:
                    logger.warning(f"Failed to get PR details for {pr['number']}: {e}")
                    continue
        
        # Calculate average cycle time
        avg_pr_cycle_hours = None
        if cycle_times:
            avg_pr_cycle_hours = sum(cycle_times) / len(cycle_times)
        
        # Fetch reviews given by user
        reviews = await github_client.search_reviews_by_user(
            login, from_date, to_date, repos
        )
        reviews_given = len(reviews)
        
        # Fetch review comments written by user
        comments = await github_client.get_review_comments_by_user(
            login, from_date, to_date, repos
        )
        comments_written = len(comments)
        
        # Build comprehensive metrics result
        result = {
            "login": login,
            "from": from_date,
            "to": to_date,
            "repositories_analyzed": repos or "all accessible",
            "metrics": {
                "pull_requests": {
                    "authored": prs_authored,
                    "merged": prs_merged,
                    "merge_rate": round(prs_merged / prs_authored, 2) if prs_authored > 0 else 0
                },
                "cycle_times": {
                    "average_hours": round(avg_pr_cycle_hours, 1) if avg_pr_cycle_hours else None,
                    "average_days": round(avg_pr_cycle_hours / 24, 1) if avg_pr_cycle_hours else None,
                    "total_merged": len(cycle_times)
                },
                "code_review": {
                    "reviews_given": reviews_given,
                    "comments_written": comments_written,
                    "review_participation": round(reviews_given / prs_authored, 1) if prs_authored > 0 else 0
                }
            }
        }
        
        logger.info(f"GitHub engineering analytics complete for {login}")
        
        return result
        
    except GitHubAPIError as e:
        error_msg = f"GitHub API error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to calculate GitHub engineering metrics: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def main():
    """Main entry point for GitHub Engineering Analytics MCP Server"""
    # Validate environment variables
    if not os.getenv("GITHUB_TOKEN"):
        print("ERROR: GITHUB_TOKEN environment variable is required")
        sys.exit(1)
    
    port = int(os.getenv("GITHUB_MCP_PORT", 4001))
    
    logger.info(f"Starting GitHub Engineering Analytics MCP server on port {port}")
    logger.info("This server provides engineering productivity metrics")
    logger.info("Use alongside the official GitHub MCP server for complete functionality")
    
    # Use SSE transport for compatibility
    import uvicorn
    sse_app = app.sse_app
    uvicorn.run(sse_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()