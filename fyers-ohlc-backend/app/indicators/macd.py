"""
MACD (Moving Average Convergence Divergence) Indicator
Trend-following momentum indicator
"""
import pandas as pd
import numpy as np


def calculate_macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    """
    Calculate MACD indicator.
    
    Args:
        df: DataFrame with column 'close'
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)
    
    Returns:
        DataFrame with columns: 'macd', 'signal', 'histogram'
    """
    close = df['close']
    
    # Calculate EMAs
    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()
    
    # Calculate MACD line
    macd = ema_fast - ema_slow
    
    # Calculate signal line
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    
    # Calculate histogram
    histogram = macd - signal
    
    result = pd.DataFrame({
        'macd': macd,
        'signal': signal,
        'histogram': histogram
    })
    
    return result


def get_macd_signal(macd_df: pd.DataFrame) -> str:
    """
    Generate signal based on MACD crossover.
    
    Args:
        macd_df: MACD DataFrame with 'macd' and 'signal' columns
    
    Returns:
        Signal string: 'BUY', 'SELL', or 'HOLD'
    """
    if len(macd_df) < 2:
        return 'INSUFFICIENT_DATA'
    
    macd = macd_df['macd']
    signal = macd_df['signal']
    
    current_macd = macd.iloc[-1]
    current_signal = signal.iloc[-1]
    prev_macd = macd.iloc[-2]
    prev_signal = signal.iloc[-2]
    
    if pd.isna(current_macd) or pd.isna(current_signal):
        return 'INSUFFICIENT_DATA'
    
    # Bullish crossover: MACD crosses above signal
    if prev_macd <= prev_signal and current_macd > current_signal:
        return 'BUY'
    # Bearish crossover: MACD crosses below signal
    elif prev_macd >= prev_signal and current_macd < current_signal:
        return 'SELL'
    else:
        return 'HOLD'


