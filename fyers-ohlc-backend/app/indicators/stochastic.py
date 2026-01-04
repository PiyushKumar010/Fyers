"""
Stochastic Oscillator Indicator
%K and %D lines for momentum analysis
"""
import pandas as pd
import numpy as np


def calculate_stochastic(df: pd.DataFrame, period: int = 14, k_smooth: int = 3, d_smooth: int = 3) -> pd.DataFrame:
    """
    Calculate Stochastic Oscillator (%K and %D).
    
    Args:
        df: DataFrame with OHLC data
        period: Lookback period for stochastic calculation (default: 14)
        k_smooth: Smoothing period for %K (default: 3)
        d_smooth: Smoothing period for %D (default: 3)
    
    Returns:
        DataFrame with 'stoch_k' and 'stoch_d' columns
    """
    result = pd.DataFrame(index=df.index)
    
    # Calculate raw %K
    lowest_low = df['low'].rolling(window=period).min()
    highest_high = df['high'].rolling(window=period).max()
    
    result['stoch_k_raw'] = 100 * (df['close'] - lowest_low) / (highest_high - lowest_low)
    
    # Smooth %K
    result['stoch_k'] = result['stoch_k_raw'].rolling(window=k_smooth).mean()
    
    # Calculate %D (moving average of %K)
    result['stoch_d'] = result['stoch_k'].rolling(window=d_smooth).mean()
    
    return result[['stoch_k', 'stoch_d']]


def get_stochastic_signal(df: pd.DataFrame, period: int = 14, oversold: int = 20, overbought: int = 80) -> str:
    """
    Generate trading signal based on Stochastic Oscillator.
    
    Signals:
    - BUY: %K crosses above %D in oversold region
    - SELL: %K crosses below %D in overbought region
    - NEUTRAL: No clear signal
    
    Args:
        df: DataFrame with stochastic data
        period: Period for calculation
        oversold: Oversold threshold (default: 20)
        overbought: Overbought threshold (default: 80)
    
    Returns:
        Signal string: 'BUY', 'SELL', or 'NEUTRAL'
    """
    if len(df) < 2:
        return 'NEUTRAL'
    
    stoch_data = calculate_stochastic(df, period)
    
    if stoch_data.empty or len(stoch_data) < 2:
        return 'NEUTRAL'
    
    # Get current and previous values
    k_current = stoch_data['stoch_k'].iloc[-1]
    k_previous = stoch_data['stoch_k'].iloc[-2]
    d_current = stoch_data['stoch_d'].iloc[-1]
    d_previous = stoch_data['stoch_d'].iloc[-2]
    
    # Check for crossovers
    bullish_crossover = k_previous < d_previous and k_current > d_current
    bearish_crossover = k_previous > d_previous and k_current < d_current
    
    # Generate signals
    if bullish_crossover and k_current < oversold:
        return 'BUY'
    elif bearish_crossover and k_current > overbought:
        return 'SELL'
    else:
        return 'NEUTRAL'
