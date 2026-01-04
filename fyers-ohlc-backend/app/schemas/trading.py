from pydantic import BaseModel, Field
from typing import List, Optional

class TradingConfig(BaseModel):
    tickers: List[str] = Field(..., description="List of tickers to trade")
    initial_capital: float = Field(100000, description="Initial trading capital")
    risk_per_trade: float = Field(0.01, description="Risk per trade as a fraction of capital")
    atr_periods: List[int] = Field([7, 14, 21], description="ATR periods for Supertrend")
    multipliers: List[float] = Field([2.0, 3.0, 4.0], description="Multipliers for Supertrend")

class TradingStatus(BaseModel):
    is_running: bool
    tracked_tickers: List[str]
    active_positions: dict
    pending_orders: dict
    config: dict

class TradingSignal(BaseModel):
    symbol: str
    signal: str
    price: float
    timestamp: str
    indicators: dict
    position_size: dict
    trend: str
    levels: dict
