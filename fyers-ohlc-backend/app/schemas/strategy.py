from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

class StrategyName(str, Enum):
    SUPERTREND = "supertrend"
    RSI = "rsi"
    BOLLINGER = "bollinger"
    RENKO = "renko"

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class StrategySignal(BaseModel):
    symbol: str
    signal: SignalType
    entry_price: float
    stop_loss: float
    target_price: float
    risk_reward: float
    confidence: float
    timestamp: str
    metadata: Dict[str, Any] = {}

class BacktestRequest(BaseModel):
    symbol: str
    strategy_name: StrategyName
    interval: str = "5"  # 5-minute candles
    days: int = 30  # Last 30 days
    initial_capital: float = 100000.0
    parameters: Dict[str, Any] = {}

class BacktestResult(BaseModel):
    strategy: str
    symbol: str
    period: str
    total_trades: int
    win_rate: float
    net_pnl: float
    max_drawdown: float
    profit_factor: float
    signals: List[Dict[str, Any]]
