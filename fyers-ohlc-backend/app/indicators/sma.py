"""
Simple Moving Average (SMA) Indicator
"""
import pandas as pd
import numpy as np


def calculate_sma(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    """
    Calculate Simple Moving Average.
    
    Args:
        df: DataFrame with price data
        period: Period for SMA calculation (default: 14)
        column: Column name to calculate SMA on (default: 'close')
    
    Returns:
        Series with SMA values
    """
    return df[column].rolling(window=period).mean()


def calculate_multiple_smas(df: pd.DataFrame, periods: list = [10, 20, 50, 200]) -> pd.DataFrame:
    """
    Calculate multiple SMAs for different periods.
    
    Args:
        df: DataFrame with OHLC data
        periods: List of periods for SMA calculation
    
    Returns:
        DataFrame with multiple SMA columns
    """
    result = pd.DataFrame(index=df.index)
    
    for period in periods:
        result[f'sma_{period}'] = calculate_sma(df, period)
    
    return result


def get_sma_signal(df: pd.DataFrame, fast_period: int = 10, slow_period: int = 20) -> str:
    """
    Generate trading signal based on SMA crossover.
    
    Args:
        df: DataFrame with OHLC data
        fast_period: Fast SMA period
        slow_period: Slow SMA period
    
    Returns:
        Signal string: 'BUY', 'SELL', or 'NEUTRAL'
    """
    if len(df) < slow_period + 1:
        return 'NEUTRAL'
    
    fast_sma = calculate_sma(df, fast_period)
    slow_sma = calculate_sma(df, slow_period)
    
    # Check for crossover
    if len(fast_sma) < 2 or len(slow_sma) < 2:
        return 'NEUTRAL'
    
    # Bullish crossover: fast crosses above slow
    if fast_sma.iloc[-2] <= slow_sma.iloc[-2] and fast_sma.iloc[-1] > slow_sma.iloc[-1]:
        return 'BUY'
    # Bearish crossover: fast crosses below slow
    elif fast_sma.iloc[-2] >= slow_sma.iloc[-2] and fast_sma.iloc[-1] < slow_sma.iloc[-1]:
        return 'SELL'
    else:
        return 'NEUTRAL'


def calculate_wma(df: pd.DataFrame, period: int = 10, column: str = 'close') -> pd.Series:
    """
    Calculate Weighted Moving Average.
    
    Args:
        df: DataFrame with price data
        period: Period for WMA calculation
        column: Column name to calculate WMA on
    
    Returns:
        Series with WMA values
    """
    weights = np.arange(1, period + 1)
    
    def weighted_average(values):
        if len(values) < period:
            return np.nan
        return np.dot(values, weights) / weights.sum()
    
    return df[column].rolling(window=period).apply(weighted_average, raw=True)
