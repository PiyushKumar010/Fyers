"""
Position Management for Paper Trading

Tracks open and closed positions with P&L calculation.
"""

from enum import Enum
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


class PositionSide(Enum):
    """Position side"""
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Position:
    """
    Represents a trading position (open or closed).
    
    Attributes:
        symbol: Stock symbol
        side: LONG or SHORT
        quantity: Number of shares
        entry_price: Average entry price
        entry_time: Position opening time
        current_price: Latest market price
        exit_price: Average exit price (if closed)
        exit_time: Position closing time (if closed)
        is_open: Whether position is still open
        stop_loss: Stop loss price (optional)
        target: Target price (optional)
        position_id: Unique position identifier
    """
    symbol: str
    side: PositionSide
    quantity: int
    entry_price: float
    entry_time: datetime = field(default_factory=datetime.now)
    current_price: Optional[float] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    is_open: bool = True
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    position_id: Optional[str] = None

    def __post_init__(self):
        """Generate position ID if not provided"""
        if self.position_id is None:
            self.position_id = f"POS{self.entry_time.strftime('%Y%m%d%H%M%S%f')}"
        if self.current_price is None:
            self.current_price = self.entry_price

    @property
    def unrealized_pnl(self) -> float:
        """
        Calculate unrealized P&L for open position.
        
        Returns:
            Unrealized profit/loss in currency units
        """
        if not self.is_open or self.current_price is None:
            return 0.0
        
        if self.side == PositionSide.LONG:
            return (self.current_price - self.entry_price) * self.quantity
        else:  # SHORT
            return (self.entry_price - self.current_price) * self.quantity

    @property
    def unrealized_pnl_percent(self) -> float:
        """
        Calculate unrealized P&L percentage.
        
        Returns:
            Unrealized P&L as percentage
        """
        if not self.is_open:
            return 0.0
        return (self.unrealized_pnl / (self.entry_price * self.quantity)) * 100

    @property
    def realized_pnl(self) -> float:
        """
        Calculate realized P&L for closed position.
        
        Returns:
            Realized profit/loss in currency units
        """
        if self.is_open or self.exit_price is None:
            return 0.0
        
        if self.side == PositionSide.LONG:
            return (self.exit_price - self.entry_price) * self.quantity
        else:  # SHORT
            return (self.entry_price - self.exit_price) * self.quantity

    @property
    def realized_pnl_percent(self) -> float:
        """
        Calculate realized P&L percentage.
        
        Returns:
            Realized P&L as percentage
        """
        if self.is_open:
            return 0.0
        return (self.realized_pnl / (self.entry_price * self.quantity)) * 100

    def update_price(self, price: float) -> None:
        """
        Update current market price for P&L calculation.
        
        Args:
            price: Latest market price
        """
        if self.is_open:
            self.current_price = price

    def close(self, exit_price: float) -> float:
        """
        Close the position.
        
        Args:
            exit_price: Price at which position is closed
            
        Returns:
            Realized P&L
        """
        if not self.is_open:
            raise ValueError("Position is already closed")
        
        self.is_open = False
        self.exit_price = exit_price
        self.exit_time = datetime.now()
        return self.realized_pnl

    def should_trigger_stop_loss(self) -> bool:
        """Check if stop loss should be triggered"""
        if not self.is_open or self.stop_loss is None or self.current_price is None:
            return False
        
        if self.side == PositionSide.LONG:
            return self.current_price <= self.stop_loss
        else:  # SHORT
            return self.current_price >= self.stop_loss

    def should_trigger_target(self) -> bool:
        """Check if target should be triggered"""
        if not self.is_open or self.target is None or self.current_price is None:
            return False
        
        if self.side == PositionSide.LONG:
            return self.current_price >= self.target
        else:  # SHORT
            return self.current_price <= self.target

    def to_dict(self) -> dict:
        """Convert position to dictionary for serialization"""
        return {
            'position_id': self.position_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat(),
            'current_price': self.current_price,
            'exit_price': self.exit_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'is_open': self.is_open,
            'stop_loss': self.stop_loss,
            'target': self.target,
            'unrealized_pnl': self.unrealized_pnl if self.is_open else 0.0,
            'realized_pnl': self.realized_pnl if not self.is_open else 0.0,
            'unrealized_pnl_percent': self.unrealized_pnl_percent if self.is_open else 0.0,
            'realized_pnl_percent': self.realized_pnl_percent if not self.is_open else 0.0,
        }
