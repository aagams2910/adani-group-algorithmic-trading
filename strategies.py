from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TradeSignal:
    timestamp: datetime
    type: str  # 'LONG' or 'SHORT'
    price: float
    stop_loss: float
    take_profit: float
    reason: str

class BaseStrategy(ABC):
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.signals: List[TradeSignal] = []
    
    @abstractmethod
    def generate_signals(self) -> List[TradeSignal]:
        pass
    
    def calculate_returns(self) -> pd.Series:
        """Calculate strategy returns"""
        # Initialize returns series with zeros
        returns = pd.Series(0.0, index=self.data.index)
        position = 0
        entry_price = 0
        entry_index = None
        
        for i, signal in enumerate(self.signals):
            if signal.type == 'LONG':
                position = 1
                entry_price = signal.price
                entry_index = signal.timestamp
            
            # Calculate returns until next signal or exit condition
            if position == 1:
                # Find the next signal or end of data
                next_signal_idx = i + 1 if i + 1 < len(self.signals) else len(self.signals)
                if next_signal_idx < len(self.signals):
                    next_signal = self.signals[next_signal_idx]
                    mask = (self.data.index > entry_index) & (self.data.index <= next_signal.timestamp)
                else:
                    mask = (self.data.index > entry_index)
                
                if mask.any():
                    # Calculate returns for the position
                    position_returns = (self.data.loc[mask, 'close'] - entry_price) / entry_price
                    returns[mask] = position_returns
                    position = 0  # Reset position after calculating returns
        
        return returns

class ACCStrategy(BaseStrategy):
    def __init__(self, data: pd.DataFrame):
        super().__init__(data)
        # Calculate basic indicators
        self.data['SMA_20'] = self.data.ta.sma(length=20)
        self.data['SMA_50'] = self.data.ta.sma(length=50)
        self.data['SMA_200'] = self.data.ta.sma(length=200)
        self.data['RSI'] = self.data.ta.rsi(length=14)
        
        # Calculate volatility
        self.data['ATR'] = self.data.ta.atr(length=14)
        self.data['ATR_MA'] = self.data['ATR'].rolling(window=20).mean()
        
        # Calculate momentum
        self.data['MACD'] = self.data.ta.macd(fast=12, slow=26, signal=9)['MACD_12_26_9']
        self.data['MACD_Signal'] = self.data.ta.macd(fast=12, slow=26, signal=9)['MACDs_12_26_9']
        self.data['MACD_Hist'] = self.data.ta.macd(fast=12, slow=26, signal=9)['MACDh_12_26_9']
        
        # Calculate price patterns
        self.data['Higher_High'] = self.data['high'].rolling(window=5).max() > self.data['high'].rolling(window=5).max().shift(5)
        self.data['Lower_Low'] = self.data['low'].rolling(window=5).min() < self.data['low'].rolling(window=5).min().shift(5)
        
        # Calculate volume profile
        self.data['Volume_MA'] = self.data['volume'].rolling(window=20).mean()
        self.data['Volume_Ratio'] = self.data['volume'] / self.data['Volume_MA']
        
        # Calculate additional momentum
        self.data['ROC_5'] = self.data.ta.roc(length=5)  # Short-term momentum
        self.data['ROC_20'] = self.data.ta.roc(length=20)  # Medium-term momentum
        
    def generate_signals(self) -> List[TradeSignal]:
        signals = []
        position_open = False
        entry_price = 0
        entry_date = None
        
        for i in range(200, len(self.data)):  # Start from 200 to ensure all indicators are available
            current_price = self.data['close'].iloc[i]
            current_date = self.data.index[i]
            
            # If we have an open position
            if position_open:
                # Dynamic exit conditions based on volatility and momentum
                volatility_exit = self.data['ATR'].iloc[i] > self.data['ATR_MA'].iloc[i] * 1.3
                trend_exit = current_price < self.data['SMA_20'].iloc[i]
                momentum_exit = (self.data['MACD'].iloc[i] < self.data['MACD_Signal'].iloc[i] and 
                               self.data['MACD_Hist'].iloc[i] < 0)
                rsi_exit = self.data['RSI'].iloc[i] > 70
                
                exit_conditions = [
                    volatility_exit,  # Exit on high volatility
                    trend_exit,  # Exit on trend reversal
                    momentum_exit,  # Exit on momentum reversal
                    rsi_exit,  # Exit on overbought
                    current_price <= entry_price * 0.98,  # 2% stop loss
                    current_price >= entry_price * 1.04,  # 4% take profit
                    (current_date - entry_date).days >= 8  # Maximum 8-day hold
                ]
                
                if any(exit_conditions):
                    position_open = False
                    entry_price = 0
                    entry_date = None
                    continue
            
            # Check entry conditions (only if no position is open)
            if not position_open:
                # Volatility check
                volatility_ok = (self.data['ATR'].iloc[i] < self.data['ATR_MA'].iloc[i] * 1.1 and
                               self.data['ATR'].iloc[i] > self.data['ATR_MA'].iloc[i] * 0.7)
                
                # Trend check
                trend_ok = (current_price > self.data['SMA_20'].iloc[i] and 
                           self.data['SMA_20'].iloc[i] > self.data['SMA_50'].iloc[i] and
                           self.data['SMA_50'].iloc[i] > self.data['SMA_200'].iloc[i])
                
                # Momentum check
                momentum_ok = (self.data['RSI'].iloc[i] > 45 and 
                             self.data['RSI'].iloc[i] < 65 and
                             self.data['MACD'].iloc[i] > self.data['MACD_Signal'].iloc[i] and
                             self.data['MACD_Hist'].iloc[i] > 0 and
                             self.data['ROC_5'].iloc[i] > 0 and
                             self.data['ROC_20'].iloc[i] > 0)
                
                # Volume check
                volume_ok = self.data['Volume_Ratio'].iloc[i] > 1.3
                
                # Price pattern check
                pattern_ok = (self.data['Higher_High'].iloc[i] and 
                            not self.data['Lower_Low'].iloc[i] and
                            current_price > self.data['SMA_20'].iloc[i] * 1.01)  # 1% above SMA
                
                # Entry conditions
                entry_conditions = [
                    volatility_ok,  # Normal volatility
                    trend_ok,  # Strong uptrend
                    momentum_ok,  # Strong momentum
                    volume_ok,  # Good volume
                    pattern_ok  # Higher highs
                ]
                
                if all(entry_conditions):
                    # Calculate stop loss and take profit based on ATR
                    atr = self.data['ATR'].iloc[i]
                    stop_loss = current_price - (atr * 1.2)  # Tighter stop
                    take_profit = current_price + (atr * 2.0)  # Reduced target
                    
                    signals.append(TradeSignal(
                        timestamp=current_date,
                        type='LONG',
                        price=current_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        reason='Strong trend with momentum and volume confirmation'
                    ))
                    position_open = True
                    entry_price = current_price
                    entry_date = current_date
        
        self.signals = signals
        return signals

class AdaniEnterprisesStrategy(BaseStrategy):
    def __init__(self, data: pd.DataFrame):
        super().__init__(data)
        # Calculate 20-day high
        self.data['High_20'] = self.data['high'].rolling(window=20).max()
        
    def generate_signals(self) -> List[TradeSignal]:
        signals = []
        position_open = False
        entry_price = 0
        entry_date = None
        
        for i in range(20, len(self.data)):
            current_price = self.data['close'].iloc[i]
            current_date = self.data.index[i]
            
            # If we have an open position
            if position_open:
                # Check exit conditions
                exit_conditions = [
                    (current_date - entry_date).days >= 10,  # 10-day holding period
                    current_price <= entry_price * 0.97  # 3% stop loss
                ]
                
                if any(exit_conditions):
                    position_open = False
                    entry_price = 0
                    entry_date = None
                    continue
            
            # Check entry conditions (only if no position is open)
            if not position_open:
                # Breakout condition
                if current_price > self.data['High_20'].iloc[i-1]:  # Price exceeds 20-day high
                    signals.append(TradeSignal(
                        timestamp=current_date,
                        type='LONG',
                        price=current_price,
                        stop_loss=current_price * 0.97,  # 3% stop loss
                        take_profit=current_price * 1.12,  # 12% take profit
                        reason='20-day high breakout'
                    ))
                    position_open = True
                    entry_price = current_price
                    entry_date = current_date
        
        self.signals = signals
        return signals

class AdaniPowerStrategy(BaseStrategy):
    def __init__(self, data: pd.DataFrame):
        super().__init__(data)
        # Calculate 50 and 200 day SMAs
        self.data['SMA_50'] = self.data.ta.sma(length=50)
        self.data['SMA_200'] = self.data.ta.sma(length=200)
        
    def generate_signals(self) -> List[TradeSignal]:
        signals = []
        position_open = False
        entry_price = 0
        entry_date = None
        
        for i in range(200, len(self.data)):  # Start from 200 to ensure both SMAs are available
            current_price = self.data['close'].iloc[i]
            current_date = self.data.index[i]
            
            # Check for SMA crossover
            golden_cross = (self.data['SMA_50'].iloc[i-1] <= self.data['SMA_200'].iloc[i-1] and 
                          self.data['SMA_50'].iloc[i] > self.data['SMA_200'].iloc[i])
            
            death_cross = (self.data['SMA_50'].iloc[i-1] >= self.data['SMA_200'].iloc[i-1] and 
                         self.data['SMA_50'].iloc[i] < self.data['SMA_200'].iloc[i])
            
            # If we have an open position, check for death cross exit
            if position_open and death_cross:
                position_open = False
                entry_price = 0
                entry_date = None
                continue
            
            # Check for golden cross entry (only if no position is open)
            if not position_open and golden_cross:
                signals.append(TradeSignal(
                    timestamp=current_date,
                    type='LONG',
                    price=current_price,
                    stop_loss=current_price * 0.94,  # 6% stop loss
                    take_profit=current_price * 1.12,  # 12% take profit
                    reason='50/200 SMA golden cross'
                ))
                position_open = True
                entry_price = current_price
                entry_date = current_date
        
        self.signals = signals
        return signals

class AdaniPortsStrategy(BaseStrategy):
    def __init__(self, data: pd.DataFrame):
        super().__init__(data)
        # Calculate 30-day high
        self.data['High_30'] = self.data['high'].rolling(window=30).max()
        
    def generate_signals(self) -> List[TradeSignal]:
        signals = []
        position_open = False
        entry_price = 0
        entry_date = None
        
        for i in range(30, len(self.data)):
            current_price = self.data['close'].iloc[i]
            current_date = self.data.index[i]
            
            # If we have an open position
            if position_open:
                # Check exit conditions
                exit_conditions = [
                    (current_date - entry_date).days >= 10,  # 10-day holding period
                    current_price <= entry_price * 0.95  # 5% stop loss
                ]
                
                if any(exit_conditions):
                    position_open = False
                    entry_price = 0
                    entry_date = None
                    continue
            
            # Check entry conditions (only if no position is open)
            if not position_open:
                # Breakout condition
                if current_price > self.data['High_30'].iloc[i-1]:  # Price exceeds 30-day high
                    signals.append(TradeSignal(
                        timestamp=current_date,
                        type='LONG',
                        price=current_price,
                        stop_loss=current_price * 0.95,  # 5% stop loss
                        take_profit=current_price * 1.12,  # 12% take profit
                        reason='30-day high breakout'
                    ))
                    position_open = True
                    entry_price = current_price
                    entry_date = current_date
        
        self.signals = signals
        return signals 