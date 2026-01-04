"""
Strategy Engine: Combines indicators and generates trading signals
"""
import pandas as pd
from typing import Dict, Any, Optional
from app.services.data_service import fetch_ohlc_data, validate_ohlc_data
from app.utils.serializer import convert_to_serializable
from app.indicators import (
    calculate_adx, get_adx_signal,
    calculate_atr,
    calculate_bollinger_bands, get_bollinger_signal,
    calculate_macd, get_macd_signal,
    calculate_rsi, get_rsi_signal,
    calculate_supertrend, get_supertrend_signal,
    calculate_renko, get_renko_signal
)


class StrategyEngine:
    """Engine for executing trading strategies"""
    
    def __init__(self):
        self.available_strategies = {
            'ADX': self._run_adx_strategy,
            'ATR': self._run_atr_strategy,
            'BOLLINGER': self._run_bollinger_strategy,
            'MACD': self._run_macd_strategy,
            'RSI': self._run_rsi_strategy,
            'SUPERTREND': self._run_supertrend_strategy,
            'RENKO': self._run_renko_strategy,
        }
    
    def list_strategies(self) -> list:
        """Return list of available strategies"""
        return list(self.available_strategies.keys())
    
    def run_strategy(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str = "5",
        lookback_days: int = 30,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """
        Execute a trading strategy.
        
        Args:
            strategy_name: Name of strategy to run
            symbol: Stock symbol
            timeframe: Timeframe (1, 5, 15, 60, D)
            lookback_days: Days to look back (used if dates not provided)
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            **params: Strategy-specific parameters
        
        Returns:
            Dictionary with strategy results and signals
        """
        if strategy_name not in self.available_strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        # Fetch OHLC data
        df = fetch_ohlc_data(symbol, timeframe, lookback_days, from_date=start_date, to_date=end_date)
        
        if not validate_ohlc_data(df):
            return {
                'error': 'Insufficient data',
                'strategy': strategy_name,
                'symbol': symbol
            }
        
        # Run strategy
        strategy_func = self.available_strategies[strategy_name]
        result = strategy_func(df, **params)
        
        result['strategy'] = strategy_name
        result['symbol'] = symbol
        result['timeframe'] = timeframe
        result['data_points'] = len(df)
        result['latest_price'] = float(df['close'].iloc[-1])
        result['timestamp'] = df.index[-1].isoformat()
        
        # Convert all numpy types to native Python types for JSON serialization
        return convert_to_serializable(result)
    
    def _run_adx_strategy(self, df: pd.DataFrame, period: int = 14, **kwargs) -> Dict[str, Any]:
        """Run ADX strategy"""
        adx = calculate_adx(df, period=period)
        signal = get_adx_signal(adx)
        
        return {
            'indicator': 'ADX',
            'value': float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else None,
            'signal': signal,
            'period': period,
            'data': {
                'adx': adx.iloc[-10:].tolist() if len(adx) >= 10 else adx.tolist()
            }
        }
    
    def _run_atr_strategy(self, df: pd.DataFrame, period: int = 14, **kwargs) -> Dict[str, Any]:
        """Run ATR strategy"""
        atr = calculate_atr(df, period=period)
        
        return {
            'indicator': 'ATR',
            'value': float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None,
            'signal': 'VOLATILITY_MEASURE',
            'period': period,
            'data': {
                'atr': atr.iloc[-10:].tolist() if len(atr) >= 10 else atr.tolist()
            }
        }
    
    def _run_bollinger_strategy(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0, **kwargs) -> Dict[str, Any]:
        """Run Bollinger Bands strategy"""
        bb = calculate_bollinger_bands(df, period=period, std_dev=std_dev)
        signal = get_bollinger_signal(df, bb)
        
        return {
            'indicator': 'BOLLINGER_BANDS',
            'signal': signal,
            'period': period,
            'std_dev': std_dev,
            'data': {
                'upper_band': float(bb['upper_band'].iloc[-1]) if not pd.isna(bb['upper_band'].iloc[-1]) else None,
                'middle_band': float(bb['middle_band'].iloc[-1]) if not pd.isna(bb['middle_band'].iloc[-1]) else None,
                'lower_band': float(bb['lower_band'].iloc[-1]) if not pd.isna(bb['lower_band'].iloc[-1]) else None,
                'current_price': float(df['close'].iloc[-1])
            }
        }
    
    def _run_macd_strategy(self, df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, **kwargs) -> Dict[str, Any]:
        """Run MACD strategy"""
        macd_df = calculate_macd(df, fast_period=fast_period, slow_period=slow_period, signal_period=signal_period)
        signal = get_macd_signal(macd_df)
        
        return {
            'indicator': 'MACD',
            'signal': signal,
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period,
            'data': {
                'macd': float(macd_df['macd'].iloc[-1]) if not pd.isna(macd_df['macd'].iloc[-1]) else None,
                'signal': float(macd_df['signal'].iloc[-1]) if not pd.isna(macd_df['signal'].iloc[-1]) else None,
                'histogram': float(macd_df['histogram'].iloc[-1]) if not pd.isna(macd_df['histogram'].iloc[-1]) else None
            }
        }
    
    def _run_rsi_strategy(self, df: pd.DataFrame, period: int = 14, oversold: float = 30, overbought: float = 70, **kwargs) -> Dict[str, Any]:
        """Run RSI strategy"""
        rsi = calculate_rsi(df, period=period)
        signal = get_rsi_signal(rsi, oversold=oversold, overbought=overbought)
        
        return {
            'indicator': 'RSI',
            'value': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
            'signal': signal,
            'period': period,
            'oversold': oversold,
            'overbought': overbought,
            'data': {
                'rsi': rsi.iloc[-10:].tolist() if len(rsi) >= 10 else rsi.tolist()
            }
        }
    
    def _run_supertrend_strategy(self, df: pd.DataFrame, atr_period: int = 7, multiplier: float = 3.0, **kwargs) -> Dict[str, Any]:
        """Run Supertrend strategy"""
        st = calculate_supertrend(df, atr_period=atr_period, multiplier=multiplier)
        signal = get_supertrend_signal(df, st)
        
        return {
            'indicator': 'SUPERTREND',
            'signal': signal,
            'atr_period': atr_period,
            'multiplier': multiplier,
            'data': {
                'supertrend': float(st['supertrend'].iloc[-1]) if not pd.isna(st['supertrend'].iloc[-1]) else None,
                'direction': int(st['direction'].iloc[-1]) if not pd.isna(st['direction'].iloc[-1]) else None,
                'current_price': float(df['close'].iloc[-1])
            }
        }
    
    def _run_renko_strategy(self, df: pd.DataFrame, brick_size: Optional[float] = None, atr_period: int = 14, atr_multiplier: float = 1.0, lookback: int = 3, **kwargs) -> Dict[str, Any]:
        """Run Renko strategy"""
        renko_df = calculate_renko(df, brick_size=brick_size, atr_period=atr_period, atr_multiplier=atr_multiplier)
        signal = get_renko_signal(renko_df, lookback=lookback)
        
        return {
            'indicator': 'RENKO',
            'signal': signal,
            'brick_size': brick_size,
            'atr_period': atr_period,
            'atr_multiplier': atr_multiplier,
            'lookback': lookback,
            'data': {
                'brick_count': len(renko_df),
                'latest_brick': renko_df.iloc[-1].to_dict() if len(renko_df) > 0 else None
            }
        }


# Global strategy engine instance
_strategy_engine = None


def get_strategy_engine() -> StrategyEngine:
    """Get or create strategy engine instance"""
    global _strategy_engine
    if _strategy_engine is None:
        _strategy_engine = StrategyEngine()
    return _strategy_engine


