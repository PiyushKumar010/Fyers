import pandas as pd
import numpy as np
from typing import List, Dict


def to_renko(df: pd.DataFrame, brick_size: float = None) -> pd.DataFrame:
    """Convert OHLC dataframe to simple Renko bricks.

    This is a light-weight Renko implementation: uses close prices and a fixed brick size.
    If brick_size is None, estimate from ATR (14) of closes.
    Returns DataFrame with columns: date, brick, direction
    """
    if brick_size is None:
        # estimate brick as ATR of close returns * close mean
        close = df["close"]
        ret = close.pct_change().abs()
        brick_size = ret.rolling(14, min_periods=1).mean().iloc[-1] * close.iloc[-1]
        if brick_size == 0 or np.isnan(brick_size):
            brick_size = (df["high"] - df["low"]).median()

    closes = df["close"].tolist()
    dates = df.index.tolist()

    bricks: List[Dict] = []
    last_brick_close = closes[0]

    for i in range(1, len(closes)):
        price = closes[i]
        move = price - last_brick_close
        if abs(move) >= brick_size:
            steps = int(abs(move) // brick_size)
            direction = 1 if move > 0 else -1
            for s in range(steps):
                last_brick_close = last_brick_close + (brick_size * direction)
                bricks.append({"date": dates[i], "brick_close": last_brick_close, "direction": direction})

    if not bricks:
        return pd.DataFrame(columns=["date", "brick_close", "direction"]) 

    renko_df = pd.DataFrame(bricks)
    renko_df["direction"] = renko_df["direction"].astype(int)
    return renko_df
