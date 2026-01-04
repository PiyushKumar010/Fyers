"""
Renko Chart Indicator
Price movement-based charting method
"""
import pandas as pd
import numpy as np
from .atr import calculate_atr


def calculate_renko(df: pd.DataFrame, brick_size: float = None, atr_period: int = 14, atr_multiplier: float = 1.0) -> pd.DataFrame:
    """
    Calculate Renko chart data.
    
    Args:
        df: DataFrame with columns ['open', 'high', 'low', 'close']
        brick_size: Fixed brick size (if None, uses ATR-based)
        atr_period: Period for ATR if brick_size is None (default: 14)
        atr_multiplier: ATR multiplier if brick_size is None (default: 1.0)
    
    Returns:
        DataFrame with Renko bricks: 'brick_price', 'brick_type', 'trend'
    """
    close = df['close']
    
    # Determine brick size
    if brick_size is None:
        atr = calculate_atr(df, period=atr_period)
        brick_size = atr.iloc[-1] * atr_multiplier
        if pd.isna(brick_size) or brick_size == 0:
            brick_size = close.iloc[-1] * 0.01  # Fallback to 1% of price
    
    # Initialize Renko data
    renko_data = []
    current_brick = None
    trend = None  # 1 for up, -1 for down
    
    for i in range(len(df)):
        price = close.iloc[i]
        
        if current_brick is None:
            # First brick - round to nearest brick
            current_brick = round(price / brick_size) * brick_size
            trend = 1
            renko_data.append({
                'brick_price': current_brick,
                'brick_type': 'up',
                'trend': trend
            })
        else:
            # Check if price moved enough for new brick
            if trend == 1:  # Uptrend
                if price >= current_brick + brick_size:
                    # New up bricks
                    while price >= current_brick + brick_size:
                        current_brick += brick_size
                        renko_data.append({
                            'brick_price': current_brick,
                            'brick_type': 'up',
                            'trend': 1
                        })
                elif price <= current_brick - brick_size:
                    # Reversal: new down brick
                    current_brick -= brick_size
                    trend = -1
                    renko_data.append({
                        'brick_price': current_brick,
                        'brick_type': 'down',
                        'trend': -1
                    })
            else:  # Downtrend
                if price <= current_brick - brick_size:
                    # New down bricks
                    while price <= current_brick - brick_size:
                        current_brick -= brick_size
                        renko_data.append({
                            'brick_price': current_brick,
                            'brick_type': 'down',
                            'trend': -1
                        })
                elif price >= current_brick + brick_size:
                    # Reversal: new up brick
                    current_brick += brick_size
                    trend = 1
                    renko_data.append({
                        'brick_price': current_brick,
                        'brick_type': 'up',
                        'trend': 1
                    })
    
    renko_df = pd.DataFrame(renko_data)
    if len(renko_df) > 0:
        # Create index based on number of bricks
        renko_df.index = pd.RangeIndex(start=0, stop=len(renko_df))
    
    return renko_df


def get_renko_signal(renko_df: pd.DataFrame, lookback: int = 3) -> str:
    """
    Generate signal based on Renko trend.
    
    Args:
        renko_df: Renko DataFrame
        lookback: Number of recent bricks to analyze (default: 3)
    
    Returns:
        Signal string: 'BULLISH', 'BEARISH', or 'HOLD'
    """
    if len(renko_df) < lookback:
        return 'INSUFFICIENT_DATA'
    
    recent_bricks = renko_df.tail(lookback)
    recent_trends = recent_bricks['trend'].values
    
    # Check for consistent trend
    if all(t == 1 for t in recent_trends):
        return 'BULLISH'
    elif all(t == -1 for t in recent_trends):
        return 'BEARISH'
    else:
        return 'HOLD'

