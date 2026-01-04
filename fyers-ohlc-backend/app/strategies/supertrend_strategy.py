from typing import Dict, List
import pandas as pd
from datetime import datetime
from .base import BaseStrategy, SignalType, TradeSignal

class SupertrendStrategy(BaseStrategy):
    def __init__(
        self,
        symbol: str,
        atr_period: int = 10,
        multiplier: float = 3.0,
        risk_reward_ratio: float = 2.0
    ):
        super().__init__(symbol, {
            'atr_period': atr_period,
            'multiplier': multiplier,
            'risk_reward_ratio': risk_reward_ratio
        })
        
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        if data.empty:
            return []
            
        # Calculate ATR
        atr = self.calculate_atr(data['high'], data['low'], data['close'], self.params['atr_period'])
        
        # Calculate Supertrend
        hl2 = (data['high'] + data['low']) / 2
        upper_band = hl2 + (self.params['multiplier'] * atr)
        lower_band = hl2 - (self.params['multiplier'] * atr)
        
        # Initialize variables
        supertrend = pd.Series(index=data.index)
        direction = pd.Series(1, index=data.index)
        
        # Calculate Supertrend
        for i in range(1, len(data)):
            if data['close'].iloc[i-1] > supertrend.iloc[i-1]:
                direction.iloc[i] = 1
            elif data['close'].iloc[i-1] < supertrend.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1]
                
            if direction.iloc[i] < 0 and upper_band.iloc[i] < supertrend.iloc[i-1]:
                supertrend.iloc[i] = upper_band.iloc[i]
            elif direction.iloc[i] > 0 and lower_band.iloc[i] > supertrend.iloc[i-1]:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                if direction.iloc[i] < 0:
                    supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i-1])
                else:
                    supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i-1])
        
        # Generate signals
        signals = []
        for i in range(1, len(data)):
            current_direction = direction.iloc[i]
            prev_direction = direction.iloc[i-1]
            
            if current_direction == 1 and prev_direction == -1:
                # Buy signal
                entry_price = data['close'].iloc[i]
                stop_loss = supertrend.iloc[i]
                risk = entry_price - stop_loss
                target_price = entry_price + (risk * self.params['risk_reward_ratio'])
                
                signals.append(TradeSignal(
                    symbol=self.symbol,
                    signal=SignalType.BUY,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    timestamp=data.index[i].to_pydatetime(),
                    confidence=0.7,
                    metadata={
                        'strategy': 'Supertrend',
                        'atr_period': self.params['atr_period'],
                        'multiplier': self.params['multiplier']
                    }
                ))
                
            elif current_direction == -1 and prev_direction == 1:
                # Sell signal
                entry_price = data['close'].iloc[i]
                stop_loss = supertrend.iloc[i]
                risk = stop_loss - entry_price
                target_price = entry_price - (risk * self.params['risk_reward_ratio'])
                
                signals.append(TradeSignal(
                    symbol=self.symbol,
                    signal=SignalType.SELL,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    timestamp=data.index[i].to_pydatetime(),
                    confidence=0.7,
                    metadata={
                        'strategy': 'Supertrend',
                        'atr_period': self.params['atr_period'],
                        'multiplier': self.params['multiplier']
                    }
                ))
                
        return signals
