"""
Paper Trading API Routes

FastAPI routes for paper trading functionality.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.paper_trading import PaperTradingEngine

router = APIRouter(prefix="/api/paper-trading", tags=["Paper Trading"])

# Global engine instance (in production, use session/user-based storage)
paper_trading_engines: Dict[str, PaperTradingEngine] = {}


class OrderRequest(BaseModel):
    """Order placement request"""
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: int
    price: float
    order_type: str = "MARKET"
    stop_loss: Optional[float] = None
    target: Optional[float] = None


class EngineConfig(BaseModel):
    """Engine configuration"""
    initial_capital: float = 100000
    max_positions: int = 10
    max_position_size: float = 0.2
    brokerage_per_trade: float = 20
    slippage_percent: float = 0.1
    allow_short: bool = False


class PriceUpdate(BaseModel):
    """Price update request"""
    prices: Dict[str, float]


def get_engine(session_id: str = "default") -> PaperTradingEngine:
    """Get or create engine for session"""
    if session_id not in paper_trading_engines:
        paper_trading_engines[session_id] = PaperTradingEngine()
    return paper_trading_engines[session_id]


@router.post("/initialize")
def initialize_engine(config: EngineConfig, session_id: str = "default"):
    """
    Initialize a new paper trading engine.
    
    Creates a new engine with specified configuration.
    Resets existing engine if it exists.
    """
    paper_trading_engines[session_id] = PaperTradingEngine(
        initial_capital=config.initial_capital,
        max_positions=config.max_positions,
        max_position_size=config.max_position_size,
        brokerage_per_trade=config.brokerage_per_trade,
        slippage_percent=config.slippage_percent,
        allow_short=config.allow_short,
    )
    
    return {
        "status": "success",
        "message": "Paper trading engine initialized",
        "config": config.dict(),
        "portfolio": paper_trading_engines[session_id].get_portfolio_summary(),
    }


@router.post("/order")
def place_order(order: OrderRequest, session_id: str = "default"):
    """
    Place a paper trading order.
    
    Places a BUY or SELL order and returns execution result.
    """
    engine = get_engine(session_id)
    
    try:
        result = engine.place_order(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price,
            order_type=order.order_type,
            stop_loss=order.stop_loss,
            target=order.target,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/prices/update")
def update_prices(price_update: PriceUpdate, session_id: str = "default"):
    """
    Update current market prices for positions.
    
    Updates prices for P&L calculation and checks stop loss/targets.
    """
    engine = get_engine(session_id)
    
    try:
        # Update prices
        engine.update_position_prices(price_update.prices)
        
        # Check stop loss and targets
        auto_orders = engine.check_stop_loss_targets()
        
        return {
            "status": "success",
            "message": "Prices updated",
            "auto_executed_orders": auto_orders,
            "portfolio": engine.get_portfolio_summary(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/portfolio")
def get_portfolio(session_id: str = "default"):
    """
    Get portfolio summary.
    
    Returns current portfolio metrics including capital, P&L, and returns.
    """
    engine = get_engine(session_id)
    return engine.get_portfolio_summary()


@router.get("/positions")
def get_all_positions(session_id: str = "default"):
    """
    Get all positions (open and closed).
    
    Returns combined list of all positions.
    """
    engine = get_engine(session_id)
    return {
        "open": engine.get_open_positions(),
        "closed": engine.get_closed_positions(),
        "open_count": len(engine.get_open_positions()),
        "closed_count": len(engine.get_closed_positions()),
    }


@router.get("/positions/open")
def get_open_positions(session_id: str = "default"):
    """
    Get all open positions.
    
    Returns list of currently open positions with P&L.
    """
    engine = get_engine(session_id)
    return {
        "positions": engine.get_open_positions(),
        "count": len(engine.get_open_positions()),
    }


@router.get("/positions/closed")
def get_closed_positions(session_id: str = "default"):
    """
    Get all closed positions.
    
    Returns list of closed positions with realized P&L.
    """
    engine = get_engine(session_id)
    return {
        "positions": engine.get_closed_positions(),
        "count": len(engine.get_closed_positions()),
    }


@router.get("/orders")
def get_orders(session_id: str = "default"):
    """
    Get all orders.
    
    Returns complete order history.
    """
    engine = get_engine(session_id)
    return {
        "orders": engine.get_all_orders(),
        "count": len(engine.get_all_orders()),
    }


@router.get("/trades")
def get_trades(session_id: str = "default"):
    """
    Get all trades.
    
    Returns complete trade history.
    """
    engine = get_engine(session_id)
    return {
        "trades": engine.get_all_trades(),
        "count": len(engine.get_all_trades()),
    }


@router.get("/metrics")
def get_performance_metrics(session_id: str = "default"):
    """
    Get performance metrics.
    
    Returns comprehensive performance analysis including win rate,
    average win/loss, total P&L, and returns.
    """
    engine = get_engine(session_id)
    return engine.get_performance_metrics()


@router.post("/add-capital")
def add_capital(amount: float, session_id: str = "default"):
    """
    Add capital to paper trading account.
    
    Adds specified amount to available capital.
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    engine = get_engine(session_id)
    engine.portfolio.current_capital += amount
    
    return {
        "status": "success",
        "message": f"Added ₹{amount:,.2f} to capital",
        "portfolio": engine.get_portfolio_summary(),
    }


@router.post("/reset")
def reset_engine(session_id: str = "default"):
    """
    Reset paper trading engine.
    
    Resets engine to initial state, clearing all positions and history.
    """
    if session_id in paper_trading_engines:
        engine = paper_trading_engines[session_id]
        engine.reset()
        return {
            "status": "success",
            "message": "Engine reset to initial state",
            "portfolio": engine.get_portfolio_summary(),
        }
    else:
        raise HTTPException(status_code=404, detail="Engine not found")


@router.delete("/session/{session_id}")
def delete_session(session_id: str):
    """
    Delete paper trading session.
    
    Removes engine instance for specified session.
    """
    if session_id in paper_trading_engines:
        del paper_trading_engines[session_id]
        return {
            "status": "success",
            "message": f"Session {session_id} deleted",
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/sessions")
def list_sessions():
    """
    List all active paper trading sessions.
    
    Returns list of session IDs with summary.
    """
    sessions = []
    for session_id, engine in paper_trading_engines.items():
        summary = engine.get_portfolio_summary()
        sessions.append({
            "session_id": session_id,
            "portfolio_value": summary["portfolio_value"],
            "returns_percent": summary["returns_percent"],
            "open_positions": summary["open_positions_count"],
        })
    
    return {
        "sessions": sessions,
        "count": len(sessions),
    }
