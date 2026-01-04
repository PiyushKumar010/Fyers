"""
Paper Trading Engine

Core engine that orchestrates order execution, position management, and P&L tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from .order import Order, OrderType, OrderStatus, OrderSide
from .position import Position, PositionSide
from .portfolio import Portfolio


class PaperTradingEngine:
    """
    Main Paper Trading Engine.
    
    Simulates realistic trading without placing real orders.
    Tracks positions, orders, and P&L like a real trading system.
    
    Features:
    - Virtual capital management
    - Order simulation (BUY/SELL)
    - Position tracking (LONG/SHORT)
    - P&L calculation (realized/unrealized)
    - Risk management (capital checks, position limits)
    - Brokerage and slippage simulation
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        max_positions: int = 10,
        max_position_size: float = 0.2,  # 20% of capital per position
        brokerage_per_trade: float = 20.0,  # ₹20 per trade
        slippage_percent: float = 0.1,  # 0.1% slippage
        allow_short: bool = False,
    ):
        """
        Initialize paper trading engine.
        
        Args:
            initial_capital: Starting capital
            max_positions: Maximum concurrent positions
            max_position_size: Max capital per position (as fraction)
            brokerage_per_trade: Brokerage per trade
            slippage_percent: Slippage percentage
            allow_short: Allow short selling
        """
        self.portfolio = Portfolio(
            initial_capital=initial_capital,
            brokerage_per_trade=brokerage_per_trade,
            slippage_percent=slippage_percent
        )
        self.max_positions = max_positions
        self.max_position_size = max_position_size
        self.allow_short = allow_short
        
        # Order and trade history
        self.orders: List[Order] = []
        self.trades: List[Dict[str, Any]] = []
        
    def place_order(
        self,
        symbol: str,
        side: str,  # "BUY" or "SELL"
        quantity: int,
        price: float,
        order_type: str = "MARKET",
        stop_loss: Optional[float] = None,
        target: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Place a paper trading order.
        
        Args:
            symbol: Stock symbol (e.g., NSE:RELIANCE-EQ)
            side: "BUY" or "SELL"
            quantity: Number of shares
            price: Current market price (LTP)
            order_type: Order type ("MARKET", "LIMIT", "STOP_LOSS")
            stop_loss: Optional stop loss price
            target: Optional target price
            
        Returns:
            Dictionary with order result
        """
        # Validate inputs
        if quantity <= 0:
            return self._rejection_response("Quantity must be positive")
        
        if price <= 0:
            return self._rejection_response("Price must be positive")
        
        # Create order
        order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        order_type_enum = OrderType[order_type.upper()]
        
        order = Order(
            symbol=symbol,
            side=order_side,
            quantity=quantity,
            order_type=order_type_enum,
            price=price,
        )
        
        # Process order based on side
        if order_side == OrderSide.BUY:
            result = self._execute_buy_order(order, price, stop_loss, target)
        else:
            result = self._execute_sell_order(order, price)
        
        # Store order
        self.orders.append(order)
        
        return result
    
    def _execute_buy_order(
        self,
        order: Order,
        price: float,
        stop_loss: Optional[float] = None,
        target: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute BUY order"""
        
        # Check if position already exists
        if self.portfolio.has_position(order.symbol):
            order.reject("Position already exists for this symbol")
            return self._rejection_response(order.rejection_reason)
        
        # Check max positions limit
        if len(self.portfolio.positions) >= self.max_positions:
            order.reject(f"Maximum positions limit ({self.max_positions}) reached")
            return self._rejection_response(order.rejection_reason)
        
        # Apply slippage
        execution_price = self.portfolio.apply_slippage(price, is_buy=True)
        
        # Calculate required capital
        required_capital = execution_price * order.quantity
        
        # Check max position size
        max_allowed = self.portfolio.initial_capital * self.max_position_size
        if required_capital > max_allowed:
            order.reject(f"Position size exceeds limit (max: ₹{max_allowed:,.2f})")
            return self._rejection_response(order.rejection_reason)
        
        # Check available capital (including brokerage)
        total_cost = required_capital + self.portfolio.brokerage_per_trade
        if self.portfolio.current_capital < total_cost:
            order.reject(f"Insufficient capital (available: ₹{self.portfolio.current_capital:,.2f})")
            return self._rejection_response(order.rejection_reason)
        
        # Execute order
        order.execute(execution_price, order.quantity)
        
        # Deduct capital
        self.portfolio.current_capital -= required_capital
        
        # Apply brokerage
        brokerage = self.portfolio.apply_brokerage()
        
        # Create position
        position = Position(
            symbol=order.symbol,
            side=PositionSide.LONG,
            quantity=order.quantity,
            entry_price=execution_price,
            stop_loss=stop_loss,
            target=target,
        )
        
        self.portfolio.add_position(position)
        
        # Record trade
        trade = {
            'trade_id': f"TRADE{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': 'BUY',
            'quantity': order.quantity,
            'price': execution_price,
            'value': required_capital,
            'brokerage': brokerage,
            'timestamp': datetime.now().isoformat(),
        }
        self.trades.append(trade)
        
        return {
            'status': 'SUCCESS',
            'message': 'BUY order executed successfully',
            'order': order.to_dict(),
            'trade': trade,
            'position': position.to_dict(),
            'portfolio': self.portfolio.get_summary(),
        }
    
    def _execute_sell_order(
        self,
        order: Order,
        price: float,
    ) -> Dict[str, Any]:
        """Execute SELL order"""
        
        # Check if position exists
        if not self.portfolio.has_position(order.symbol):
            order.reject("No open position to sell")
            return self._rejection_response(order.rejection_reason)
        
        position = self.portfolio.get_position(order.symbol)
        
        # Verify quantity
        if order.quantity > position.quantity:
            order.reject(f"Insufficient quantity (available: {position.quantity})")
            return self._rejection_response(order.rejection_reason)
        
        # Apply slippage
        execution_price = self.portfolio.apply_slippage(price, is_buy=False)
        
        # Execute order
        order.execute(execution_price, order.quantity)
        
        # Close position
        realized_pnl = position.close(execution_price)
        
        # Add proceeds to capital
        proceeds = execution_price * order.quantity
        self.portfolio.current_capital += proceeds
        
        # Apply brokerage
        brokerage = self.portfolio.apply_brokerage()
        
        # Remove position from portfolio
        self.portfolio.remove_position(order.symbol)
        
        # Record trade
        trade = {
            'trade_id': f"TRADE{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': 'SELL',
            'quantity': order.quantity,
            'price': execution_price,
            'value': proceeds,
            'brokerage': brokerage,
            'realized_pnl': realized_pnl,
            'timestamp': datetime.now().isoformat(),
        }
        self.trades.append(trade)
        
        return {
            'status': 'SUCCESS',
            'message': 'SELL order executed successfully',
            'order': order.to_dict(),
            'trade': trade,
            'position': position.to_dict(),
            'portfolio': self.portfolio.get_summary(),
        }
    
    def update_position_prices(self, prices: Dict[str, float]) -> None:
        """
        Update current prices for all positions.
        
        Args:
            prices: Dictionary mapping symbol to current price
        """
        for symbol, price in prices.items():
            self.portfolio.update_positions_price(symbol, price)
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        Update current prices for all positions (alias for update_position_prices).
        
        Args:
            prices: Dictionary mapping symbol to current price
        """
        self.update_position_prices(prices)
    
    def check_stop_loss_targets(self) -> List[Dict[str, Any]]:
        """
        Check and execute stop loss / target triggers.
        
        Returns:
            List of auto-executed orders
        """
        auto_orders = []
        
        for symbol, position in list(self.portfolio.positions.items()):
            # Check stop loss
            if position.should_trigger_stop_loss():
                result = self.place_order(
                    symbol=symbol,
                    side="SELL",
                    quantity=position.quantity,
                    price=position.stop_loss,
                )
                result['trigger'] = 'STOP_LOSS'
                auto_orders.append(result)
            
            # Check target
            elif position.should_trigger_target():
                result = self.place_order(
                    symbol=symbol,
                    side="SELL",
                    quantity=position.quantity,
                    price=position.target,
                )
                result['trigger'] = 'TARGET'
                auto_orders.append(result)
        
        return auto_orders
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get complete portfolio summary"""
        return self.portfolio.get_summary()
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        return [pos.to_dict() for pos in self.portfolio.positions.values()]
    
    def get_closed_positions(self) -> List[Dict[str, Any]]:
        """Get all closed positions"""
        return [pos.to_dict() for pos in self.portfolio.closed_positions]
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders"""
        return [order.to_dict() for order in self.orders]
    
    def get_all_trades(self) -> List[Dict[str, Any]]:
        """Get all trades"""
        return self.trades
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        closed_pnls = [pos.realized_pnl for pos in self.portfolio.closed_positions]
        winning_trades = [pnl for pnl in closed_pnls if pnl > 0]
        losing_trades = [pnl for pnl in closed_pnls if pnl < 0]
        
        total_trades = len(closed_pnls)
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        
        return {
            'total_trades': total_trades,
            'winning_trades': win_count,
            'losing_trades': loss_count,
            'win_rate': (win_count / total_trades * 100) if total_trades > 0 else 0,
            'average_win': sum(winning_trades) / win_count if win_count > 0 else 0,
            'average_loss': sum(losing_trades) / loss_count if loss_count > 0 else 0,
            'largest_win': max(winning_trades) if winning_trades else 0,
            'largest_loss': min(losing_trades) if losing_trades else 0,
            'total_realized_pnl': self.portfolio.realized_pnl,
            'total_unrealized_pnl': self.portfolio.unrealized_pnl,
            'total_pnl': self.portfolio.total_pnl,
            'returns_percent': self.portfolio.returns_percent,
            'total_brokerage_paid': self.portfolio.total_brokerage_paid,
        }
    
    def _rejection_response(self, reason: str) -> Dict[str, Any]:
        """Generate rejection response"""
        return {
            'status': 'REJECTED',
            'message': reason,
            'order': None,
            'trade': None,
            'position': None,
            'portfolio': self.portfolio.get_summary(),
        }
    
    def reset(self) -> None:
        """Reset engine to initial state"""
        self.__init__(
            initial_capital=self.portfolio.initial_capital,
            max_positions=self.max_positions,
            max_position_size=self.max_position_size,
            brokerage_per_trade=self.portfolio.brokerage_per_trade,
            slippage_percent=self.portfolio.slippage_percent,
            allow_short=self.allow_short,
        )
