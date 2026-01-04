"""
Order Management for Paper Trading

Handles order creation, validation, and tracking.
"""

from enum import Enum
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


class OrderType(Enum):
    """Order types supported"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"


class OrderStatus(Enum):
    """Order status lifecycle"""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class OrderSide(Enum):
    """Order side - Buy or Sell"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Order:
    """
    Represents a trading order in the paper trading system.
    
    Attributes:
        symbol: Stock symbol (e.g., NSE:RELIANCE-EQ)
        side: BUY or SELL
        quantity: Number of shares
        order_type: MARKET, LIMIT, or STOP_LOSS
        price: Order price (for LIMIT orders)
        stop_price: Stop loss price (for STOP_LOSS orders)
        timestamp: Order creation time
        status: Current order status
        executed_price: Actual execution price
        executed_quantity: Actual executed quantity
        executed_at: Execution timestamp
        order_id: Unique order identifier
        rejection_reason: Reason if order is rejected
    """
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    executed_price: Optional[float] = None
    executed_quantity: Optional[int] = None
    executed_at: Optional[datetime] = None
    order_id: Optional[str] = None
    rejection_reason: Optional[str] = None

    def __post_init__(self):
        """Generate order ID if not provided"""
        if self.order_id is None:
            self.order_id = f"PT{self.timestamp.strftime('%Y%m%d%H%M%S%f')}"

    def execute(self, price: float, quantity: int) -> None:
        """
        Mark order as executed.
        
        Args:
            price: Execution price
            quantity: Executed quantity
        """
        self.status = OrderStatus.EXECUTED
        self.executed_price = price
        self.executed_quantity = quantity
        self.executed_at = datetime.now()

    def reject(self, reason: str) -> None:
        """
        Mark order as rejected.
        
        Args:
            reason: Rejection reason
        """
        self.status = OrderStatus.REJECTED
        self.rejection_reason = reason

    def cancel(self) -> None:
        """Mark order as cancelled"""
        self.status = OrderStatus.CANCELLED

    def to_dict(self) -> dict:
        """Convert order to dictionary for serialization"""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'order_type': self.order_type.value,
            'price': self.price,
            'stop_price': self.stop_price,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'executed_price': self.executed_price,
            'executed_quantity': self.executed_quantity,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'rejection_reason': self.rejection_reason,
        }
