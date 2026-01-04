from fastapi import APIRouter, HTTPException, Query
from app.services.fyers import fetch_ohlc, normalize_symbol
from app.services import indicators, patterns, renko, strategies
from app.utils.serializer import serialize_dataframe_records
import pandas as pd

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.get("")
def get_signals(
    symbol: str = Query(..., description="Symbol e.g. RELIANCE or NSE:RELIANCE-EQ"),
    resolution: str = Query("5", description="Resolution: 1,5,15,60,D"),
    from_date: str = Query(...),
    to_date: str = Query(...),
    renko_brick: float = Query(None, description="Optional brick size for Renko")
):
    try:
        symbol_norm = normalize_symbol(symbol)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        candles = fetch_ohlc(symbol_norm, resolution, from_date, to_date)
    except Exception as e:
        msg = str(e).lower()
        if any(k in msg for k in ["not authenticated", "could not authenticate", "authenticate", "-16"]):
            raise HTTPException(status_code=401, detail="FYERS authentication required. Please authenticate via /auth/login")
        raise HTTPException(status_code=500, detail=f"Failed to fetch OHLC: {str(e)}")

    if not candles:
        raise HTTPException(status_code=404, detail="No OHLC data returned")

    # convert to dataframe
    df = pd.DataFrame(candles)
    # expecting time, open, high, low, close, volume
    df = df.rename(columns={"time": "date"})
    df["date"] = pd.to_datetime(df["date"]) if not pd.api.types.is_datetime64_any_dtype(df["date"]) else df["date"]
    df = df.set_index("date")

    # ensure numeric types
    df["open"] = pd.to_numeric(df["open"], errors="coerce")
    df["high"] = pd.to_numeric(df["high"], errors="coerce")
    df["low"] = pd.to_numeric(df["low"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0)

    # compute indicators
    df_ind = indicators.macd(df)
    df = df.join(df_ind)
    df["rsi"] = indicators.rsi(df)
    df["atr"] = indicators.atr(df)
    df["adx"] = indicators.adx(df)
    df["supertrend"] = indicators.supertrend(df)
    bb = indicators.bollinger_bands(df)
    df = df.join(bb)

    # patterns
    df = patterns.flag_patterns(df)

    # renko
    renko_df = renko.to_renko(df, brick_size=renko_brick)

    # strategies
    strat = strategies.macd_rsi_supertrend_signal(df)

    # prepare payload
    latest = strat.tail(50).reset_index()
    latest_records = serialize_dataframe_records(latest)

    return {
        "symbol": symbol_norm,
        "count": len(df),
        "indicators_sample": latest_records,
        "renko": serialize_dataframe_records(renko_df.tail(200))
    }
