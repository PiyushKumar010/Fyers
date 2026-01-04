from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.trading_system import get_trading_system, TradingSystem
from app.schemas.trading import (
    TradingConfig,
    TradingStatus,
    TradingSignal
)

router = APIRouter()

@router.post("/start", response_model=TradingStatus)
async def start_trading(config: TradingConfig):
    """Start the trading system with the given configuration"""
    try:
        trading_system = await get_trading_system()
        trading_system.config = config.dict()
        trading_system.tracked_tickers = config.tickers
        trading_system.capital = config.initial_capital
        trading_system.risk_per_trade = config.risk_per_trade
        trading_system.atr_periods = config.atr_periods
        trading_system.multipliers = config.multipliers
        
        await trading_system.start()
        
        return {
            "is_running": trading_system.is_running,
            "tracked_tickers": trading_system.tracked_tickers,
            "active_positions": trading_system.active_positions,
            "pending_orders": trading_system.pending_orders,
            "config": config.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stop", response_model=Dict[str, bool])
async def stop_trading():
    """Stop the trading system"""
    try:
        trading_system = await get_trading_system()
        await trading_system.stop()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status", response_model=TradingStatus)
async def get_status():
    """Get current trading system status"""
    try:
        trading_system = await get_trading_system()
        return {
            "is_running": trading_system.is_running,
            "tracked_tickers": trading_system.tracked_tickers,
            "active_positions": trading_system.active_positions,
            "pending_orders": trading_system.pending_orders,
            "config": {
                "tickers": trading_system.tracked_tickers,
                "initial_capital": trading_system.capital,
                "risk_per_trade": trading_system.risk_per_trade,
                "atr_periods": trading_system.atr_periods,
                "multipliers": trading_system.multipliers
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/signals/{ticker}", response_model=TradingSignal)
async def get_signals(ticker: str, interval: str = "5", days: int = 5):
    """Get trading signals for a specific ticker"""
    try:
        from app.indicators.candlestick_patterns import generate_trading_signals
        from app.services.fyers import fetch_ohlc
        
        ohlc_data = await fetch_ohlc(ticker, interval, days)
        if not ohlc_data:
            raise HTTPException(status_code=404, detail="No data available")
            
        signals = generate_trading_signals(ohlc_data)
        return {
            "symbol": ticker,
            "signal": signals['signal'],
            "price": signals['current_price'],
            "timestamp": signals['timestamp'].isoformat(),
            "indicators": signals['indicators'],
            "position_size": signals['position_size'],
            "trend": signals['trend'],
            "levels": signals['levels']
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/positions/close/{ticker}", response_model=Dict[str, str])
async def close_position(ticker: str):
    """Close a specific position"""
    try:
        trading_system = await get_trading_system()
        await trading_system._exit_position(ticker)
        return {"status": f"Position closed for {ticker}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/config", response_model=TradingConfig)
async def get_config():
    """Get current trading configuration"""
    trading_system = await get_trading_system()
    return {
        "tickers": trading_system.tracked_tickers,
        "initial_capital": trading_system.capital,
        "risk_per_trade": trading_system.risk_per_trade,
        "atr_periods": trading_system.atr_periods,
        "multipliers": trading_system.multipliers
    }
