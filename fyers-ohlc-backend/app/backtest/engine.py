from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
from ..strategies.base import TradeSignal

class BacktestResult:
    def __init__(self):
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.net_pnl = 0.0
        self.max_drawdown = 0.0
        self.win_rate = 0.0
        self.avg_profit = 0.0
        self.avg_loss = 0.0
        self.trade_history = []
        
    def add_trade(self, trade: Dict[str, Any]):
        self.trade_history.append(trade)
        self.total_trades += 1
        
        if trade['pnl'] > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
            
        self.net_pnl += trade['pnl']
        self.win_rate = (self.winning_trades / self.total_trades) * 100 if self.total_trades > 0 else 0
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'net_pnl': self.net_pnl,
            'win_rate': self.win_rate,
            'max_drawdown': self.max_drawdown,
            'avg_profit': self.avg_profit,
            'avg_loss': self.avg_loss,
            'profit_factor': abs(self.avg_profit / self.avg_loss) if self.avg_loss != 0 else float('inf')
        }

class BacktestEngine:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position = None
        self.trade_history = []
        
    def run(
        self,
        data: pd.DataFrame,
        signals: List[TradeSignal],
        commission: float = 0.0005,  # 0.05% commission per trade
        slippage: float = 0.0005     # 0.05% slippage per trade
    ) -> Dict[str, Any]:
        result = BacktestResult()
        
        for signal in signals:
            if signal.signal == 'BUY' and not self.position:
                # Calculate position size (1% risk per trade)
                risk_amount = self.current_capital * 0.01
                risk_per_share = abs(signal.entry_price - signal.stop_loss)
                position_size = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
                
                if position_size > 0:
                    # Calculate costs
                    cost = signal.entry_price * position_size
                    commission_cost = cost * commission
                    slippage_cost = cost * slippage
                    total_cost = cost + commission_cost + slippage_cost
                    
                    # Update position
                    self.position = {
                        'entry_price': signal.entry_price,
                        'stop_loss': signal.stop_loss,
                        'target': signal.target_price,
                        'size': position_size,
                        'entry_time': signal.timestamp,
                        'entry_signal': signal
                    }
                    
                    # Update capital
                    self.current_capital -= total_cost
                    
            elif signal.signal == 'SELL' and self.position:
                # Calculate exit price with slippage
                exit_price = signal.entry_price * (1 - slippage)
                
                # Calculate P&L
                entry_price = self.position['entry_price']
                pnl = (exit_price - entry_price) * self.position['size']
                pnl -= (entry_price * self.position['size'] * commission)  # Commission on exit
                
                # Update trade history
                trade = {
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'size': self.position['size'],
                    'entry_time': self.position['entry_time'],
                    'exit_time': signal.timestamp,
                    'pnl': pnl,
                    'return_pct': (exit_price - entry_price) / entry_price * 100,
                    'signal': signal.to_dict()
                }
                
                result.add_trade(trade)
                
                # Update capital
                self.current_capital += (exit_price * self.position['size']) - (exit_price * self.position['size'] * commission)
                self.position = None
                
        # Calculate metrics
        if result.total_trades > 0:
            winning_pnls = [t['pnl'] for t in result.trade_history if t['pnl'] > 0]
            losing_pnls = [t['pnl'] for t in result.trade_history if t['pnl'] <= 0]
            
            result.avg_profit = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
            result.avg_loss = abs(sum(losing_pnls) / len(losing_pnls)) if losing_pnls else 0
            
            # Calculate max drawdown
            equity_curve = [self.initial_capital]
            for trade in result.trade_history:
                equity_curve.append(equity_curve[-1] + trade['pnl'])
                
            peak = equity_curve[0]
            max_dd = 0
            for value in equity_curve:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
            result.max_drawdown = max_dd * 100  # as percentage
            
        return result.to_dict()
