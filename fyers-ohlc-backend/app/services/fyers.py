from fyers_apiv3 import fyersModel
from app import database
from app.config import settings
from datetime import datetime
from typing import Optional


def normalize_symbol(symbol: str) -> str:
    """
    Convert plain symbols like RELIANCE to FYERS format NSE:RELIANCE-EQ
    """
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty")
    
    symbol = symbol.strip().upper()
    if ":" not in symbol:
        return f"NSE:{symbol}-EQ"
    return symbol


def get_login_url():
    session = fyersModel.SessionModel(
        client_id=settings.FYERS_CLIENT_ID,
        redirect_uri=settings.FYERS_REDIRECT_URI,
        secret_key=settings.FYERS_SECRET_KEY,
        response_type="code",
        state="state123"
    )
    return session.generate_authcode()


def get_fyers_client():
    # tokens_collection may be None if Mongo is unavailable; handle that gracefully
    tokens_collection = database.tokens_collection
    if tokens_collection is None:
        print("[FYERS CLIENT] MongoDB not available")
        raise Exception("FYERS not authenticated: tokens storage is not available (MongoDB disconnected)")

    token_doc = tokens_collection.find_one()
    print(f"[FYERS CLIENT] Token document from DB: {token_doc}")
    if not token_doc or "access_token" not in token_doc:
        print("[FYERS CLIENT] No valid token found in DB")
        raise Exception("FYERS not authenticated: no token found in DB")

    # auto-refresh if token is near expiry (with small buffer)
    try:
        expires_in = int(token_doc.get("expires_in", 0))
        obtained_at = float(token_doc.get("obtained_at", 0))
    except Exception:
        expires_in = 0
        obtained_at = 0

    if expires_in > 0 and obtained_at > 0:
        expiry_time = obtained_at + expires_in
        # refresh if already expired or will expire within 60 seconds
        if datetime.utcnow().timestamp() >= (expiry_time - 60):
            # attempt refresh; this will update DB entry
            try:
                refresh_access_token()
                token_doc = tokens_collection.find_one()
            except Exception as e:
                # allow falling through and raising if refresh fails
                print(f"Token refresh attempt failed: {e}")

    access_token = token_doc["access_token"]

    fyers = fyersModel.FyersModel(
        client_id=settings.FYERS_CLIENT_ID,
        token=access_token,
        log_path=""
    )

    return fyers


def refresh_access_token() -> dict:
    """
    Refresh the access token using the stored refresh token and update the DB.

    Returns the new token document.
    """
    tokens_collection = database.tokens_collection
    if tokens_collection is None:
        raise Exception("Tokens storage is not available (MongoDB disconnected)")

    token_doc = tokens_collection.find_one()
    if not token_doc:
        raise Exception("No token document found to refresh")

    refresh_token = token_doc.get("refresh_token")
    if not refresh_token:
        raise Exception("Refresh token not available; re-authentication required")

    session = fyersModel.SessionModel(
        client_id=settings.FYERS_CLIENT_ID,
        secret_key=settings.FYERS_SECRET_KEY,
        redirect_uri=settings.FYERS_REDIRECT_URI,
        response_type="code",
        grant_type="refresh_token",
    )

    session.set_token(refresh_token)
    response = session.generate_token()

    if not isinstance(response, dict) or "access_token" not in response:
        raise Exception(f"Failed to refresh token: {response}")

    # add timestamp and store
    token_entry = dict(response)
    token_entry["obtained_at"] = datetime.utcnow().timestamp()

    tokens_collection.delete_many({})
    tokens_collection.insert_one(token_entry)

    return token_entry


def get_latest_candle(symbol: str, resolution: str):
    """
    Fetch the most recent candle for a symbol at given resolution.
    Returns a single formatted candle dict or None.
    """
    fyers = get_fyers_client()

    # request a small range (today) and pick last candle
    today = datetime.utcnow().strftime("%Y-%m-%d")
    data = {
        "symbol": symbol,
        "resolution": resolution,
        "date_format": "1",
        "range_from": today,
        "range_to": today,
        "cont_flag": "1",
    }

    try:
        response = fyers.history(data)
    except Exception as e:
        raise Exception(f"Fyers API request failed: {str(e)}")
    # Handle no-data responses gracefully
    status = response.get("s")
    if status == "no_data":
        return None

    if status != "ok":
        raise Exception(f"Fyers API error: {response}")

    candles = response.get("candles", [])
    if not candles:
        return None

    c = candles[-1]
    if len(c) < 5:
        return None

    return {
        "time": datetime.fromtimestamp(c[0]).strftime("%Y-%m-%d %H:%M"),
        "open": float(c[1]),
        "high": float(c[2]),
        "low": float(c[3]),
        "close": float(c[4]),
        "volume": int(c[5]) if len(c) > 5 else 0,
    }


def fetch_ohlc(symbol: str, resolution: str, from_date: str, to_date: str):
    """
    Fetch OHLC data from Fyers API.
    
    Args:
        symbol: Stock symbol in Fyers format (e.g., NSE:RELIANCE-EQ)
        resolution: Time resolution (1, 5, 15, 60, D)
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
    
    Returns:
        List of formatted OHLC candles
    
    Raises:
        Exception: If API call fails or returns error
    """
    fyers = get_fyers_client()

    data = {
        "symbol": symbol,
        "resolution": resolution,
        "date_format": "1",
        "range_from": from_date,
        "range_to": to_date,
        "cont_flag": "1"
    }

    try:
        response = fyers.history(data)
    except Exception as e:
        raise Exception(f"Fyers API request failed: {str(e)}")

    status = response.get("s")
    # If Fyers returns 'no_data', return empty list so routes can reply with 404/empty payload
    if status == "no_data":
        return []

    if status != "ok":
        error_msg = response.get("message", "Unknown error from Fyers API")
        error_code = response.get("code", "UNKNOWN")
        raise Exception(f"Fyers API error [{error_code}]: {error_msg}")

    candles = response.get("candles", [])

    if not candles:
        return []

    formatted = []
    for c in candles:
        if len(c) < 6:
            continue  # Skip invalid candle data
        
        try:
            formatted.append({
                "time": datetime.fromtimestamp(c[0]).strftime("%Y-%m-%d %H:%M"),
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": int(c[5]) if len(c) > 5 else 0
            })
        except (ValueError, IndexError, TypeError) as e:
            print(f"Warning: Skipping invalid candle data: {c}, error: {e}")
            continue

    return formatted
