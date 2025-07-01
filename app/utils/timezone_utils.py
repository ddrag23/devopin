from datetime import datetime, timezone
import pytz
from typing import Optional


def convert_utc_to_user_timezone(utc_datetime: datetime, user_timezone: str) -> datetime:
    """
    Convert UTC datetime to user's timezone
    
    Args:
        utc_datetime: datetime object in UTC
        user_timezone: User's timezone string (e.g., 'Asia/Jakarta', 'America/New_York')
    
    Returns:
        datetime converted to user's timezone
    """
    if not utc_datetime:
        return utc_datetime
    
    # Ensure the datetime is timezone aware and in UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    try:
        user_tz = pytz.timezone(user_timezone)
        return utc_datetime.astimezone(user_tz)
    except pytz.exceptions.UnknownTimeZoneError:
        # Fallback to UTC if timezone is invalid
        return utc_datetime


def convert_user_timezone_to_utc(local_datetime: datetime, user_timezone: str) -> datetime:
    """
    Convert user's local datetime to UTC
    
    Args:
        local_datetime: datetime object in user's timezone
        user_timezone: User's timezone string
    
    Returns:
        datetime converted to UTC
    """
    if not local_datetime:
        return local_datetime
    
    try:
        user_tz = pytz.timezone(user_timezone)
        
        # If datetime is naive, localize it to user's timezone
        if local_datetime.tzinfo is None:
            local_datetime = user_tz.localize(local_datetime)
        
        return local_datetime.astimezone(timezone.utc)
    except pytz.exceptions.UnknownTimeZoneError:
        # Fallback: assume it's already UTC
        if local_datetime.tzinfo is None:
            return local_datetime.replace(tzinfo=timezone.utc)
        return local_datetime


def get_user_timezone_from_session(session_data: dict) -> str:
    """
    Extract user timezone from session data, fallback to UTC
    
    Args:
        session_data: Session data dictionary containing user info
    
    Returns:
        User's timezone string
    """
    return session_data.get('user_timezone', 'UTC') if session_data else 'UTC'


def format_datetime_for_user(utc_datetime: datetime, user_timezone: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format UTC datetime for display in user's timezone
    
    Args:
        utc_datetime: UTC datetime object
        user_timezone: User's timezone string
        format_str: Format string for datetime display
    
    Returns:
        Formatted datetime string in user's timezone
    """
    if not utc_datetime:
        return ""
    
    user_datetime = convert_utc_to_user_timezone(utc_datetime, user_timezone)
    return user_datetime.strftime(format_str)


def get_available_timezones():
    """
    Get list of common timezones for user selection
    
    Returns:
        List of timezone strings
    """
    return [
        'UTC',
        'Asia/Jakarta',
        'Asia/Bangkok',
        'Asia/Singapore',
        'Asia/Kuala_Lumpur',
        'Asia/Manila',
        'Asia/Ho_Chi_Minh',
        'Asia/Tokyo',
        'Asia/Shanghai',
        'Asia/Kolkata',
        'Europe/London',
        'Europe/Paris',
        'Europe/Berlin',
        'America/New_York',
        'America/Los_Angeles',
        'America/Chicago',
        'Australia/Sydney',
        'Australia/Melbourne',
    ]