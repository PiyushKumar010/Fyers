"""
Data Service for fetching and processing OHLC data from FYERS
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from app.services.fyers import fetch_ohlc, normalize_symbol


def fetch_ohlc_data(
    symbol: str,
    timeframe: str = "5",
    lookback_days: int = 30,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch OHLC data from FYERS and convert to pandas DataFrame.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE' or 'NSE:RELIANCE-EQ')
        timeframe: Timeframe in minutes or 'D' for daily (default: '5')
        lookback_days: Number of days to look back if dates not provided (default: 30)
        from_date: Start date in YYYY-MM-DD format (optional)
        to_date: End date in YYYY-MM-DD format (optional)
    
    Returns:
        DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume']
    """
    # Normalize symbol
    normalized_symbol = normalize_symbol(symbol)
    
    # Calculate dates if not provided
    if not from_date or not to_date:
        to_date_obj = datetime.now()
        from_date_obj = to_date_obj - timedelta(days=lookback_days)
        from_date = from_date_obj.strftime("%Y-%m-%d")
        to_date = to_date_obj.strftime("%Y-%m-%d")
    
    # Fetch data from FYERS
    candles = fetch_ohlc(normalized_symbol, timeframe, from_date, to_date)
    
    if not candles:
        return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    # Convert to DataFrame
    df = pd.DataFrame(candles)
    
    # Convert time string to datetime
    df['date'] = pd.to_datetime(df['time'])
    
    # Rename and reorder columns
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
    
    # Ensure numeric types
    df['open'] = pd.to_numeric(df['open'], errors='coerce')
    df['high'] = pd.to_numeric(df['high'], errors='coerce')
    df['low'] = pd.to_numeric(df['low'], errors='coerce')
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    
    # Set date as index
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    
    # Remove any NaN rows
    df.dropna(inplace=True)
    
    return df


def validate_ohlc_data(df: pd.DataFrame) -> bool:
    """
    Validate OHLC DataFrame structure.
    
    Args:
        df: DataFrame to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    
    if df.empty:
        return False
    
    if not all(col in df.columns for col in required_columns):
        return False
    
    if len(df) < 2:
        return False
    
    return True


