"""GitHub API client for MCP server"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx
from shared.date_utils import parse_iso_date, calculate_hours_between, get_date_range_query_string

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """GitHub API specific error"""
    pass


class GitHubClient:
    """GitHub API client with authentication, pagination, and error handling"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to GitHub API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient() as client:
            try:
                logger.debug(f"Making {method} request to {url} with params: {params}")
                response = await client.request(method, url, headers=self.headers, params=params)
                
                if response.status_code == 429:
                    raise GitHubAPIError("Rate limit exceeded. Please wait before making more requests.")
                
                if not response.is_success:
                    error_msg = f"GitHub API request failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise GitHubAPIError(error_msg)
                
                return response.json()
                
            except httpx.RequestError as e:
                error_msg = f"Network error making request to GitHub API: {str(e)}"
                logger.error(error_msg)
                raise GitHubAPIError(error_msg) from e
    
    async def _paginate_search(self, endpoint: str, params: Dict[str, Any], max_items: int = 200) -> List[Dict[str, Any]]:
        """Paginate through search results"""
        items = []
        page = 1
        per_page = min(100, max_items)  # GitHub max is 100 per page
        
        while len(items) < max_items:
            current_params = {**params, "page": page, "per_page": per_page}
            result = await self._make_request("GET", endpoint, current_params)
            
            page_items = result.get("items", [])
            if not page_items:
                break
            
            items.extend(page_items)
            
            # Stop if we've gotten all items or reached the max
            if len(page_items) < per_page or len(items) >= max_items:
                break
            
            page += 1
        
        return items[:max_items]
    
    async def search_prs_by_author(
        self, 
        login: str, 
        from_date: str, 
        to_date: str, 
        repos: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for PRs authored by user in date range"""
        # Build search query
        date_range = get_date_range_query_string(from_date, to_date, "created")
        query_parts = [
            f"author:{login}",
            f"type:pr",
            date_range
        ]
        
        if repos:
            repo_filter = " ".join([f"repo:{repo}" for repo in repos])
            query_parts.append(f"({repo_filter})")
        
        query = " ".join(query_parts)
        
        params = {
            "q": query,
            "sort": "created",
            "order": "desc"
        }
        
        logger.info(f"Searching PRs for {login} with query: {query}")
        return await self._paginate_search("search/issues", params)
    
    async def get_pr_details(self, repo_owner: str, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Get detailed PR information including merge status"""
        endpoint = f"repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        return await self._make_request("GET", endpoint)
    
    async def search_reviews_by_user(
        self, 
        login: str, 
        from_date: str, 
        to_date: str, 
        repos: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for PR reviews given by user in date range"""
        # GitHub doesn't have a direct review search, so we need to:
        # 1. Search for PRs in the date range
        # 2. Check reviews on those PRs for our user
        
        # First, get all PRs in the date range
        date_range = get_date_range_query_string(from_date, to_date, "created")
        query_parts = [
            "type:pr",
            date_range
        ]
        
        if repos:
            repo_filter = " ".join([f"repo:{repo}" for repo in repos])
            query_parts.append(f"({repo_filter})")
        
        query = " ".join(query_parts)
        
        params = {
            "q": query,
            "sort": "created", 
            "order": "desc"
        }
        
        logger.info(f"Searching PRs for reviews by {login}")
        prs = await self._paginate_search("search/issues", params, max_items=50)  # Limit to avoid too many API calls
        
        user_reviews = []
        from_dt = parse_iso_date(from_date)
        to_dt = parse_iso_date(to_date)
        
        for pr in prs:
            if not pr.get("pull_request"):
                continue
                
            # Extract repo info from URL
            repo_url = pr["repository_url"]
            repo_parts = repo_url.split("/")
            repo_owner, repo_name = repo_parts[-2], repo_parts[-1]
            
            try:
                # Get reviews for this PR
                endpoint = f"repos/{repo_owner}/{repo_name}/pulls/{pr['number']}/reviews"
                reviews = await self._make_request("GET", endpoint)
                
                # Filter reviews by user and date
                for review in reviews:
                    if (review.get("user", {}).get("login") == login and 
                        review.get("submitted_at")):
                        
                        review_dt = parse_iso_date(review["submitted_at"])
                        if from_dt <= review_dt <= to_dt:
                            user_reviews.append(review)
                            
            except GitHubAPIError as e:
                logger.warning(f"Failed to get reviews for PR {pr['number']}: {e}")
                continue
        
        return user_reviews
    
    async def get_review_comments_by_user(
        self,
        login: str,
        from_date: str, 
        to_date: str,
        repos: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get PR review comments by user in date range"""
        # Similar approach as reviews - get PRs then check comments
        date_range = get_date_range_query_string(from_date, to_date, "created")
        query_parts = [
            "type:pr",
            date_range
        ]
        
        if repos:
            repo_filter = " ".join([f"repo:{repo}" for repo in repos])
            query_parts.append(f"({repo_filter})")
        
        query = " ".join(query_parts)
        
        params = {
            "q": query,
            "sort": "created",
            "order": "desc"
        }
        
        prs = await self._paginate_search("search/issues", params, max_items=50)
        
        user_comments = []
        from_dt = parse_iso_date(from_date)
        to_dt = parse_iso_date(to_date)
        
        for pr in prs:
            if not pr.get("pull_request"):
                continue
                
            repo_url = pr["repository_url"] 
            repo_parts = repo_url.split("/")
            repo_owner, repo_name = repo_parts[-2], repo_parts[-1]
            
            try:
                # Get review comments for this PR
                endpoint = f"repos/{repo_owner}/{repo_name}/pulls/{pr['number']}/comments"
                comments = await self._make_request("GET", endpoint)
                
                # Filter comments by user and date
                for comment in comments:
                    if (comment.get("user", {}).get("login") == login and 
                        comment.get("created_at")):
                        
                        comment_dt = parse_iso_date(comment["created_at"])
                        if from_dt <= comment_dt <= to_dt:
                            user_comments.append(comment)
                            
            except GitHubAPIError as e:
                logger.warning(f"Failed to get comments for PR {pr['number']}: {e}")
                continue
        
        return user_comments