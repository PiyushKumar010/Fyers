"""
Portfolio Management for Paper Trading

Tracks capital, positions, and overall performance.
"""

from typing import Dict, List
from datetime import datetime
from .position import Position


class Portfolio:
    """
    Manages the paper trading portfolio including capital and positions.
    
    Attributes:
        initial_capital: Starting capital amount
        current_capital: Available cash
        positions: Dictionary of open positions by symbol
        closed_positions: List of closed positions
        brokerage_per_trade: Brokerage fees per trade (default: 0)
        slippage_percent: Slippage percentage (default: 0)
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        brokerage_per_trade: float = 0.0,
        slippage_percent: float = 0.0
    ):
        """
        Initialize portfolio.
        
        Args:
            initial_capital: Starting capital (default: ₹1,00,000)
            brokerage_per_trade: Brokerage per trade (default: 0)
            slippage_percent: Slippage percentage (default: 0)
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.brokerage_per_trade = brokerage_per_trade
        self.slippage_percent = slippage_percent
        self.total_brokerage_paid = 0.0
        
    @property
    def invested_capital(self) -> float:
        """Calculate capital locked in open positions"""
        return sum(
            pos.entry_price * pos.quantity 
            for pos in self.positions.values()
        )
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L from open positions"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    @property
    def realized_pnl(self) -> float:
        """Calculate total realized P&L from closed positions"""
        return sum(pos.realized_pnl for pos in self.closed_positions)
    
    @property
    def total_pnl(self) -> float:
        """Calculate total P&L (realized + unrealized)"""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def portfolio_value(self) -> float:
        """
        Calculate total portfolio value.
        
        Returns:
            Current capital + Invested capital + Unrealized P&L
        """
        return self.current_capital + self.invested_capital + self.unrealized_pnl
    
    @property
    def returns_percent(self) -> float:
        """Calculate portfolio returns as percentage"""
        return ((self.portfolio_value - self.initial_capital) / self.initial_capital) * 100
    
    def has_position(self, symbol: str) -> bool:
        """Check if position exists for symbol"""
        return symbol in self.positions
    
    def get_position(self, symbol: str) -> Position:
        """Get open position for symbol"""
        if not self.has_position(symbol):
            raise ValueError(f"No open position for {symbol}")
        return self.positions[symbol]
    
    def add_position(self, position: Position) -> None:
        """
        Add a new position to portfolio.
        
        Args:
            position: Position to add
        """
        if position.symbol in self.positions:
            raise ValueError(f"Position already exists for {position.symbol}")
        self.positions[position.symbol] = position
    
    def remove_position(self, symbol: str) -> Position:
        """
        Remove and return position from portfolio.
        
        Args:
            symbol: Symbol to remove
            
        Returns:
            Removed position
        """
        if symbol not in self.positions:
            raise ValueError(f"No position found for {symbol}")
        position = self.positions.pop(symbol)
        self.closed_positions.append(position)
        return position
    
    def update_positions_price(self, symbol: str, price: float) -> None:
        """
        Update price for a position.
        
        Args:
            symbol: Symbol to update
            price: New price
        """
        if symbol in self.positions:
            self.positions[symbol].update_price(price)
    
    def apply_brokerage(self) -> float:
        """
        Apply brokerage charges.
        
        Returns:
            Brokerage amount charged
        """
        self.current_capital -= self.brokerage_per_trade
        self.total_brokerage_paid += self.brokerage_per_trade
        return self.brokerage_per_trade
    
    def apply_slippage(self, price: float, is_buy: bool) -> float:
        """
        Apply slippage to price.
        
        Args:
            price: Original price
            is_buy: True if buying, False if selling
            
        Returns:
            Price after slippage
        """
        if self.slippage_percent == 0:
            return price
        
        slippage_amount = price * (self.slippage_percent / 100)
        if is_buy:
            return price + slippage_amount  # Buy at higher price
        else:
            return price - slippage_amount  # Sell at lower price
    
    def get_summary(self) -> dict:
        """
        Get portfolio summary.
        
        Returns:
            Dictionary with portfolio metrics
        """
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'invested_capital': self.invested_capital,
            'portfolio_value': self.portfolio_value,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'total_pnl': self.total_pnl,
            'returns_percent': self.returns_percent,
            'total_brokerage_paid': self.total_brokerage_paid,
            'open_positions_count': len(self.positions),
            'closed_positions_count': len(self.closed_positions),
            'timestamp': datetime.now().isoformat(),
        }
