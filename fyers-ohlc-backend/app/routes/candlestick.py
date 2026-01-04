from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import asyncio
from app.services.fyers import fetch_ohlc, normalize_symbol
from app.indicators.candlestick_patterns import analyze_candlestick_patterns

router = APIRouter()

@router.get("/analyze/{symbol}")
async def analyze_candlestick(symbol: str, interval: str = "5", days: int = 5) -> Dict[str, Any]:
    """
    Analyze candlestick patterns for a given symbol and time frame.
    
    Args:
        symbol: Stock symbol (e.g., 'NSE:RELIANCE-EQ')
        interval: Candle interval in minutes (1, 5, 15, 30, 60, etc.)
        days: Number of days of historical data to fetch
        
    Returns:
        Dict containing candlestick pattern analysis
    """
    try:
        # Fetch OHLC data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Normalize symbol and prepare resolution expected by fetch_ohlc
        try:
            symbol_norm = normalize_symbol(symbol)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        resolution = interval  # fetch_ohlc expects '1','5','15','60','D', etc.

        # Fetch OHLC data off the event loop
        ohlc_data = await asyncio.to_thread(
            fetch_ohlc,
            symbol_norm,
            resolution,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if not ohlc_data or len(ohlc_data) == 0:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # fetch_ohlc returns a list of dicts with keys: time, open, high, low, close, volume
        df = pd.DataFrame(ohlc_data)
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
            df = df.set_index('time')
        elif 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.set_index('timestamp')
        else:
            raise HTTPException(status_code=500, detail="Unexpected OHLC format from FYERS")
        
        # Analyze candlestick patterns
        analysis = analyze_candlestick_patterns(df)
        
        # Add symbol and time frame info
        analysis['symbol'] = symbol
        analysis['interval'] = interval
        analysis['timeframe'] = f"{interval}min"
        
        return analysis
        
    except Exception as e:
        msg = str(e)
        low = msg.lower()
        if any(k in low for k in ["not authenticated", "could not authenticate", "authenticate", "-16"]):
            raise HTTPException(status_code=401, detail="FYERS authentication required. Please authenticate via /auth/login")
        raise HTTPException(status_code=500, detail=f"Error analyzing candlestick patterns: {msg}")

@router.get("/signals")
async def get_candlestick_signals(
    symbols: str = "NSE:RELIANCE-EQ,NSE:TATAMOTORS-EQ,NSE:INFY-EQ,NSE:HDFCBANK-EQ,NSE:ICICIBANK-EQ",
    interval: str = "5",
    days: int = 5,
) -> Dict[str, Any]:
    """
    Get candlestick signals for multiple symbols.
    
    Args:
        symbols: Comma-separated list of symbols
        interval: Candle interval in minutes
        days: Number of days of historical data
        
    Returns:
        Dict containing signals for all symbols
    """
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    results = {}
    
    for symbol in symbol_list:
        try:
            analysis = await analyze_candlestick(symbol, interval, days)
            results[symbol] = {
                "signal": analysis.get("signal", "neutral"),
                "signal_strength": analysis.get("signal_strength", "weak"),
                "patterns": analysis.get("patterns", {}),
                "trend": analysis.get("trend", "unknown"),
                "current_price": analysis.get("current_price"),
                "nearest_support": analysis.get("nearest_support"),
                "nearest_resistance": analysis.get("nearest_resistance"),
                "support_distance_pct": analysis.get("support_distance_pct"),
                "resistance_distance_pct": analysis.get("resistance_distance_pct")
            }
        except Exception as e:
            results[symbol] = {"error": str(e)}
    
    return {"signals": results}
