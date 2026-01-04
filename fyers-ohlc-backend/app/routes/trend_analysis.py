from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import pytz

from app.services import fyers as fyers_service
from app.indicators.trend_analyzer import TrendAnalyzer
from app.utils.serializer import convert_to_serializable

router = APIRouter(prefix="/api/trend", tags=["trend_analysis"])

@router.get("/analyze")
async def analyze_trend(
    symbol: str,
    interval: str = Query("5", description="Candle interval in minutes (e.g., '5' for 5 minutes)"),
    duration: int = Query(5, description="Number of days of historical data to analyze (max 30)")
):
    """
    Analyze market trend and indicators for a given symbol
    
    Parameters:
    - symbol: Stock symbol (e.g., 'NSE:RELIANCE-EQ')
    - interval: Candle interval in minutes (e.g., '5' for 5 minutes)
    - duration: Number of days of historical data to analyze (max 30)
    """
    try:
        # Validate inputs
        if duration > 30:
            raise HTTPException(status_code=400, detail="Duration cannot exceed 30 days")
            
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        # Initialize analyzer
        analyzer = TrendAnalyzer()
        
        # Perform analysis
        result = analyzer.analyze_market(symbol, interval, duration)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
            
        return {
            "status": "success",
            "data": convert_to_serializable(result)
        }
        
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stochastic")
async def get_stochastic_oscillator(
    symbol: str,
    interval: str = Query("5", description="Candle interval in minutes"),
    duration: int = Query(5, description="Number of days of historical data"),
    k_period: int = Query(14, description="Lookback period for %K"),
    d_period: int = Query(3, description="Smoothing period for %D")
):
    """
    Get Stochastic Oscillator values for a given symbol
    """
    try:
        if duration > 30:
            raise HTTPException(status_code=400, detail="Duration cannot exceed 30 days")
            
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
            
        analyzer = TrendAnalyzer()
        
        # Fetch OHLC data
        df = analyzer.fetch_ohlc_data(symbol, interval, duration)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available for the given parameters")
        
        # Calculate Stochastic Oscillator
        k, d = analyzer.calculate_stochastic_oscillator(df, k_period, d_period)
        
        # Prepare response
        result = []
        for i in range(len(df)):
            if i >= k_period - 1:  # Only include periods where we have enough data
                result.append({
                    'timestamp': df['datetime'].iloc[i].isoformat(),
                    'close': float(df['close'].iloc[i]),
                    'k': float(k.iloc[i]) if not pd.isna(k.iloc[i]) else None,
                    'd': float(d.iloc[i]) if not pd.isna(d.iloc[i]) else None,
                    'is_overbought': k.iloc[i] > 80 if not pd.isna(k.iloc[i]) else False,
                    'is_oversold': k.iloc[i] < 20 if not pd.isna(k.iloc[i]) else False
                })
        
        return {
            "status": "success",
            "symbol": symbol,
            "interval": interval,
            "data": convert_to_serializable(result)
        }
        
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_trend_history(
    symbol: str,
    interval: str = Query("5", description="Candle interval in minutes"),
    duration: int = Query(5, description="Number of days of historical data")
):
    """
    Get historical trend data for a symbol
    """
    try:
        if duration > 30:
            raise HTTPException(status_code=400, detail="Duration cannot exceed 30 days")
            
        analyzer = TrendAnalyzer()
        
        # Fetch OHLC data
        df = analyzer.fetch_ohlc_data(symbol, interval, duration)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available for the given parameters")
        
        # Calculate trends for each period
        trends = []
        for i in range(len(df)):
            if i >= 4:  # Need at least 5 candles for trend detection
                window = df.iloc[i-4:i+1].copy()
                trend_label = analyzer.detect_trend(window)
                trends.append({
                    'timestamp': df['datetime'].iloc[i].isoformat(),
                    'open': float(df['open'].iloc[i]),
                    'high': float(df['high'].iloc[i]),
                    'low': float(df['low'].iloc[i]),
                    'close': float(df['close'].iloc[i]),
                    'trend': trend_label,
                    'confidence': 100 if trend_label else 0
                })
        
        return {
            "status": "success",
            "symbol": symbol,
            "interval": interval,
            "data": convert_to_serializable(trends)
        }
        
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
