"""
Simple Moving Average Crossover Strategy
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
import logging

from src.core.strategy_base import StrategyBase


logger = logging.getLogger(__name__)


class MovingAverageStrategy(StrategyBase):
    """
    A simple moving average crossover strategy.
    
    Generates buy signals when short MA crosses above long MA,
    and sell signals when short MA crosses below long MA.
    """
    
    def __init__(self):
        super().__init__("moving_average")
        
        # Strategy parameters
        self.short_window = 20
        self.long_window = 50
        self.symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        # Data storage
        self.price_data: Dict[str, pd.DataFrame] = {}
        self.last_signals: Dict[str, str] = {}
        
        # Initialize parameters
        self.set_parameters({
            'short_window': self.short_window,
            'long_window': self.long_window,
            'symbols': self.symbols
        })
    
    async def on_market_data(self, data: Dict[str, Any]):
        """Process incoming market data and generate signals."""
        try:
            symbol = data.get('symbol')
            price = data.get('price')
            timestamp = data.get('timestamp')
            
            if not all([symbol, price, timestamp]):
                return
            
            # Only process symbols we're interested in
            if symbol not in self.symbols:
                return
            
            # Initialize price data for new symbols
            if symbol not in self.price_data:
                self.price_data[symbol] = pd.DataFrame(columns=['timestamp', 'price'])
            
            # Add new price data
            new_row = pd.DataFrame({
                'timestamp': [timestamp],
                'price': [price]
            })
            self.price_data[symbol] = pd.concat([self.price_data[symbol], new_row], ignore_index=True)
            
            # Keep only recent data (last 200 points)
            if len(self.price_data[symbol]) > 200:
                self.price_data[symbol] = self.price_data[symbol].tail(200).reset_index(drop=True)
            
            # Calculate moving averages and generate signals
            await self._check_signals(symbol)
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
    
    async def _check_signals(self, symbol: str):
        """Check for trading signals based on moving average crossover."""
        df = self.price_data[symbol]
        
        # Need enough data points
        if len(df) < self.long_window:
            return
        
        # Calculate moving averages
        df['short_ma'] = df['price'].rolling(window=self.short_window).mean()
        df['long_ma'] = df['price'].rolling(window=self.long_window).mean()
        
        # Get the last few values
        current_short_ma = df['short_ma'].iloc[-1]
        current_long_ma = df['long_ma'].iloc[-1]
        prev_short_ma = df['short_ma'].iloc[-2]
        prev_long_ma = df['long_ma'].iloc[-2]
        
        # Check for valid values
        if pd.isna(current_short_ma) or pd.isna(current_long_ma):
            return
        
        current_position = self.get_position(symbol)
        last_signal = self.last_signals.get(symbol, 'none')
        
        # Check for crossover signals
        if (prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma and 
            current_position <= 0 and last_signal != 'buy'):
            # Golden cross - buy signal
            await self.emit_signal(
                symbol=symbol,
                action='buy',
                confidence=0.8,
                reason='golden_cross',
                short_ma=current_short_ma,
                long_ma=current_long_ma
            )
            self.last_signals[symbol] = 'buy'
            
        elif (prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma and 
              current_position >= 0 and last_signal != 'sell'):
            # Death cross - sell signal
            await self.emit_signal(
                symbol=symbol,
                action='sell',
                confidence=0.8,
                reason='death_cross',
                short_ma=current_short_ma,
                long_ma=current_long_ma
            )
            self.last_signals[symbol] = 'sell'
    
    async def on_order_filled(self, fill: Dict[str, Any]):
        """Handle order fill notifications."""
        symbol = fill.get('symbol')
        side = fill.get('side')
        quantity = fill.get('quantity', 0)
        
        if not symbol:
            return
        
        # Update position tracking
        current_position = self.get_position(symbol)
        
        if side == 'buy':
            new_position = current_position + quantity
        else:  # sell
            new_position = current_position - quantity
        
        self.update_position(symbol, new_position)
        
        logger.info(f"Position updated for {symbol}: {current_position} -> {new_position}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information and current state."""
        return {
            'name': self.name,
            'type': 'trend_following',
            'parameters': self.parameters,
            'positions': self.positions,
            'symbols_tracked': len(self.price_data),
            'data_points': {symbol: len(df) for symbol, df in self.price_data.items()},
            'last_signals': self.last_signals
        }