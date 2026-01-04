from app import database
from datetime import datetime, timedelta
from app.config import settings


def get_cached_ohlc(symbol, resolution, from_date, to_date):
    """
    Retrieve cached OHLC data from MongoDB.
    Converts date strings to datetime objects for proper comparison.
    """
    ohlc_collection = database.ohlc_collection
    if ohlc_collection is None:
        return None

    try:
        # Convert date strings to datetime objects for proper comparison
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        # Set to end of day for to_date to include all data for that day
        to_dt = to_dt.replace(hour=23, minute=59, second=59)

        cursor = ohlc_collection.find(
            {
                "symbol": symbol,
                "resolution": resolution,
                "time": {
                    "$gte": from_date,
                    "$lte": to_date
                }
            },
            {"_id": 0}
        ).sort("time", 1)

        data = list(cursor)
        
        # If we have data, check if it covers the full range
        if data:
            # Convert time strings to datetime for comparison
            first_time = datetime.strptime(data[0]["time"], "%Y-%m-%d %H:%M")
            last_time = datetime.strptime(data[-1]["time"], "%Y-%m-%d %H:%M")
            
            # If cached data doesn't cover the full range, return None to fetch fresh data
            if first_time > from_dt or last_time < to_dt:
                return None
                
        return data if data else None
    except Exception as e:
        print(f"Error retrieving cached OHLC: {e}")
        return None


def save_ohlc(symbol, resolution, candles, force_save=False):
    """
    Save OHLC data to MongoDB with duplicate prevention.
    Uses upsert to avoid duplicate entries.
    
    Args:
        symbol: Stock symbol
        resolution: Timeframe resolution
        candles: List of candle data
        force_save: If True, saves regardless of live data settings (default: False)
    """
    ohlc_collection = database.ohlc_collection
    if ohlc_collection is None:
        return

    if not candles:
        return
    
    # Check if we should skip saving live data
    if not force_save and settings.DISABLE_LIVE_DATA_STORAGE:
        # Check if this is recent/live data
        try:
            # Get the timestamp of the most recent candle
            if candles:
                # Try to parse the time from the last candle
                last_candle_time = None
                if isinstance(candles[-1], dict) and 'time' in candles[-1]:
                    try:
                        # Try parsing as datetime string
                        last_candle_time = datetime.strptime(candles[-1]['time'], "%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        try:
                            # Try parsing as timestamp
                            last_candle_time = datetime.fromtimestamp(candles[-1]['time'])
                        except (ValueError, TypeError, OSError):
                            pass
                
                if last_candle_time:
                    # Calculate the threshold for "live" data
                    threshold_date = datetime.now() - timedelta(days=settings.LIVE_DATA_THRESHOLD_DAYS)
                    
                    # If data is recent (within threshold), don't save it
                    if last_candle_time >= threshold_date:
                        print(f"⏭️  Skipping save for live data: {symbol} (data from {last_candle_time})")
                        return
        except Exception as e:
            print(f"⚠️  Warning: Could not check if data is live: {e}. Saving anyway.")
            # If we can't determine, err on the side of saving

    try:
        # Use bulk_write with update_one and upsert=True to prevent duplicates
        from pymongo import UpdateOne
        
        operations = []
        for c in candles:
            operations.append(
                UpdateOne(
                    {
                        "symbol": symbol,
                        "resolution": resolution,
                        "time": c["time"]
                    },
                    {
                        "$set": {
                            "symbol": symbol,
                            "resolution": resolution,
                            **c
                        }
                    },
                    upsert=True
                )
            )

        if operations:
            ohlc_collection.bulk_write(operations, ordered=False)
            print(f"✅ Saved {len(operations)} OHLC records for {symbol}")
    except Exception as e:
        print(f"❌ Failed to save OHLC to DB: {e}")
