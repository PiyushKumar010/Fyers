"""
Average True Range (ATR) Indicator
Measures market volatility
"""
import pandas as pd
import numpy as np


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Args:
        df: DataFrame with columns ['high', 'low', 'close']
        period: Period for ATR calculation (default: 14)
    
    Returns:
        Series with ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR as moving average of TR
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_stop_loss(close: pd.Series, atr: pd.Series, multiplier: float = 2.0, side: str = 'long') -> pd.Series:
    """
    Calculate stop loss using ATR.
    
    Args:
        close: Close price Series
        atr: ATR Series
        multiplier: ATR multiplier for stop loss (default: 2.0)
        side: 'long' or 'short' (default: 'long')
    
    Returns:
        Series with stop loss values
    """
    if side.lower() == 'long':
        stop_loss = close - (atr * multiplier)
    else:
        stop_loss = close + (atr * multiplier)
    
    return stop_loss


