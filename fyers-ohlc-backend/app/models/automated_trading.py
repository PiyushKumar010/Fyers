"""
Database models for Automated Trading History
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AutoTradingSession(BaseModel):
    """Model for storing automated trading session data"""
    session_id: str
    symbols: List[str]
    strategies: List[str]
    start_date: str
    end_date: Optional[str] = None
    mode: str  # HISTORICAL or LIVE
    initial_capital: float
    stop_loss_percent: float
    profit_target_percent: float
    status: str  # RUNNING, COMPLETED, STOPPED, ERROR
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_1234567890",
                "symbols": ["NSE:RELIANCE-EQ"],
                "strategies": ["RSI", "MACD"],
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "mode": "HISTORICAL",
                "initial_capital": 100000.0,
                "stop_loss_percent": 2.0,
                "profit_target_percent": 5.0,
                "status": "COMPLETED",
                "created_at": "2025-01-01T10:00:00",
                "completed_at": "2025-01-01T15:00:00"
            }
        }


class AutoTradingResult(BaseModel):
    """Model for storing automated trading results with proper P&L separation"""
    session_id: str
    
    # Configuration (input parameters)
    symbols: List[str]
    strategies: List[str]
    start_date: str
    end_date: Optional[str] = None
    mode: str  # HISTORICAL or LIVE
    stop_loss_percent: float
    profit_target_percent: float
    initial_capital: float
    max_positions: int
    position_size_percent: float
    timeframe: str
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Capital tracking
    current_capital: float  # Cash available (reference only)
    invested_capital: float  # Capital locked in open positions (reference only)
    final_value: float  # SINGLE SOURCE OF TRUTH: initial + realized + unrealized - charges
    
    # P&L breakdown (CRITICAL: Must add up to total_pnl)
    realized_pnl: float  # P&L from closed trades only (locked in)
    unrealized_pnl: float  # P&L from open positions (paper gains/losses, 0 if no open)
    total_charges: float  # Brokerage + fees + slippage (subtracted from final value)
    total_pnl: float  # DERIVED: final_value - initial_capital (NOT independent calculation)
    
    # Returns calculation (MUST be derived from final_value)
    returns_percent: float  # DERIVED: (final_value - initial_capital) / initial_capital * 100
    
    # ACCOUNTING IDENTITY (ENFORCED):
    # final_value = initial_capital + realized_pnl + unrealized_pnl - total_charges
    # total_pnl = final_value - initial_capital
    # returns_percent = total_pnl / initial_capital * 100
    
    # Trade statistics (completed round trips only)
    total_trades: int  # Number of completed BUY→SELL round trips
    winning_trades: int  # Trades with positive P&L
    losing_trades: int  # Trades with negative P&L
    win_rate: float  # (winning_trades / total_trades) * 100
    avg_win: float  # Average profit of winning trades
    avg_loss: float  # Average loss of losing trades
    profit_factor: float  # abs(avg_win / avg_loss) if avg_loss != 0
    
    # Position tracking
    open_positions_count: int
    closed_positions_count: int
    
    # Costs breakdown
    total_brokerage: float  # Part of total_charges
    
    # Signals vs Trades (CRITICAL: Signals ≠ Trades)
    total_signals_generated: int  # Raw strategy signals
    signal_breakdown: Dict[str, Any]  # Breakdown by strategy
    
    # Trade data with exits
    executed_trades: List[Dict[str, Any]]  # All trades with entry AND exit
    
    # Daily tracking
    daily_pnl: Dict[str, float]
    equity_curve: List[Dict[str, Any]]  # Daily portfolio value tracking
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_1234567890",
                "initial_capital": 100000.0,
                "current_capital": 95000.0,
                "invested_capital": 5000.0,
                "final_value": 102200.0,
                "realized_pnl": 2000.0,
                "unrealized_pnl": 500.0,
                "total_charges": 300.0,
                "total_pnl": 2200.0,
                "returns_percent": 2.2,
                "total_trades": 15,
                "winning_trades": 9,
                "losing_trades": 6,
                "win_rate": 60.0,
                "avg_win": 350.0,
                "avg_loss": -150.0,
                "profit_factor": 2.33,
                "open_positions_count": 2,
                "closed_positions_count": 15,
                "total_brokerage": 300.0,
                "total_signals_generated": 250,
                "signal_breakdown": {"RSI": {"BUY": 50, "SELL": 45, "total": 95}},
                "executed_trades": [],
                "daily_pnl": {"2025-01-01": 500.0},
                "equity_curve": [],
                "timestamp": "2025-01-01T15:00:00"
            }
        }


class AutoTradingTrade(BaseModel):
    """Model for completed trades (BUY→SELL round trips only)"""
    session_id: str
    symbol: str
    
    # Entry details
    entry_side: str  # Always "BUY" for long trades
    entry_price: float
    entry_timestamp: datetime
    quantity: int
    
    # Exit details (REQUIRED - every trade must have an exit)
    exit_side: str  # "SELL" for long, "BUY" for short
    exit_price: float
    exit_timestamp: datetime
    exit_reason: str  # "TARGET", "STOP_LOSS", "AUTO_EXIT", "SIGNAL_EXIT"
    
    # Trade parameters
    strategy: str  # Strategy that generated the signal
    stop_loss: float
    target: float
    
    # P&L calculation (MUST be calculated: (exit_price - entry_price) * quantity - brokerage)
    gross_pnl: float  # Before brokerage
    brokerage: float  # Total brokerage for this trade
    net_pnl: float  # After brokerage (this is the realized P&L)
    
    # Trade metadata
    holding_period_minutes: int  # Time between entry and exit
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_1234567890",
                "symbol": "NSE:RELIANCE-EQ",
                "entry_side": "BUY",
                "entry_price": 1500.0,
                "entry_timestamp": "2025-01-01T10:30:00",
                "quantity": 10,
                "exit_side": "SELL",
                "exit_price": 1525.0,
                "exit_timestamp": "2025-01-01T14:00:00",
                "exit_reason": "TARGET",
                "strategy": "RSI",
                "stop_loss": 1470.0,
                "target": 1575.0,
                "gross_pnl": 250.0,
                "brokerage": 40.0,
                "net_pnl": 210.0,
                "holding_period_minutes": 210
            }
        }
