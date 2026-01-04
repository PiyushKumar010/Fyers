"""
Positions and holdings routes
"""
from fastapi import APIRouter, HTTPException
from app.services.fyers import get_fyers_client

router = APIRouter(prefix="/positions", tags=["Positions"])


@router.get("")
def get_positions():
    """
    Get all open positions.
    """
    try:
        fyers = get_fyers_client()
        
        response = fyers.positions()
        
        if response.get("s") != "ok":
            error_msg = response.get("message", "Unknown error")
            raise HTTPException(status_code=400, detail=f"Fyers API error: {error_msg}")
        
        net_positions = response.get("netPositions", [])
        
        # Format positions for better readability
        formatted_positions = []
        for pos in net_positions:
            formatted_positions.append({
                "symbol": pos.get("symbol", ""),
                "productType": pos.get("productType", ""),
                "side": pos.get("side", 0),  # 1 for long, -1 for short
                "qty": pos.get("qty", 0),
                "avgPrice": pos.get("avgPrice", 0),
                "netPrice": pos.get("netPrice", 0),
                "ltp": pos.get("ltp", 0),
                "pnl": pos.get("pl", 0),
                "realizedPnl": pos.get("realizedPnl", 0),
                "unrealizedPnl": pos.get("unrealizedPnl", 0),
                "qtyMultiplier": pos.get("qtyMultiplier", 1)
            })
        
        return {
            "positions": formatted_positions,
            "count": len(formatted_positions)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")


@router.get("/holdings")
def get_holdings():
    """
    Get all holdings (CNC positions).
    """
    try:
        fyers = get_fyers_client()
        
        response = fyers.holdings()
        
        if response.get("s") != "ok":
            error_msg = response.get("message", "Unknown error")
            raise HTTPException(status_code=400, detail=f"Fyers API error: {error_msg}")
        
        holdings = response.get("holdings", [])
        
        # Format holdings for better readability
        formatted_holdings = []
        for holding in holdings:
            formatted_holdings.append({
                "symbol": holding.get("symbol", ""),
                "quantity": holding.get("quantity", 0),
                "avgPrice": holding.get("avgPrice", 0),
                "ltp": holding.get("ltp", 0),
                "currentValue": holding.get("currentValue", 0),
                "investedValue": holding.get("investedValue", 0),
                "pnl": holding.get("pl", 0),
                "pnlPercent": holding.get("plPercent", 0)
            })
        
        return {
            "holdings": formatted_holdings,
            "count": len(formatted_holdings)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch holdings: {str(e)}")


