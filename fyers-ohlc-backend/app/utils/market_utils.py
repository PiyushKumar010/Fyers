"""
Utility functions for market status, trading days, and holidays
"""
from datetime import datetime, timedelta
from typing import Tuple


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
    Check if the market is open on a given date.
    
    Args:
        date: datetime object (defaults to today)
    
    Returns:
        Tuple of (is_open: bool, reason: str)
    """
    if date is None:
        date = datetime.now()
    
    # Check if weekend
    if is_weekend(date):
        day_name = date.strftime("%A")
        return False, f"Weekend ({day_name})"
    
    # Check if holiday
    if is_holiday(date):
        return False, "Market Holiday"
    
    # Check market hours (9:15 AM to 3:30 PM IST)
    # For simplicity, we'll just check if it's a trading day
    # You can add time-based checks here if needed
    
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
    now = datetime.now()
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
        "next_check": "Market status updated"
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
