"""
Market data routes: LTP, Quotes, and other market information
"""
from fastapi import APIRouter, Query, HTTPException
from app.services.fyers import get_fyers_client
from app.utils.market_utils import get_market_status, is_market_open
from typing import List

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/status")
def market_status():
    """
    Get current market status (open/closed, reason, last trading day).
    Useful for determining if the market is open or closed.
    """
    return get_market_status()


@router.get("/ltp")
def get_ltp(symbol: str = Query(..., description="Stock symbol, e.g. NSE:RELIANCE-EQ")):
    """
    Get Last Traded Price (LTP) for a symbol.
    """
    try:
        fyers = get_fyers_client()
        
        # Fyers API endpoint for market quotes
        data = {
            "symbols": symbol
        }
        
        response = fyers.quotes(data)

        if response.get("s") != "ok":
            error_msg = response.get("message", "Unknown error")
            error_code = response.get("code")
            print(f"[MARKET][LTP] Fyers error for {symbol}: {response}")
            status_code = 429 if error_code == 429 else 400
            raise HTTPException(status_code=status_code, detail=f"Fyers API error [{error_code}]: {error_msg}")
        
        d = response.get("d", [])
        if not d:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        
        # Extract LTP from quote data
        quote = d[0].get("v", {})
        ltp = quote.get("lp", 0)  # Last price
        
        return {
            "symbol": symbol,
            "ltp": ltp,
            "timestamp": quote.get("t", 0),
            "volume": quote.get("v", 0),
            "change": quote.get("ch", 0),
            "change_percent": quote.get("chp", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch LTP: {str(e)}")


@router.get("/quote")
def get_quote(symbol: str = Query(..., description="Stock symbol, e.g. NSE:RELIANCE-EQ")):
    """
    Get complete quote data (OHLC, volume, etc.) for a symbol.
    """
    try:
        fyers = get_fyers_client()
        
        data = {
            "symbols": symbol
        }
        
        response = fyers.quotes(data)

        if response.get("s") != "ok":
            error_msg = response.get("message", "Unknown error")
            error_code = response.get("code")
            print(f"[MARKET][QUOTE] Fyers error for {symbol}: {response}")
            status_code = 429 if error_code == 429 else 400
            raise HTTPException(status_code=status_code, detail=f"Fyers API error [{error_code}]: {error_msg}")
        
        d = response.get("d", [])
        if not d:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        
        quote = d[0].get("v", {})
        
        return {
            "symbol": symbol,
            "open": quote.get("open_price", 0),
            "high": quote.get("high_price", 0),
            "low": quote.get("low_price", 0),
            "close": quote.get("prev_close_price", 0),
            "ltp": quote.get("lp", 0),  # Last traded price
            "volume": quote.get("volume", 0),
            "change": quote.get("ch", 0),
            "change_percent": quote.get("chp", 0),
            "timestamp": quote.get("t", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {str(e)}")


@router.get("/quotes")
def get_quotes(symbols: str = Query(..., description="Comma-separated symbols, e.g. NSE:RELIANCE-EQ,NSE:TCS-EQ")):
    """
    Get quotes for multiple symbols at once.
    """
    try:
        fyers = get_fyers_client()
        
        symbol_list = [s.strip() for s in symbols.split(",")]
        
        data = {
            "symbols": ",".join(symbol_list)
        }
        
        response = fyers.quotes(data)

        if response.get("s") != "ok":
            error_msg = response.get("message", "Unknown error")
            error_code = response.get("code")
            print(f"[MARKET][QUOTES] Fyers error for {symbols}: {response}")
            status_code = 429 if error_code == 429 else 400
            raise HTTPException(status_code=status_code, detail=f"Fyers API error [{error_code}]: {error_msg}")
        
        d = response.get("d", [])
        quotes = []
        
        for item in d:
            quote = item.get("v", {})
            quotes.append({
                "symbol": item.get("n", ""),
                "open": quote.get("open_price", 0),
                "high": quote.get("high_price", 0),
                "low": quote.get("low_price", 0),
                "close": quote.get("prev_close_price", 0),
                "ltp": quote.get("lp", 0),
                "volume": quote.get("volume", 0),
                "change": quote.get("ch", 0),
                "change_percent": quote.get("chp", 0),
                "timestamp": quote.get("t", 0)
            })
        
        return {
            "quotes": quotes,
            "count": len(quotes)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quotes: {str(e)}")

