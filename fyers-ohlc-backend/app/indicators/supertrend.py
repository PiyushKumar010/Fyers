"""
Supertrend Indicator
Trend-following indicator based on ATR
"""
import pandas as pd
import numpy as np
from .atr import calculate_atr


def calculate_supertrend(df: pd.DataFrame, atr_period: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
    """
    Calculate Supertrend indicator.
    
    Args:
        df: DataFrame with columns ['high', 'low', 'close']
        atr_period: Period for ATR calculation (default: 7)
        multiplier: ATR multiplier (default: 3.0)
    
    Returns:
        DataFrame with columns: 'supertrend', 'direction'
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate ATR
    atr = calculate_atr(df, period=atr_period)
    
    # Calculate basic bands
    hl_avg = (high + low) / 2
    upper_band = hl_avg + (multiplier * atr)
    lower_band = hl_avg - (multiplier * atr)
    
    # Initialize arrays
    supertrend = pd.Series(index=df.index, dtype='float64')
    direction = pd.Series(index=df.index, dtype='int64')
    
    # Initialize first values
    supertrend.iloc[0] = upper_band.iloc[0]
    direction.iloc[0] = 1
    
    # Calculate Supertrend
    for i in range(1, len(df)):
        # Update upper and lower bands
        if close.iloc[i-1] > upper_band.iloc[i-1]:
            upper_band.iloc[i] = max(upper_band.iloc[i], upper_band.iloc[i-1])
        else:
            upper_band.iloc[i] = upper_band.iloc[i]
        
        if close.iloc[i-1] < lower_band.iloc[i-1]:
            lower_band.iloc[i] = min(lower_band.iloc[i], lower_band.iloc[i-1])
        else:
            lower_band.iloc[i] = lower_band.iloc[i]
        
        # Determine direction and supertrend
        if close.iloc[i] <= lower_band.iloc[i-1]:
            direction.iloc[i] = -1  # Bearish
            supertrend.iloc[i] = lower_band.iloc[i]
        elif close.iloc[i] >= upper_band.iloc[i-1]:
            direction.iloc[i] = 1  # Bullish
            supertrend.iloc[i] = upper_band.iloc[i]
        else:
            # Continue previous trend
            direction.iloc[i] = direction.iloc[i-1]
            if direction.iloc[i] == 1:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]
    
    result = pd.DataFrame({
        'supertrend': supertrend,
        'direction': direction
    })
    
    return result


def get_supertrend_signal(df: pd.DataFrame, st: pd.DataFrame) -> str:
    """
    Generate signal based on Supertrend.
    
    Args:
        df: Original DataFrame with 'close' column
        st: Supertrend DataFrame with 'supertrend' and 'direction' columns
    
    Returns:
        Signal string: 'BULLISH', 'BEARISH', or 'HOLD'
    """
    if len(df) == 0 or len(st) == 0:
        return 'INSUFFICIENT_DATA'
    
    current_price = df['close'].iloc[-1]
    current_supertrend = st['supertrend'].iloc[-1]
    current_direction = st['direction'].iloc[-1]
    
    if pd.isna(current_price) or pd.isna(current_supertrend):
        return 'INSUFFICIENT_DATA'
    
    if current_direction == 1:
        return 'BULLISH'  # Price above supertrend
    elif current_direction == -1:
        return 'BEARISH'  # Price below supertrend
    else:
        return 'HOLD'

