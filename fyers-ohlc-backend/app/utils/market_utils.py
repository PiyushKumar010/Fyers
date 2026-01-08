"""
Utility functions for market status, trading days, and holidays
"""
from datetime import datetime, timedelta, timezone
from typing import Tuple

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


# Indian Stock Market holidays for 2026 (NSE)
MARKET_HOLIDAYS_2026 = [
    "2026-01-26",  # Republic Day
    "2026-03-03",  # Maha Shivaratri
    "2026-03-25",  # Holi
    "2026-03-30",  # Ram Navami
    "2026-04-02",  # Mahavir Jayanti
    "2026-04-03",  # Good Friday
    "2026-04-06",  # Gudi Padwa (Maharashtra Day)
    "2026-04-14",  # Dr. Ambedkar Jayanti
    "2026-05-01",  # Maharashtra Day
    "2026-05-26",  # Buddha Purnima
    "2026-08-15",  # Independence Day
    "2026-08-19",  # Parsi New Year
    "2026-09-02",  # Ganesh Chaturthi
    "2026-10-02",  # Gandhi Jayanti
    "2026-10-20",  # Dussehra
    "2026-10-28",  # Diwali-Laxmi Pujan
    "2026-10-29",  # Diwali-Balipratipada
    "2026-11-05",  # Guru Nanak Jayanti
    "2026-12-25",  # Christmas
]

# Convert to datetime objects for easier comparison
HOLIDAYS = set([datetime.strptime(d, "%Y-%m-%d").date() for d in MARKET_HOLIDAYS_2026])


def is_weekend(date: datetime) -> bool:
    """Check if date is Saturday (5) or Sunday (6)"""
    return date.weekday() in [5, 6]


def is_holiday(date: datetime) -> bool:
    """Check if date is a market holiday"""
    return date.date() in HOLIDAYS


def is_market_open(date: datetime = None) -> Tuple[bool, str]:
    """
    Check if the market is open on a given date and time.
    
    Args:
        date: datetime object (defaults to current time in IST)
    
    Returns:
        Tuple of (is_open: bool, reason: str)
    """
    if date is None:
        # Get current time in IST - use UTC first then convert to IST
        # This ensures consistent behavior across different server timezones
        utc_now = datetime.now(timezone.utc)
        date = utc_now.astimezone(IST)
    elif date.tzinfo is None:
        # If naive datetime provided, assume it's IST
        date = date.replace(tzinfo=IST)
    else:
        # Convert to IST if it's in a different timezone
        date = date.astimezone(IST)
    
    # Check if weekend
    if is_weekend(date):
        day_name = date.strftime("%A")
        return False, f"Weekend ({day_name})"
    
    # Check if holiday
    if is_holiday(date):
        return False, "Market Holiday"
    
    # If checking a date with time at midnight (00:00:00), it's a date-only check
    # In this case, we only care if it's a valid trading day, not the time
    if date.hour == 0 and date.minute == 0 and date.second == 0:
        return True, "Trading Day"
    
    # Check market hours (9:15 AM to 3:30 PM IST)
    hour = date.hour
    minute = date.minute
    
    # Before market opens (before 9:15 AM)
    if hour < 9 or (hour == 9 and minute < 15):
        return False, "Market Not Yet Open"
    
    # After market closes (after 3:30 PM)
    if hour > 15 or (hour == 15 and minute > 30):
        return False, "Market Closed for the Day"
    
    # Market is open
    return True, "Market Open"


def get_last_trading_day(from_date: datetime = None, max_lookback_days: int = 10) -> datetime:
    """
    Get the last trading day (not weekend/holiday) from a given date.
    
    Args:
        from_date: Starting date (defaults to today)
        max_lookback_days: Maximum days to look back
    
    Returns:
        datetime object of the last trading day
    """
    if from_date is None:
        from_date = datetime.now()
    
    current_date = from_date
    
    for _ in range(max_lookback_days):
        is_open, reason = is_market_open(current_date)
        if is_open:
            return current_date
        current_date = current_date - timedelta(days=1)
    
    # If no trading day found in lookback period, return the from_date
    return from_date


def get_market_status() -> dict:
    """
    Get comprehensive market status information.
    
    Returns:
        Dictionary with market status details
    """
    # Get current time in IST - always use UTC first then convert
    # This ensures consistent behavior across different deployment environments
    utc_now = datetime.now(timezone.utc)
    now = utc_now.astimezone(IST)
    is_open, reason = is_market_open(now)
    last_trading_day = get_last_trading_day(now)
    
    return {
        "is_open": is_open,
        "status": "open" if is_open else "closed",
        "reason": reason,
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M:%S"),
        "current_day": now.strftime("%A"),
        "last_trading_day": last_trading_day.strftime("%Y-%m-%d"),
        "next_check": "Market status updated",
        "timezone": "IST (UTC+5:30)",
        "utc_time": utc_now.strftime("%H:%M:%S")
    }


def adjust_date_for_market(date_str: str) -> str:
    """
    Adjust a date string to the last trading day if the date is non-trading.
    
    Args:
        date_str: Date in YYYY-MM-DD format
    
    Returns:
        Adjusted date string in YYYY-MM-DD format
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        is_open, _ = is_market_open(date)
        
        if not is_open:
            # Get last trading day
            adjusted_date = get_last_trading_day(date)
            return adjusted_date.strftime("%Y-%m-%d")
        
        return date_str
    except Exception:
        return date_str
