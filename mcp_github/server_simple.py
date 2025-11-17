"""GitHub MCP Server for Engineering Activity Analytics - Simplified Version"""
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
    """Input schema for GitHub engineer activity tool"""
    login: str = Field(description="GitHub username, e.g. 'alice'")
    from_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    to_date: str = Field(description="ISO date string 'YYYY-MM-DD'", pattern=r'^\d{4}-\d{2}-\d{2}$')
    repos: Optional[List[str]] = Field(default=None, description="Optional list of 'owner/repo' strings to filter")


class GitHubMCPServer:
    """GitHub MCP Server implementation"""
    
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            logger.error("GITHUB_TOKEN environment variable is required")
            sys.exit(1)
        
        self.github_client = GitHubClient(self.github_token)
        logger.info("GitHub MCP Server initialized successfully")
    
    async def github_engineer_activity(
        self, 
        login: str, 
        from_date: str, 
        to_date: str, 
        repos: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Summarize PR and review activity for a GitHub user over a time range."""
        try:
            # Validate inputs
            input_data = GitHubEngineerActivityInput(
                login=login,
                from_date=from_date,
                to_date=to_date,
                repos=repos
            )
            
            logger.info(f"Fetching GitHub activity for {login} from {from_date} to {to_date}")
            
            # Fetch PRs authored by user
            prs = await self.github_client.search_prs_by_author(
                login, from_date, to_date, repos
            )
            
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
                        pr_details = await self.github_client.get_pr_details(
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
            reviews = await self.github_client.search_reviews_by_user(
                login, from_date, to_date, repos
            )
            reviews_given = len(reviews)
            
            # Fetch review comments written by user
            comments = await self.github_client.get_review_comments_by_user(
                login, from_date, to_date, repos
            )
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
            
            return {
                "structuredContent": result,
                "content": [
                    {"type": "text", "text": json.dumps(result, indent=2)}
                ]
            }
            
        except GitHubAPIError as e:
            error_msg = f"GitHub API error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to analyze GitHub activity: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)


# FastAPI app for HTTP transport
app = FastAPI(title="GitHub Engineering Activity MCP Server")
mcp_server = GitHubMCPServer()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "server": "github-eng-activity", 
        "version": "0.1.0",
        "status": "running",
        "endpoints": ["/health", "/mcp", "/test"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "github-eng-activity", "version": "0.1.0"}


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
            
            if tool_name == "github_engineer_activity":
                # Extract arguments
                login = arguments.get("login")
                from_date = arguments.get("from_date")
                to_date = arguments.get("to_date")
                repos = arguments.get("repos")
                
                # Call the tool
                result = await mcp_server.github_engineer_activity(login, from_date, to_date, repos)
                
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
                            "name": "github_engineer_activity",
                            "description": "Summarize PR and review activity for a GitHub user over a time range",
                            "inputSchema": GitHubEngineerActivityInput.model_json_schema()
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


@app.get("/test")
async def test_github_activity():
    """Test endpoint to verify GitHub integration"""
    try:
        # Test with a simple GitHub user lookup
        result = await mcp_server.github_engineer_activity(
            login="octocat",  # GitHub's mascot account
            from_date="2024-01-01", 
            to_date="2024-12-31"
        )
        return {"status": "success", "test_result": result}
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {"status": "error", "error": str(e)}


def main():
    """Main entry point"""
    # Validate environment variables
    if not os.getenv("GITHUB_TOKEN"):
        print("ERROR: GITHUB_TOKEN environment variable is required")
        sys.exit(1)
    
    port = int(os.getenv("GITHUB_MCP_PORT", 4001))
    
    logger.info(f"Starting GitHub MCP server on port {port}")
    logger.info(f"Access the server at http://localhost:{port}/mcp")
    logger.info(f"Test endpoint: http://localhost:{port}/test")
    
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()