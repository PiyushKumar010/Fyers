from typing import Optional
from app import database


def lookup_instrument_by_symbol(symbol: str) -> Optional[dict]:
    """Return instrument info from DB if available, otherwise return minimal dict.

    This helper allows future expansion to query Fyers instruments API.
    """
    instruments_collection = getattr(database, "instruments_collection", None)
    if instruments_collection:
        doc = instruments_collection.find_one({"symbol": symbol})
        if doc:
            return doc

    # Fallback: return basic structure
    return {"symbol": symbol, "token": None}
