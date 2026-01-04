"""
Exponential Moving Average (EMA) Indicator
"""
import pandas as pd
import numpy as np


def calculate_ema(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        df: DataFrame with price data
        period: Period for EMA calculation (default: 14)
        column: Column name to calculate EMA on (default: 'close')
    
    Returns:
        Series with EMA values
    """
    return df[column].ewm(span=period, adjust=False).mean()


def calculate_multiple_emas(df: pd.DataFrame, periods: list = [9, 21, 50, 200]) -> pd.DataFrame:
    """
    Calculate multiple EMAs for different periods.
    
    Args:
        df: DataFrame with OHLC data
        periods: List of periods for EMA calculation
    
    Returns:
        DataFrame with multiple EMA columns
    """
    result = pd.DataFrame(index=df.index)
    
    for period in periods:
        result[f'ema_{period}'] = calculate_ema(df, period)
    
    return result


def get_ema_signal(df: pd.DataFrame, fast_period: int = 9, slow_period: int = 21) -> str:
    """
    Generate trading signal based on EMA crossover.
    
    Args:
        df: DataFrame with OHLC data
        fast_period: Fast EMA period
        slow_period: Slow EMA period
    
    Returns:
        Signal string: 'BUY', 'SELL', or 'NEUTRAL'
    """
    if len(df) < slow_period + 1:
        return 'NEUTRAL'
    
    fast_ema = calculate_ema(df, fast_period)
    slow_ema = calculate_ema(df, slow_period)
    
    # Check for crossover
    if len(fast_ema) < 2 or len(slow_ema) < 2:
        return 'NEUTRAL'
    
    # Bullish crossover: fast crosses above slow
    if fast_ema.iloc[-2] <= slow_ema.iloc[-2] and fast_ema.iloc[-1] > slow_ema.iloc[-1]:
        return 'BUY'
    # Bearish crossover: fast crosses below slow
    elif fast_ema.iloc[-2] >= slow_ema.iloc[-2] and fast_ema.iloc[-1] < slow_ema.iloc[-1]:
        return 'SELL'
    else:
        return 'NEUTRAL'
