from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
from enum import Enum

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class TradeSignal:
    def __init__(
        self,
        symbol: str,
        signal: SignalType,
        entry_price: float,
        stop_loss: float,
        target_price: float,
        timestamp: datetime,
        confidence: float = 0.0,
        metadata: Optional[Dict] = None
    ):
        self.symbol = symbol
        self.signal = signal
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.target_price = target_price
        self.timestamp = timestamp
        self.confidence = confidence
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "signal": self.signal.value,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "target_price": self.target_price,
            "risk_reward": self.calculate_risk_reward(),
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    def calculate_risk_reward(self) -> float:
        if self.signal == SignalType.BUY:
            risk = self.entry_price - self.stop_loss
            reward = self.target_price - self.entry_price
        else:  # SELL
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.target_price
        return reward / risk if risk != 0 else 0

class BaseStrategy(ABC):
    def __init__(self, symbol: str, params: Optional[Dict] = None):
        self.symbol = symbol
        self.params = params or {}
        self.name = self.__class__.__name__

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """Generate trading signals based on the strategy logic"""
        pass

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Helper method to calculate ATR"""
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.rolling(window=period, min_periods=1).mean()
