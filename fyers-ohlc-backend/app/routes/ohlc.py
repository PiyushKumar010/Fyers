from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from app.services.fyers import fetch_ohlc, normalize_symbol
from app.services.ohlc_cache import get_cached_ohlc, save_ohlc
from app.utils.market_utils import adjust_date_for_market, is_market_open, get_last_trading_day
from fastapi import WebSocket, WebSocketDisconnect
from app.services.fyers import get_latest_candle
from app.utils.serializer import convert_to_serializable
import asyncio

router = APIRouter(prefix="/ohlc", tags=["OHLC"])


def validate_date(date_str: str) -> datetime:
    """
    Validate and parse date string in YYYY-MM-DD format
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")


@router.get("")
@router.get("/")
def get_ohlc(
    symbol: str = Query(..., description="Stock symbol, e.g. RELIANCE or NSE:RELIANCE-EQ"),
    resolution: str = Query("5", description="Resolution: 1, 5, 15, 60, D"),
    from_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    to_date: str = Query(..., description="End date in YYYY-MM-DD format")
):
    """
    Fetch OHLC (Open, High, Low, Close) data for a given symbol.
    Returns cached data if available, otherwise fetches from Fyers API.
    Automatically adjusts dates to last trading day if market is closed.
    """
    try:
        # Store original dates for response metadata
        original_from_date = from_date
        original_to_date = to_date
        
        # Validate inputs
        try:
            from_dt = validate_date(from_date)
            to_dt = validate_date(to_date)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if from_dt > to_dt:
            raise HTTPException(
                status_code=400,
                detail="from_date cannot be after to_date"
            )

        if to_dt > datetime.now():
            raise HTTPException(
                status_code=400,
                detail="to_date cannot be in the future"
            )

        # Check if the requested date is a non-trading day and adjust
        is_open, close_reason = is_market_open(to_dt)
        adjusted_date = False
        
        if not is_open:
            # Adjust to last trading day
            adjusted_to_dt = get_last_trading_day(to_dt)
            print(f"[OHLC] Market closed on {to_date} ({close_reason}). Adjusting to last trading day: {adjusted_to_dt.strftime('%Y-%m-%d')}")
            to_date = adjusted_to_dt.strftime("%Y-%m-%d")
            to_dt = adjusted_to_dt
            adjusted_date = True
            
            # Also adjust from_date if it's after the adjusted to_date
            if from_dt > to_dt:
                from_date = to_date
                from_dt = to_dt

        # Validate resolution
        valid_resolutions = ["1", "5", "15", "60", "D"]
        if resolution not in valid_resolutions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid resolution. Must be one of: {', '.join(valid_resolutions)}"
            )

        # Normalize symbol for FYERS
        try:
            symbol = normalize_symbol(symbol)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # 1️⃣ Check cache
        cached = get_cached_ohlc(symbol, resolution, from_date, to_date)
        if cached:
            return {
                "source": "mongodb",
                "data": convert_to_serializable(cached),
                "count": len(cached),
                "market_closed": adjusted_date,
                "close_reason": close_reason if adjusted_date else None,
                "requested_date": original_to_date,
                "actual_date": to_date
            }

        # 2️⃣ Fetch from FYERS
        candles = fetch_ohlc(symbol, resolution, from_date, to_date)

        if not candles or len(candles) == 0:
            # FYERS returned no data for this symbol/date range.
            # Return an empty payload (200) so frontend can handle it gracefully
            return {
                "source": "fyers",
                "data": [],
                "count": 0,
                "note": "no_data",
                "market_closed": adjusted_date,
                "close_reason": close_reason if adjusted_date else None,
                "requested_date": original_to_date,
                "actual_date": to_date
            }

        # 3️⃣ Save to DB (async, non-blocking) - only for historical data
        # Live data is not saved to MongoDB by default (configurable)
        try:
            # The save_ohlc function will check if this is live data and skip if configured
            save_ohlc(symbol, resolution, candles)
        except Exception as e:
            # Log but don't fail the request if cache save fails
            print(f"Warning: Failed to cache OHLC data: {e}")

        return {
            "source": "fyers",
            "data": convert_to_serializable(candles),
            "count": len(candles),
            "market_closed": adjusted_date,
            "close_reason": close_reason if adjusted_date else None,
            "requested_date": original_to_date,
            "actual_date": to_date
        }

    except HTTPException:
        # Let FastAPI handle known HTTP errors
        raise

    except Exception as e:
        error_message = str(e)

        # FYERS-specific error handling
        # Map various authentication-related messages from services or FYERS API
        lowered = error_message.lower()
        if any(k in lowered for k in ["not authenticated", "could not authenticate", "authenticate", "authentication required", "-16"]):
            raise HTTPException(
                status_code=401,
                detail="FYERS authentication required. Please authenticate via /auth/login and complete the OAuth flow."
            )

        if "invalid symbol" in error_message.lower() or "symbol" in error_message.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid symbol: {symbol}. Use format like NSE:RELIANCE-EQ"
            )

        # Log unexpected errors
        print(f"Unexpected error in get_ohlc: {error_message}")

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {error_message}"
        )


@router.websocket("/ws")
async def websocket_ohlc(websocket: WebSocket, symbol: str = "", resolution: str = "1", interval: int = 5):
    """
    WebSocket endpoint for live OHLC updates.
    Query params: symbol, resolution, interval (seconds)
    """
    await websocket.accept()
    try:
        if not symbol:
            await websocket.send_json({"error": "symbol query parameter required"})
            await websocket.close()
            return

        # normalize symbol
        try:
            symbol = normalize_symbol(symbol)
        except Exception as e:
            await websocket.send_json({"error": str(e)})
            await websocket.close()
            return

        poll_interval = max(int(interval), 1)

        last_sent_time = None
        while True:
            try:
                try:
                    candle = await asyncio.to_thread(get_latest_candle, symbol, resolution)
                except Exception as e:
                    # Send error to client but keep the loop alive
                    try:
                        await websocket.send_json({"error": f"fetch_failed: {str(e)}"})
                    except Exception:
                        pass
                    await asyncio.sleep(poll_interval)
                    continue

                if candle is not None:
                    # Only send if new or different from last
                    if last_sent_time != candle.get("time"):
                        try:
                            await websocket.send_json({"symbol": symbol, "candle": candle})
                        except Exception:
                            # If sending fails (client disconnected), exit loop
                            break
                        last_sent_time = candle.get("time")

                await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                # Application or server is shutting down; close websocket gracefully
                try:
                    await websocket.close()
                except Exception:
                    pass
                break
            except Exception:
                # Log and continue; avoid letting unexpected exceptions bubble
                try:
                    await websocket.send_json({"error": "internal_websocket_error"})
                except Exception:
                    pass
                await asyncio.sleep(poll_interval)

    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass
