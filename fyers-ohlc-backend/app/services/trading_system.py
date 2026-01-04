import asyncio
from datetime import datetime, time
import pytz
from typing import Dict, List, Optional, Any
import pandas as pd

from app.indicators.candlestick_patterns import generate_trading_signals
from app.services.fyers import (
    fetch_ohlc,
    place_order,
    get_positions,
    get_orders,
    cancel_order
)

class TradingSystem:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active_positions = {}
        self.pending_orders = {}
        self.tracked_tickers = config.get('tickers', [])
        self.capital = config.get('initial_capital', 100000)
        self.risk_per_trade = config.get('risk_per_trade', 0.01)
        self.atr_periods = config.get('atr_periods', [7, 14, 21])
        self.multipliers = config.get('multipliers', [2.0, 3.0, 4.0])
        self.is_running = False
        self.task = None

    async def start(self):
        """Start the trading system"""
        if self.is_running:
            return
            
        self.is_running = True
        self.task = asyncio.create_task(self._run_loop())
        return True

    async def stop(self):
        """Stop the trading system"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        return True

    async def _run_loop(self):
        """Main trading loop"""
        try:
            while self.is_running:
                if self._is_market_open():
                    await self._update_positions()
                    await self._check_signals()
                    await self._manage_orders()
                
                # Wait for next check (5 minutes)
                await asyncio.sleep(300)
                
        except asyncio.CancelledError:
            # Handle graceful shutdown
            await self._close_all_positions()
        except Exception as e:
            print(f"Error in trading loop: {e}")
            # Attempt to restart the loop after a delay
            await asyncio.sleep(60)
            if self.is_running:
                self.task = asyncio.create_task(self._run_loop())

    async def _update_positions(self):
        """Update current positions from broker"""
        try:
            positions = await get_positions()
            self.active_positions = {
                pos['symbol']: pos for pos in positions
            }
        except Exception as e:
            print(f"Error updating positions: {e}")

    async def _check_signals(self):
        """Check for new trading signals"""
        for ticker in self.tracked_tickers:
            try:
                # Skip if we already have an open position
                if ticker in self.active_positions:
                    continue

                # Fetch OHLC data
                ohlc_data = await fetch_ohlc(
                    ticker,
                    interval='5',  # 5-minute candles
                    days=5         # Last 5 days of data
                )
                
                if not ohlc_data:
                    continue
                    
                # Generate trading signals
                signals = generate_trading_signals(
                    ohlc_data,
                    atr_periods=self.atr_periods,
                    multipliers=self.multipliers
                )
                
                # Execute trade based on signal
                if signals['signal'] == 'bullish':
                    await self._enter_long(ticker, signals)
                elif signals['signal'] == 'bearish':
                    await self._exit_position(ticker, signals)
                    
            except Exception as e:
                print(f"Error processing {ticker}: {e}")

    async def _enter_long(self, ticker: str, signals: Dict[str, Any]):
        """Enter a long position"""
        try:
            position_size = signals.get('position_size', {})
            quantity = position_size.get('quantity', 0)
            
            if quantity <= 0:
                return
                
            # Place buy order
            order = await place_order(
                symbol=ticker,
                side='BUY',
                quantity=quantity,
                order_type='MARKET'
            )
            
            if order and order.get('status') == 'COMPLETE':
                # Place stop loss order
                sl_order = await place_order(
                    symbol=ticker,
                    side='SELL',
                    quantity=quantity,
                    order_type='SL',
                    stop_loss=position_size.get('stop_loss', 0)
                )
                
                self.pending_orders[ticker] = {
                    'entry': order,
                    'stop_loss': sl_order
                }
                
        except Exception as e:
            print(f"Error entering long position for {ticker}: {e}")

    async def _exit_position(self, ticker: str, signals: Dict[str, Any] = None):
        """Exit an existing position"""
        try:
            if ticker in self.active_positions:
                position = self.active_positions[ticker]
                await place_order(
                    symbol=ticker,
                    side='SELL',
                    quantity=position['quantity'],
                    order_type='MARKET'
                )
        except Exception as e:
            print(f"Error exiting position for {ticker}: {e}")

    async def _manage_orders(self):
        """Update and manage pending orders"""
        for ticker, orders in list(self.pending_orders.items()):
            try:
                # Check if position is now active
                if ticker in self.active_positions:
                    # Cancel any pending stop loss if position is active
                    if 'stop_loss' in orders and orders['stop_loss']:
                        await cancel_order(orders['stop_loss']['id'])
                    del self.pending_orders[ticker]
                    continue
                    
                # Update order status
                updated_orders = {}
                for order_type, order in orders.items():
                    if order and 'id' in order:
                        status = await get_orders(order['id'])
                        if status and status.get('status') in ['COMPLETE', 'CANCELLED', 'REJECTED']:
                            continue
                        updated_orders[order_type] = order
                
                if updated_orders:
                    self.pending_orders[ticker] = updated_orders
                else:
                    del self.pending_orders[ticker]
                    
            except Exception as e:
                print(f"Error managing orders for {ticker}: {e}")

    async def _close_all_positions(self):
        """Close all open positions"""
        for ticker in list(self.active_positions.keys()):
            await self._exit_position(ticker)

    def _is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            
            # Check if it's a weekday (0 = Monday, 6 = Sunday)
            if now.weekday() >= 5:
                return False
                
            # Market hours: 9:15 AM to 3:30 PM IST
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            return market_open <= now.time() <= market_close
            
        except Exception as e:
            print(f"Error checking market hours: {e}")
            return False

# Global instance
trading_system = TradingSystem({})

async def get_trading_system() -> TradingSystem:
    """Get the global trading system instance"""
    return trading_system
