from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from pydantic import BaseModel
from app.services.strategy_engine import get_strategy_engine

router = APIRouter(prefix="/strategies", tags=["Strategies"])


class StrategyRequest(BaseModel):
    strategy: str
    symbol: str
    timeframe: str = "5"
    start_date: str = None
    end_date: str = None
    lookback_days: int = 30
    params: Dict[str, Any] = {}


@router.get("")
def list_strategies():
    """
    Get list of all available strategies.
    """
    engine = get_strategy_engine()
    strategies = engine.list_strategies()

    strategy_info = {
        'ADX': {
            'name': 'Average Directional Index',
            'description': 'Measures trend strength',
            'params': {'period': 14}
        },
        'ATR': {
            'name': 'Average True Range',
            'description': 'Measures volatility',
            'params': {'period': 14}
        },
        'BOLLINGER': {
            'name': 'Bollinger Bands',
            'description': 'Volatility bands for buy/sell signals',
            'params': {'period': 20, 'std_dev': 2.0}
        },
        'MACD': {
            'name': 'Moving Average Convergence Divergence',
            'description': 'Trend-following momentum indicator',
            'params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
        },
        'RSI': {
            'name': 'Relative Strength Index',
            'description': 'Momentum oscillator for overbought/oversold',
            'params': {'period': 14, 'oversold': 30, 'overbought': 70}
        },
        'SUPERTREND': {
            'name': 'Supertrend',
            'description': 'Trend-following indicator based on ATR',
            'params': {'atr_period': 7, 'multiplier': 3.0}
        },
        'RENKO': {
            'name': 'Renko Chart',
            'description': 'Price movement-based trend detection',
            'params': {'brick_size': None, 'atr_period': 14, 'atr_multiplier': 1.0, 'lookback': 3}
        }
    }

    return {
        'strategies': strategies,
        'details': {s: strategy_info.get(s, {}) for s in strategies}
    }


@router.post("/run")
def run_strategy(request: StrategyRequest):
    """
    Execute a trading strategy.
    """
    try:
        engine = get_strategy_engine()
        result = engine.run_strategy(
            strategy_name=request.strategy,
            symbol=request.symbol,
            timeframe=request.timeframe,
            lookback_days=request.lookback_days,
            start_date=request.start_date,
            end_date=request.end_date,
            **request.params
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy execution failed: {str(e)}")


@router.get("/run")
def run_strategy_get(
    strategy: str = Query(..., description="Strategy name"),
    symbol: str = Query(..., description="Stock symbol"),
    timeframe: str = Query("5", description="Timeframe (1, 5, 15, 60, D)"),
    lookback_days: int = Query(30, description="Lookback days"),
    **params
):
    """
    Execute a trading strategy (GET method for easy testing).
    """
    try:
        engine = get_strategy_engine()

        # Convert string params to appropriate types
        converted_params = {}
        for key, value in params.items():
            try:
                converted_params[key] = float(value)
                if isinstance(converted_params[key], float) and converted_params[key].is_integer():
                    converted_params[key] = int(converted_params[key])
            except Exception:
                converted_params[key] = value

        result = engine.run_strategy(
            strategy_name=strategy,
            symbol=symbol,
            timeframe=timeframe,
            lookback_days=lookback_days,
            **converted_params
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy execution failed: {str(e)}")


@router.get("/signals")
def get_latest_signals(
    symbol: str = Query(..., description="Stock symbol"),
    timeframe: str = Query("5", description="Timeframe"),
    lookback_days: int = Query(30, description="Lookback days")
):
    """
    Get latest signals from all strategies for a symbol.
    """
    try:
        engine = get_strategy_engine()
        strategies = engine.list_strategies()

        signals = {}
        last_ts = None
        for strategy_name in strategies:
            try:
                result = engine.run_strategy(
                    strategy_name=strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    lookback_days=lookback_days
                )
                signals[strategy_name] = {
                    'signal': result.get('signal', 'UNKNOWN'),
                    'value': result.get('value'),
                    'indicator': result.get('indicator')
                }
                if 'timestamp' in result:
                    last_ts = result['timestamp']
            except Exception as e:
                signals[strategy_name] = {
                    'error': str(e)
                }

        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'signals': signals,
            'timestamp': last_ts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")


