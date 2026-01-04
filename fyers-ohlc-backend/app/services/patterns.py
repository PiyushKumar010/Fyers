import pandas as pd
import numpy as np


def detect_doji(df: pd.DataFrame, threshold: float = 0.1) -> pd.Series:
    """Mark True where candle body is small relative to range. threshold is fraction of range."""
    body = (df["close"] - df["open"]).abs()
    range_ = (df["high"] - df["low"]).replace(0, np.nan)
    is_doji = (body / range_) <= threshold
    return is_doji.fillna(False)


def detect_hammer(df: pd.DataFrame) -> pd.Series:
    body = (df["close"] - df["open"]).abs()
    lower_wick = df["open"].where(df["close"] >= df["open"], df["close"]) - df["low"]
    upper_wick = df["high"] - df["close"].where(df["close"] >= df["open"], df["open"]) 

    condition = (body <= (upper_wick + lower_wick) * 0.3) & (lower_wick >= 2 * body)
    return condition.fillna(False)


def detect_shooting_star(df: pd.DataFrame) -> pd.Series:
    body = (df["close"] - df["open"]).abs()
    upper_wick = df["high"] - df["close"].where(df["close"] >= df["open"], df["open"]) 
    lower_wick = df["open"].where(df["close"] >= df["open"], df["close"]) - df["low"]

    condition = (body <= (upper_wick + lower_wick) * 0.3) & (upper_wick >= 2 * body)
    return condition.fillna(False)


def detect_marubozu(df: pd.DataFrame, wick_threshold: float = 0.01) -> pd.Series:
    # Marubozu: almost no wicks
    upper_wick = df["high"] - df[["open", "close"]].max(axis=1)
    lower_wick = df[["open", "close"]].min(axis=1) - df["low"]
    candle_range = df["high"] - df["low"]
    is_marubozu = ((upper_wick / candle_range) <= wick_threshold) & ((lower_wick / candle_range) <= wick_threshold)
    return is_marubozu.fillna(False)


def flag_patterns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["pattern_doji"] = detect_doji(df)
    df["pattern_hammer"] = detect_hammer(df)
    df["pattern_shooting_star"] = detect_shooting_star(df)
    df["pattern_marubozu"] = detect_marubozu(df)
    return df
