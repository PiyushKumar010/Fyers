"""
Average Directional Index (ADX) Indicator
Measures trend strength without regard to direction
"""
import pandas as pd
import numpy as np


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average Directional Index (ADX).
    
    Args:
        df: DataFrame with columns ['open', 'high', 'low', 'close']
        period: Period for ADX calculation (default: 14)
    
    Returns:
        Series with ADX values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate Directional Movement
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    # Calculate Directional Indicators
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    # Calculate DX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    
    # Calculate ADX
    adx = dx.rolling(window=period).mean()
    
    return adx


def get_adx_signal(adx: pd.Series, threshold_strong: float = 25, threshold_weak: float = 20) -> str:
    """
    Generate signal based on ADX value.
    
    Args:
        adx: ADX Series
        threshold_strong: ADX value above which trend is strong (default: 25)
        threshold_weak: ADX value below which trend is weak (default: 20)
    
    Returns:
        Signal string: 'STRONG_TREND', 'WEAK_TREND', or 'SIDEWAYS'
    """
    if pd.isna(adx.iloc[-1]):
        return 'INSUFFICIENT_DATA'
    
    current_adx = adx.iloc[-1]
    
    if current_adx > threshold_strong:
        return 'STRONG_TREND'
    elif current_adx < threshold_weak:
        return 'WEAK_TREND'
    else:
        return 'SIDEWAYS'


