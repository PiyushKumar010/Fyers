from fastapi import APIRouter
from app import database
from datetime import datetime

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/mongo-test")
def mongo_test():
    if database.ohlc_collection is None:
        return {"mongo": "disconnected"}

    database.ohlc_collection.insert_one({"test": "connected"})
    return {"mongo": "connected"}


@router.get("/market/status")
def market_status():
    """
    Check if NSE market is currently open.
    Market hours: 9:15 AM to 3:30 PM IST, Monday to Friday
    """
    now = datetime.now()
    day = now.weekday()  # 0 = Monday, 6 = Sunday
    hour = now.hour
    minute = now.minute

    # Market is closed on weekends
    if day >= 5:  # Saturday (5) or Sunday (6)
        return {
            "is_open": False,
            "message": "Market is closed (Weekend)",
            "next_open": "Monday 9:15 AM IST"
        }

    # NSE market hours: 9:15 AM to 3:30 PM IST
    market_open_hour = 9
    market_open_minute = 15
    market_close_hour = 15
    market_close_minute = 30

    # Check if current time is within market hours
    if hour < market_open_hour or (hour == market_open_hour and minute < market_open_minute):
        return {
            "is_open": False,
            "message": "Market is closed",
            "next_open": f"Today at {market_open_hour}:{market_open_minute:02d} AM IST"
        }

    if hour > market_close_hour or (hour == market_close_hour and minute > market_close_minute):
        return {
            "is_open": False,
            "message": "Market is closed",
            "next_open": "Tomorrow 9:15 AM IST" if day < 4 else "Monday 9:15 AM IST"
        }

    return {
        "is_open": True,
        "message": "Market is open",
        "closes_at": f"{market_close_hour}:{market_close_minute:02d} PM IST"
    }