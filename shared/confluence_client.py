"""Confluence API client for MCP server"""
import logging
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx
from shared.date_utils import parse_iso_date
from shared.errors import ConfluenceAPIError, RateLimitError, NetworkError, create_confluence_error

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Confluence API client with authentication and error handling"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        
        # Create basic auth header
        auth_string = f"{email}:{api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Confluence API"""
        url = f"{self.base_url}/rest/api/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient() as client:
            try:
                logger.debug(f"Making {method} request to {url} with params: {params}")
                response = await client.request(
                    method, 
                    url, 
                    headers=self.headers, 
                    params=params,
                    json=json_data,
                    timeout=30.0
                )
                
                if response.status_code == 429:
                    # Try to extract retry-after header
                    retry_after = None
                    if 'retry-after' in response.headers:
                        try:
                            retry_after = int(response.headers['retry-after'])
                        except ValueError:
                            pass
                    raise RateLimitError("Confluence", retry_after)
                
                if not response.is_success:
                    # Use the new error creation function
                    raise create_confluence_error(response)
                
                return response.json()
                
            except httpx.RequestError as e:
                error_msg = f"Network error making request to Confluence API: {str(e)}"
                logger.error(error_msg)
                raise NetworkError(error_msg, "Confluence") from e
    
    async def _paginate_content(self, endpoint: str, params: Dict[str, Any], max_items: int = 200) -> List[Dict[str, Any]]:
        """Paginate through content results"""
        items = []
        start = 0
        limit = min(50, max_items)  # Confluence typically uses 50 as reasonable page size
        
        while len(items) < max_items:
            current_params = {**params, "start": start, "limit": limit}
            result = await self._make_request("GET", endpoint, current_params)
            
            page_items = result.get("results", [])
            if not page_items:
                break
            
            items.extend(page_items)
            
            # Stop if we've gotten all items or reached the max
            if len(page_items) < limit or len(items) >= max_items:
                break
            
            start += limit
        
        return items[:max_items]
    
    async def search_content_by_creator(
        self,
        user_email_or_account_id: str,
        from_date: str,
        to_date: str,
        space_key: Optional[str] = None,
        content_type: str = "page"
    ) -> List[Dict[str, Any]]:
        """Search for content created by user in date range"""
        # Build CQL (Confluence Query Language) query
        cql_parts = [
            f'creator = "{user_email_or_account_id}"',
            f'created >= "{from_date}"',
            f'created <= "{to_date}"',
            f'type = {content_type}'
        ]
        
        if space_key:
            cql_parts.append(f'space = "{space_key}"')
        
        cql = " AND ".join(cql_parts)
        
        params = {
            "cql": cql,
            "expand": "version,space,history"
        }
        
        logger.info(f"Searching Confluence content with CQL: {cql}")
        
        try:
            return await self._paginate_content("search", params)
        except ConfluenceAPIError as e:
            logger.error(f"Failed to search content by creator: {e}")
            raise
    
    async def search_updated_content_by_user(
        self,
        user_email_or_account_id: str,
        from_date: str,
        to_date: str,
        space_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for content updated by user in date range"""
        # Search for pages that were last modified by the user in the date range
        cql_parts = [
            f'lastModified >= "{from_date}"',
            f'lastModified <= "{to_date}"',
            'type = page'
        ]
        
        if space_key:
            cql_parts.append(f'space = "{space_key}"')
        
        cql = " AND ".join(cql_parts)
        
        params = {
            "cql": cql,
            "expand": "version,space,history.lastUpdated"
        }
        
        logger.info(f"Searching updated Confluence content with CQL: {cql}")
        
        try:
            content_items = await self._paginate_content("search", params)
            
            # Filter by actual last modifier (since CQL can't filter by specific modifier)
            user_updated_items = []
            for item in content_items:
                history = item.get("history", {})
                last_updated = history.get("lastUpdated", {})
                last_modifier = last_updated.get("by", {})
                
                # Check both email and account ID
                modifier_email = last_modifier.get("email")
                modifier_account_id = last_modifier.get("accountId")
                
                if (modifier_email == user_email_or_account_id or 
                    modifier_account_id == user_email_or_account_id):
                    user_updated_items.append(item)
            
            return user_updated_items
            
        except ConfluenceAPIError as e:
            logger.error(f"Failed to search updated content: {e}")
            raise
    
    async def search_comments_by_user(
        self,
        user_email_or_account_id: str,
        from_date: str,
        to_date: str,
        space_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for comments written by user in date range"""
        # Confluence doesn't have great comment search via CQL, so we need to:
        # 1. Get pages in the date range
        # 2. Check their comments for our user
        
        # First, get pages that might have comments in our date range
        cql_parts = [
            f'lastModified >= "{from_date}"',
            f'lastModified <= "{to_date}"',
            'type = page'
        ]
        
        if space_key:
            cql_parts.append(f'space = "{space_key}"')
        
        cql = " AND ".join(cql_parts)
        
        params = {
            "cql": cql,
            "expand": "version"
        }
        
        try:
            pages = await self._paginate_content("search", params, max_items=100)  # Limit to avoid too many API calls
            
            user_comments = []
            from_dt = parse_iso_date(from_date)
            to_dt = parse_iso_date(to_date)
            
            for page in pages:
                page_id = page.get("id")
                if not page_id:
                    continue
                
                try:
                    # Get comments for this page
                    comments_endpoint = f"content/{page_id}/child/comment"
                    comments_params = {"expand": "version,body.storage"}
                    comments_result = await self._make_request("GET", comments_endpoint, comments_params)
                    
                    comments = comments_result.get("results", [])
                    
                    # Filter comments by user and date
                    for comment in comments:
                        version = comment.get("version", {})
                        created_date = version.get("when")
                        author = version.get("by", {})
                        
                        if not created_date:
                            continue
                        
                        # Check if comment is by our user
                        author_email = author.get("email")
                        author_account_id = author.get("accountId")
                        
                        if (author_email == user_email_or_account_id or 
                            author_account_id == user_email_or_account_id):
                            
                            # Check if comment is in date range
                            try:
                                comment_dt = parse_iso_date(created_date)
                                if from_dt <= comment_dt <= to_dt:
                                    user_comments.append(comment)
                            except Exception as e:
                                logger.warning(f"Failed to parse comment date {created_date}: {e}")
                                continue
                    
                except ConfluenceAPIError as e:
                    logger.warning(f"Failed to get comments for page {page_id}: {e}")
                    continue
            
            return user_comments
            
        except ConfluenceAPIError as e:
            logger.error(f"Failed to search comments by user: {e}")
            raise