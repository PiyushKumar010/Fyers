"""
RSI (Relative Strength Index) Indicator
Momentum oscillator measuring speed and magnitude of price changes
"""
import pandas as pd
import numpy as np


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        df: DataFrame with column 'close'
        period: Period for RSI calculation (default: 14)
    
    Returns:
        Series with RSI values (0-100)
    """
    close = df['close']
    
    # Calculate price changes
    delta = close.diff()
    
    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def get_rsi_signal(rsi: pd.Series, oversold: float = 30, overbought: float = 70) -> str:
    """
    Generate signal based on RSI levels.
    
    Args:
        rsi: RSI Series
        oversold: RSI level below which market is oversold (default: 30)
        overbought: RSI level above which market is overbought (default: 70)
    
    Returns:
        Signal string: 'OVERSOLD', 'OVERBOUGHT', or 'NEUTRAL'
    """
    if pd.isna(rsi.iloc[-1]):
        return 'INSUFFICIENT_DATA'
    
    current_rsi = rsi.iloc[-1]
    
    if current_rsi < oversold:
        return 'OVERSOLD'  # Potential buy signal
    elif current_rsi > overbought:
        return 'OVERBOUGHT'  # Potential sell signal
    else:
        return 'NEUTRAL'


