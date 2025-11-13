"""
ICICI Direct Breeze Broker Implementation
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import hashlib
import json
import base64
from pathlib import Path

import aiohttp
import pandas as pd
from breeze_connect import BreezeConnect
from dotenv import load_dotenv

from src.brokers.broker_interface import BrokerInterface
from src.utils.events import Event


logger = logging.getLogger(__name__)


class ICICIBreezeBroker(BrokerInterface):
    """
    ICICI Direct Breeze broker implementation for algorithmic trading.
    """
    
    def __init__(self, paper_trading: bool = True):
        super().__init__("icici_breeze", paper_trading)
        
        # Load environment variables
        self._load_env_vars()
        
        # API credentials
        self.api_key: Optional[str] = os.getenv('API_KEY')
        self.api_secret: Optional[str] = os.getenv('API_SECRET')
        self.session_token: Optional[str] = os.getenv('SESSION_TOKEN')
        
        # Breeze SDK instance
        self.breeze: Optional[BreezeConnect] = None
        
        # Connection state
        self.is_connected = False
        self.is_authenticated = False
        
        # API rate limiting
        self.requests_per_minute = 100
        self.requests_per_day = 5000
        self.request_count = 0
        self.daily_request_count = 0
        
        # WebSocket for real-time data
        self.ws_connected = False
        
    def _load_env_vars(self):
        """Load environment variables from .env file."""
        # Try to find .env file in multiple locations
        possible_paths = [
            Path(".env"),  # Current directory
            Path("../.env"),  # Parent directory
            Path("../../.env"),  # Two levels up
            Path("d:/Algo Trading/Icici/.env"),  # Specific path
        ]
        
        for env_path in possible_paths:
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded environment variables from: {env_path}")
                break
        else:
            logger.warning("No .env file found in expected locations")
        
    async def connect(self, config: Optional[Dict] = None):
        """Connect to ICICI Breeze API."""
        try:
            if config:
                self.api_key = config.get('api_key') or self.api_key
                self.api_secret = config.get('api_secret') or self.api_secret
                self.session_token = config.get('session_token') or self.session_token
            
            if not all([self.api_key, self.api_secret]):
                raise ValueError("API key and secret are required. Please set them in environment variables or config.")
            
            # Initialize Breeze SDK
            self.breeze = BreezeConnect(api_key=self.api_key)
            
            # Generate session if session_token is provided
            if self.session_token:
                try:
                    response = self.breeze.generate_session(
                        api_secret=self.api_secret,
                        session_token=self.session_token
                    )
                    
                    logger.info(f"Session response: {response}")
                    
                    # Note: generate_session may return None but still authenticate successfully
                    # We'll verify authentication by making a test API call
                    try:
                        # Verify authentication with a test API call
                        test_response = self.breeze.get_customer_details(api_session=self.session_token)
                        
                        if test_response and test_response.get('Status') == 200:
                            self.is_authenticated = True
                            user_name = test_response.get('Success', {}).get('idirect_user_name', 'Unknown')
                            logger.info(f"Successfully authenticated with ICICI Breeze for user: {user_name}")
                        else:
                            raise Exception(f"Authentication verification failed: {test_response}")
                            
                    except Exception as verify_error:
                        raise Exception(f"Failed to verify authentication: {verify_error}")
                        
                except Exception as session_error:
                    logger.error(f"Session generation error: {session_error}")
                    raise Exception(f"Failed to generate session: {session_error}")
            
            self.is_connected = True
            
            # Get customer details to verify connection
            customer_details = await self._get_customer_details()
            if customer_details:
                logger.info(f"Connected to ICICI Breeze for user: {customer_details.get('idirect_user_name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to connect to ICICI Breeze: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from ICICI Breeze API."""
        try:
            if self.ws_connected and self.breeze:
                self.breeze.ws_disconnect()
                self.ws_connected = False
            
            self.is_connected = False
            self.is_authenticated = False
            
            logger.info("Disconnected from ICICI Breeze")
            
        except Exception as e:
            logger.error(f"Error disconnecting from ICICI Breeze: {e}")
    
    async def submit_order(self, order: Dict[str, Any]) -> Optional[str]:
        """Submit an order to ICICI Breeze."""
        if not self.is_authenticated:
            raise Exception("Not authenticated with ICICI Breeze")
        
        if self.paper_trading:
            return await self._submit_paper_order(order)
        
        try:
            # Convert our order format to Breeze format
            breeze_order = self._convert_to_breeze_order(order)
            
            # Submit order using Breeze SDK
            response = self.breeze.place_order(**breeze_order)
            
            if response.get('Status') == 200:
                order_id = response['Success']['order_id']
                logger.info(f"Order submitted successfully: {order_id}")
                
                # Emit order submitted event
                await self._emit_order_event('order_submitted', {
                    'order_id': order_id,
                    'original_order': order,
                    'broker_response': response
                })
                
                return order_id
            else:
                error_msg = response.get('Error', 'Unknown error')
                logger.error(f"Order submission failed: {error_msg}")
                raise Exception(f"Order submission failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            raise
    
    async def cancel_order(self, order_id: str, exchange_code: str = "NSE") -> bool:
        """Cancel an order."""
        if not self.is_authenticated:
            raise Exception("Not authenticated with ICICI Breeze")
        
        try:
            response = self.breeze.cancel_order(
                exchange_code=exchange_code,
                order_id=order_id
            )
            
            if response.get('Status') == 200:
                logger.info(f"Order cancelled successfully: {order_id}")
                
                await self._emit_order_event('order_cancelled', {
                    'order_id': order_id,
                    'broker_response': response
                })
                
                return True
            else:
                error_msg = response.get('Error', 'Unknown error')
                logger.error(f"Order cancellation failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> bool:
        """Modify an existing order."""
        if not self.is_authenticated:
            raise Exception("Not authenticated with ICICI Breeze")
        
        try:
            # Convert modifications to Breeze format
            breeze_modifications = self._convert_modifications_to_breeze(modifications)
            breeze_modifications['order_id'] = order_id
            
            response = self.breeze.modify_order(**breeze_modifications)
            
            if response.get('Status') == 200:
                logger.info(f"Order modified successfully: {order_id}")
                
                await self._emit_order_event('order_modified', {
                    'order_id': order_id,
                    'modifications': modifications,
                    'broker_response': response
                })
                
                return True
            else:
                error_msg = response.get('Error', 'Unknown error')
                logger.error(f"Order modification failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return False
    
    async def get_orders(self, exchange_code: str = "NSE") -> List[Dict[str, Any]]:
        """Get list of orders."""
        if not self.is_authenticated:
            raise Exception("Not authenticated with ICICI Breeze")
        
        try:
            # Get orders for today
            today = datetime.now(timezone.utc)
            from_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            to_date = today
            
            response = self.breeze.get_order_list(
                exchange_code=exchange_code,
                from_date=from_date.isoformat()[:19] + '.000Z',
                to_date=to_date.isoformat()[:19] + '.000Z'
            )
            
            if response.get('Status') == 200:
                return response.get('Success', [])
            else:
                logger.error(f"Failed to get orders: {response.get('Error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        if not self.is_authenticated:
            raise Exception("Not authenticated with ICICI Breeze")
        
        try:
            # get_portfolio_positions doesn't take parameters
            response = self.breeze.get_portfolio_positions()
            
            if response and response.get('Status') == 200:
                success_data = response.get('Success', [])
                # Ensure we return an empty list if None
                return success_data if success_data is not None else []
            else:
                logger.warning(f"Failed to get positions: {response.get('Error') if response else 'No response'}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        if not self.is_authenticated:
            raise Exception("Not authenticated with ICICI Breeze")
        
        try:
            # Get customer details
            customer_details = await self._get_customer_details()
            
            # Get funds information
            funds_response = self.breeze.get_funds()
            funds_info = {}
            balance = 0.0
            available_margin = 0.0
            used_margin = 0.0
            account_id = ""
            
            if funds_response and funds_response.get('Status') == 200:
                funds_data = funds_response.get('Success', {})
                if funds_data:
                    funds_info = funds_data
                    balance = float(funds_data.get('total_bank_balance', 0))
                    # Calculate available margin (allocated - blocked)
                    allocated_fno = float(funds_data.get('allocated_fno', 0))
                    blocked_fno = float(funds_data.get('block_by_trade_fno', 0))
                    available_margin = allocated_fno - blocked_fno
                    used_margin = blocked_fno
                    account_id = str(funds_data.get('bank_account', ''))
            
            return {
                'account_id': account_id,
                'balance': balance,
                'available_margin': available_margin,
                'used_margin': used_margin,
                'customer_details': customer_details,
                'funds': funds_info,
                'broker': 'icici_breeze',
                'paper_trading': self.paper_trading
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {
                'account_id': '',
                'balance': 0.0,
                'available_margin': 0.0,
                'used_margin': 0.0,
                'broker': 'icici_breeze',
                'paper_trading': self.paper_trading
            }
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Get market data for symbols."""
        if not self.is_authenticated:
            raise Exception("Not authenticated with ICICI Breeze")
        
        market_data = {}
        
        try:
            for symbol in symbols:
                # Parse symbol to get exchange and stock code
                exchange_code, stock_code = self._parse_symbol(symbol)
                
                response = self.breeze.get_quotes(
                    stock_code=stock_code,
                    exchange_code=exchange_code,
                    product_type="cash",
                    expiry_date="",
                    right="",
                    strike_price=""
                )
                
                if response.get('Status') == 200:
                    quote_data = response.get('Success', [])
                    if quote_data:
                        market_data[symbol] = quote_data[0]
                
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
        
        return market_data
    
    async def start_market_data_stream(self, symbols: List[str], callback):
        """Start real-time market data stream."""
        if not self.is_authenticated:
            raise Exception("Not authenticated with ICICI Breeze")
        
        try:
            # Connect to WebSocket
            self.breeze.ws_connect()
            self.ws_connected = True
            
            # Set up callback
            def on_ticks(ticks):
                # Convert Breeze tick format to our standard format
                converted_ticks = self._convert_breeze_ticks(ticks)
                asyncio.create_task(callback(converted_ticks))
            
            self.breeze.on_ticks = on_ticks
            
            # Subscribe to symbols
            for symbol in symbols:
                exchange_code, stock_code = self._parse_symbol(symbol)
                
                self.breeze.subscribe_feeds(
                    exchange_code=exchange_code,
                    stock_code=stock_code,
                    product_type="cash",
                    get_exchange_quotes=True,
                    get_market_depth=False
                )
            
            logger.info(f"Started market data stream for {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error starting market data stream: {e}")
            raise
    
    async def stop_market_data_stream(self):
        """Stop real-time market data stream."""
        try:
            if self.ws_connected and self.breeze:
                self.breeze.ws_disconnect()
                self.ws_connected = False
                logger.info("Stopped market data stream")
                
        except Exception as e:
            logger.error(f"Error stopping market data stream: {e}")
    
    async def get_historical_data(self, symbol: str, interval: str = "1minute", 
                                from_date: str = None, to_date: str = None) -> List[Dict[str, Any]]:
        """Get historical OHLC data for a symbol."""
        if not self.is_authenticated:
            raise Exception("Not authenticated with ICICI Breeze")
        
        try:
            exchange_code, stock_code = self._parse_symbol(symbol)
            
            # Default to last 30 days if dates not provided
            if not from_date:
                from_date = (datetime.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%dT00:00:00.000Z')
            if not to_date:
                to_date = datetime.now().strftime('%Y-%m-%dT23:59:59.000Z')
            
            response = self.breeze.get_historical_data(
                interval=interval,
                from_date=from_date,
                to_date=to_date,
                stock_code=stock_code,
                exchange_code=exchange_code,
                product_type="cash"
            )
            
            if response and response.get('Status') == 200:
                data = response.get('Success', [])
                
                # Convert to standard format
                historical_data = []
                for candle in data:
                    historical_data.append({
                        'timestamp': candle.get('datetime'),
                        'open': float(candle.get('open', 0)),
                        'high': float(candle.get('high', 0)),
                        'low': float(candle.get('low', 0)),
                        'close': float(candle.get('close', 0)),
                        'volume': int(candle.get('volume', 0))
                    })
                
                logger.info(f"Retrieved {len(historical_data)} historical candles for {symbol}")
                return historical_data
            else:
                logger.error(f"Failed to get historical data: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    async def get_intraday_levels(self, symbol: str, 
                                lookback_periods: int = 20) -> Dict[str, List[float]]:
        """Identify intraday support and resistance levels from recent price action."""
        try:
            # Get intraday data (5-minute candles)
            to_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')
            from_date = (datetime.now() - pd.Timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            historical_data = await self.get_historical_data(
                symbol=symbol,
                interval="5minute",
                from_date=from_date,
                to_date=to_date
            )
            
            if not historical_data:
                return {'resistance': [], 'support': []}
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(historical_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Identify pivot highs and lows
            resistance_levels = []
            support_levels = []
            
            for i in range(lookback_periods, len(df) - lookback_periods):
                current_high = df.iloc[i]['high']
                current_low = df.iloc[i]['low']
                
                # Check for resistance (pivot high)
                is_resistance = True
                for j in range(max(0, i - lookback_periods), min(len(df), i + lookback_periods + 1)):
                    if j != i and df.iloc[j]['high'] >= current_high:
                        is_resistance = False
                        break
                
                if is_resistance:
                    resistance_levels.append(current_high)
                
                # Check for support (pivot low)
                is_support = True
                for j in range(max(0, i - lookback_periods), min(len(df), i + lookback_periods + 1)):
                    if j != i and df.iloc[j]['low'] <= current_low:
                        is_support = False
                        break
                
                if is_support:
                    support_levels.append(current_low)
            
            # Remove duplicate levels that are very close to each other
            resistance_levels = self._cluster_levels(resistance_levels)
            support_levels = self._cluster_levels(support_levels)
            
            logger.info(f"Identified {len(resistance_levels)} intraday resistance levels and {len(support_levels)} support levels")
            
            return {
                'resistance': sorted(resistance_levels, reverse=True),
                'support': sorted(support_levels)
            }
            
        except Exception as e:
            logger.error(f"Error identifying intraday levels: {e}")
            return {'resistance': [], 'support': []}
    
    def _cluster_levels(self, levels: List[float], threshold_pct: float = 0.1) -> List[float]:
        """Cluster nearby levels together to avoid duplicates."""
        if not levels:
            return []
        
        levels = sorted(levels)
        clustered = [levels[0]]
        
        for level in levels[1:]:
            # Check if this level is close to any existing clustered level
            is_close = False
            for existing in clustered:
                if abs(level - existing) / existing * 100 < threshold_pct:
                    is_close = True
                    break
            
            if not is_close:
                clustered.append(level)
        
        return clustered
    
    # Helper methods
    
    async def _get_customer_details(self) -> Dict[str, Any]:
        """Get customer details from ICICI Breeze."""
        try:
            response = self.breeze.get_customer_details(api_session=self.session_token)
            if response.get('Status') == 200:
                return response.get('Success', {})
            return {}
        except Exception as e:
            logger.error(f"Error getting customer details: {e}")
            return {}
    
    def _convert_to_breeze_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Convert our standard order format to Breeze format."""
        symbol = order['symbol']
        exchange_code, stock_code = self._parse_symbol(symbol)
        
        breeze_order = {
            'stock_code': stock_code,
            'exchange_code': exchange_code,
            'product': order.get('product_type', 'cash'),
            'action': order['side'].lower(),  # 'buy' or 'sell'
            'order_type': order.get('type', 'market').lower(),
            'quantity': str(order['qty']),
            'price': str(order.get('price', 0)),
            'validity': order.get('time_in_force', 'day').lower(),
            'disclosed_quantity': str(order.get('disclosed_qty', 0)),
            'user_remark': order.get('user_remark', 'algo_trade')
        }
        
        # Handle F&O specific fields
        if order.get('product_type') in ['futures', 'options']:
            breeze_order.update({
                'expiry_date': order.get('expiry_date', ''),
                'right': order.get('right', 'others'),
                'strike_price': str(order.get('strike_price', 0))
            })
        
        return breeze_order
    
    def _convert_modifications_to_breeze(self, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Convert order modifications to Breeze format."""
        breeze_mods = {}
        
        if 'qty' in modifications:
            breeze_mods['quantity'] = str(modifications['qty'])
        if 'price' in modifications:
            breeze_mods['price'] = str(modifications['price'])
        if 'type' in modifications:
            breeze_mods['order_type'] = modifications['type'].lower()
        if 'time_in_force' in modifications:
            breeze_mods['validity'] = modifications['time_in_force'].lower()
        
        return breeze_mods
    
    def _parse_symbol(self, symbol: str) -> tuple:
        """Parse symbol to get exchange and stock code."""
        # Simple mapping - you can extend this based on your symbol format
        if '.' in symbol:
            parts = symbol.split('.')
            if len(parts) == 2:
                return parts[0], parts[1]  # e.g., "NSE.RELIANCE"
        
        # Default to NSE for equity symbols
        return "NSE", symbol
    
    def _convert_breeze_ticks(self, ticks) -> Dict[str, Any]:
        """Convert Breeze tick format to our standard format."""
        if not ticks:
            return {}
        
        # Extract relevant data from Breeze tick format
        converted = {
            'symbol': ticks.get('symbol', ''),
            'last_price': ticks.get('last', 0),
            'bid_price': ticks.get('bPrice', 0),
            'ask_price': ticks.get('sPrice', 0),
            'bid_qty': ticks.get('bQty', 0),
            'ask_qty': ticks.get('sQty', 0),
            'volume': ticks.get('ttq', 0),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'exchange': ticks.get('exchange', 'NSE')
        }
        
        return converted
    
    async def _submit_paper_order(self, order: Dict[str, Any]) -> str:
        """Submit a paper trading order."""
        # Generate a fake order ID for paper trading
        order_id = f"PAPER_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{order['symbol']}"
        
        logger.info(f"Paper trading order submitted: {order_id}")
        
        # Simulate order fill after a short delay
        await asyncio.sleep(1)
        
        await self._emit_order_event('order_filled', {
            'order_id': order_id,
            'symbol': order['symbol'],
            'side': order['side'],
            'quantity': order['qty'],
            'price': order.get('price', 0),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'paper_trading': True
        })
        
        return order_id
    
    async def _emit_order_event(self, event_type: str, data: Dict[str, Any]):
        """Emit order-related events."""
        if self.event_manager:
            event = Event(event_type, data)
            await self.event_manager.emit(event)