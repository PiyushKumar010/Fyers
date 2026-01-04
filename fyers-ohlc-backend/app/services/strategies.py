import pandas as pd
from typing import Dict, Any
from .indicators import macd, rsi, supertrend, bollinger_bands


def macd_rsi_supertrend_signal(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df_ind = macd(df)
    df = df.join(df_ind)
    df["rsi"] = rsi(df)
    df["supertrend"] = supertrend(df)
    bb = bollinger_bands(df)
    df = df.join(bb)

    # generate simple signals
    df["signal"] = ""

    for i in range(1, len(df)):
        # MACD crossover
        prev_macd = df["macd"].iat[i - 1]
        prev_sig = df["signal"].iat[i - 1] if "signal" in df.columns else 0
        macd_now = df["macd"].iat[i]
        sig_now = df["signal"].iat[i]

        macd_prev_line = df["macd"].iat[i - 1]
        signal_prev_line = df["signal"].iat[i - 1] if "signal" in df.columns else df["signal"].iat[i - 1] if "signal" in df.columns else 0

        cross_up = (df["macd"].iat[i - 1] < df["signal"].iat[i - 1]) and (df["macd"].iat[i] > df["signal"].iat[i])
        cross_down = (df["macd"].iat[i - 1] > df["signal"].iat[i - 1]) and (df["macd"].iat[i] < df["signal"].iat[i])

        buy = cross_up and df["rsi"].iat[i] < 70 and df["close"].iat[i] > df["supertrend"].iat[i]
        sell = cross_down and df["rsi"].iat[i] > 30 and df["close"].iat[i] < df["supertrend"].iat[i]

        if buy:
            df.at[df.index[i], "signal"] = "buy"
        elif sell:
            df.at[df.index[i], "signal"] = "sell"
        else:
            df.at[df.index[i], "signal"] = ""

    return df
