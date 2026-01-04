import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List, Optional
# Use pandas to compute ATR instead of relying on external talib

def detect_doji(ohlc_df: pd.DataFrame, threshold: float = 0.1) -> pd.Series:
    """
    Detect Doji candlestick pattern.
    A Doji has a very small body relative to the total range.
    
    Args:
        ohlc_df: DataFrame with OHLC data
        threshold: Maximum body to range ratio to be considered a Doji (default: 0.1)
        
    Returns:
        pd.Series: Boolean series indicating Doji pattern
    """
    body_size = np.abs(ohlc_df['close'] - ohlc_df['open'])
    total_range = ohlc_df['high'] - ohlc_df['low']
    is_doji = (body_size / (total_range + 1e-8)) < threshold
    return is_doji

def detect_hammer(ohlc_df: pd.DataFrame, body_threshold: float = 0.3, lower_wick_ratio: float = 2.0) -> pd.Series:
    """
    Detect Hammer candlestick pattern (bullish reversal).
    
    Args:
        ohlc_df: DataFrame with OHLC data
        body_threshold: Maximum body to total range ratio (default: 0.3)
        lower_wick_ratio: Minimum lower wick to body ratio (default: 2.0)
        
    Returns:
        pd.Series: Boolean series indicating Hammer pattern
    """
    body_size = np.abs(ohlc_df['close'] - ohlc_df['open'])
    total_range = ohlc_df['high'] - ohlc_df['low']
    
    # Calculate wick sizes
    upper_wick = ohlc_df['high'] - ohlc_df[['open', 'close']].max(axis=1)
    lower_wick = ohlc_df[['open', 'close']].min(axis=1) - ohlc_df['low']
    
    # Hammer conditions
    small_body = (body_size / (total_range + 1e-8)) < body_threshold
    long_lower_wick = (lower_wick / (body_size + 1e-8)) > lower_wick_ratio
    small_upper_wick = upper_wick < body_size
    
    return small_body & long_lower_wick & small_upper_wick

def detect_shooting_star(ohlc_df: pd.DataFrame, body_threshold: float = 0.3, upper_wick_ratio: float = 2.0) -> pd.Series:
    """
    Detect Shooting Star candlestick pattern (bearish reversal).
    
    Args:
        ohlc_df: DataFrame with OHLC data
        body_threshold: Maximum body to total range ratio (default: 0.3)
        upper_wick_ratio: Minimum upper wick to body ratio (default: 2.0)
        
    Returns:
        pd.Series: Boolean series indicating Shooting Star pattern
    """
    body_size = np.abs(ohlc_df['close'] - ohlc_df['open'])
    total_range = ohlc_df['high'] - ohlc_df['low']
    
    # Calculate wick sizes
    upper_wick = ohlc_df['high'] - ohlc_df[['open', 'close']].max(axis=1)
    lower_wick = ohlc_df[['open', 'close']].min(axis=1) - ohlc_df['low']
    
    # Shooting Star conditions
    small_body = (body_size / (total_range + 1e-8)) < body_threshold
    long_upper_wick = (upper_wick / (body_size + 1e-8)) > upper_wick_ratio
    small_lower_wick = lower_wick < body_size
    
    return small_body & long_upper_wick & small_lower_wick

def detect_marubozu(ohlc_df: pd.DataFrame, wick_threshold: float = 0.1) -> Tuple[pd.Series, pd.Series]:
    """
    Detect Marubozu candlestick patterns (bullish and bearish).
    
    Args:
        ohlc_df: DataFrame with OHLC data
        wick_threshold: Maximum wick to body ratio (default: 0.1)
        
    Returns:
        Tuple[pd.Series, pd.Series]: Two boolean series for bullish and bearish Marubozu patterns
    """
    body_size = np.abs(ohlc_df['close'] - ohlc_df['open'])
    total_range = ohlc_df['high'] - ohlc_df['low']
    
    # Calculate wick sizes
    upper_wick = ohlc_df['high'] - ohlc_df[['open', 'close']].max(axis=1)
    lower_wick = ohlc_df[['open', 'close']].min(axis=1) - ohlc_df['low']
    
    # Marubozu conditions
    small_wicks = (upper_wick + lower_wick) / (body_size + 1e-8) < wick_threshold
    bullish = (ohlc_df['close'] > ohlc_df['open']) & small_wicks
    bearish = (ohlc_df['close'] < ohlc_df['open']) & small_wicks
    
    return bullish, bearish

def detect_engulfing(ohlc_df: pd.DataFrame) -> tuple:
    """
    Detect bullish and bearish engulfing candlestick patterns.
    
    Bullish Engulfing: Previous candle is bearish (close < open), current candle is bullish (close > open),
                       current candle's body completely engulfs previous candle's body.
    
    Bearish Engulfing: Previous candle is bullish (close > open), current candle is bearish (close < open),
                       current candle's body completely engulfs previous candle's body.
    
    Args:
        ohlc_df: DataFrame with OHLC data (must have 'open', 'high', 'low', 'close' columns)
        
    Returns:
        Tuple[pd.Series, pd.Series]: Two boolean series for bullish and bearish engulfing patterns
    """
    # Shift data to get previous candle
    prev_open = ohlc_df['open'].shift(1)
    prev_close = ohlc_df['close'].shift(1)
    
    curr_open = ohlc_df['open']
    curr_close = ohlc_df['close']
    
    # Bullish Engulfing conditions
    # Previous candle is bearish (close < open)
    prev_bearish = prev_close < prev_open
    # Current candle is bullish (close > open)
    curr_bullish = curr_close > curr_open
    # Current candle's body engulfs previous candle's body
    curr_open_below_prev_close = curr_open <= prev_close
    curr_close_above_prev_open = curr_close >= prev_open
    
    bullish_engulfing = prev_bearish & curr_bullish & curr_open_below_prev_close & curr_close_above_prev_open
    
    # Bearish Engulfing conditions
    # Previous candle is bullish (close > open)
    prev_bullish = prev_close > prev_open
    # Current candle is bearish (close < open)
    curr_bearish = curr_close < curr_open
    # Current candle's body engulfs previous candle's body
    curr_open_above_prev_close = curr_open >= prev_close
    curr_close_below_prev_open = curr_close <= prev_open
    
    bearish_engulfing = prev_bullish & curr_bearish & curr_open_above_prev_close & curr_close_below_prev_open
    
    return bullish_engulfing, bearish_engulfing

def calculate_support_resistance(ohlc_df: pd.DataFrame, window: int = 20) -> Dict[str, Any]:
    """
    Calculate support and resistance levels using pivot points and recent price action.
    
    Args:
        ohlc_df: DataFrame with OHLC data
        window: Lookback window for calculating recent highs/lows (default: 20)
        
    Returns:
        Dict containing support and resistance levels
    """
    if len(ohlc_df) < window:
        window = len(ohlc_df)
        
    # Pivot Point (PP)
    pp = (ohlc_df['high'].iloc[-1] + ohlc_df['low'].iloc[-1] + ohlc_df['close'].iloc[-1]) / 3
    
    # Standard support and resistance levels
    r1 = 2 * pp - ohlc_df['low'].iloc[-1]
    s1 = 2 * pp - ohlc_df['high'].iloc[-1]
    r2 = pp + (ohlc_df['high'].iloc[-1] - ohlc_df['low'].iloc[-1])
    s2 = pp - (ohlc_df['high'].iloc[-1] - ohlc_df['low'].iloc[-1])
    
    # Recent price action levels
    recent_high = ohlc_df['high'].rolling(window=window).max().iloc[-1]
    recent_low = ohlc_df['low'].rolling(window=window).min().iloc[-1]
    
    return {
        'pivot_point': pp,
        'resistance1': r1,
        'support1': s1,
        'resistance2': r2,
        'support2': s2,
        'recent_high': recent_high,
        'recent_low': recent_low
    }

def detect_trend(ohlc_df: pd.DataFrame, period: int = 20) -> str:
    """
    Detect the current trend based on moving averages.
    
    Args:
        ohlc_df: DataFrame with OHLC data
        period: Period for moving average (default: 20)
        
    Returns:
        str: 'uptrend', 'downtrend', or 'sideways'
    """
    if len(ohlc_df) < period:
        return 'insufficient_data'
        
    # Calculate moving averages
    ma = ohlc_df['close'].rolling(window=period).mean()
    
    # Determine trend based on price position relative to MA and MA slope
    last_price = ohlc_df['close'].iloc[-1]
    last_ma = ma.iloc[-1]
    prev_ma = ma.iloc[-2] if len(ma) > 1 else last_ma
    
    if last_ma > prev_ma * 1.001:  # Uptrend if MA is rising
        return 'uptrend'
    elif last_ma < prev_ma * 0.999:  # Downtrend if MA is falling
        return 'downtrend'
    else:
        return 'sideways'  # Sideways if MA is flat

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR) for volatility measurement."""
    # True Range = max(high-low, abs(high - prev_close), abs(low - prev_close))
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period, min_periods=1).mean()
    return atr

def calculate_supertrend(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    atr_period: int = 10,
    multiplier: float = 3.0
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Calculate Supertrend indicator.
    
    Returns:
        Tuple of (supertrend, direction, upper_band, lower_band)
    """
    # Calculate ATR
    atr = calculate_atr(high, low, close, atr_period)
    
    # Basic upper and lower bands
    hl2 = (high + low) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    # Initialize columns
    supertrend = pd.Series(index=close.index, dtype='float64')
    direction = pd.Series(1, index=close.index)
    
    for i in range(1, len(close)):
        if close.iloc[i-1] > supertrend.iloc[i-1]:
            direction.iloc[i] = 1
        elif close.iloc[i-1] < supertrend.iloc[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]
            
        if direction.iloc[i] < 0 and upper_band.iloc[i] < supertrend.iloc[i-1]:
            supertrend.iloc[i] = upper_band.iloc[i]
        elif direction.iloc[i] > 0 and lower_band.iloc[i] > supertrend.iloc[i-1]:
            supertrend.iloc[i] = lower_band.iloc[i]
        else:
            if direction.iloc[i] < 0:
                supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i-1])
            else:
                supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i-1])
    
    return supertrend, direction, upper_band, lower_band

def generate_trading_signals(
    ohlc_df: pd.DataFrame,
    atr_periods: List[int] = [7, 14, 21],
    multipliers: List[float] = [2.0, 3.0, 4.0]
) -> Dict[str, Any]:
    """
    Generate trading signals based on multiple Supertrend indicators.
    
    Returns:
        Dict containing trading signals and analysis
    """
    if ohlc_df.empty or len(ohlc_df) < max(atr_periods) * 2:
        return {"error": "Insufficient data for analysis"}
    
    # Calculate multiple Supertrend indicators
    signals = {}
    for period in atr_periods:
        for mult in multipliers:
            _, direction, _, _ = calculate_supertrend(
                ohlc_df['high'], ohlc_df['low'], ohlc_df['close'], period, mult
            )
            signals[f'supertrend_{period}_{mult}'] = direction
    
    # Combine signals
    signals_df = pd.DataFrame(signals)
    
    # Generate final signal (1 for buy, -1 for sell, 0 for neutral)
    signals_df['all_bullish'] = (signals_df > 0).all(axis=1).astype(int)
    signals_df['all_bearish'] = (signals_df < 0).all(axis=1).astype(int) * -1
    signals_df['signal'] = signals_df[['all_bullish', 'all_bearish']].sum(axis=1)
    
    # Add signal metadata
    current_signal = signals_df['signal'].iloc[-1]
    signal_strength = (signals_df == current_signal).mean().mean()
    
    # Calculate position size (example values, adjust as needed)
    current_price = ohlc_df['close'].iloc[-1]
    position_size = calculate_position_size(
        capital=100000,  # Example capital
        price=current_price,
        risk_per_trade=0.01,
        stop_loss_pct=0.02
    )
    
    # Get trend and levels
    trend = detect_trend(ohlc_df)
    levels = calculate_support_resistance(ohlc_df)
    
    # Find nearest support/resistance
    current_close = ohlc_df['close'].iloc[-1]
    support_levels = [levels['support1'], levels['support2'], levels['recent_low']]
    resistance_levels = [levels['resistance1'], levels['resistance2'], levels['recent_high']]
    
    nearest_support = max([s for s in support_levels if s < current_close], default=min(support_levels, default=None))
    nearest_resistance = min([r for r in resistance_levels if r > current_close], default=max(resistance_levels, default=None))
    
    # Calculate distances
    support_distance_pct = ((current_close - nearest_support) / nearest_support * 100) if nearest_support else None
    resistance_distance_pct = ((nearest_resistance - current_close) / current_close * 100) if nearest_resistance else None
    
    return {
        'signal': 'bullish' if current_signal > 0 else 'bearish' if current_signal < 0 else 'neutral',
        'signal_strength': signal_strength,
        'current_price': current_price,
        'trend': trend,
        'levels': levels,
        'position_size': position_size,
        'nearest_support': nearest_support,
        'nearest_resistance': nearest_resistance,
        'support_distance_pct': support_distance_pct,
        'resistance_distance_pct': resistance_distance_pct,
        'timestamp': ohlc_df.index[-1],
        'indicators': {
            'supertrend': signals_df.to_dict(orient='list')
        }
    }

def calculate_position_size(
    capital: float,
    price: float,
    risk_per_trade: float = 0.01,
    stop_loss_pct: float = 0.02
) -> Dict[str, float]:
    """
    Calculate position size based on risk management rules.
    
    Args:
        capital: Total trading capital
        price: Current price of the asset
        risk_per_trade: Percentage of capital to risk per trade (0-1)
        stop_loss_pct: Stop loss as percentage of price (0-1)
        
    Returns:
        Dict containing position details
    """
    risk_amount = capital * risk_per_trade
    stop_loss_amount = price * stop_loss_pct
    quantity = int(risk_amount / stop_loss_amount) if stop_loss_amount > 0 else 0
    
    return {
        'quantity': quantity,
        'risk_amount': risk_amount,
        'stop_loss': price - (price * stop_loss_pct) if quantity > 0 else 0,
        'target': price + (price * (stop_loss_pct * 2))  # 2:1 reward:risk
    }

def analyze_candlestick_patterns(ohlc_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze candlestick patterns and return a summary of the analysis.
    
    Args:
        ohlc_df: DataFrame with OHLC data
        
    Returns:
        Dict containing pattern analysis results
    """
    if ohlc_df.empty or len(ohlc_df) < 2:
        return {"error": "Insufficient data for analysis"}
    
    # Detect patterns
    is_doji = detect_doji(ohlc_df)
    is_hammer = detect_hammer(ohlc_df)
    is_shooting_star = detect_shooting_star(ohlc_df)
    is_bullish_marubozu, is_bearish_marubozu = detect_marubozu(ohlc_df)
    
    # Get support/resistance levels
    levels = calculate_support_resistance(ohlc_df)
    
    # Determine trend
    trend = detect_trend(ohlc_df)
    
    # Current price action
    current_close = ohlc_df['close'].iloc[-1]
    current_open = ohlc_df['open'].iloc[-1]
    is_bullish_candle = current_close > current_open
    
    # Determine proximity to support/resistance
    support_levels = [levels['support1'], levels['support2'], levels['recent_low']]
    resistance_levels = [levels['resistance1'], levels['resistance2'], levels['recent_high']]
    
    # Find nearest support and resistance
    nearest_support = max([s for s in support_levels if s < current_close], default=min(support_levels, default=None))
    nearest_resistance = min([r for r in resistance_levels if r > current_close], default=max(resistance_levels, default=None))
    
    # Calculate distance to support/resistance as percentage
    support_distance_pct = ((current_close - nearest_support) / nearest_support * 100) if nearest_support else None
    resistance_distance_pct = ((nearest_resistance - current_close) / current_close * 100) if nearest_resistance else None
    
    # Determine signal
    signal = "neutral"
    signal_strength = "weak"
    
    # Check for bullish signals
    if (is_hammer.iloc[-1] or is_bullish_marubozu.iloc[-1]) and \
       (support_distance_pct is not None and support_distance_pct < 1.0):
        signal = "bullish"
        signal_strength = "strong" if is_bullish_marubozu.iloc[-1] else "moderate"
    # Check for bearish signals
    elif (is_shooting_star.iloc[-1] or is_bearish_marubozu.iloc[-1]) and \
         (resistance_distance_pct is not None and resistance_distance_pct < 1.0):
        signal = "bearish"
        signal_strength = "strong" if is_bearish_marubozu.iloc[-1] else "moderate"
    
    # Compile results
    result = {
        "patterns": {
            "doji": bool(is_doji.iloc[-1]),
            "hammer": bool(is_hammer.iloc[-1]),
            "shooting_star": bool(is_shooting_star.iloc[-1]),
            "bullish_marubozu": bool(is_bullish_marubozu.iloc[-1]),
            "bearish_marubozu": bool(is_bearish_marubozu.iloc[-1])
        },
        "levels": levels,
        "trend": trend,
        "current_price": current_close,
        "signal": signal,
        "signal_strength": signal_strength,
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "support_distance_pct": support_distance_pct,
        "resistance_distance_pct": resistance_distance_pct,
        "timestamp": ohlc_df.index[-1]
    }
    
    return result
