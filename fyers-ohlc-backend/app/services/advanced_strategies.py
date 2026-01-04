"""
Advanced Strategy Builder
Combines multiple indicators and patterns for comprehensive trading strategies
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.indicators import (
    calculate_rsi, calculate_macd, calculate_supertrend,
    calculate_bollinger_bands, calculate_adx, calculate_atr,
    calculate_stochastic, calculate_ema, calculate_sma,
    calculate_pivot_points, get_nearest_support_resistance
)
from app.indicators.candlestick_patterns import (
    detect_doji, detect_hammer, detect_shooting_star,
    detect_marubozu, detect_engulfing
)


class StrategyBuilder:
    """
    Build and execute trading strategies using multiple indicators and patterns.
    """
    
    def __init__(self):
        self.indicators = {}
        self.patterns = {}
        self.signals = []
    
    def add_all_indicators(self, df: pd.DataFrame, config: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Add all available indicators to the dataframe.
        
        Args:
            df: OHLC DataFrame
            config: Optional configuration for indicator parameters
        
        Returns:
            DataFrame with all indicators added
        """
        if config is None:
            config = {}
        
        df = df.copy()
        
        # RSI
        rsi_period = config.get('rsi_period', 14)
        df['rsi'] = calculate_rsi(df, rsi_period)
        
        # MACD
        macd_data = calculate_macd(df, 
                                   fast_period=config.get('macd_fast', 12),
                                   slow_period=config.get('macd_slow', 26),
                                   signal_period=config.get('macd_signal', 9))
        for col in macd_data.columns:
            df[col] = macd_data[col]
        
        # Supertrend
        supertrend_data = calculate_supertrend(df,
                                               atr_period=config.get('supertrend_period', 7),
                                               multiplier=config.get('supertrend_mult', 3))
        for col in supertrend_data.columns:
            df[col] = supertrend_data[col]
        
        # Bollinger Bands
        bb_data = calculate_bollinger_bands(df,
                                           period=config.get('bb_period', 20),
                                           std_dev=config.get('bb_std', 2))
        for col in bb_data.columns:
            df[col] = bb_data[col]
        
        # ADX
        df['adx'] = calculate_adx(df, period=config.get('adx_period', 14))
        
        # ATR
        df['atr'] = calculate_atr(df, period=config.get('atr_period', 14))
        
        # Stochastic
        stoch_data = calculate_stochastic(df, period=config.get('stoch_period', 14))
        for col in stoch_data.columns:
            df[col] = stoch_data[col]
        
        # EMA
        ema_periods = config.get('ema_periods', [9, 21, 50])
        for period in ema_periods:
            df[f'ema_{period}'] = calculate_ema(df, period)
        
        # SMA
        sma_periods = config.get('sma_periods', [10, 20, 50])
        for period in sma_periods:
            df[f'sma_{period}'] = calculate_sma(df, period)
        
        return df
    
    def detect_all_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect all candlestick patterns.
        
        Args:
            df: OHLC DataFrame
        
        Returns:
            DataFrame with pattern detection columns
        """
        df = df.copy()
        
        # Doji
        df['pattern_doji'] = detect_doji(df)
        
        # Hammer
        df['pattern_hammer'] = detect_hammer(df)
        
        # Shooting Star
        df['pattern_shooting_star'] = detect_shooting_star(df)
        
        # Marubozu
        bullish_maru, bearish_maru = detect_marubozu(df)
        df['pattern_marubozu_bull'] = bullish_maru
        df['pattern_marubozu_bear'] = bearish_maru
        
        # Engulfing
        bullish_eng, bearish_eng = detect_engulfing(df)
        df['pattern_engulfing_bull'] = bullish_eng
        df['pattern_engulfing_bear'] = bearish_eng
        
        return df
    
    def supertrend_rsi_strategy(self, df: pd.DataFrame, 
                                 rsi_oversold: int = 30, 
                                 rsi_overbought: int = 70) -> List[Dict[str, Any]]:
        """
        Supertrend + RSI Strategy.
        
        BUY: Supertrend green + RSI > oversold
        SELL: Supertrend red + RSI < overbought
        """
        signals = []
        
        if len(df) < 2:
            return signals
        
        for i in range(1, len(df)):
            signal = None
            
            # Current values
            st_current = df['supertrend'].iloc[i]
            close_current = df['close'].iloc[i]
            rsi_current = df['rsi'].iloc[i]
            
            # Previous values
            st_previous = df['supertrend'].iloc[i-1]
            close_previous = df['close'].iloc[i-1]
            
            # Supertrend bullish (price above supertrend)
            st_bullish = close_current > st_current
            st_bearish = close_current < st_current
            
            # Crossover detection
            st_bull_crossover = close_previous <= st_previous and close_current > st_current
            st_bear_crossover = close_previous >= st_previous and close_current < st_current
            
            # Generate signals
            if st_bull_crossover and rsi_current > rsi_oversold:
                signal = {
                    'index': i,
                    'timestamp': df.index[i] if hasattr(df.index[i], 'strftime') else i,
                    'type': 'BUY',
                    'price': close_current,
                    'strategy': 'supertrend_rsi',
                    'indicators': {
                        'rsi': rsi_current,
                        'supertrend': st_current
                    }
                }
            elif st_bear_crossover and rsi_current < rsi_overbought:
                signal = {
                    'index': i,
                    'timestamp': df.index[i] if hasattr(df.index[i], 'strftime') else i,
                    'type': 'SELL',
                    'price': close_current,
                    'strategy': 'supertrend_rsi',
                    'indicators': {
                        'rsi': rsi_current,
                        'supertrend': st_current
                    }
                }
            
            if signal:
                signals.append(signal)
        
        return signals
    
    def macd_bb_strategy(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        MACD + Bollinger Bands Strategy.
        
        BUY: MACD bullish crossover + price near lower BB
        SELL: MACD bearish crossover + price near upper BB
        """
        signals = []
        
        if len(df) < 2:
            return signals
        
        for i in range(1, len(df)):
            signal = None
            
            # Current values
            macd_current = df['macd'].iloc[i]
            signal_current = df['signal'].iloc[i]
            close_current = df['close'].iloc[i]
            bb_upper = df['upper_band'].iloc[i]
            bb_lower = df['lower_band'].iloc[i]
            bb_middle = df['middle_band'].iloc[i]
            
            # Previous values
            macd_previous = df['macd'].iloc[i-1]
            signal_previous = df['signal'].iloc[i-1]
            
            # Crossovers
            macd_bull_cross = macd_previous < signal_previous and macd_current > signal_current
            macd_bear_cross = macd_previous > signal_previous and macd_current < signal_current
            
            # BB position
            near_lower_bb = close_current < bb_middle and (close_current - bb_lower) < (bb_middle - bb_lower) * 0.3
            near_upper_bb = close_current > bb_middle and (bb_upper - close_current) < (bb_upper - bb_middle) * 0.3
            
            # Generate signals
            if macd_bull_cross and near_lower_bb:
                signal = {
                    'index': i,
                    'timestamp': df.index[i] if hasattr(df.index[i], 'strftime') else i,
                    'type': 'BUY',
                    'price': close_current,
                    'strategy': 'macd_bb',
                    'indicators': {
                        'macd': macd_current,
                        'macd_signal': signal_current,
                        'bb_position': 'lower'
                    }
                }
            elif macd_bear_cross and near_upper_bb:
                signal = {
                    'index': i,
                    'timestamp': df.index[i] if hasattr(df.index[i], 'strftime') else i,
                    'type': 'SELL',
                    'price': close_current,
                    'strategy': 'macd_bb',
                    'indicators': {
                        'macd': macd_current,
                        'macd_signal': signal_current,
                        'bb_position': 'upper'
                    }
                }
            
            if signal:
                signals.append(signal)
        
        return signals
    
    def ema_crossover_strategy(self, df: pd.DataFrame, 
                                fast_period: int = 9, 
                                slow_period: int = 21) -> List[Dict[str, Any]]:
        """
        EMA Crossover Strategy.
        
        BUY: Fast EMA crosses above slow EMA
        SELL: Fast EMA crosses below slow EMA
        """
        signals = []
        
        fast_col = f'ema_{fast_period}'
        slow_col = f'ema_{slow_period}'
        
        if fast_col not in df.columns or slow_col not in df.columns:
            return signals
        
        if len(df) < 2:
            return signals
        
        for i in range(1, len(df)):
            fast_current = df[fast_col].iloc[i]
            slow_current = df[slow_col].iloc[i]
            fast_previous = df[fast_col].iloc[i-1]
            slow_previous = df[slow_col].iloc[i-1]
            
            # Bullish crossover
            if fast_previous <= slow_previous and fast_current > slow_current:
                signals.append({
                    'index': i,
                    'timestamp': df.index[i] if hasattr(df.index[i], 'strftime') else i,
                    'type': 'BUY',
                    'price': df['close'].iloc[i],
                    'strategy': 'ema_crossover',
                    'indicators': {
                        f'ema_{fast_period}': fast_current,
                        f'ema_{slow_period}': slow_current
                    }
                })
            # Bearish crossover
            elif fast_previous >= slow_previous and fast_current < slow_current:
                signals.append({
                    'index': i,
                    'timestamp': df.index[i] if hasattr(df.index[i], 'strftime') else i,
                    'type': 'SELL',
                    'price': df['close'].iloc[i],
                    'strategy': 'ema_crossover',
                    'indicators': {
                        f'ema_{fast_period}': fast_current,
                        f'ema_{slow_period}': slow_current
                    }
                })
        
        return signals
    
    def pattern_with_trend_strategy(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Candlestick pattern with trend confirmation strategy.
        
        Uses patterns like hammer in downtrend (bullish reversal)
        or shooting star in uptrend (bearish reversal).
        """
        signals = []
        
        if len(df) < 10:  # Need enough data for trend determination
            return signals
        
        # Detect trend using EMA
        if 'ema_50' not in df.columns:
            df['ema_50'] = calculate_ema(df, 50)
        
        for i in range(10, len(df)):
            signal = None
            close_current = df['close'].iloc[i]
            ema_50 = df['ema_50'].iloc[i]
            
            # Determine trend
            uptrend = close_current > ema_50
            downtrend = close_current < ema_50
            
            # Check patterns
            if downtrend and df['pattern_hammer'].iloc[i]:
                signal = {
                    'index': i,
                    'timestamp': df.index[i] if hasattr(df.index[i], 'strftime') else i,
                    'type': 'BUY',
                    'price': close_current,
                    'strategy': 'pattern_trend',
                    'pattern': 'hammer',
                    'trend': 'downtrend_reversal'
                }
            elif uptrend and df['pattern_shooting_star'].iloc[i]:
                signal = {
                    'index': i,
                    'timestamp': df.index[i] if hasattr(df.index[i], 'strftime') else i,
                    'type': 'SELL',
                    'price': close_current,
                    'strategy': 'pattern_trend',
                    'pattern': 'shooting_star',
                    'trend': 'uptrend_reversal'
                }
            elif downtrend and df['pattern_engulfing_bull'].iloc[i]:
                signal = {
                    'index': i,
                    'timestamp': df.index[i] if hasattr(df.index[i], 'strftime') else i,
                    'type': 'BUY',
                    'price': close_current,
                    'strategy': 'pattern_trend',
                    'pattern': 'bullish_engulfing',
                    'trend': 'downtrend_reversal'
                }
            elif uptrend and df['pattern_engulfing_bear'].iloc[i]:
                signal = {
                    'index': i,
                    'timestamp': df.index[i] if hasattr(df.index[i], 'strftime') else i,
                    'type': 'SELL',
                    'price': close_current,
                    'strategy': 'pattern_trend',
                    'pattern': 'bearish_engulfing',
                    'trend': 'uptrend_reversal'
                }
            
            if signal:
                signals.append(signal)
        
        return signals
    
    def execute_strategy(self, df: pd.DataFrame, strategy_name: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute a specific strategy.
        
        Args:
            df: OHLC DataFrame with indicators
            strategy_name: Name of strategy to execute
            **kwargs: Strategy-specific parameters
        
        Returns:
            List of trading signals
        """
        if strategy_name == 'supertrend_rsi':
            return self.supertrend_rsi_strategy(df, **kwargs)
        elif strategy_name == 'macd_bb':
            return self.macd_bb_strategy(df)
        elif strategy_name == 'ema_crossover':
            return self.ema_crossover_strategy(df, **kwargs)
        elif strategy_name == 'pattern_trend':
            return self.pattern_with_trend_strategy(df)
        else:
            return []
    
    def backtest_strategy(self, df: pd.DataFrame, signals: List[Dict[str, Any]], 
                         initial_capital: float = 100000) -> Dict[str, Any]:
        """
        Backtest a strategy and calculate performance metrics.
        
        Args:
            df: OHLC DataFrame
            signals: List of trading signals
            initial_capital: Starting capital
        
        Returns:
            Dictionary with backtest results
        """
        if not signals:
            return {'error': 'No signals to backtest'}
        
        capital = initial_capital
        position = None
        trades = []
        
        for signal in signals:
            if signal['type'] == 'BUY' and position is None:
                # Enter long position
                quantity = int(capital * 0.95 / signal['price'])  # Use 95% of capital
                if quantity > 0:
                    position = {
                        'type': 'LONG',
                        'entry_price': signal['price'],
                        'quantity': quantity,
                        'entry_time': signal['timestamp']
                    }
            
            elif signal['type'] == 'SELL' and position and position['type'] == 'LONG':
                # Exit long position
                exit_value = position['quantity'] * signal['price']
                entry_value = position['quantity'] * position['entry_price']
                pnl = exit_value - entry_value
                
                trades.append({
                    'entry_price': position['entry_price'],
                    'exit_price': signal['price'],
                    'quantity': position['quantity'],
                    'pnl': pnl,
                    'pnl_percent': (pnl / entry_value) * 100,
                    'entry_time': position['entry_time'],
                    'exit_time': signal['timestamp']
                })
                
                capital += pnl
                position = None
        
        # Calculate metrics
        if not trades:
            return {'error': 'No completed trades'}
        
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]
        
        total_pnl = sum(t['pnl'] for t in trades)
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        return {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_pnl': total_pnl,
            'total_pnl_percent': (total_pnl / initial_capital) * 100,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'trades': trades
        }
