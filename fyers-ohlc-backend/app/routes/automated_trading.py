"""
Automated Trading API Routes

FastAPI routes for automated trading with multiple strategies.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone, timedelta
import asyncio

from app.paper_trading.automated_trading import (
    AutomatedTradingEngine,
    AutoTradingConfig,
    TradingMode
)
from app.database import get_db
from app.models.automated_trading import (
    AutoTradingSession,
    AutoTradingResult,
    AutoTradingTrade
)

router = APIRouter(prefix="/api/automated-trading", tags=["Automated Trading"])

# Store active trading engines
active_engines: Dict[str, AutomatedTradingEngine] = {}
background_tasks_status: Dict[str, Dict[str, Any]] = {}

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)


class AutoTradingRequest(BaseModel):
    """Request to start automated trading"""
    symbols: List[str] = Field(..., description="List of stock symbols (e.g., ['NSE:RELIANCE-EQ', 'NSE:TCS-EQ'])")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD) - Required for HISTORICAL mode")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD) - Required for HISTORICAL mode")
    stop_loss_percent: float = Field(2.0, description="Stop loss percentage (default: 2%)", ge=0.1, le=10)
    profit_target_percent: float = Field(5.0, description="Profit target percentage (default: 5%)", ge=0.5, le=20)
    initial_capital: float = Field(100000.0, description="Initial capital (default: ₹1,00,000)", ge=10000)
    max_positions: int = Field(5, description="Maximum concurrent positions (default: 5)", ge=1, le=10)
    position_size_percent: float = Field(20.0, description="Position size as % of capital (default: 20%)", ge=5, le=50)
    strategies: Optional[List[str]] = Field(
        None, 
        description="List of strategies to run (default: all). Options: RSI, MACD, SUPERTREND, BOLLINGER, ADX, ATR, RENKO"
    )
    mode: str = Field("HISTORICAL", description="Trading mode: HISTORICAL or LIVE")
    timeframe: str = Field("5", description="Timeframe (1, 5, 15, 60, D)")
    session_id: str = Field("default", description="Session ID for this trading instance")


class TradingStatusResponse(BaseModel):
    """Response for trading status"""
    session_id: str
    status: str  # "running", "completed", "error", "not_found"
    progress: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/start")
async def start_automated_trading(
    request: AutoTradingRequest,
    background_tasks: BackgroundTasks
):
    """
    Start automated trading.
    
    Initiates automated trading session that runs strategies in background
    and executes trades with stop loss and profit targets.
    
    - **HISTORICAL mode**: Backtests on historical data from start_date to end_date
    - **LIVE mode**: Runs continuously on live market data
    """
    try:
        # Validate mode
        try:
            mode = TradingMode[request.mode.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid mode. Must be HISTORICAL or LIVE"
            )
        
        # Parse and validate dates for HISTORICAL mode
        if mode == TradingMode.HISTORICAL:
            if not request.start_date or not request.end_date:
                raise HTTPException(
                    status_code=400,
                    detail="start_date and end_date are required for HISTORICAL mode"
                )
            
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()
            
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="start_date must be before end_date")
        else:
            # LIVE mode - use current date
            start_date = date.today()
            end_date = date.today()
        
        # Validate strategies
        valid_strategies = ["RSI", "MACD", "SUPERTREND", "BOLLINGER", "ADX", "ATR", "RENKO"]
        if request.strategies:
            invalid = [s for s in request.strategies if s.upper() not in valid_strategies]
            if invalid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid strategies: {invalid}. Valid options: {valid_strategies}"
                )
            strategies = [s.upper() for s in request.strategies]
        else:
            strategies = valid_strategies
        
        # Create configuration
        config = AutoTradingConfig(
            symbols=request.symbols,
            start_date=start_date,
            end_date=end_date,
            stop_loss_percent=request.stop_loss_percent,
            profit_target_percent=request.profit_target_percent,
            initial_capital=request.initial_capital,
            max_positions=request.max_positions,
            position_size_percent=request.position_size_percent,
            strategies=strategies,
            mode=mode,
            timeframe=request.timeframe
        )
        
        # Create engine
        engine = AutomatedTradingEngine(config)
        active_engines[request.session_id] = engine
        
        # Initialize status
        background_tasks_status[request.session_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "progress": 0
        }
        
        # Run in background
        if mode == TradingMode.HISTORICAL:
            background_tasks.add_task(run_historical_trading, request.session_id, engine)
        else:
            background_tasks.add_task(run_live_trading, request.session_id, engine)
        
        return {
            "status": "started",
            "message": f"Automated trading started in {mode.value} mode",
            "session_id": request.session_id,
            "config": {
                "symbols": request.symbols,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "stop_loss_percent": request.stop_loss_percent,
                "profit_target_percent": request.profit_target_percent,
                "strategies": strategies,
                "mode": mode.value
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start automated trading: {str(e)}")


async def run_historical_trading(session_id: str, engine: AutomatedTradingEngine):
    """Background task to run historical trading"""
    try:
        background_tasks_status[session_id]["status"] = "running"
        
        print(f"\n>>> Starting historical backtest for session {session_id}")
        
        # Get database connection
        db = get_db()
        
        # Run backtest
        results = await engine.run_historical_backtest()
        
        print(f"\n[OK] Backtest completed for session {session_id}")
        print(f"Results: {results}")
        
        # Check if backtest returned an error
        if 'error' in results:
            error_msg = results['error']
            print(f"[ERROR] Backtest returned error: {error_msg}")
            background_tasks_status[session_id] = {
                "status": "error",
                "error": error_msg,
                "failed_at": datetime.now().isoformat()
            }
            return
        
        # Save results to database with proper P&L separation
        portfolio = results['portfolio']
        performance = results['performance']
        signals = results.get('signals', {})
        config_data = results.get('config', {})
        
        print(f"[DEBUG] Portfolio data: {portfolio}")
        print(f"[DEBUG] Performance data: {performance}")
        
        result_data = AutoTradingResult(
            session_id=session_id,
            # Configuration (stored with results since no separate session)
            symbols=config_data.get('symbols', engine.config.symbols),
            start_date=config_data.get('start_date', engine.config.start_date.isoformat()),
            end_date=config_data.get('end_date', engine.config.end_date.isoformat() if engine.config.end_date else None),
            strategies=config_data.get('strategies', engine.config.strategies),
            stop_loss_percent=config_data.get('stop_loss_percent', engine.config.stop_loss_percent),
            profit_target_percent=config_data.get('profit_target_percent', engine.config.profit_target_percent),
            mode=config_data.get('mode', engine.config.mode.value),
            initial_capital=config_data.get('initial_capital', portfolio['initial_capital']),
            max_positions=config_data.get('max_positions', engine.config.max_positions),
            position_size_percent=config_data.get('position_size_percent', engine.config.position_size_percent),
            timeframe=config_data.get('timeframe', engine.config.timeframe),
            # Timestamps
            created_at=get_ist_now(),
            completed_at=get_ist_now(),
            # Capital breakdown
            current_capital=portfolio['current_capital'],
            invested_capital=portfolio['invested_capital'],
            final_value=portfolio['final_value'],
            # P&L breakdown (CRITICAL: Separate realized and unrealized)
            realized_pnl=portfolio['realized_pnl'],
            unrealized_pnl=portfolio['unrealized_pnl'],
            total_charges=portfolio['total_charges'],
            total_pnl=portfolio['total_pnl'],
            # Returns
            returns_percent=portfolio['returns_percent'],
            # Trade statistics
            total_trades=performance['total_trades'],
            winning_trades=performance['winning_trades'],
            losing_trades=performance['losing_trades'],
            win_rate=performance['win_rate'],
            avg_win=performance.get('avg_win', 0),
            avg_loss=performance.get('avg_loss', 0),
            profit_factor=performance.get('profit_factor', 0),
            # Positions
            open_positions_count=portfolio.get('open_positions_count', 0),
            closed_positions_count=portfolio.get('closed_positions_count', 0),
            # Signals (NOT trades)
            total_signals_generated=signals.get('total_signals_generated', 0),
            signal_breakdown=signals.get('signal_breakdown', {}),
            # Costs and tracking
            total_brokerage=portfolio.get('total_brokerage', 0),
            executed_trades=results.get('executed_trades', []),
            daily_pnl=results.get('daily_pnl', {}),
            equity_curve=results.get('equity_curve', [])
        )
        
        try:
            # Convert to dict for MongoDB
            result_dict = result_data.dict()
            
            # Add timestamp for sorting in history
            result_dict['timestamp'] = get_ist_now()
            
            print(f"[DB] Attempting to save result for session {session_id}")
            print(f"[DB] Result data keys: {list(result_dict.keys())}")
            
            # Insert into database
            insert_result = db.automated_trading_results.insert_one(result_dict)
            print(f"[DB] ✅ Successfully saved results for session {session_id}")
            print(f"[DB] Inserted document ID: {insert_result.inserted_id}")
            
            # Verify the save by reading it back
            saved_doc = db.automated_trading_results.find_one({"session_id": session_id})
            if saved_doc:
                print(f"[DB] ✅ Verified: Document exists in database")
            else:
                print(f"[DB] ⚠️  Warning: Document not found after insert")
                
        except Exception as e:
            import traceback
            print(f"[DB] ❌ ERROR: Failed to save results to database: {e}")
            print(f"[DB] Traceback: {traceback.format_exc()}")
            # Don't raise - continue to update status
        
        # Update status
        background_tasks_status[session_id] = {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "results": results
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n[ERROR] Backtest failed for session {session_id}:")
        print(error_details)
        
        background_tasks_status[session_id] = {
            "status": "error",
            "error": str(e),
            "error_details": error_details,
            "failed_at": datetime.now().isoformat()
        }


async def run_live_trading(session_id: str, engine: AutomatedTradingEngine):
    """Background task to run live trading"""
    try:
        background_tasks_status[session_id]["status"] = "running"
        
        # Run live trading (runs indefinitely)
        await engine.run_live_trading()
        
    except Exception as e:
        background_tasks_status[session_id] = {
            "status": "error",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }


@router.get("/status/{session_id}")
async def get_trading_status(session_id: str):
    """
    Get status of automated trading session.
    
    Returns current status, progress, and results (if completed).
    """
    if session_id not in background_tasks_status:
        return TradingStatusResponse(
            session_id=session_id,
            status="not_found",
            error="Session not found"
        )
    
    status_info = background_tasks_status[session_id]
    
    # Get current portfolio state if engine exists
    progress = None
    if session_id in active_engines:
        engine = active_engines[session_id]
        progress = {
            "current_capital": engine.engine.portfolio.current_capital,
            "portfolio_value": engine.engine.portfolio.portfolio_value,
            "total_pnl": engine.engine.portfolio.total_pnl,
            "open_positions": len(engine.engine.portfolio.positions),
            "total_trades": len(engine.executed_trades),
            "total_signals": len(engine.all_signals)
        }
    
    return TradingStatusResponse(
        session_id=session_id,
        status=status_info["status"],
        progress=progress,
        results=status_info.get("results"),
        error=status_info.get("error")
    )


@router.get("/results/{session_id}")
async def get_trading_results(session_id: str):
    """
    Get detailed results of automated trading session.
    
    Returns comprehensive results including portfolio stats, trades,
    daily P&L, and strategy performance.
    """
    if session_id not in active_engines:
        raise HTTPException(status_code=404, detail="Session not found")
    
    engine = active_engines[session_id]
    results = engine.get_results()
    
    return results


@router.post("/stop/{session_id}")
async def stop_trading(session_id: str):
    """
    Stop automated trading session.
    
    Closes all open positions and stops the trading engine.
    """
    if session_id not in active_engines:
        raise HTTPException(status_code=404, detail="Session not found")
    
    engine = active_engines[session_id]
    
    # Close all open positions
    closed_positions = []
    for symbol, position in list(engine.engine.portfolio.positions.items()):
        try:
            # Get latest price (use entry price as fallback)
            current_price = position.current_price
            
            result = engine.engine.place_order(
                symbol=symbol,
                side="SELL" if position.side.value == "LONG" else "BUY",
                quantity=position.quantity,
                price=current_price
            )
            
            if result.get("status") == "EXECUTED":
                closed_positions.append({
                    "symbol": symbol,
                    "quantity": position.quantity,
                    "pnl": position.unrealized_pnl
                })
        except Exception as e:
            print(f"Error closing position for {symbol}: {e}")
    
    # Update status
    background_tasks_status[session_id]["status"] = "stopped"
    background_tasks_status[session_id]["stopped_at"] = datetime.now().isoformat()
    
    # Get final results
    results = engine.get_results()
    
    return {
        "status": "stopped",
        "message": f"Trading stopped. Closed {len(closed_positions)} positions.",
        "closed_positions": closed_positions,
        "final_results": results
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a trading session.
    
    Removes the session from active engines, status tracking, and database.
    """
    try:
        # Remove from active engines
        if session_id in active_engines:
            del active_engines[session_id]
        
        if session_id in background_tasks_status:
            del background_tasks_status[session_id]
        
        # Remove from database
        db = get_db()
        db.automated_trading_results.delete_one({"session_id": session_id})
        db.automated_trading_sessions.delete_one({"session_id": session_id})
        db.automated_trading_trades.delete_many({"session_id": session_id})
        
        return {
            "status": "success",
            "message": f"Session {session_id} deleted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.get("/sessions")
async def list_sessions():
    """
    List all active trading sessions.
    
    Returns list of session IDs and their current status.
    """
    sessions = []
    
    for session_id, status_info in background_tasks_status.items():
        session_data = {
            "session_id": session_id,
            "status": status_info["status"],
            "started_at": status_info.get("started_at")
        }
        
        # Add current progress if available
        if session_id in active_engines:
            engine = active_engines[session_id]
            session_data["portfolio_value"] = engine.engine.portfolio.portfolio_value
            session_data["total_pnl"] = engine.engine.portfolio.total_pnl
            session_data["open_positions"] = len(engine.engine.portfolio.positions)
        
        sessions.append(session_data)
    
    return {
        "total_sessions": len(sessions),
        "sessions": sessions
    }


@router.get("/strategies")
async def list_available_strategies():
    """
    List all available strategies for automated trading.
    
    Returns list of strategy names with descriptions.
    """
    strategies = [
        {
            "name": "RSI",
            "description": "Relative Strength Index - identifies overbought/oversold conditions",
            "signals": "BUY when RSI < 30, SELL when RSI > 70"
        },
        {
            "name": "MACD",
            "description": "Moving Average Convergence Divergence - trend-following momentum",
            "signals": "BUY when MACD crosses above signal, SELL when crosses below"
        },
        {
            "name": "SUPERTREND",
            "description": "Supertrend - ATR-based trend following indicator",
            "signals": "BUY on bullish trend change, SELL on bearish trend change"
        },
        {
            "name": "BOLLINGER",
            "description": "Bollinger Bands - volatility-based trading bands",
            "signals": "BUY at lower band, SELL at upper band"
        },
        {
            "name": "ADX",
            "description": "Average Directional Index - measures trend strength",
            "signals": "BUY when ADX > 25 and DI+ > DI-, SELL when ADX > 25 and DI- > DI+"
        }
    ]
    
    return {
        "total_strategies": len(strategies),
        "strategies": strategies
    }


@router.get("/history")
async def get_trading_history(limit: int = 50, skip: int = 0):
    """
    Get historical automated trading results from database.
    
    Returns list of final results only (no separate sessions or trades).
    """
    try:
        db = get_db()
        
        print(f"[DB] Fetching trading history (limit={limit}, skip={skip})")
        
        # Get all results from database
        # Try to sort by timestamp, fallback to created_at, then completed_at
        try:
            results_cursor = db.automated_trading_results.find().sort("timestamp", -1).skip(skip).limit(limit)
        except:
            try:
                results_cursor = db.automated_trading_results.find().sort("created_at", -1).skip(skip).limit(limit)
            except:
                results_cursor = db.automated_trading_results.find().sort("completed_at", -1).skip(skip).limit(limit)
        
        results_list = list(results_cursor)
        
        print(f"[DB] Found {len(results_list)} results in database")
        
        # Format history items from results
        history = []
        for result in results_list:
            try:
                # Remove MongoDB _id field
                if '_id' in result:
                    del result['_id']
                
                # Get timestamp (try multiple fields)
                timestamp = result.get('timestamp') or result.get('completed_at') or result.get('created_at')
                
                # Convert timestamp to ISO format
                if timestamp and hasattr(timestamp, 'isoformat'):
                    timestamp = timestamp.isoformat()
                elif isinstance(timestamp, str):
                    # Already a string
                    pass
                else:
                    # Use current time as fallback
                    timestamp = get_ist_now().isoformat()
                
                # Build history item with all result data
                history_item = {
                    "session_id": result.get('session_id'),
                    "symbols": result.get('symbols', []),
                    "strategies": result.get('strategies', []),
                    "start_date": result.get('start_date'),
                    "end_date": result.get('end_date'),
                    "mode": result.get('mode'),
                    "status": "COMPLETED",  # If result exists, it's completed
                    "created_at": timestamp,
                    "completed_at": timestamp,
                    "initial_capital": result.get('initial_capital'),
                    "final_value": result.get('final_value'),
                    "final_capital": result.get('current_capital'),
                    "invested_capital": result.get('invested_capital', 0),
                    # P&L breakdown (CRITICAL: Separate realized and unrealized)
                    "realized_pnl": result.get('realized_pnl', 0),
                    "unrealized_pnl": result.get('unrealized_pnl', 0),
                    "total_charges": result.get('total_charges', 0),
                    "total_pnl": result.get('total_pnl', 0),
                    "returns_percent": result.get('returns_percent', 0),
                    # Trade statistics
                    "total_trades": result.get('total_trades', 0),
                    "winning_trades": result.get('winning_trades', 0),
                    "losing_trades": result.get('losing_trades', 0),
                    "win_rate": result.get('win_rate', 0),
                    "avg_win": result.get('avg_win', 0),
                    "avg_loss": result.get('avg_loss', 0),
                    # Signals (NOT trades)
                    "total_signals_generated": result.get('total_signals_generated', 0),
                    "total_signals": result.get('total_signals_generated', 0),  # Backward compatibility
                }
                
                history.append(history_item)
                
            except Exception as e:
                print(f"[DB] Warning: Failed to process result {result.get('session_id', 'unknown')}: {e}")
                continue
        
        print(f"[DB] Returning {len(history)} history items")
        
        return {
            "total": len(history),
            "history": history
        }
        
    except Exception as e:
        import traceback
        print(f"[DB] ERROR fetching history: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.get("/history/{session_id}")
async def get_session_details(session_id: str):
    """
    Get detailed information for a specific trading session from database.
    
    Returns final results with all details (results only, no separate session/trades).
    """
    try:
        db = get_db()
        
        # Get results (this is the only data we store)
        result = db.automated_trading_results.find_one({"session_id": session_id})
        
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Remove MongoDB _id field
        if '_id' in result:
            del result['_id']
        
        # Convert timestamp to isoformat string
        if 'timestamp' in result and hasattr(result['timestamp'], 'isoformat'):
            result['timestamp'] = result['timestamp'].isoformat()
        
        # Prepare trades from result data (trades are embedded in results)
        trades = result.get('executed_trades', [])
        for trade in trades:
            # Ensure timestamps are strings
            if 'entry_timestamp' in trade and hasattr(trade['entry_timestamp'], 'isoformat'):
                trade['entry_timestamp'] = trade['entry_timestamp'].isoformat()
            if 'exit_timestamp' in trade and hasattr(trade['exit_timestamp'], 'isoformat'):
                trade['exit_timestamp'] = trade['exit_timestamp'].isoformat()
        
        # Build session info from result data
        return {
            "session": {
                "session_id": result['session_id'],
                "symbols": result.get('symbols', []),
                "strategies": result.get('strategies', []),
                "start_date": result.get('start_date'),
                "end_date": result.get('end_date'),
                "mode": result.get('mode'),
                "initial_capital": result.get('initial_capital'),
                "stop_loss_percent": result.get('stop_loss_percent'),
                "profit_target_percent": result.get('profit_target_percent'),
                "status": "COMPLETED",
                "created_at": result.get('created_at') if isinstance(result.get('created_at'), str) else result.get('created_at').isoformat() if result.get('created_at') else result.get('timestamp'),
                "completed_at": result.get('completed_at') if isinstance(result.get('completed_at'), str) else result.get('completed_at').isoformat() if result.get('completed_at') else result.get('timestamp'),
            },
            "results": result,
            "trades": trades,
            "total_trades": len(trades)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session details: {str(e)}")


@router.get("/live-trades/{session_id}")
async def get_live_trades(session_id: str):
    """
    Get current trades from an active live trading session.
    
    Returns real-time portfolio status, open positions, and recent closed trades.
    """
    try:
        # Check if session exists and is active
        if session_id not in active_engines:
            raise HTTPException(status_code=404, detail="Active session not found")
        
        engine = active_engines[session_id]
        portfolio = engine.engine.portfolio
        
        # Get open positions
        open_positions = []
        for position in portfolio.positions.values():
            open_positions.append({
                "symbol": position.symbol,
                "entry_price": position.entry_price,
                "quantity": position.quantity,
                "current_price": position.current_price,
                "unrealized_pnl": position.unrealized_pnl,
                "pnl_percent": ((position.current_price - position.entry_price) / position.entry_price) * 100,
                "entry_time": position.entry_time.isoformat() if hasattr(position.entry_time, 'isoformat') else str(position.entry_time),
                "strategy": getattr(position, 'strategy', 'N/A'),
                "stop_loss": position.stop_loss,
                "profit_target": position.profit_target
            })
        
        # Get closed trades (limited to last 20 for live display)
        closed_trades = []
        for trade in list(portfolio.closed_positions)[-20:]:
            closed_trades.append({
                "symbol": trade.symbol,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "quantity": trade.quantity,
                "realized_pnl": trade.realized_pnl,
                "pnl_percent": ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100,
                "entry_time": trade.entry_time.isoformat() if hasattr(trade.entry_time, 'isoformat') else str(trade.entry_time),
                "exit_time": trade.exit_time.isoformat() if hasattr(trade.exit_time, 'isoformat') else str(trade.exit_time),
                "strategy": getattr(trade, 'strategy', 'N/A'),
                "exit_reason": getattr(trade, 'exit_reason', 'N/A')
            })
        
        # Get portfolio status
        return {
            "session_id": session_id,
            "status": background_tasks_status.get(session_id, {}).get("status", "running"),
            "portfolio": {
                "cash": portfolio.current_capital,
                "portfolio_value": portfolio.portfolio_value,
                "total_pnl": portfolio.total_pnl,
                "total_pnl_percent": (portfolio.total_pnl / engine.config.initial_capital) * 100
            },
            "positions": {
                "open": open_positions,
                "open_count": len(open_positions),
                "closed": closed_trades,
                "closed_count": len(portfolio.closed_positions)
            },
            "statistics": {
                "total_trades": len(portfolio.closed_positions),
                "winning_trades": len([t for t in portfolio.closed_positions if t.realized_pnl > 0]),
                "losing_trades": len([t for t in portfolio.closed_positions if t.realized_pnl < 0]),
                "win_rate": (len([t for t in portfolio.closed_positions if t.realized_pnl > 0]) / len(portfolio.closed_positions) * 100) if len(portfolio.closed_positions) > 0 else 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] Failed to get live trades: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch live trades: {str(e)}")

