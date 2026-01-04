"""
Pivot Points Calculation
Support and Resistance levels based on pivot points
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple


def calculate_pivot_points(df: pd.DataFrame, method: str = 'standard') -> Dict[str, float]:
    """
    Calculate pivot points and support/resistance levels.
    
    Args:
        df: DataFrame with OHLC data
        method: Calculation method - 'standard', 'fibonacci', 'woodie', 'camarilla'
    
    Returns:
        Dictionary with pivot, support (S1-S3), and resistance (R1-R3) levels
    """
    if len(df) < 2:
        return {}
    
    # Use the previous day's data (second last candle)
    high = df['high'].iloc[-2]
    low = df['low'].iloc[-2]
    close = df['close'].iloc[-2]
    
    if method == 'standard':
        return _standard_pivot(high, low, close)
    elif method == 'fibonacci':
        return _fibonacci_pivot(high, low, close)
    elif method == 'woodie':
        open_price = df['open'].iloc[-2]
        return _woodie_pivot(high, low, close, open_price)
    elif method == 'camarilla':
        return _camarilla_pivot(high, low, close)
    else:
        return _standard_pivot(high, low, close)


def _standard_pivot(high: float, low: float, close: float) -> Dict[str, float]:
    """Standard Pivot Point calculation."""
    pivot = round((high + low + close) / 3, 2)
    r1 = round(2 * pivot - low, 2)
    r2 = round(pivot + (high - low), 2)
    r3 = round(high + 2 * (pivot - low), 2)
    s1 = round(2 * pivot - high, 2)
    s2 = round(pivot - (high - low), 2)
    s3 = round(low - 2 * (high - pivot), 2)
    
    return {
        'pivot': pivot,
        'r1': r1, 'r2': r2, 'r3': r3,
        's1': s1, 's2': s2, 's3': s3
    }


def _fibonacci_pivot(high: float, low: float, close: float) -> Dict[str, float]:
    """Fibonacci Pivot Point calculation."""
    pivot = round((high + low + close) / 3, 2)
    range_val = high - low
    
    r1 = round(pivot + 0.382 * range_val, 2)
    r2 = round(pivot + 0.618 * range_val, 2)
    r3 = round(pivot + range_val, 2)
    s1 = round(pivot - 0.382 * range_val, 2)
    s2 = round(pivot - 0.618 * range_val, 2)
    s3 = round(pivot - range_val, 2)
    
    return {
        'pivot': pivot,
        'r1': r1, 'r2': r2, 'r3': r3,
        's1': s1, 's2': s2, 's3': s3
    }


def _woodie_pivot(high: float, low: float, close: float, open_price: float) -> Dict[str, float]:
    """Woodie's Pivot Point calculation."""
    pivot = round((high + low + 2 * close) / 4, 2)
    r1 = round(2 * pivot - low, 2)
    r2 = round(pivot + high - low, 2)
    s1 = round(2 * pivot - high, 2)
    s2 = round(pivot - high + low, 2)
    
    return {
        'pivot': pivot,
        'r1': r1, 'r2': r2,
        's1': s1, 's2': s2
    }


def _camarilla_pivot(high: float, low: float, close: float) -> Dict[str, float]:
    """Camarilla Pivot Point calculation."""
    range_val = high - low
    
    r1 = round(close + 1.1 * range_val / 12, 2)
    r2 = round(close + 1.1 * range_val / 6, 2)
    r3 = round(close + 1.1 * range_val / 4, 2)
    r4 = round(close + 1.1 * range_val / 2, 2)
    
    s1 = round(close - 1.1 * range_val / 12, 2)
    s2 = round(close - 1.1 * range_val / 6, 2)
    s3 = round(close - 1.1 * range_val / 4, 2)
    s4 = round(close - 1.1 * range_val / 2, 2)
    
    return {
        'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4,
        's1': s1, 's2': s2, 's3': s3, 's4': s4,
        'pivot': close
    }


def get_nearest_support_resistance(df: pd.DataFrame, current_price: float, method: str = 'standard') -> Tuple[float, float]:
    """
    Get the nearest support and resistance levels based on pivot points.
    
    Args:
        df: DataFrame with OHLC data
        current_price: Current price level
        method: Pivot calculation method
    
    Returns:
        Tuple of (nearest_support, nearest_resistance)
    """
    pivots = calculate_pivot_points(df, method)
    
    if not pivots:
        return (None, None)
    
    # Extract all levels
    levels = []
    for key, value in pivots.items():
        if key != 'pivot':
            levels.append(value)
        else:
            levels.append(value)
    
    levels.sort()
    
    # Find nearest support and resistance
    resistance = None
    support = None
    
    for level in levels:
        if level > current_price and resistance is None:
            resistance = level
        if level < current_price:
            support = level
    
    return (support, resistance)


def get_pivot_signal(df: pd.DataFrame, method: str = 'standard') -> str:
    """
    Generate trading signal based on pivot points.
    
    Args:
        df: DataFrame with OHLC data
        method: Pivot calculation method
    
    Returns:
        Signal string: 'BUY', 'SELL', or 'NEUTRAL'
    """
    if len(df) < 2:
        return 'NEUTRAL'
    
    pivots = calculate_pivot_points(df, method)
    current_price = df['close'].iloc[-1]
    
    if not pivots:
        return 'NEUTRAL'
    
    pivot = pivots['pivot']
    
    # Simple strategy: Buy if above pivot, sell if below
    if current_price > pivot and current_price > pivots['s1']:
        return 'BUY'
    elif current_price < pivot and current_price < pivots['r1']:
        return 'SELL'
    else:
        return 'NEUTRAL'
