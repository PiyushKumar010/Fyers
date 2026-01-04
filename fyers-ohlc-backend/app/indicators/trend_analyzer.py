"""Trend analyzer - clean implementation

This module implements the exact trend detection and Stochastic Oscillator
logic provided in the prompt but in a single, well-structured class.
The trading logic (higher-high/higher-low for uptrend, lower-high/lower-low
for downtrend, last 3 candles confirmation and previous 2-candle opposite
pattern) is preserved exactly.
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import pytz

from app.services import fyers as fyers_service
from app.utils.market_utils import adjust_date_for_market


class TrendAnalyzer:
    def __init__(self, fyers_client: Optional[object] = None):
        # keep optional client for compatibility; service functions use internal client
        self.fyers_client = fyers_client
        self.ist = pytz.timezone("Asia/Kolkata")

    def fetch_ohlc_data(self, symbol: str, interval: str, duration: int) -> pd.DataFrame:
        """
        Fetch OHLC data using the project's Fyers service and return a pandas DataFrame
        with columns: datetime (tz-aware IST), open, high, low, close, volume.
        """
        if duration <= 0:
            raise ValueError("duration must be a positive integer")

        # calculate range and adjust for non-trading days
        range_to_raw = datetime.now().date().strftime("%Y-%m-%d")
        range_to = adjust_date_for_market(range_to_raw)
        range_from = (datetime.strptime(range_to, "%Y-%m-%d").date() - timedelta(days=duration)).strftime("%Y-%m-%d")

        # normalize symbol and fetch raw candles
        symbol_norm = fyers_service.normalize_symbol(symbol)
        try:
            raw = fyers_service.fetch_ohlc(symbol_norm, interval, range_from, range_to)
        except Exception as exc:
            message = str(exc)
            if "no_data" in message.lower():
                return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
            raise

        if not raw:
            return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(raw)

        # parse time strings to timezone-aware datetimes (IST)
        if "time" in df.columns:
            df["datetime"] = pd.to_datetime(df["time"], format="%Y-%m-%d %H:%M")
            df.drop(columns=["time"], inplace=True)
        elif "timestamp" in df.columns:
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
            df.drop(columns=["timestamp"], inplace=True)

        if df["datetime"].dt.tz is None:
            df["datetime"] = df["datetime"].dt.tz_localize(self.ist)
        else:
            df["datetime"] = df["datetime"].dt.tz_convert(self.ist)

        # ensure numeric types and consistent column names
        df = df.rename(columns={
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        })

        for c in ["open", "high", "low", "close"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0).astype(int)

        # keep ordering by datetime
        df = df.sort_values("datetime").reset_index(drop=True)

        return df[["datetime", "open", "high", "low", "close", "volume"]]

    def detect_trend(self, df: pd.DataFrame) -> Optional[str]:
        """
        Detect Uptrend/Downtrend using the exact candle logic described:
        - Last 3 candles must be bullish for Uptrend (close>open) and show
          higher highs and higher lows across those 3 candles.
        - Additionally, the prior 2 candles must be bearish and show lower highs/lows.
        - Symmetric logic for Downtrend.

        Returns 'Uptrend', 'Downtrend', or None.
        """
        # Need at least 5 candles to perform checks (3 for recent, 2 for prior)
        if len(df) < 5:
            return None

        i = len(df) - 1

        # helper to access columns with original capitalization compatibility
        O = df["open"]
        H = df["high"]
        L = df["low"]
        C = df["close"]

        try:
            # Uptrend checks
            recent_bullish = all(C.iloc[i - j] > O.iloc[i - j] for j in range(3))
            higher_highs = all(H.iloc[i - j] > H.iloc[i - j - 1] for j in range(2, -1, -1))
            higher_lows = all(L.iloc[i - j] > L.iloc[i - j - 1] for j in range(2, -1, -1))

            prior_bearish = all(C.iloc[i - 3 - j] < O.iloc[i - 3 - j] for j in range(2))
            prior_lower_highs = all(H.iloc[i - 2 - j] < H.iloc[i - 3 - j] for j in range(2))
            prior_lower_lows = all(L.iloc[i - 2 - j] < L.iloc[i - 3 - j] for j in range(2))

            if recent_bullish and higher_highs and higher_lows and prior_bearish and prior_lower_highs and prior_lower_lows:
                return "Uptrend"

            # Downtrend checks
            recent_bearish = all(C.iloc[i - j] < O.iloc[i - j] for j in range(3))
            lower_highs = all(H.iloc[i - j] < H.iloc[i - j - 1] for j in range(2, -1, -1))
            lower_lows = all(L.iloc[i - j] < L.iloc[i - j - 1] for j in range(2, -1, -1))

            prior_bullish = all(C.iloc[i - 3 - j] > O.iloc[i - 3 - j] for j in range(2))
            prior_higher_highs = all(H.iloc[i - 2 - j] > H.iloc[i - 3 - j] for j in range(2))
            prior_higher_lows = all(L.iloc[i - 2 - j] > L.iloc[i - 3 - j] for j in range(2))

            if recent_bearish and lower_highs and lower_lows and prior_bullish and prior_higher_highs and prior_higher_lows:
                return "Downtrend"

        except IndexError:
            return None

        return None

    def calculate_stochastic_oscillator(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic %K and %D using pandas rolling windows.

        %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
        %D = simple moving average of %K over d_period

        Returns two pandas Series aligned with the dataframe; values will be NaN
        until enough data points exist.
        """
        if len(df) < k_period:
            # return empty series aligned to df index
            return pd.Series(index=df.index, dtype='float64'), pd.Series(index=df.index, dtype='float64')

        low_min = df["low"].rolling(window=k_period, min_periods=k_period).min()
        high_max = df["high"].rolling(window=k_period, min_periods=k_period).max()

        denom = high_max - low_min
        k = 100 * ((df["close"] - low_min) / denom.replace(0, pd.NA))
        d = k.rolling(window=d_period, min_periods=d_period).mean()

        return k, d

    def analyze_market(self, symbol: str, interval: str = "5", duration: int = 5) -> Dict[str, Any]:
        """
        High-level helper that fetches data, detects trend and computes stochastic values.
        Returns a clean dictionary suitable for API responses.
        """
        df = self.fetch_ohlc_data(symbol, interval, duration)
        if df.empty:
            return {"error": "no_data"}

        trend = self.detect_trend(df)
        k, d = self.calculate_stochastic_oscillator(df)

        latest = df.iloc[-1]

        return {
            "symbol": symbol,
            "timestamp": latest["datetime"].isoformat(),
            "open": float(latest["open"]),
            "high": float(latest["high"]),
            "low": float(latest["low"]),
            "close": float(latest["close"]),
            "volume": int(latest["volume"]),
            "trend": trend,
            "stochastic": {
                "k": float(k.iloc[-1]) if not k.empty and pd.notna(k.iloc[-1]) else None,
                "d": float(d.iloc[-1]) if not d.empty and pd.notna(d.iloc[-1]) else None,
            },
            "is_overbought": (k.iloc[-1] > 80) if (not k.empty and pd.notna(k.iloc[-1])) else False,
            "is_oversold": (k.iloc[-1] < 20) if (not k.empty and pd.notna(k.iloc[-1])) else False,
            "candle_count": len(df),
        }

