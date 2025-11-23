"""GitHub MCP Server for Engineering Activity Analytics - Using FastMCP"""
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

from shared.github_client import GitHubClient
from shared.date_utils import parse_iso_date, calculate_hours_between
from shared.errors import (
    GitHubAPIError, ValidationError, ConfigurationError, 
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


class GitHubEngineerActivityInput(BaseModel):
    """Input schema for GitHub engineer activity tool"""
    login: str = Field(description="GitHub username, e.g. 'alice'")
    from_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    to_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    repos: Optional[List[str]] = Field(default=None, description="Optional list of 'owner/repo' strings to filter")


# Create FastMCP server
app = FastMCP("GitHub Engineering Activity Analytics")

# Initialize GitHub client
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    error_msg = "GITHUB_TOKEN environment variable is required"
    logger.error(error_msg)
    raise ConfigurationError(error_msg, missing_config="GITHUB_TOKEN")

try:
    github_client = GitHubClient(github_token)
    logger.info("GitHub MCP Server initialized successfully")
except Exception as e:
    log_and_raise_error(ConfigurationError(f"Failed to initialize GitHub client: {str(e)}"), "GitHub Server Init")


@app.tool("github_engineer_activity")
async def github_engineer_activity(
    login: str, 
    from_date: str, 
    to_date: str, 
    repos: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Summarize PR and review activity for a GitHub user over a time range.
    
    Args:
        login: GitHub username, e.g. "alice"
        from_date: ISO date string "YYYY-MM-DD"
        to_date: ISO date string "YYYY-MM-DD"
        repos: Optional list of "owner/repo" strings to filter
    
    Returns:
        Dictionary with PR and review activity metrics
    """
    try:
        # Validate inputs
        try:
            input_data = GitHubEngineerActivityInput(
                login=login,
                from_date=from_date,
                to_date=to_date,
                repos=repos
            )
        except Exception as e:
            raise ValidationError(f"Invalid input parameters: {str(e)}")
        
        logger.info(f"Fetching GitHub activity for {login} from {from_date} to {to_date}")
        
        # Fetch PRs authored by user
        try:
            prs = await github_client.search_prs_by_author(
                login, from_date, to_date, repos
            )
        except GitHubAPIError as e:
            log_and_raise_error(e, f"Fetching PRs for {login}")
        
        prs_authored = len(prs)
        prs_merged = 0
        cycle_times = []
        
        # Analyze PR details for merge status and cycle times
        for pr in prs:
            if pr.get("state") == "closed" and pr.get("pull_request"):
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
                except Exception as e:
                    logger.warning(f"Unexpected error processing PR {pr['number']}: {e}")
                    continue
        
        # Calculate average cycle time
        avg_pr_cycle_hours = None
        if cycle_times:
            avg_pr_cycle_hours = sum(cycle_times) / len(cycle_times)
        
        # Fetch reviews given by user
        try:
            reviews = await github_client.search_reviews_by_user(
                login, from_date, to_date, repos
            )
        except GitHubAPIError as e:
            log_and_raise_error(e, f"Fetching reviews for {login}")
            
        reviews_given = len(reviews)
        
        # Fetch review comments written by user
        try:
            comments = await github_client.get_review_comments_by_user(
                login, from_date, to_date, repos
            )
        except GitHubAPIError as e:
            log_and_raise_error(e, f"Fetching review comments for {login}")
            
        comments_written = len(comments)
        
        # Build result
        result = {
            "login": login,
            "from": from_date,
            "to": to_date,
            "prsAuthored": prs_authored,
            "prsMerged": prs_merged,
            "avgPrCycleHours": avg_pr_cycle_hours,
            "reviewsGiven": reviews_given,
            "commentsWritten": comments_written
        }
        
        logger.info(f"GitHub activity analysis complete for {login}: {result}")
        
        return result
        
    except (GitHubAPIError, ValidationError, ConfigurationError) as e:
        # Re-raise known errors
        raise e
    except Exception as e:
        # Wrap unexpected errors
        error_msg = f"Failed to analyze GitHub activity: {str(e)}"
        logger.error(error_msg)
        log_and_raise_error(GitHubAPIError(error_msg), "GitHub Activity Analysis")


def main():
    """Main entry point"""
    # Validate environment variables
    if not os.getenv("GITHUB_TOKEN"):
        error_msg = "GITHUB_TOKEN environment variable is required"
        print(f"ERROR: {error_msg}")
        raise ConfigurationError(error_msg, missing_config="GITHUB_TOKEN")
    
    port = int(os.getenv("GITHUB_MCP_PORT", 4001))
    
    logger.info(f"Starting GitHub MCP server on port {port}")
    logger.info(f"Using MCP SDK with FastMCP server")
    
    try:
        # FastMCP supports different transports. Let's try SSE (Server-Sent Events)
        import uvicorn
        
        # Use the SSE app from FastMCP  
        sse_app = app.sse_app
        uvicorn.run(sse_app, host="0.0.0.0", port=port)
    except Exception as e:
        log_and_raise_error(
            ConfigurationError(f"Failed to start server: {str(e)}"),
            "GitHub Server Startup"
        )


if __name__ == "__main__":
    main()