import pandas as pd
import numpy as np
from typing import Tuple


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period, min_periods=1).mean()
    return atr


def bollinger_bands(df: pd.DataFrame, window: int = 20, std_multiplier: float = 2.0) -> pd.DataFrame:
    close = df["close"]
    ma = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = ma + std_multiplier * std
    lower = ma - std_multiplier * std
    return pd.DataFrame({"bb_mid": ma, "bb_upper": upper, "bb_lower": lower})


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    close = df["close"]
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    close = df["close"]
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(period, min_periods=1).mean()
    avg_loss = loss.rolling(period, min_periods=1).mean()
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _plus_minus_dm(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    return plus_dm, minus_dm


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]

    plus_dm, minus_dm = _plus_minus_dm(df)
    atr_series = atr(df, period)

    plus_di = 100 * (plus_dm.rolling(period).sum() / atr_series)
    minus_di = 100 * (minus_dm.rolling(period).sum() / atr_series)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(period).mean()
    return adx.fillna(0)


def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    hl2 = (df["high"] + df["low"]) / 2
    atr_series = atr(df, period)
    upperband = hl2 + (multiplier * atr_series)
    lowerband = hl2 - (multiplier * atr_series)

    final_upper = upperband.copy()
    final_lower = lowerband.copy()
    supertrend = pd.Series(index=df.index, dtype='float64')
    in_uptrend = True

    for i in range(len(df)):
        if i == 0:
            final_upper.iat[i] = upperband.iat[i]
            final_lower.iat[i] = lowerband.iat[i]
            supertrend.iat[i] = final_lower.iat[i]
            continue

        if upperband.iat[i] < final_upper.iat[i - 1] or df["close"].iat[i - 1] > final_upper.iat[i - 1]:
            final_upper.iat[i] = upperband.iat[i]
        else:
            final_upper.iat[i] = final_upper.iat[i - 1]

        if lowerband.iat[i] > final_lower.iat[i - 1] or df["close"].iat[i - 1] < final_lower.iat[i - 1]:
            final_lower.iat[i] = lowerband.iat[i]
        else:
            final_lower.iat[i] = final_lower.iat[i - 1]

        if supertrend.iat[i - 1] == final_upper.iat[i - 1] and df["close"].iat[i] <= final_upper.iat[i]:
            supertrend.iat[i] = final_upper.iat[i]
        elif supertrend.iat[i - 1] == final_upper.iat[i - 1] and df["close"].iat[i] > final_upper.iat[i]:
            supertrend.iat[i] = final_lower.iat[i]
        elif supertrend.iat[i - 1] == final_lower.iat[i - 1] and df["close"].iat[i] >= final_lower.iat[i]:
            supertrend.iat[i] = final_lower.iat[i]
        else:
            supertrend.iat[i] = final_upper.iat[i]

    return supertrend
