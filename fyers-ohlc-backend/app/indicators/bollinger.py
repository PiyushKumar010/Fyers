"""
Bollinger Bands Indicator
Volatility bands placed above and below a moving average
"""
import pandas as pd
import numpy as np


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.
    
    Args:
        df: DataFrame with column 'close'
        period: Period for moving average (default: 20)
        std_dev: Standard deviation multiplier (default: 2.0)
    
    Returns:
        DataFrame with columns: 'upper_band', 'middle_band', 'lower_band'
    """
    close = df['close']
    
    # Calculate middle band (SMA)
    middle_band = close.rolling(window=period).mean()
    
    # Calculate standard deviation
    std = close.rolling(window=period).std()
    
    # Calculate upper and lower bands
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    result = pd.DataFrame({
        'upper_band': upper_band,
        'middle_band': middle_band,
        'lower_band': lower_band
    })
    
    return result


def get_bollinger_signal(df: pd.DataFrame, bb: pd.DataFrame, tolerance: float = 0.01) -> str:
    """
    Generate signal based on Bollinger Bands.
    
    Args:
        df: Original DataFrame with 'close' column
        bb: Bollinger Bands DataFrame
        tolerance: Price proximity tolerance to band (default: 0.01 = 1%)
    
    Returns:
        Signal string: 'BUY', 'SELL', or 'HOLD'
    """
    if len(df) == 0 or len(bb) == 0:
        return 'INSUFFICIENT_DATA'
    
    current_price = df['close'].iloc[-1]
    upper_band = bb['upper_band'].iloc[-1]
    lower_band = bb['lower_band'].iloc[-1]
    middle_band = bb['middle_band'].iloc[-1]
    
    if pd.isna(current_price) or pd.isna(upper_band) or pd.isna(lower_band):
        return 'INSUFFICIENT_DATA'
    
    # Check if price touches lower band (potential buy)
    if current_price <= lower_band * (1 + tolerance):
        return 'BUY'
    # Check if price touches upper band (potential sell)
    elif current_price >= upper_band * (1 - tolerance):
        return 'SELL'
    else:
        return 'HOLD'


