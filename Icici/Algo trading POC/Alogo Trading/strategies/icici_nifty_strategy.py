"""
ICICI Breeze specific trading strategy using NIFTY index.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import logging

from src.core.strategy_base import StrategyBase


logger = logging.getLogger(__name__)


class ICICINiftyStrategy(StrategyBase):
    """
    A NIFTY-focused strategy using ICICI Breeze data.
    
    Strategy:
    - Uses NIFTY and BANKNIFTY data from ICICI Breeze
    - Implements trend-following with momentum indicators
    - Trades NIFTY futures and options
    """
    
    def __init__(self):
        super().__init__("icici_nifty_strategy")
        
        # Strategy parameters
        self.ema_short = 9
        self.ema_long = 21
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        # Symbols to trade
        self.symbols = {
            'NIFTY': 'NSE.NIFTY',
            'BANKNIFTY': 'NSE.BANKNIFTY'
        }
        
        # Data storage
        self.price_data: Dict[str, pd.DataFrame] = {}
        self.indicators: Dict[str, Dict[str, float]] = {}
        self.last_signals: Dict[str, str] = {}
        
        # Position tracking
        self.target_positions: Dict[str, float] = {}
        
        # ICICI Breeze specific settings
        self.exchange_code = "NFO"  # For futures and options
        self.product_type = "futures"
        self.expiry_date = self._get_next_expiry()
        
        # Initialize parameters
        self.set_parameters({
            'ema_short': self.ema_short,
            'ema_long': self.ema_long,
            'rsi_period': self.rsi_period,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'symbols': list(self.symbols.keys()),
            'exchange_code': self.exchange_code,
            'product_type': self.product_type
        })
    
    async def on_market_data(self, data: Dict[str, Any]):
        """Process incoming market data from ICICI Breeze."""
        try:
            symbol = data.get('symbol', '')
            price = data.get('last_price', data.get('ltp', 0))
            timestamp = data.get('timestamp')
            volume = data.get('volume', data.get('ttq', 0))
            
            if not all([symbol, price, timestamp]):
                return
            
            # Check if this is a symbol we're interested in
            symbol_key = None
            for key, breeze_symbol in self.symbols.items():
                if symbol == breeze_symbol or symbol.endswith(key):
                    symbol_key = key
                    break
            
            if not symbol_key:
                return
            
            # Initialize data storage for symbol
            if symbol_key not in self.price_data:
                self.price_data[symbol_key] = pd.DataFrame(columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume'
                ])
            
            # Convert timestamp
            if isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp)
            elif not isinstance(timestamp, pd.Timestamp):
                timestamp = pd.Timestamp.now()
            
            # Add new data point
            new_row = pd.DataFrame({
                'timestamp': [timestamp],
                'open': [price],
                'high': [price],
                'low': [price],
                'close': [price],
                'volume': [volume]
            })
            
            self.price_data[symbol_key] = pd.concat([
                self.price_data[symbol_key], new_row
            ], ignore_index=True)
            
            # Keep only recent data (last 200 points)
            if len(self.price_data[symbol_key]) > 200:
                self.price_data[symbol_key] = self.price_data[symbol_key].tail(200).reset_index(drop=True)
            
            # Update indicators and check for signals
            await self._update_indicators(symbol_key)
            await self._check_signals(symbol_key)
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
    
    async def _update_indicators(self, symbol: str):
        """Update technical indicators for the symbol."""
        df = self.price_data[symbol]
        
        if len(df) < max(self.ema_long, self.rsi_period):
            return
        
        # Calculate EMAs
        df['ema_short'] = df['close'].ewm(span=self.ema_short).mean()
        df['ema_long'] = df['close'].ewm(span=self.ema_long).mean()
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Store current indicators
        if symbol not in self.indicators:
            self.indicators[symbol] = {}
        
        self.indicators[symbol] = {
            'ema_short': df['ema_short'].iloc[-1],
            'ema_long': df['ema_long'].iloc[-1],
            'rsi': df['rsi'].iloc[-1],
            'price': df['close'].iloc[-1],
            'volume': df['volume'].iloc[-1]
        }
    
    async def _check_signals(self, symbol: str):
        """Check for trading signals."""
        if symbol not in self.indicators:
            return
        
        indicators = self.indicators[symbol]
        
        # Check if we have valid indicator values
        if any(pd.isna(val) for val in indicators.values()):
            return
        
        current_position = self.get_position(symbol)
        last_signal = self.last_signals.get(symbol, 'none')
        
        ema_short = indicators['ema_short']
        ema_long = indicators['ema_long']
        rsi = indicators['rsi']
        price = indicators['price']
        
        # Trend detection
        trend = 'up' if ema_short > ema_long else 'down'
        
        # Signal generation
        signal_strength = abs(ema_short - ema_long) / ema_long
        
        # Buy signal: Uptrend + RSI oversold recovery
        if (trend == 'up' and 
            rsi > self.rsi_oversold and rsi < 50 and
            current_position <= 0 and 
            last_signal != 'buy' and
            signal_strength > 0.005):  # 0.5% EMA divergence
            
            await self.emit_signal(
                symbol=f"{self.exchange_code}.{symbol}",
                action='buy',
                confidence=min(0.8, signal_strength * 10),
                price=price,
                quantity=self._calculate_position_size(symbol, price),
                product_type=self.product_type,
                expiry_date=self.expiry_date,
                right='others' if self.product_type == 'futures' else 'call',
                strike_price='0' if self.product_type == 'futures' else str(int(price)),
                reason='ema_crossover_rsi_recovery',
                indicators={
                    'ema_short': ema_short,
                    'ema_long': ema_long,
                    'rsi': rsi,
                    'trend': trend,
                    'signal_strength': signal_strength
                }
            )
            self.last_signals[symbol] = 'buy'
        
        # Sell signal: Downtrend + RSI overbought decline
        elif (trend == 'down' and 
              rsi < self.rsi_overbought and rsi > 50 and
              current_position >= 0 and 
              last_signal != 'sell' and
              signal_strength > 0.005):
            
            await self.emit_signal(
                symbol=f"{self.exchange_code}.{symbol}",
                action='sell',
                confidence=min(0.8, signal_strength * 10),
                price=price,
                quantity=self._calculate_position_size(symbol, price),
                product_type=self.product_type,
                expiry_date=self.expiry_date,
                right='others' if self.product_type == 'futures' else 'put',
                strike_price='0' if self.product_type == 'futures' else str(int(price)),
                reason='ema_crossover_rsi_decline',
                indicators={
                    'ema_short': ema_short,
                    'ema_long': ema_long,
                    'rsi': rsi,
                    'trend': trend,
                    'signal_strength': signal_strength
                }
            )
            self.last_signals[symbol] = 'sell'
    
    def _calculate_position_size(self, symbol: str, price: float) -> int:
        """Calculate position size based on symbol and price."""
        # NIFTY lot size is typically 75, BANKNIFTY is 15
        lot_sizes = {
            'NIFTY': 75,
            'BANKNIFTY': 15
        }
        
        lot_size = lot_sizes.get(symbol, 1)
        
        # For futures, trade 1 lot to start
        if self.product_type == 'futures':
            return lot_size
        
        # For options, can trade multiple lots based on premium
        base_lots = 1
        if price < 50:  # Cheap options, can afford more lots
            base_lots = 2
        elif price > 200:  # Expensive options, stick to 1 lot
            base_lots = 1
        
        return lot_size * base_lots
    
    def _get_next_expiry(self) -> str:
        """Get the next Thursday expiry date for NIFTY."""
        today = datetime.now()
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0 and today.hour >= 15:  # After 3 PM on Thursday
            days_until_thursday = 7
        
        next_thursday = today + timedelta(days=days_until_thursday)
        return next_thursday.strftime("%Y-%m-%dT06:00:00.000Z")
    
    async def on_order_filled(self, fill: Dict[str, Any]):
        """Handle order fill notifications."""
        symbol = fill.get('symbol', '').split('.')[-1]  # Extract symbol from exchange.symbol
        side = fill.get('side', '')
        quantity = fill.get('quantity', 0)
        
        if not symbol or symbol not in self.symbols:
            return
        
        # Update position tracking
        current_position = self.get_position(symbol)
        
        if side.lower() == 'buy':
            new_position = current_position + quantity
        else:  # sell
            new_position = current_position - quantity
        
        self.update_position(symbol, new_position)
        
        logger.info(f"Position updated for {symbol}: {current_position} -> {new_position}")
        
        # Update target position
        self.target_positions[symbol] = new_position
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get comprehensive strategy information."""
        return {
            'name': self.name,
            'type': 'trend_momentum',
            'exchange': self.exchange_code,
            'product_type': self.product_type,
            'expiry_date': self.expiry_date,
            'parameters': self.parameters,
            'positions': self.positions,
            'target_positions': self.target_positions,
            'symbols_tracked': list(self.symbols.keys()),
            'indicators': self.indicators,
            'last_signals': self.last_signals,
            'data_points': {symbol: len(df) for symbol, df in self.price_data.items()},
            'market_data_status': {
                symbol: {
                    'last_update': df['timestamp'].iloc[-1].isoformat() if len(df) > 0 else None,
                    'latest_price': df['close'].iloc[-1] if len(df) > 0 else None
                } for symbol, df in self.price_data.items()
            }
        }