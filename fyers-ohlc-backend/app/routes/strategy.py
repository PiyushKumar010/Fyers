from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta

from ..services.fyers import fetch_ohlc
from ..strategies import SupertrendStrategy
from ..backtest.engine import BacktestEngine
from ..schemas.strategy import BacktestRequest, BacktestResult, StrategySignal

router = APIRouter(prefix="/strategy", tags=["strategy"])

@router.post("/backtest", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest):
    try:
        # Fetch historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days)
        
        ohlc_data = await fetch_ohlc(
            symbol=request.symbol,
            interval=request.interval,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not ohlc_data:
            raise HTTPException(status_code=404, detail="No data available for the given parameters")
            
        # Convert to DataFrame
        df = pd.DataFrame(ohlc_data)
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
            df = df.set_index('time')
        
        # Initialize strategy
        if request.strategy_name == "supertrend":
            strategy = SupertrendStrategy(
                symbol=request.symbol,
                atr_period=request.parameters.get('atr_period', 10),
                multiplier=request.parameters.get('multiplier', 3.0),
                risk_reward_ratio=request.parameters.get('risk_reward_ratio', 2.0)
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported strategy: {request.strategy_name}")
        
        # Generate signals
        signals = strategy.generate_signals(df)
        
        # Run backtest
        engine = BacktestEngine(initial_capital=request.initial_capital)
        result = engine.run(df, signals)
        
        # Prepare response
        return {
            "strategy": request.strategy_name,
            "symbol": request.symbol,
            "period": f"{start_date.date()} to {end_date.date()}",
            "total_trades": result['total_trades'],
            "win_rate": result['win_rate'],
            "net_pnl": result['net_pnl'],
            "max_drawdown": result['max_drawdown'],
            "profit_factor": result['profit_factor'],
            "signals": [s.to_dict() for s in signals[-10:]]  # Last 10 signals
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/{symbol}", response_model=List[StrategySignal])
async def get_latest_signals(
    symbol: str,
    strategy: str = "supertrend",
    interval: str = "5",
    days: int = 5
):
    try:
        # Fetch historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        ohlc_data = await fetch_ohlc(
            symbol=symbol,
            interval=interval,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not ohlc_data:
            raise HTTPException(status_code=404, detail="No data available")
            
        # Convert to DataFrame
        df = pd.DataFrame(ohlc_data)
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
            df = df.set_index('time')
        
        # Initialize strategy
        if strategy == "supertrend":
            strategy = SupertrendStrategy(symbol=symbol)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported strategy: {strategy}")
        
        # Generate signals
        signals = strategy.generate_signals(df)
        
        # Return only the latest signal
        latest_signal = signals[-1] if signals else None
        if latest_signal:
            return [latest_signal.to_dict()]
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
