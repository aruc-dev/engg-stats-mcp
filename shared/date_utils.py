"""Date utilities for MCP servers"""
from datetime import datetime, timedelta
from typing import Optional
try:
    from dateutil.parser import parse as parse_date
except ImportError:
    # Fallback to basic datetime parsing if dateutil is not available
    def parse_date(date_str: str) -> datetime:
        """Basic ISO date parsing fallback"""
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))


def parse_iso_date(date_str: str) -> datetime:
    """Parse ISO date string to datetime object"""
    try:
        return parse_date(date_str)
    except Exception as e:
        raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD format.") from e


def calculate_hours_between(start_dt: datetime, end_dt: datetime) -> float:
    """Calculate hours between two datetime objects"""
    delta = end_dt - start_dt
    return delta.total_seconds() / 3600


def format_iso_date(dt: datetime) -> str:
    """Format datetime as ISO date string"""
    return dt.strftime("%Y-%m-%d")


def get_date_range_query_string(from_date: str, to_date: str, field_name: str = "created") -> str:
    """Generate date range query string for various APIs"""
    from_dt = parse_iso_date(from_date)
    to_dt = parse_iso_date(to_date)
    
    # Add one day to 'to' date to make it inclusive
    to_dt_inclusive = to_dt + timedelta(days=1)
    
    return f"{field_name}:{from_dt.strftime('%Y-%m-%d')}..{to_dt_inclusive.strftime('%Y-%m-%d')}"