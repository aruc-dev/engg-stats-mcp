"""Comprehensive error handling for MCP servers"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MCPServerError(Exception):
    """Base exception class for MCP server errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_mcp_error(self) -> Dict[str, Any]:
        """Convert to MCP error format"""
        return {
            "code": -32000,  # Generic server error
            "message": self.message,
            "data": {
                "error_code": self.error_code,
                "details": self.details
            }
        }


class ConfigurationError(MCPServerError):
    """Raised when server configuration is invalid or missing"""
    
    def __init__(self, message: str, missing_config: Optional[str] = None):
        super().__init__(
            message, 
            error_code="CONFIGURATION_ERROR",
            details={"missing_config": missing_config} if missing_config else {}
        )


class ValidationError(MCPServerError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        super().__init__(
            message,
            error_code="VALIDATION_ERROR", 
            details={"field": field, "value": value} if field else {}
        )


class APIError(MCPServerError):
    """Base class for external API errors"""
    
    def __init__(self, message: str, api_name: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(
            message,
            error_code="API_ERROR",
            details={
                "api_name": api_name,
                "status_code": status_code,
                "response_body": response_body
            }
        )
        self.api_name = api_name
        self.status_code = status_code
        self.response_body = response_body


class GitHubAPIError(APIError):
    """GitHub API specific errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message, "GitHub", status_code, response_body)


class JiraAPIError(APIError):
    """Jira API specific errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message, "Jira", status_code, response_body)


class ConfluenceAPIError(APIError):
    """Confluence API specific errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message, "Confluence", status_code, response_body)


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded"""
    
    def __init__(self, api_name: str, retry_after: Optional[int] = None):
        message = f"{api_name} API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        
        super().__init__(
            message,
            api_name,
            status_code=429,
        )
        self.retry_after = retry_after
        self.details["retry_after"] = retry_after


class AuthenticationError(APIError):
    """Raised when API authentication fails"""
    
    def __init__(self, api_name: str, message: Optional[str] = None):
        super().__init__(
            message or f"{api_name} API authentication failed. Check your credentials.",
            api_name,
            status_code=401
        )


class PermissionError(APIError):
    """Raised when API access is forbidden"""
    
    def __init__(self, api_name: str, resource: Optional[str] = None):
        message = f"Access forbidden to {api_name}"
        if resource:
            message += f" resource: {resource}"
        
        super().__init__(message, api_name, status_code=403)


class NotFoundError(APIError):
    """Raised when requested resource is not found"""
    
    def __init__(self, api_name: str, resource: Optional[str] = None):
        message = f"Resource not found in {api_name}"
        if resource:
            message += f": {resource}"
            
        super().__init__(message, api_name, status_code=404)


class NetworkError(MCPServerError):
    """Raised when network connectivity issues occur"""
    
    def __init__(self, message: str, api_name: Optional[str] = None):
        super().__init__(
            message,
            error_code="NETWORK_ERROR",
            details={"api_name": api_name} if api_name else {}
        )


class TimeoutError(MCPServerError):
    """Raised when operations timeout"""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None):
        super().__init__(
            message,
            error_code="TIMEOUT_ERROR",
            details={"timeout_seconds": timeout_seconds} if timeout_seconds else {}
        )


def handle_mcp_error(error: Exception) -> Dict[str, Any]:
    """Convert any exception to MCP error format"""
    if isinstance(error, MCPServerError):
        return error.to_mcp_error()
    
    # Handle standard Python exceptions
    if isinstance(error, ValueError):
        validation_error = ValidationError(str(error))
        return validation_error.to_mcp_error()
    
    # Generic error fallback
    generic_error = MCPServerError(f"Unexpected error: {str(error)}")
    return generic_error.to_mcp_error()


def log_and_raise_error(error: Exception, context: str = "") -> None:
    """Log error with context and re-raise"""
    if context:
        logger.error(f"{context}: {error}")
    else:
        logger.error(f"Error: {error}")
    
    # Add stack trace for debugging
    if logger.isEnabledFor(logging.DEBUG):
        import traceback
        logger.debug(f"Stack trace: {traceback.format_exc()}")
    
    raise error


def create_api_error_from_response(api_name: str, response) -> APIError:
    """Create appropriate API error from HTTP response"""
    status_code = getattr(response, 'status_code', None)
    response_text = getattr(response, 'text', None) or str(response)
    
    # Map status codes to specific errors
    if status_code == 401:
        return AuthenticationError(api_name)
    elif status_code == 403:
        return PermissionError(api_name)
    elif status_code == 404:
        return NotFoundError(api_name)
    elif status_code == 429:
        # Try to extract retry-after header
        retry_after = None
        if hasattr(response, 'headers'):
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                try:
                    retry_after = int(retry_after)
                except ValueError:
                    retry_after = None
        return RateLimitError(api_name, retry_after)
    else:
        # Generic API error
        message = f"{api_name} API request failed"
        if status_code:
            message += f" with status {status_code}"
        return APIError(message, api_name, status_code, response_text)


# Specific API error factory functions
def create_github_error(response) -> GitHubAPIError:
    """Create GitHub-specific error from response"""
    base_error = create_api_error_from_response("GitHub", response)
    return GitHubAPIError(base_error.message, base_error.status_code, base_error.response_body)


def create_jira_error(response) -> JiraAPIError:
    """Create Jira-specific error from response"""
    base_error = create_api_error_from_response("Jira", response)
    return JiraAPIError(base_error.message, base_error.status_code, base_error.response_body)


def create_confluence_error(response) -> ConfluenceAPIError:
    """Create Confluence-specific error from response"""
    base_error = create_api_error_from_response("Confluence", response)
    return ConfluenceAPIError(base_error.message, base_error.status_code, base_error.response_body)