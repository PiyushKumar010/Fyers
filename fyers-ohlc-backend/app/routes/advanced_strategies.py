"""
Advanced Strategies API Routes
Endpoints for strategy building, backtesting, and signal generation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

from app.services import fyers as fyers_service
from app.services.advanced_strategies import StrategyBuilder
from app.indicators import calculate_pivot_points

router = APIRouter(prefix="/api/advanced-strategies", tags=["Advanced Strategies"])


class StrategyRequest(BaseModel):
    symbol: str
    interval: str
    duration: int  # days
    strategy_name: str
    parameters: Optional[Dict[str, Any]] = {}


class IndicatorRequest(BaseModel):
    symbol: str
    interval: str
    duration: int
    indicators: List[str]  # List of indicator names
    config: Optional[Dict[str, Any]] = {}


class BacktestRequest(BaseModel):
    symbol: str
    interval: str
    duration: int
    strategy_name: str
    parameters: Optional[Dict[str, Any]] = {}
    initial_capital: Optional[float] = 100000


@router.post("/calculate-indicators")
async def calculate_indicators(request: IndicatorRequest):
    """
    Calculate specified indicators for a symbol.
    
    Available indicators:
    - rsi, macd, supertrend, bollinger, adx, atr, stochastic
    - ema, sma, pivot_points
    """
    try:
        # Fetch OHLC data
        symbol_norm = fyers_service.normalize_symbol(request.symbol)
        
        from datetime import date, timedelta
        range_from = (date.today() - timedelta(days=request.duration)).strftime("%Y-%m-%d")
        range_to = date.today().strftime("%Y-%m-%d")
        
        raw_data = fyers_service.fetch_ohlc(symbol_norm, request.interval, range_from, range_to)
        
        if not raw_data or len(raw_data) == 0:
            raise HTTPException(
                status_code=404, 
                detail="No data available. Market might be closed or symbol is invalid."
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        
        # Validate DataFrame has enough data
        if len(df) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data points ({len(df)} rows). Need at least 50 for indicator calculation."
            )
        
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        # Handle timestamp conversion - check if it's Unix timestamp or string
        if pd.api.types.is_numeric_dtype(df['timestamp']):
            # Unix timestamp (seconds)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        else:
            # String datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        df.set_index('timestamp', inplace=True)
        
        # Initialize strategy builder
        builder = StrategyBuilder()
        
        # Add requested indicators
        if 'all' in request.indicators:
            try:
                df = builder.add_all_indicators(df, request.config)
            except Exception as ind_error:
                import traceback
                error_trace = traceback.format_exc()
                print(f"Error in add_all_indicators: {error_trace}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error calculating indicators: {str(ind_error)}"
                )
        else:
            # Add specific indicators
            config = request.config or {}
            
            if 'rsi' in request.indicators:
                from app.indicators import calculate_rsi
                df['rsi'] = calculate_rsi(df, config.get('rsi_period', 14))
            
            if 'macd' in request.indicators:
                from app.indicators import calculate_macd
                macd_data = calculate_macd(df, 
                                          fast_period=config.get('macd_fast', 12),
                                          slow_period=config.get('macd_slow', 26),
                                          signal_period=config.get('macd_signal', 9))
                for col in macd_data.columns:
                    df[col] = macd_data[col]
            
            if 'supertrend' in request.indicators:
                from app.indicators import calculate_supertrend
                st_data = calculate_supertrend(df, 
                                               atr_period=config.get('supertrend_period', 7),
                                               multiplier=config.get('supertrend_mult', 3))
                for col in st_data.columns:
                    df[col] = st_data[col]
            
            if 'bollinger' in request.indicators:
                from app.indicators import calculate_bollinger_bands
                bb_data = calculate_bollinger_bands(df, 
                                                    period=config.get('bb_period', 20),
                                                    std_dev=config.get('bb_std', 2))
                for col in bb_data.columns:
                    df[col] = bb_data[col]
            
            if 'adx' in request.indicators:
                from app.indicators import calculate_adx
                df['adx'] = calculate_adx(df, period=config.get('adx_period', 14))
            
            if 'atr' in request.indicators:
                from app.indicators import calculate_atr
                df['atr'] = calculate_atr(df, period=config.get('atr_period', 14))
            
            if 'stochastic' in request.indicators:
                from app.indicators import calculate_stochastic
                stoch_data = calculate_stochastic(df, period=config.get('stoch_period', 14))
                for col in stoch_data.columns:
                    df[col] = stoch_data[col]
            
            if 'ema' in request.indicators:
                from app.indicators import calculate_ema
                periods = config.get('ema_periods', [9, 21, 50])
                for period in periods:
                    df[f'ema_{period}'] = calculate_ema(df, period)
            
            if 'sma' in request.indicators:
                from app.indicators import calculate_sma
                periods = config.get('sma_periods', [10, 20, 50])
                for period in periods:
                    df[f'sma_{period}'] = calculate_sma(df, period)
            
            if 'pivot_points' in request.indicators:
                pivots = calculate_pivot_points(df, method=config.get('pivot_method', 'standard'))
                return {
                    "symbol": request.symbol,
                    "pivot_points": pivots,
                    "current_price": float(df['close'].iloc[-1])
                }
        
        # Convert to JSON-serializable format
        df_reset = df.reset_index()
        df_reset['timestamp'] = df_reset['timestamp'].astype(str)
        
        # Return last 100 data points to avoid huge response
        result_df = df_reset.tail(100)
        
        return {
            "symbol": request.symbol,
            "interval": request.interval,
            "data": result_df.to_dict(orient='records'),
            "latest": result_df.iloc[-1].to_dict() if len(result_df) > 0 else {}
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error calculating indicators: {str(e)}"
        )


@router.post("/generate-signals")
async def generate_signals(request: StrategyRequest):
    """
    Generate trading signals using specified strategy.
    
    Available strategies:
    - supertrend_rsi: Supertrend + RSI combination
    - macd_bb: MACD + Bollinger Bands
    - ema_crossover: EMA crossover strategy
    - pattern_trend: Candlestick patterns with trend
    """
    try:
        # Fetch OHLC data
        symbol_norm = fyers_service.normalize_symbol(request.symbol)
        
        from datetime import date, timedelta
        range_from = (date.today() - timedelta(days=request.duration)).strftime("%Y-%m-%d")
        range_to = date.today().strftime("%Y-%m-%d")
        
        raw_data = fyers_service.fetch_ohlc(symbol_norm, request.interval, range_from, range_to)
        
        if not raw_data:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        # Handle timestamp conversion - check if it's Unix timestamp or string
        if pd.api.types.is_numeric_dtype(df['timestamp']):
            # Unix timestamp (seconds)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        else:
            # String datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        df.set_index('timestamp', inplace=True)
        
        # Initialize strategy builder
        builder = StrategyBuilder()
        
        # Add all indicators
        df = builder.add_all_indicators(df, request.parameters)
        
        # Add patterns if needed
        if request.strategy_name == 'pattern_trend':
            df = builder.detect_all_patterns(df)
        
        # Execute strategy
        signals = builder.execute_strategy(df, request.strategy_name, **request.parameters)
        
        # Format signals for response
        formatted_signals = []
        for signal in signals:
            formatted_signals.append({
                'timestamp': str(signal['timestamp']),
                'type': signal['type'],
                'price': float(signal['price']),
                'strategy': signal['strategy'],
                'indicators': signal.get('indicators', {}),
                'pattern': signal.get('pattern'),
                'trend': signal.get('trend')
            })
        
        return {
            "symbol": request.symbol,
            "interval": request.interval,
            "strategy": request.strategy_name,
            "total_signals": len(formatted_signals),
            "signals": formatted_signals
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(status_code=500, detail=f"Internal error generating signals: {str(e)}")


@router.post("/backtest")
async def backtest_strategy(request: BacktestRequest):
    """
    Backtest a strategy and return performance metrics.
    """
    try:
        # Fetch OHLC data
        symbol_norm = fyers_service.normalize_symbol(request.symbol)
        
        from datetime import date, timedelta
        range_from = (date.today() - timedelta(days=request.duration)).strftime("%Y-%m-%d")
        range_to = date.today().strftime("%Y-%m-%d")
        
        raw_data = fyers_service.fetch_ohlc(symbol_norm, request.interval, range_from, range_to)
        
        if not raw_data:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        # Handle timestamp conversion - check if it's Unix timestamp or string
        if pd.api.types.is_numeric_dtype(df['timestamp']):
            # Unix timestamp (seconds)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        else:
            # String datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        df.set_index('timestamp', inplace=True)
        
        # Initialize strategy builder
        builder = StrategyBuilder()
        
        # Add all indicators
        df = builder.add_all_indicators(df, request.parameters)
        
        # Add patterns if needed
        if request.strategy_name == 'pattern_trend':
            df = builder.detect_all_patterns(df)
        
        # Generate signals
        signals = builder.execute_strategy(df, request.strategy_name, **request.parameters)
        
        # Backtest
        results = builder.backtest_strategy(df, signals, request.initial_capital)
        
        # Format trades
        if 'trades' in results:
            formatted_trades = []
            for trade in results['trades']:
                formatted_trades.append({
                    'entry_price': float(trade['entry_price']),
                    'exit_price': float(trade['exit_price']),
                    'quantity': int(trade['quantity']),
                    'pnl': float(trade['pnl']),
                    'pnl_percent': float(trade['pnl_percent']),
                    'entry_time': str(trade['entry_time']),
                    'exit_time': str(trade['exit_time'])
                })
            results['trades'] = formatted_trades
        
        return {
            "symbol": request.symbol,
            "interval": request.interval,
            "strategy": request.strategy_name,
            "backtest_results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-strategies")
async def get_available_strategies():
    """
    Get list of available trading strategies and their descriptions.
    """
    return {
        "strategies": [
            {
                "name": "supertrend_rsi",
                "description": "Combines Supertrend indicator with RSI for trend-following with momentum confirmation",
                "parameters": {
                    "rsi_oversold": "RSI oversold level (default: 30)",
                    "rsi_overbought": "RSI overbought level (default: 70)",
                    "supertrend_period": "Supertrend period (default: 7)",
                    "supertrend_mult": "Supertrend multiplier (default: 3)"
                }
            },
            {
                "name": "macd_bb",
                "description": "MACD crossover with Bollinger Bands for trend and volatility analysis",
                "parameters": {
                    "macd_fast": "MACD fast period (default: 12)",
                    "macd_slow": "MACD slow period (default: 26)",
                    "macd_signal": "MACD signal period (default: 9)",
                    "bb_period": "Bollinger Bands period (default: 20)",
                    "bb_std": "Bollinger Bands standard deviation (default: 2)"
                }
            },
            {
                "name": "ema_crossover",
                "description": "Simple EMA crossover strategy for trend identification",
                "parameters": {
                    "fast_period": "Fast EMA period (default: 9)",
                    "slow_period": "Slow EMA period (default: 21)"
                }
            },
            {
                "name": "pattern_trend",
                "description": "Candlestick patterns combined with trend analysis for reversal signals",
                "parameters": {
                    "ema_period": "EMA period for trend detection (default: 50)"
                }
            }
        ]
    }


@router.get("/available-indicators")
async def get_available_indicators():
    """
    Get list of available technical indicators (matching available strategies).
    """
    return {
        "indicators": [
            {"name": "rsi", "description": "Relative Strength Index - momentum oscillator"},
            {"name": "macd", "description": "Moving Average Convergence Divergence - trend and momentum"},
            {"name": "supertrend", "description": "Supertrend - trend-following indicator"},
            {"name": "bollinger", "description": "Bollinger Bands - volatility indicator"},
            {"name": "adx", "description": "Average Directional Index - trend strength"},
            {"name": "atr", "description": "Average True Range - volatility measurement"},
            {"name": "renko", "description": "Renko Chart - price movement-based trend detection"}
        ]
    }
