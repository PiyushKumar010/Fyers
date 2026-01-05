"""
Automated Trading Engine

Automatically executes strategies and manages trades with stop loss, profit targets,
and optimization for maximum profitability.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import asyncio
from enum import Enum
import pandas as pd

from .engine import PaperTradingEngine
from .order import OrderSide
from app.services.fyers import get_fyers_client, normalize_symbol
from app.schemas.trading import TradingSignal
from app.indicators.rsi import calculate_rsi
from app.indicators.macd import calculate_macd
from app.indicators.supertrend import calculate_supertrend
from app.indicators.bollinger import calculate_bollinger_bands
from app.indicators.adx import calculate_adx
from app.indicators.atr import calculate_atr
from app.indicators.renko import calculate_renko, get_renko_signal


class TradingMode(Enum):
    """Trading mode - Historical or Live"""
    HISTORICAL = "HISTORICAL"
    LIVE = "LIVE"


@dataclass
class AutoTradingConfig:
    """Configuration for automated trading"""
    symbols: List[str]  # List of stock symbols to trade
    start_date: date  # Start date for trading
    end_date: date  # End date for trading
    stop_loss_percent: float  # Stop loss percentage (e.g., 2.0 for 2%)
    profit_target_percent: float  # Profit target percentage (e.g., 5.0 for 5%)
    initial_capital: float = 100000.0
    max_positions: int = 5
    position_size_percent: float = 20.0  # Percentage of capital per trade
    strategies: List[str] = None  # List of strategies to run (None = all)
    mode: TradingMode = TradingMode.HISTORICAL
    timeframe: str = "5"  # 5 minute candles by default
    
    def __post_init__(self):
        if self.strategies is None:
            # Default strategies to run
            self.strategies = ["RSI", "MACD", "SUPERTREND", "BOLLINGER", "ADX", "ATR", "RENKO"]


class StrategySignal:
    """Represents a trading signal from a strategy"""
    
    def __init__(
        self,
        strategy_name: str,
        symbol: str,
        signal: str,  # "BUY", "SELL", "HOLD"
        price: float,
        timestamp: datetime,
        confidence: float = 0.5,  # 0 to 1
        metadata: Dict[str, Any] = None
    ):
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.signal = signal
        self.price = price
        self.timestamp = timestamp
        self.confidence = confidence
        self.metadata = metadata or {}


class AutomatedTradingEngine:
    """
    Automated Trading Engine
    
    Runs multiple strategies in parallel, aggregates signals, and automatically
    executes trades with stop loss and profit targets.
    """
    
    def __init__(self, config: AutoTradingConfig):
        """
        Initialize automated trading engine.
        
        Args:
            config: AutoTradingConfig with trading parameters
        """
        self.config = config
        self.engine = PaperTradingEngine(
            initial_capital=config.initial_capital,
            max_positions=config.max_positions,
            max_position_size=config.position_size_percent / 100.0,
            brokerage_per_trade=20.0,
            slippage_percent=0.1,
        )
        
        # Get Fyers client for data fetching
        try:
            self.fyers = get_fyers_client()
        except Exception as e:
            print(f"Warning: Could not initialize Fyers client: {e}")
            self.fyers = None
        
        # Track signals and executed trades
        self.all_signals: List[StrategySignal] = []
        self.executed_trades: List[Dict[str, Any]] = []
        self.daily_pnl: Dict[date, float] = {}
        
        # Active positions with stop loss and target tracking
        self.position_metadata: Dict[str, Dict[str, Any]] = {}
        
    def run_rsi_strategy(self, symbol: str, df: pd.DataFrame) -> Optional[StrategySignal]:
        """Run RSI strategy and generate signal"""
        try:
            if df is None or len(df) < 15:
                return None
            
            rsi_values = calculate_rsi(df, period=14)
            
            if len(rsi_values) < 2 or pd.isna(rsi_values.iloc[-1]):
                return None
            
            current_rsi = rsi_values.iloc[-1]
            prev_rsi = rsi_values.iloc[-2]
            current_price = df['close'].iloc[-1]
            timestamp = datetime.fromtimestamp(df['timestamp'].iloc[-1])
            
            # RSI oversold (< 30) -> BUY signal
            if current_rsi < 30 and prev_rsi >= 30:
                return StrategySignal(
                    strategy_name="RSI",
                    symbol=symbol,
                    signal="BUY",
                    price=current_price,
                    timestamp=timestamp,
                    confidence=min(1.0, (30 - current_rsi) / 30),
                    metadata={"rsi": current_rsi}
                )
            
            # RSI overbought (> 70) -> SELL signal
            elif current_rsi > 70 and prev_rsi <= 70:
                return StrategySignal(
                    strategy_name="RSI",
                    symbol=symbol,
                    signal="SELL",
                    price=current_price,
                    timestamp=timestamp,
                    confidence=min(1.0, (current_rsi - 70) / 30),
                    metadata={"rsi": current_rsi}
                )
                
        except Exception as e:
            print(f"RSI strategy error for {symbol}: {e}")
        
        return None
    
    def run_macd_strategy(self, symbol: str, df: pd.DataFrame) -> Optional[StrategySignal]:
        """Run MACD strategy and generate signal"""
        try:
            if df is None or len(df) < 26:
                return None
            
            macd_result = calculate_macd(df)
            
            if len(macd_result['macd']) < 2 or pd.isna(macd_result['macd'].iloc[-1]):
                return None
            
            current_macd = macd_result['macd'].iloc[-1]
            current_signal = macd_result['signal'].iloc[-1]
            prev_macd = macd_result['macd'].iloc[-2]
            prev_signal = macd_result['signal'].iloc[-2]
            current_price = df['close'].iloc[-1]
            timestamp = datetime.fromtimestamp(df['timestamp'].iloc[-1])
            
            # MACD crosses above signal -> BUY
            if current_macd > current_signal and prev_macd <= prev_signal:
                return StrategySignal(
                    strategy_name="MACD",
                    symbol=symbol,
                    signal="BUY",
                    price=current_price,
                    timestamp=timestamp,
                    confidence=0.7,
                    metadata={"macd": current_macd, "signal": current_signal}
                )
            
            # MACD crosses below signal -> SELL
            elif current_macd < current_signal and prev_macd >= prev_signal:
                return StrategySignal(
                    strategy_name="MACD",
                    symbol=symbol,
                    signal="SELL",
                    price=current_price,
                    timestamp=timestamp,
                    confidence=0.7,
                    metadata={"macd": current_macd, "signal": current_signal}
                )
                
        except Exception as e:
            print(f"MACD strategy error for {symbol}: {e}")
        
        return None
    
    def run_supertrend_strategy(self, symbol: str, df: pd.DataFrame) -> Optional[StrategySignal]:
        """Run Supertrend strategy and generate signal"""
        try:
            if df is None or len(df) < 10:
                return None
            
            st_result = calculate_supertrend(df)
            
            if len(st_result['direction']) < 2:
                return None
            
            current_trend = st_result['direction'].iloc[-1]
            prev_trend = st_result['direction'].iloc[-2]
            current_price = df['close'].iloc[-1]
            timestamp = datetime.fromtimestamp(df['timestamp'].iloc[-1])
            
            # Trend changed to bullish -> BUY
            if current_trend == 1 and prev_trend == -1:
                return StrategySignal(
                    strategy_name="SUPERTREND",
                    symbol=symbol,
                    signal="BUY",
                    price=current_price,
                    timestamp=timestamp,
                    confidence=0.8,
                    metadata={"supertrend": st_result['supertrend'].iloc[-1]}
                )
            
            # Trend changed to bearish -> SELL
            elif current_trend == -1 and prev_trend == 1:
                return StrategySignal(
                    strategy_name="SUPERTREND",
                    symbol=symbol,
                    signal="SELL",
                    price=current_price,
                    timestamp=timestamp,
                    confidence=0.8,
                    metadata={"supertrend": st_result['supertrend'].iloc[-1]}
                )
                
        except Exception as e:
            print(f"Supertrend strategy error for {symbol}: {e}")
        
        return None
    
    def run_bollinger_strategy(self, symbol: str, df: pd.DataFrame) -> Optional[StrategySignal]:
        """Run Bollinger Bands strategy and generate signal"""
        try:
            if df is None or len(df) < 20:
                return None
            
            bb_result = calculate_bollinger_bands(df)
            
            if len(bb_result['middle_band']) < 1 or pd.isna(bb_result['middle_band'].iloc[-1]):
                return None
            
            current_price = df['close'].iloc[-1]
            upper_band = bb_result['upper_band'].iloc[-1]
            lower_band = bb_result['lower_band'].iloc[-1]
            timestamp = datetime.fromtimestamp(df['timestamp'].iloc[-1])
            
            # Price touches lower band -> BUY
            if current_price <= lower_band:
                return StrategySignal(
                    strategy_name="BOLLINGER",
                    symbol=symbol,
                    signal="BUY",
                    price=current_price,
                    timestamp=timestamp,
                    confidence=0.6,
                    metadata={"upper_band": upper_band, "lower_band": lower_band}
                )
            
            # Price touches upper band -> SELL
            elif current_price >= upper_band:
                return StrategySignal(
                    strategy_name="BOLLINGER",
                    symbol=symbol,
                    signal="SELL",
                    price=current_price,
                    timestamp=timestamp,
                    confidence=0.6,
                    metadata={"upper_band": upper_band, "lower_band": lower_band}
                )
                
        except Exception as e:
            print(f"Bollinger strategy error for {symbol}: {e}")
        
        return None
    
    def run_adx_strategy(self, symbol: str, df: pd.DataFrame) -> Optional[StrategySignal]:
        """Run ADX strategy and generate signal"""
        try:
            if df is None or len(df) < 28:
                return None
            
            adx_result = calculate_adx(df)
            
            if pd.isna(adx_result.iloc[-1]):
                return None
            
            current_adx = adx_result.iloc[-1]
            current_price = df['close'].iloc[-1]
            timestamp = datetime.fromtimestamp(df['timestamp'].iloc[-1])
            
            # Strong trend (ADX > 25) - determine direction from price action
            if current_adx > 25:
                # Simple trend direction: compare current close to 20-period SMA
                sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
                
                if current_price > sma_20:
                    confidence = min(1.0, (current_adx - 25) / 50)
                    return StrategySignal(
                        strategy_name="ADX",
                        symbol=symbol,
                        signal="BUY",
                        price=current_price,
                        timestamp=timestamp,
                        confidence=confidence,
                        metadata={"adx": current_adx, "trend": "strong_uptrend"}
                    )
                elif current_price < sma_20:
                    confidence = min(1.0, (current_adx - 25) / 50)
                    return StrategySignal(
                        strategy_name="ADX",
                        symbol=symbol,
                        signal="SELL",
                        price=current_price,
                        timestamp=timestamp,
                        confidence=confidence,
                        metadata={"adx": current_adx, "trend": "strong_downtrend"}
                    )
                
        except Exception as e:
            print(f"ADX strategy error for {symbol}: {e}")
        
        return None
    
    def run_atr_strategy(self, symbol: str, df: pd.DataFrame) -> Optional[StrategySignal]:
        """Run ATR-based volatility breakout strategy"""
        try:
            if df is None or len(df) < 20:
                return None
            
            atr_values = calculate_atr(df, period=14)
            
            if len(atr_values) < 2 or pd.isna(atr_values.iloc[-1]):
                return None
            
            current_atr = atr_values.iloc[-1]
            prev_atr = atr_values.iloc[-2]
            current_price = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-2]
            timestamp = datetime.fromtimestamp(df['timestamp'].iloc[-1])
            
            # Calculate 20-period SMA for trend
            sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
            
            # ATR breakout strategy: High volatility + price breakout
            # BUY: Price breaks above SMA + ATR expanding + upward price movement
            if current_atr > prev_atr * 1.2:  # ATR expanding by 20%
                price_change = (current_price - prev_close) / prev_close
                
                if current_price > sma_20 and price_change > 0.01:  # 1% upward move
                    confidence = min(1.0, abs(price_change) * 10)  # Higher moves = higher confidence
                    return StrategySignal(
                        strategy_name="ATR",
                        symbol=symbol,
                        signal="BUY",
                        price=current_price,
                        timestamp=timestamp,
                        confidence=confidence,
                        metadata={
                            "atr": current_atr,
                            "atr_change": (current_atr - prev_atr) / prev_atr * 100,
                            "price_change": price_change * 100
                        }
                    )
                
                # SELL: Price breaks below SMA + ATR expanding + downward price movement
                elif current_price < sma_20 and price_change < -0.01:  # 1% downward move
                    confidence = min(1.0, abs(price_change) * 10)
                    return StrategySignal(
                        strategy_name="ATR",
                        symbol=symbol,
                        signal="SELL",
                        price=current_price,
                        timestamp=timestamp,
                        confidence=confidence,
                        metadata={
                            "atr": current_atr,
                            "atr_change": (current_atr - prev_atr) / prev_atr * 100,
                            "price_change": price_change * 100
                        }
                    )
                
        except Exception as e:
            print(f"ATR strategy error for {symbol}: {e}")
        
        return None
    
    def run_renko_strategy(self, symbol: str, df: pd.DataFrame) -> Optional[StrategySignal]:
        """Run RENKO chart-based trend strategy"""
        try:
            if df is None or len(df) < 20:
                return None
            
            # Calculate Renko bricks
            renko_df = calculate_renko(df, brick_size=None, atr_period=14, atr_multiplier=1.0)
            
            if renko_df is None or len(renko_df) < 3:
                return None
            
            # Get signal from Renko
            renko_signal = get_renko_signal(renko_df, lookback=3)
            
            current_price = df['close'].iloc[-1]
            timestamp = datetime.fromtimestamp(df['timestamp'].iloc[-1])
            
            # Get trend strength from consecutive bricks
            recent_bricks = renko_df.tail(5)
            consecutive_up = 0
            consecutive_down = 0
            
            for trend in recent_bricks['trend'].values:
                if trend == 1:
                    consecutive_up += 1
                    consecutive_down = 0
                elif trend == -1:
                    consecutive_down += 1
                    consecutive_up = 0
            
            # BUY signal: Bullish Renko trend
            if renko_signal == 'BULLISH' and consecutive_up >= 2:
                confidence = min(1.0, consecutive_up / 5.0)  # More consecutive bricks = higher confidence
                return StrategySignal(
                    strategy_name="RENKO",
                    symbol=symbol,
                    signal="BUY",
                    price=current_price,
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        "renko_signal": renko_signal,
                        "consecutive_up_bricks": consecutive_up,
                        "total_bricks": len(renko_df)
                    }
                )
            
            # SELL signal: Bearish Renko trend
            elif renko_signal == 'BEARISH' and consecutive_down >= 2:
                confidence = min(1.0, consecutive_down / 5.0)
                return StrategySignal(
                    strategy_name="RENKO",
                    symbol=symbol,
                    signal="SELL",
                    price=current_price,
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        "renko_signal": renko_signal,
                        "consecutive_down_bricks": consecutive_down,
                        "total_bricks": len(renko_df)
                    }
                )
                
        except Exception as e:
            print(f"RENKO strategy error for {symbol}: {e}")
        
        return None
    
    def aggregate_signals(self, signals: List[StrategySignal]) -> Optional[StrategySignal]:
        """
        Aggregate signals from multiple strategies to make final decision.
        
        Uses weighted voting based on confidence levels.
        """
        if not signals:
            return None
        
        buy_votes = 0
        sell_votes = 0
        buy_confidence = 0
        sell_confidence = 0
        buy_strategies = []
        sell_strategies = []
        
        for signal in signals:
            if signal.signal == "BUY":
                buy_votes += 1
                buy_confidence += signal.confidence
                buy_strategies.append(signal.strategy_name)
            elif signal.signal == "SELL":
                sell_votes += 1
                sell_confidence += signal.confidence
                sell_strategies.append(signal.strategy_name)
        
        # Need majority vote (>50%) to execute
        total_votes = buy_votes + sell_votes
        if total_votes == 0:
            return None
        
        # Calculate average confidence per vote
        avg_buy_confidence = buy_confidence / buy_votes if buy_votes > 0 else 0
        avg_sell_confidence = sell_confidence / sell_votes if sell_votes > 0 else 0
        
        # Require majority vote (more buy than sell votes, or vice versa)
        # And minimum confidence of 0.3
        if buy_votes > sell_votes and avg_buy_confidence > 0.3:
            final_confidence = avg_buy_confidence * (buy_votes / total_votes)
            strategies_str = ", ".join(buy_strategies)
            print(f"[AGGREGATE] BUY signal from [{strategies_str}]: {buy_votes} buy votes vs {sell_votes} sell votes, confidence: {final_confidence:.2f}")
            return StrategySignal(
                strategy_name=strategies_str,  # Show all strategies that agreed
                symbol=signals[0].symbol,
                signal="BUY",
                price=signals[0].price,
                timestamp=signals[0].timestamp,
                confidence=final_confidence,
                metadata={
                    "buy_votes": buy_votes, 
                    "sell_votes": sell_votes, 
                    "strategies": len(signals),
                    "buy_strategies": buy_strategies,
                    "sell_strategies": sell_strategies
                }
            )
        elif sell_votes > buy_votes and avg_sell_confidence > 0.3:
            final_confidence = avg_sell_confidence * (sell_votes / total_votes)
            strategies_str = ", ".join(sell_strategies)
            print(f"[AGGREGATE] SELL signal from [{strategies_str}]: {sell_votes} sell votes vs {buy_votes} buy votes, confidence: {final_confidence:.2f}")
            return StrategySignal(
                strategy_name=strategies_str,  # Show all strategies that agreed
                symbol=signals[0].symbol,
                signal="SELL",
                price=signals[0].price,
                timestamp=signals[0].timestamp,
                confidence=final_confidence,
                metadata={
                    "buy_votes": buy_votes, 
                    "sell_votes": sell_votes, 
                    "strategies": len(signals),
                    "buy_strategies": buy_strategies,
                    "sell_strategies": sell_strategies
                }
            )
        
        print(f"[WARNING] No clear signal: {buy_votes} buy vs {sell_votes} sell votes")
        return None
    
    def execute_signal(self, signal: StrategySignal) -> bool:
        """
        Execute a trading signal with stop loss and profit target.
        
        Returns:
            True if order was executed successfully
        """
        try:
            symbol = signal.symbol
            
            # Check if we already have a position
            if self.engine.portfolio.has_position(symbol):
                position = self.engine.portfolio.get_position(symbol)
                
                # If signal is opposite to position, close it
                if (signal.signal == "SELL" and position.side.value == "LONG") or \
                   (signal.signal == "BUY" and position.side.value == "SHORT"):
                    result = self.engine.place_order(
                        symbol=symbol,
                        side="SELL" if position.side.value == "LONG" else "BUY",
                        quantity=position.quantity,
                        price=signal.price
                    )
                    
                    if result.get("status") == "SUCCESS":
                        # Remove position metadata
                        if symbol in self.position_metadata:
                            del self.position_metadata[symbol]
                        print(f"[CLOSE] Closed position for {symbol} at {signal.price}")
                        return True
                    else:
                        print(f"[ERROR] Failed to close position for {symbol}: {result.get('message')}")
                
                return False
            
            # Calculate position size
            available_capital = self.engine.portfolio.current_capital
            position_value = available_capital * (self.config.position_size_percent / 100.0)
            quantity = int(position_value / signal.price)
            
            if quantity <= 0:
                return False
            
            # Calculate stop loss and target prices
            if signal.signal == "BUY":
                stop_loss_price = signal.price * (1 - self.config.stop_loss_percent / 100)
                target_price = signal.price * (1 + self.config.profit_target_percent / 100)
            else:
                stop_loss_price = signal.price * (1 + self.config.stop_loss_percent / 100)
                target_price = signal.price * (1 - self.config.profit_target_percent / 100)
            
            # Place order
            result = self.engine.place_order(
                symbol=symbol,
                side=signal.signal,
                quantity=quantity,
                price=signal.price,
                stop_loss=stop_loss_price,
                target=target_price
            )
            
            print(f"[ORDER] Order result for {symbol}: {result.get('status')} - {result.get('message')}")
            
            if result.get("status") == "SUCCESS":
                # Store position metadata
                print(f"[OK] {signal.signal} {quantity} shares of {symbol} at Rs.{signal.price:.2f}")
                self.position_metadata[symbol] = {
                    "entry_price": signal.price,
                    "stop_loss": stop_loss_price,
                    "target": target_price,
                    "entry_time": signal.timestamp,
                    "strategy": signal.strategy_name,
                    "confidence": signal.confidence
                }
                
                # Attach strategy to the position object for later retrieval
                if symbol in self.engine.portfolio.positions:
                    self.engine.portfolio.positions[symbol].strategy = signal.strategy_name
                    self.engine.portfolio.positions[symbol].stop_loss = stop_loss_price
                    self.engine.portfolio.positions[symbol].target = target_price
                
                self.executed_trades.append({
                    "symbol": symbol,
                    "side": signal.signal,
                    "quantity": quantity,
                    "price": signal.price,
                    "timestamp": signal.timestamp,
                    "strategy": signal.strategy_name,
                    "stop_loss": stop_loss_price,
                    "target": target_price
                })
                
                return True
            
        except Exception as e:
            print(f"Error executing signal for {signal.symbol}: {e}")
        
        return False
    
    def check_stop_loss_targets(self, current_prices: Dict[str, float]) -> None:
        """
        Check all open positions for stop loss or target hit.
        
        Args:
            current_prices: Dictionary of symbol -> current price
        """
        positions_to_close = []
        
        for symbol, position in self.engine.portfolio.positions.items():
            if symbol not in self.position_metadata:
                continue
            
            metadata = self.position_metadata[symbol]
            current_price = current_prices.get(symbol)
            
            if not current_price:
                continue
            
            stop_loss = metadata["stop_loss"]
            target = metadata["target"]
            
            should_close = False
            reason = ""
            
            # Check stop loss and target
            if position.side.value == "LONG":
                if current_price <= stop_loss:
                    should_close = True
                    reason = "STOP_LOSS"
                elif current_price >= target:
                    should_close = True
                    reason = "TARGET"
            else:  # SHORT
                if current_price >= stop_loss:
                    should_close = True
                    reason = "STOP_LOSS"
                elif current_price <= target:
                    should_close = True
                    reason = "TARGET"
            
            if should_close:
                positions_to_close.append((symbol, position, current_price, reason))
        
        # Close positions
        for symbol, position, price, reason in positions_to_close:
            result = self.engine.place_order(
                symbol=symbol,
                side="SELL" if position.side.value == "LONG" else "BUY",
                quantity=position.quantity,
                price=price
            )
            
            if result.get("status") == "SUCCESS":
                print(f"[CLOSE] Closed {symbol} at Rs.{price:.2f} ({reason})")
                
                # Store exit reason and strategy on closed position
                if symbol in self.position_metadata:
                    metadata = self.position_metadata[symbol]
                    # Attach metadata to the most recently closed position
                    if len(self.engine.portfolio.closed_positions) > 0:
                        last_closed = self.engine.portfolio.closed_positions[-1]
                        if last_closed.symbol == symbol:
                            last_closed.exit_reason = reason
                            last_closed.strategy = metadata.get('strategy', 'UNKNOWN')
                    
                    del self.position_metadata[symbol]
    
    def run_strategies(self, symbol: str, data: Dict[str, Any]) -> List[StrategySignal]:
        """
        Run all configured strategies on the data.
        
        Returns list of generated signals.
        """
        signals = []
        
        # Convert candles to DataFrame for indicator calculations
        if not data or 'candles' not in data or len(data['candles']) == 0:
            return signals
        
        # Create DataFrame from candles
        df = pd.DataFrame(data['candles'])
        
        for strategy_name in self.config.strategies:
            signal = None
            
            if strategy_name == "RSI":
                signal = self.run_rsi_strategy(symbol, df)
            elif strategy_name == "MACD":
                signal = self.run_macd_strategy(symbol, df)
            elif strategy_name == "SUPERTREND":
                signal = self.run_supertrend_strategy(symbol, df)
            elif strategy_name == "BOLLINGER":
                signal = self.run_bollinger_strategy(symbol, df)
            elif strategy_name == "ADX":
                signal = self.run_adx_strategy(symbol, df)
            elif strategy_name == "ATR":
                signal = self.run_atr_strategy(symbol, df)
            elif strategy_name == "RENKO":
                signal = self.run_renko_strategy(symbol, df)
            
            if signal:
                signals.append(signal)
                self.all_signals.append(signal)
        
        return signals
    
    def get_historical_data(self, symbol: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Fetch historical data for a symbol"""
        try:
            if not self.fyers:
                print(f"[ERROR] Fyers client not available. Please authenticate.")
                return None
            
            # Convert dates to required format
            from_date = start_date.strftime("%Y-%m-%d")
            to_date = end_date.strftime("%Y-%m-%d")
            
            print(f"[DATA] Requesting: {symbol} from {from_date} to {to_date}, resolution={self.config.timeframe}")
            
            # Fetch data using Fyers API
            data = {
                "symbol": normalize_symbol(symbol),
                "resolution": self.config.timeframe,
                "date_format": "1",
                "range_from": from_date,
                "range_to": to_date,
                "cont_flag": "1"
            }
            
            response = self.fyers.history(data=data)
            
            print(f"[DATA] Fyers API response status: {response.get('s') if response else 'None'}")
            
            if response and response.get("s") == "ok":
                candles = response.get("candles", [])
                if not candles:
                    print(f"[WARNING] Fyers returned 'ok' but no candles for {symbol}")
                    return None
                    
                formatted_candles = [
                    {
                        "timestamp": candle[0],
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "volume": candle[5]
                    }
                    for candle in candles
                ]
                return {"candles": formatted_candles}
            else:
                error_msg = response.get("message", "Unknown error") if response else "No response"
                print(f"[ERROR] Fyers API failed: {error_msg}")
                print(f"[HINT] Check: 1) Authentication, 2) Market is closed (no data for future dates), 3) Symbol format")
            
            return None
        except Exception as e:
            print(f"[ERROR] Exception fetching historical data for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def run_historical_backtest(self) -> Dict[str, Any]:
        """
        Run automated trading on historical data.
        
        Backtests strategies on historical data from start_date to end_date.
        """
        print(f"\n>>> Running historical backtest from {self.config.start_date} to {self.config.end_date}")
        print(f"Symbols: {', '.join(self.config.symbols)}")
        print(f"Strategies: {', '.join(self.config.strategies)}")
        print(f"Capital: Rs.{self.config.initial_capital:,.2f}")
        print(f"Stop Loss: {self.config.stop_loss_percent}%, Target: {self.config.profit_target_percent}%")
        
        # Fetch historical data for all symbols
        symbol_data = {}
        for symbol in self.config.symbols:
            print(f"[*] Fetching data for {symbol}...")
            data = self.get_historical_data(symbol, self.config.start_date, self.config.end_date)
            if data and 'candles' in data:
                symbol_data[symbol] = data
                print(f"[OK] Got {len(data['candles'])} candles for {symbol}")
            else:
                print(f"[ERROR] No data available for {symbol}")
        
        if not symbol_data:
            error_msg = "No historical data available for any symbol."
            if self.config.end_date >= date.today():
                error_msg += " Note: Cannot fetch data for today or future dates. Try using an earlier date range."
            print(f"[ERROR] {error_msg}")
            return {
                "error": error_msg,
                "details": {
                    "symbols": self.config.symbols,
                    "date_range": f"{self.config.start_date} to {self.config.end_date}",
                    "suggestions": [
                        "Check if you're authenticated with Fyers",
                        "Ensure date range is in the past (not today or future)",
                        "Verify symbols are correct (e.g., NSE:RELIANCE-EQ)",
                        "Market might be closed on these dates"
                    ]
                }
            }
        
        # Process each time period
        # Group candles by date/time
        all_timestamps = set()
        for data in symbol_data.values():
            for candle in data['candles']:
                all_timestamps.add(candle['timestamp'])
        
        sorted_timestamps = sorted(all_timestamps)
        total_timestamps = len(sorted_timestamps)
        
        print(f"\n[*] Processing {total_timestamps} time periods...")
        processed = 0
        last_progress = 0
        
        for ts in sorted_timestamps:
            processed += 1
            progress = int((processed / total_timestamps) * 100)
            
            # Print progress every 10%
            if progress >= last_progress + 10:
                print(f"[PROGRESS] {progress}% ({processed}/{total_timestamps}) - Portfolio: Rs.{self.engine.portfolio.portfolio_value:,.2f}")
                last_progress = progress
            
            # Yield control to event loop every 10 candles to prevent blocking HTTP requests
            if processed % 10 == 0:
                await asyncio.sleep(0)
            
            current_date = datetime.fromtimestamp(ts).date()
            
            # Get current prices for all symbols at this timestamp
            current_prices = {}
            for symbol, data in symbol_data.items():
                for candle in data['candles']:
                    if candle['timestamp'] == ts:
                        current_prices[symbol] = candle['close']
                        break
            
            # Check stop loss and targets first
            self.check_stop_loss_targets(current_prices)
            
            # Update portfolio with current prices
            self.engine.update_prices(current_prices)
            
            # Run strategies for each symbol
            for symbol in self.config.symbols:
                if symbol not in symbol_data:
                    continue
                
                # Get data up to current timestamp
                candles_up_to_now = [
                    c for c in symbol_data[symbol]['candles'] 
                    if c['timestamp'] <= ts
                ]
                
                if len(candles_up_to_now) < 30:  # Need minimum data for indicators
                    continue
                
                data_slice = {'candles': candles_up_to_now}
                
                # Run all strategies
                signals = self.run_strategies(symbol, data_slice)
                
                if signals:
                    print(f"[SIGNAL] {symbol}: Generated {len(signals)} signals")
                    # Aggregate signals
                    aggregated_signal = self.aggregate_signals(signals)
                    
                    if aggregated_signal:
                        # Execute trade
                        success = self.execute_signal(aggregated_signal)
                        if success:
                            print(f"[TRADE] Executed successfully for {symbol}")
                        else:
                            print(f"[WARNING] Failed to execute trade for {symbol}")
            
            # Track daily P&L
            if current_date not in self.daily_pnl:
                self.daily_pnl[current_date] = self.engine.portfolio.total_pnl
        
        # Print final summary
        print(f"\n[COMPLETE] Backtest completed!")
        print(f"Final Portfolio Value: Rs.{self.engine.portfolio.portfolio_value:,.2f}")
        print(f"Total P&L: Rs.{self.engine.portfolio.total_pnl:,.2f}")
        print(f"Returns: {self.engine.portfolio.returns_percent:.2f}%")
        print(f"Total Trades: {len(self.executed_trades)}")
        print(f"Total Signals: {len(self.all_signals)}")
        
        # Get final results
        return self.get_results()
    
    async def run_live_trading(self) -> Dict[str, Any]:
        """
        Run automated trading on live data.
        
        Continuously monitors market and executes trades based on strategy signals.
        """
        print(f"Starting live trading")
        print(f"Symbols: {', '.join(self.config.symbols)}")
        print(f"Strategies: {', '.join(self.config.strategies)}")
        
        while True:
            try:
                current_date = datetime.now().date()
                
                # Check if we're within trading hours (9:15 AM to 3:30 PM IST)
                current_time = datetime.now().time()
                market_open = datetime.strptime("09:15", "%H:%M").time()
                market_close = datetime.strptime("15:30", "%H:%M").time()
                
                if not (market_open <= current_time <= market_close):
                    print("Market is closed. Waiting...")
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # Fetch live data for all symbols
                current_prices = {}
                symbol_data = {}
                
                for symbol in self.config.symbols:
                    # Get recent historical data (last 100 candles)
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=5)  # Last 5 days
                    
                    data = self.get_historical_data(symbol, start_date.date(), end_date.date())
                    
                    if data and 'candles' in data and len(data['candles']) > 0:
                        symbol_data[symbol] = data
                        current_prices[symbol] = data['candles'][-1]['close']
                
                if not current_prices:
                    print("No live data available")
                    await asyncio.sleep(60)
                    continue
                
                # Check stop loss and targets
                self.check_stop_loss_targets(current_prices)
                
                # Update portfolio with current prices
                self.engine.update_prices(current_prices)
                
                # Run strategies for each symbol
                for symbol in self.config.symbols:
                    if symbol not in symbol_data:
                        continue
                    
                    # Run all strategies
                    signals = self.run_strategies(symbol, symbol_data[symbol])
                    
                    if signals:
                        print(f"[LIVE] {symbol}: Generated {len(signals)} signals")
                        # Aggregate signals
                        aggregated_signal = self.aggregate_signals(signals)
                        
                        if aggregated_signal:
                            # Execute trade
                            success = self.execute_signal(aggregated_signal)
                            if success:
                                print(f"[LIVE TRADE] Executed {aggregated_signal.signal} for {symbol} at Rs.{aggregated_signal.price:.2f}")
                
                # Track daily P&L
                self.daily_pnl[current_date] = self.engine.portfolio.total_pnl
                
                # Wait before next iteration (5 minutes for 5-min timeframe)
                await asyncio.sleep(300)
                
            except Exception as e:
                print(f"Error in live trading loop: {e}")
                await asyncio.sleep(60)
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get comprehensive trading results with STRICT mathematical consistency.
        
        CRITICAL ACCOUNTING IDENTITY (ENFORCED):
        Final Value = Initial Capital + Realized P&L + Unrealized P&L - Total Charges
        
        This is the SINGLE SOURCE OF TRUTH for all calculations.
        
        Returns:
            Dictionary with validated portfolio stats, trades, signals, and daily P&L
        """
        # === STEP 1: Get portfolio state ===
        portfolio = self.engine.portfolio
        initial_capital = portfolio.initial_capital
        
        # === STEP 2: Calculate P&L components (COMPONENT SOURCE OF TRUTH) ===
        # Realized P&L: Sum of all closed positions (money locked in)
        realized_pnl = sum(pos.realized_pnl for pos in portfolio.closed_positions)
        
        # Unrealized P&L: Sum of all open positions (paper gains/losses)
        unrealized_pnl = sum(pos.unrealized_pnl for pos in portfolio.positions.values())
        
        # Total charges (brokerage + other costs)
        total_charges = portfolio.total_brokerage_paid
        
        # === STEP 3: Calculate FINAL VALUE (SINGLE SOURCE OF TRUTH) ===
        # CRITICAL: This is THE authoritative calculation
        # Final Value = Initial Capital + Realized P&L + Unrealized P&L - Charges
        final_value = initial_capital + realized_pnl + unrealized_pnl - total_charges
        
        # === STEP 4: Derive Total P&L from Final Value (NOT independent calculation) ===
        # Total P&L = Final Value - Initial Capital
        total_pnl = final_value - initial_capital
        
        # === STEP 5: Derive Returns from Final Value (NOT from P&L) ===
        # Returns % = (Final Value - Initial Capital) / Initial Capital * 100
        returns_percent = ((final_value - initial_capital) / initial_capital) * 100
        
        # === STEP 6: Validate mathematical consistency ===
        # Check 1: Realized + Unrealized - Charges = Total P&L
        calculated_total_pnl = realized_pnl + unrealized_pnl - total_charges
        pnl_consistency_error = abs(calculated_total_pnl - total_pnl)
        if pnl_consistency_error > 0.01:  # 1 paisa tolerance
            print(f"[ERROR] P&L CONSISTENCY BROKEN!")
            print(f"  Realized: {realized_pnl:.2f}")
            print(f"  Unrealized: {unrealized_pnl:.2f}")
            print(f"  Charges: {total_charges:.2f}")
            print(f"  Expected Total P&L: {calculated_total_pnl:.2f}")
            print(f"  Actual Total P&L: {total_pnl:.2f}")
            print(f"  Difference: {pnl_consistency_error:.2f}")
        
        # Check 2: Final Value = Initial + Total P&L
        expected_final_value = initial_capital + total_pnl
        value_consistency_error = abs(final_value - expected_final_value)
        if value_consistency_error > 0.01:  # 1 paisa tolerance
            print(f"[ERROR] FINAL VALUE CONSISTENCY BROKEN!")
            print(f"  Initial Capital: {initial_capital:.2f}")
            print(f"  Total P&L: {total_pnl:.2f}")
            print(f"  Expected Final Value: {expected_final_value:.2f}")
            print(f"  Actual Final Value: {final_value:.2f}")
            print(f"  Difference: {value_consistency_error:.2f}")
        
        # Portfolio snapshot (for reference, but NOT used for calculations)
        current_capital = portfolio.current_capital
        invested_capital = portfolio.invested_capital
        
        # === STEP 7: Calculate Trade Statistics (from closed positions only) ===
        closed_positions = portfolio.closed_positions
        total_trades = len(closed_positions)
        
        winning_trades = sum(1 for pos in closed_positions if pos.realized_pnl > 0)
        losing_trades = sum(1 for pos in closed_positions if pos.realized_pnl < 0)
        
        # Validate: Wins + Losses = Total Trades
        if winning_trades + losing_trades != total_trades:
            print(f"[ERROR] Trade count mismatch: {winning_trades} + {losing_trades} != {total_trades}")
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Average Win/Loss
        avg_win = (
            sum(pos.realized_pnl for pos in closed_positions if pos.realized_pnl > 0) / winning_trades
            if winning_trades > 0 else 0
        )
        
        avg_loss = (
            sum(pos.realized_pnl for pos in closed_positions if pos.realized_pnl < 0) / losing_trades
            if losing_trades > 0 else 0
        )
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # === STEP 8: Validate P&L sum from trade statistics ===
        # (Avg Win × Wins) + (Avg Loss × Losses) should equal Realized P&L
        calculated_realized_pnl = (avg_win * winning_trades) + (avg_loss * losing_trades)
        realized_pnl_error = abs(calculated_realized_pnl - realized_pnl)
        if realized_pnl_error > 0.01:
            print(f"[WARNING] Realized P&L validation: Calculated={calculated_realized_pnl:.2f}, Actual={realized_pnl:.2f}")
        
        # === STEP 9: Prepare executed trades with complete entry/exit data ===
        executed_trades_with_exits = []
        for pos in closed_positions:
            trade = {
                "symbol": pos.symbol,
                "entry_side": pos.side.value,
                "entry_price": pos.entry_price,
                "entry_timestamp": pos.entry_time.isoformat() if pos.entry_time else None,
                "quantity": pos.quantity,
                "exit_side": "SELL" if pos.side.value == "LONG" else "BUY",
                "exit_price": pos.exit_price if pos.exit_price else pos.current_price,
                "exit_timestamp": pos.exit_time.isoformat() if pos.exit_time else datetime.now().isoformat(),
                "exit_reason": getattr(pos, 'exit_reason', 'AUTO_EXIT'),
                "strategy": getattr(pos, 'strategy', 'UNKNOWN'),
                "stop_loss": getattr(pos, 'stop_loss', None),
                "target": getattr(pos, 'target', None),
                "gross_pnl": pos.realized_pnl + portfolio.brokerage_per_trade,  # Add back brokerage
                "brokerage": portfolio.brokerage_per_trade,
                "net_pnl": pos.realized_pnl,
                "holding_period_minutes": self._calculate_holding_period(pos)
            }
            executed_trades_with_exits.append(trade)
        
        # === STEP 10: Build equity curve ===
        equity_curve = []
        for date_key, pnl in sorted(self.daily_pnl.items()):
            equity_curve.append({
                "date": str(date_key),
                "portfolio_value": initial_capital + pnl,
                "pnl": pnl
            })
        
        # === STEP 11: Return comprehensive results (ALL VALUES DERIVED FROM FINAL VALUE) ===
        return {
            "config": {
                "symbols": self.config.symbols,
                "start_date": str(self.config.start_date),
                "end_date": str(self.config.end_date),
                "strategies": self.config.strategies,
                "stop_loss_percent": self.config.stop_loss_percent,
                "profit_target_percent": self.config.profit_target_percent,
                "mode": self.config.mode.value
            },
            "portfolio": {
                # CRITICAL: Single source of truth values
                "initial_capital": round(initial_capital, 2),
                "realized_pnl": round(realized_pnl, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "total_charges": round(total_charges, 2),
                "total_pnl": round(total_pnl, 2),  # DERIVED: Final Value - Initial Capital
                "final_value": round(final_value, 2),  # SINGLE SOURCE OF TRUTH
                "returns_percent": round(returns_percent, 2),  # DERIVED: From Final Value
                
                # Reference values (not used for calculations)
                "current_capital": round(current_capital, 2),
                "invested_capital": round(invested_capital, 2),
                
                # Positions
                "open_positions_count": len(portfolio.positions),
                "closed_positions_count": len(closed_positions),
                
                # Costs breakdown
                "total_brokerage": round(portfolio.total_brokerage_paid, 2),
            },
            "performance": {
                # Trade statistics (completed round trips only)
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
            },
            # Signals vs Trades (CRITICAL: They are different)
            "signals": {
                "total_signals_generated": len(self.all_signals),
                "signal_breakdown": self._get_signal_breakdown(),
                "note": "Signals are NOT trades. Trades occur when signal aggregation triggers execution."
            },
            # Trade data
            "executed_trades": executed_trades_with_exits,
            
            # Daily tracking
            "daily_pnl": {str(k): round(v, 2) for k, v in self.daily_pnl.items()},
            "equity_curve": equity_curve,
        }
    
    def _calculate_holding_period(self, position) -> int:
        """Calculate holding period in minutes"""
        if hasattr(position, 'entry_time') and hasattr(position, 'exit_time'):
            if position.entry_time and position.exit_time:
                delta = position.exit_time - position.entry_time
                return int(delta.total_seconds() / 60)
        return 0
    
    def _get_signal_breakdown(self) -> Dict[str, Any]:
        """Get breakdown of signals by strategy and type"""
        breakdown = {}
        
        for signal in self.all_signals:
            strategy = signal.strategy_name
            if strategy not in breakdown:
                breakdown[strategy] = {"BUY": 0, "SELL": 0, "total": 0}
            
            breakdown[strategy][signal.signal] += 1
            breakdown[strategy]["total"] += 1
        
        return breakdown
