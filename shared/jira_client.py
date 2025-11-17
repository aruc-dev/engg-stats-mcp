"""Jira API client for MCP server"""
import logging
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx
from shared.date_utils import parse_iso_date, calculate_hours_between

logger = logging.getLogger(__name__)


class JiraAPIError(Exception):
    """Jira API specific error"""
    pass


class JiraClient:
    """Jira API client with authentication and error handling"""
    
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
        """Make authenticated request to Jira API"""
        url = f"{self.base_url}/rest/api/3/{endpoint.lstrip('/')}"
        
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
                    raise JiraAPIError("Rate limit exceeded. Please wait before making more requests.")
                
                if not response.is_success:
                    error_msg = f"Jira API request failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise JiraAPIError(error_msg)
                
                return response.json()
                
            except httpx.RequestError as e:
                error_msg = f"Network error making request to Jira API: {str(e)}"
                logger.error(error_msg)
                raise JiraAPIError(error_msg) from e
    
    async def search_issues(self, jql: str, expand: Optional[List[str]] = None, max_results: int = 100) -> Dict[str, Any]:
        """Search issues using JQL"""
        params = {
            "jql": jql,
            "maxResults": min(max_results, 100),  # Jira max is 100
            "startAt": 0
        }
        
        if expand:
            params["expand"] = ",".join(expand)
        
        logger.info(f"Searching Jira issues with JQL: {jql}")
        return await self._make_request("GET", "search", params)
    
    async def get_issue_changelog(self, issue_key: str) -> Dict[str, Any]:
        """Get issue changelog for status transitions"""
        endpoint = f"issue/{issue_key}"
        params = {"expand": "changelog"}
        
        return await self._make_request("GET", endpoint, params)
    
    async def search_issues_assigned_to_user(
        self,
        user_email_or_account_id: str,
        from_date: str,
        to_date: str,
        jql_extra: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for issues assigned to user in date range"""
        # Build JQL query
        jql_parts = [
            f'assignee = "{user_email_or_account_id}"',
            f'created >= "{from_date}"',
            f'created <= "{to_date}"'
        ]
        
        if jql_extra:
            jql_parts.append(jql_extra)
        
        jql = " AND ".join(jql_parts)
        
        try:
            result = await self.search_issues(jql, expand=["changelog"], max_results=200)
            return result.get("issues", [])
        except JiraAPIError as e:
            logger.error(f"Failed to search assigned issues: {e}")
            raise
    
    async def search_issues_resolved_by_user(
        self,
        user_email_or_account_id: str,
        from_date: str,
        to_date: str,
        jql_extra: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for issues resolved by user in date range"""
        # Use resolved date for filtering
        jql_parts = [
            f'assignee = "{user_email_or_account_id}"',
            f'resolved >= "{from_date}"',
            f'resolved <= "{to_date}"',
            'status in (Done, Resolved, Closed, "Fix Released")'  # Common resolved statuses
        ]
        
        if jql_extra:
            jql_parts.append(jql_extra)
        
        jql = " AND ".join(jql_parts)
        
        try:
            result = await self.search_issues(jql, expand=["changelog"], max_results=200)
            return result.get("issues", [])
        except JiraAPIError as e:
            logger.error(f"Failed to search resolved issues: {e}")
            raise
    
    def _extract_status_transitions(self, issue: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract status transitions from issue changelog"""
        transitions = []
        
        changelog = issue.get("changelog", {})
        histories = changelog.get("histories", [])
        
        for history in histories:
            created = history.get("created")
            if not created:
                continue
                
            for item in history.get("items", []):
                if item.get("field") == "status":
                    transitions.append({
                        "date": created,
                        "from_status": item.get("fromString"),
                        "to_status": item.get("toString"),
                        "author": history.get("author", {}).get("emailAddress")
                    })
        
        return transitions
    
    def _count_reopened_issues(self, issues: List[Dict[str, Any]]) -> int:
        """Count issues that were reopened (transitioned from resolved back to active)"""
        reopened_count = 0
        resolved_statuses = {"Done", "Resolved", "Closed", "Fix Released", "Complete"}
        active_statuses = {"Open", "In Progress", "To Do", "Reopened", "In Review", "Testing"}
        
        for issue in issues:
            transitions = self._extract_status_transitions(issue)
            
            was_resolved = False
            for transition in sorted(transitions, key=lambda x: x["date"]):
                to_status = transition["to_status"]
                
                if to_status in resolved_statuses:
                    was_resolved = True
                elif was_resolved and to_status in active_statuses:
                    reopened_count += 1
                    break  # Count each issue only once
        
        return reopened_count
    
    def _calculate_lead_times(self, issues: List[Dict[str, Any]]) -> List[float]:
        """Calculate lead times for resolved issues (hours from created to resolved)"""
        lead_times = []
        
        for issue in issues:
            fields = issue.get("fields", {})
            created = fields.get("created")
            resolved = fields.get("resolutiondate")
            
            if created and resolved:
                try:
                    created_dt = parse_iso_date(created)
                    resolved_dt = parse_iso_date(resolved)
                    lead_time_hours = calculate_hours_between(created_dt, resolved_dt)
                    if lead_time_hours >= 0:  # Sanity check
                        lead_times.append(lead_time_hours)
                except Exception as e:
                    logger.warning(f"Failed to calculate lead time for issue {issue.get('key')}: {e}")
                    continue
        
        return lead_times