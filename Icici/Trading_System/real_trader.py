#!/usr/bin/env python3
"""
REAL TRADING BOT - Live Breeze Connect Implementation
- 1 lot (75 quantity) NIFTY options
- ₹10 target per lot (immediate exit)
- Level-based stop-loss (2 consecutive 5-min candles against direction)
- On-demand price fetching (no background collection)
- API-safe: <95 calls/minute
"""

import sqlite3
import os
from datetime import datetime, timedelta, time
import asyncio
import logging
from collections import deque
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Setup logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.stream.reconfigure(encoding='utf-8')
logger.addHandler(console_handler)

file_handler = RotatingFileHandler('real_trader.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

logger.propagate = False

# Get absolute paths for databases and files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
DB_PAPER_TRADES = os.path.join(PARENT_DIR, 'paper_trades.db')
DB_NIFTY_5MIN = os.path.join(PARENT_DIR, 'NIFTY_5min_data.db')
ENV_FILE = os.path.join(PARENT_DIR, '.env')

# Load environment from parent directory
load_dotenv(ENV_FILE)

# Import super pranni monitor
import sys
sys.path.append(BASE_DIR)
from super_pranni_monitor import super_pranni_monitor


class SafeAPIManager:
    """Manages API calls to NEVER exceed 95 per minute"""
    
    def __init__(self, max_calls_per_minute=95):
        self.max_calls_per_minute = max_calls_per_minute
        self.call_history = deque()
        self.total_session_calls = 0
        logger.info(f"🛡️ Safe API Manager: {max_calls_per_minute} calls/minute limit")
    
    def can_make_api_call(self):
        """Check if we can make an API call safely"""
        now = datetime.now()
        
        # Remove calls older than 60 seconds
        while self.call_history and (now - self.call_history[0]).total_seconds() > 60:
            self.call_history.popleft()
        
        current_minute_calls = len(self.call_history)
        
        if current_minute_calls >= self.max_calls_per_minute:
            logger.warning(f"⚠️ API limit reached: {current_minute_calls}/{self.max_calls_per_minute}")
            return False
        
        return True
    
    def record_api_call(self, call_type="general"):
        """Record an API call"""
        now = datetime.now()
        self.call_history.append(now)
        self.total_session_calls += 1
        
        current_usage = len(self.call_history)
        remaining = self.max_calls_per_minute - current_usage
        
        logger.debug(f"📡 API Call #{current_usage}/{self.max_calls_per_minute} ({call_type}) - {remaining} remaining")
    
    async def safe_api_call(self, api_function, call_type="general", *args, **kwargs):
        """Make API call with automatic throttling"""
        # Wait until we can safely make the call
        while not self.can_make_api_call():
            logger.warning("⚠️ API throttling - waiting 1 second...")
            await asyncio.sleep(1)
        
        # Record the call
        self.record_api_call(call_type)
        
        # Make the API call (Breeze API is synchronous, not async)
        try:
            result = api_function(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"❌ API call failed ({call_type}): {e}")
            return None
    
    def get_usage_stats(self):
        """Get current API usage statistics"""
        now = datetime.now()
        
        # Remove old calls
        while self.call_history and (now - self.call_history[0]).total_seconds() > 60:
            self.call_history.popleft()
        
        current_minute_usage = len(self.call_history)
        remaining_calls = self.max_calls_per_minute - current_minute_usage
        
        return {
            'current_minute_usage': current_minute_usage,
            'remaining_calls': remaining_calls,
            'usage_percentage': (current_minute_usage / self.max_calls_per_minute) * 100,
            'total_session_calls': self.total_session_calls,
            'is_safe': current_minute_usage < self.max_calls_per_minute * 0.9
        }


class RealTrader:
    """
    Real money trading bot with Breeze Connect
    - Real order placement via breeze.place_order()
    - Real exits via breeze.square_off()
    - On-demand price fetching via breeze.get_quotes()
    """
    
    def __init__(self):
        # Initialize API manager
        self.api_manager = SafeAPIManager(max_calls_per_minute=95)
        
        # Trading parameters
        self.lot_size = 75  # NIFTY lot size
        self.target_per_lot = 10  # ₹10 profit target
        self.sl_consecutive_candles = 1  # Stop-loss after 1 consecutive candle
        
        # Breeze connection
        self.breeze = None
        self.paper_trading = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
        
        # Super Pranni Monitor
        self.monitor = super_pranni_monitor()
        
        logger.info("🎯 Real Trader initialized")
        logger.info(f"   {'📝 PAPER TRADING MODE' if self.paper_trading else '💰 LIVE TRADING MODE'}")
        logger.info(f"   Lot size: {self.lot_size}")
        logger.info(f"   Target: ₹{self.target_per_lot}/lot")
        logger.info(f"   Stop-loss: {self.sl_consecutive_candles} consecutive candles")
    
    def connect_to_breeze(self):
        """Connect to Breeze API (real or simulated)"""
        try:
            if self.paper_trading:
                logger.info("📝 PAPER TRADING: Using simulated Breeze connection")
                self.breeze = type('MockBreeze', (), {
                    'place_order': lambda *args, **kwargs: {'Success': {'order_id': f'PAPER{datetime.now().strftime("%Y%m%d%H%M%S")}', 'message': 'Paper order placed'}},
                    'square_off': lambda *args, **kwargs: {'Success': {'order_id': f'PAPEREX{datetime.now().strftime("%Y%m%d%H%M%S")}', 'message': 'Paper exit placed'}},
                    'get_quotes': lambda *args, **kwargs: {'Success': [{'ltp': 100.0}]},
                    'get_order_detail': lambda *args, **kwargs: {'Success': [{'status': 'Executed'}]},
                    'get_portfolio_positions': lambda *args, **kwargs: {'Success': []}
                })()
                logger.info("✅ Simulated Breeze connection established")
                return True
            
            # Real Breeze connection
            from breeze_connect import BreezeConnect
            
            api_key = os.getenv('ICICI_API_KEY')
            api_secret = os.getenv('ICICI_API_SECRET')
            session_token = os.getenv('ICICI_SESSION_TOKEN')
            
            if not all([api_key, api_secret, session_token]):
                logger.error("❌ Missing Breeze API credentials in .env file")
                return False
            
            self.breeze = BreezeConnect(api_key=api_key)
            self.breeze.generate_session(api_secret=api_secret, session_token=session_token)
            
            logger.info("✅ Connected to ICICI Breeze API (LIVE)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Breeze connection failed: {e}")
            return False
    
    def get_next_expiry(self):
        """Get next Thursday expiry date"""
        today = datetime.now()
        days_ahead = 3 - today.weekday()  # Thursday is 3
        
        if days_ahead <= 0:  # If today is Thursday or later
            days_ahead += 7  # Get next Thursday
        
        expiry = today + timedelta(days=days_ahead)
        return expiry.strftime("%Y-%m-%dT06:00:00.000Z")
    
    async def get_option_premium(self, strike, direction):
        """
        Fetch live option price via Breeze API
        Called on-demand only (no background collection)
        """
        try:
            option_type = "call" if direction == "CALL" else "put"
            expiry_date = self.get_next_expiry()
            
            # Use API manager for safe call
            result = await self.api_manager.safe_api_call(
                lambda: self.breeze.get_quotes(
                    stock_code="NIFTY",
                    exchange_code="NFO",
                    expiry_date=expiry_date,
                    product_type="options",
                    right=option_type,
                    strike_price=str(strike)
                ),
                call_type=f"get_quotes_{option_type}"
            )
            
            if result and 'Success' in result and result['Success']:
                ltp = float(result['Success'][0]['ltp'])
                logger.debug(f"💰 {strike} {direction} @ ₹{ltp:.2f}")
                return ltp
            
            logger.warning(f"⚠️ Could not fetch price for {strike} {direction}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error fetching option premium: {e}")
            return None
    
    def calculate_nearest_strike(self, nifty_price):
        """Calculate nearest 100s strike"""
        return round(nifty_price / 100) * 100
    
    async def place_real_order(self, strike, direction, entry_premium, breakout_signal):
        """
        Place REAL order via Breeze API
        Returns order_id if successful
        """
        try:
            option_type = "call" if direction == "CALL" else "put"
            expiry_date = self.get_next_expiry()
            
            logger.info(f"🔥 PLACING ORDER: {strike} {direction} @ ₹{entry_premium:.2f}")
            
            # Place market order
            result = await self.api_manager.safe_api_call(
                lambda: self.breeze.place_order(
                    stock_code="NIFTY",
                    exchange_code="NFO",
                    product="options",
                    action="buy",
                    order_type="market",
                    stoploss="",
                    quantity=str(self.lot_size),
                    price="0",  # Market order
                    validity="day",
                    disclosed_quantity="0",
                    expiry_date=expiry_date,
                    right=option_type,
                    strike_price=str(strike),
                    user_remark="SuperPranni"
                ),
                call_type="place_order"
            )
            
            if result and 'Success' in result:
                order_id = result['Success']['order_id']
                logger.info(f"✅ ORDER PLACED: {order_id}")
                
                # Verify order execution
                await asyncio.sleep(2)  # Wait for execution
                order_status = await self.verify_order_status(order_id)
                
                # Save to database
                self.save_trade_to_db(
                    strike=strike,
                    direction=direction,
                    entry_premium=entry_premium,
                    breakout_level=breakout_signal.get('level', 0),
                    confluence_score=breakout_signal.get('probability', 0),
                    order_id=order_id,
                    order_status=order_status
                )
                
                return order_id
            
            logger.error(f"❌ Order placement failed: {result}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return None
    
    async def verify_order_status(self, order_id):
        """Verify if order was executed"""
        try:
            result = await self.api_manager.safe_api_call(
                lambda: self.breeze.get_order_detail(
                    exchange_code="NFO",
                    order_id=order_id
                ),
                call_type="get_order_detail"
            )
            
            if result and 'Success' in result and result['Success']:
                status = result['Success'][0]['status']
                logger.info(f"📋 Order {order_id}: {status}")
                return status
            
            return "Unknown"
            
        except Exception as e:
            logger.error(f"❌ Error verifying order: {e}")
            return "Error"
    
    def save_trade_to_db(self, strike, direction, entry_premium, breakout_level, confluence_score, order_id, order_status):
        """Save trade to real_trades database"""
        try:
            conn = sqlite3.connect(DB_PAPER_TRADES)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO real_trades (
                    timestamp, strike, direction, entry_premium, 
                    breakout_level, confluence_score, quantity,
                    order_id, entry_order_status, status,
                    sl_candle_count, last_sl_check_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                strike,
                direction,
                entry_premium,
                breakout_level,
                confluence_score,
                self.lot_size,
                order_id,
                order_status,
                'OPEN',
                0,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            trade_id = cursor.lastrowid
            conn.close()
            
            logger.info(f"💾 Trade #{trade_id} saved to database")
            return trade_id
            
        except Exception as e:
            logger.error(f"❌ Error saving trade: {e}")
            return None
    
    async def monitor_open_trades(self):
        """
        Monitor open trades for:
        1. ₹10 target (immediate exit)
        2. Level-based stop-loss (2 consecutive 5-min candles)
        """
        try:
            conn = sqlite3.connect(DB_PAPER_TRADES)
            cursor = conn.cursor()
            
            # Get all open trades
            open_trades = cursor.execute('''
                SELECT id, strike, direction, entry_premium, quantity, 
                       breakout_level, order_id, sl_candle_count, last_sl_check_time
                FROM real_trades 
                WHERE status = 'OPEN'
                ORDER BY timestamp DESC
            ''').fetchall()
            
            if not open_trades:
                return
            
            logger.info(f"📊 Monitoring {len(open_trades)} open trade(s)")
            
            for trade in open_trades:
                trade_id, strike, direction, entry_premium, quantity, breakout_level, order_id, sl_candle_count, last_sl_check = trade
                
                # Fetch current premium
                current_premium = await self.get_option_premium(strike, direction)
                
                if current_premium is None:
                    logger.warning(f"⚠️ Trade #{trade_id}: Could not fetch current price")
                    continue
                
                # Calculate P&L
                pnl_per_lot = current_premium - entry_premium
                total_pnl = pnl_per_lot * quantity
                
                logger.info(f"📊 Trade #{trade_id}: {strike} {direction} | Entry: ₹{entry_premium:.2f} | Current: ₹{current_premium:.2f} | P&L: ₹{pnl_per_lot:.2f}/lot (Total: ₹{total_pnl:.2f})")
                
                # Check TARGET (₹10 profit)
                if pnl_per_lot >= self.target_per_lot:
                    logger.info(f"🎯 TARGET HIT: Trade #{trade_id} - Profit ₹{pnl_per_lot:.2f}/lot")
                    await self.exit_trade(trade_id, strike, direction, current_premium, "TARGET", order_id)
                    continue
                
                # Check STOP-LOSS (level-based)
                await self.check_level_based_stoploss(trade_id, strike, direction, entry_premium, current_premium, breakout_level, sl_candle_count, last_sl_check, order_id)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error monitoring trades: {e}")
    
    async def check_level_based_stoploss(self, trade_id, strike, direction, entry_premium, current_premium, breakout_level, sl_candle_count, last_sl_check, order_id):
        """
        Check level-based stop-loss:
        - For CALL: Exit if 2 consecutive 5-min candles close BELOW breakout level
        - For PUT: Exit if 2 consecutive 5-min candles close ABOVE breakout level
        """
        try:
            # Get last 2 completed 5-min candles
            conn = sqlite3.connect(DB_NIFTY_5MIN)
            candles = conn.execute('''
                SELECT close, datetime 
                FROM data_5min 
                WHERE TIME(datetime) >= '09:15:00'
                AND TIME(datetime) <= '15:30:00'
                ORDER BY datetime DESC 
                LIMIT 2
            ''').fetchall()
            conn.close()
            
            if len(candles) < 2:
                logger.debug(f"Trade #{trade_id}: Not enough candles for SL check")
                return
            
            candle1_close, candle1_time = candles[0]  # Most recent
            candle2_close, candle2_time = candles[1]  # Previous
            
            # Check if candles violate level
            if direction == "CALL":
                # For CALL: Exit if both candles close BELOW breakout level
                violation = candle1_close < breakout_level and candle2_close < breakout_level
                condition = f"close < {breakout_level}"
            else:  # PUT
                # For PUT: Exit if both candles close ABOVE breakout level
                violation = candle1_close > breakout_level and candle2_close > breakout_level
                condition = f"close > {breakout_level}"
            
            if violation:
                logger.warning(f"🛑 STOP-LOSS: Trade #{trade_id} - 2 consecutive candles violated {condition}")
                logger.warning(f"   Candle 1: {candle1_time} @ ₹{candle1_close:.2f}")
                logger.warning(f"   Candle 2: {candle2_time} @ ₹{candle2_close:.2f}")
                
                await self.exit_trade(trade_id, strike, direction, current_premium, "STOP_LOSS_LEVEL", order_id)
            else:
                logger.debug(f"Trade #{trade_id}: SL check OK - {candle1_close:.2f}, {candle2_close:.2f} vs level {breakout_level:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error checking stop-loss: {e}")
    
    async def exit_trade(self, trade_id, strike, direction, exit_premium, exit_reason, entry_order_id):
        """
        Exit trade via breeze.square_off()
        """
        try:
            option_type = "call" if direction == "CALL" else "put"
            expiry_date = self.get_next_expiry()
            
            logger.info(f"🚪 EXITING Trade #{trade_id}: {strike} {direction} @ ₹{exit_premium:.2f} ({exit_reason})")
            
            # Square off via Breeze
            result = await self.api_manager.safe_api_call(
                lambda: self.breeze.square_off(
                    exchange_code="NFO",
                    product="options",
                    stock_code="NIFTY",
                    expiry_date=expiry_date,
                    right=option_type,
                    strike_price=str(strike),
                    action="sell",
                    order_type="market",
                    validity="day",
                    stoploss="0",
                    quantity=str(self.lot_size),
                    price="0"
                ),
                call_type="square_off"
            )
            
            exit_order_id = None
            exit_order_status = "Unknown"
            
            if result and 'Success' in result:
                exit_order_id = result['Success']['order_id']
                logger.info(f"✅ EXIT ORDER: {exit_order_id}")
                
                # Verify exit
                await asyncio.sleep(2)
                exit_order_status = await self.verify_order_status(exit_order_id)
            
            # Update database
            conn = sqlite3.connect(DB_PAPER_TRADES)
            cursor = conn.cursor()
            
            # Get entry premium for P&L calculation
            entry_premium = cursor.execute('SELECT entry_premium, quantity FROM real_trades WHERE id = ?', (trade_id,)).fetchone()
            if entry_premium:
                entry_prem, qty = entry_premium
                pnl = (exit_premium - entry_prem) * qty
                
                cursor.execute('''
                    UPDATE real_trades 
                    SET status = 'CLOSED',
                        exit_premium = ?,
                        exit_timestamp = ?,
                        pnl = ?,
                        exit_reason = ?,
                        exit_order_id = ?,
                        exit_order_status = ?
                    WHERE id = ?
                ''', (exit_premium, datetime.now().isoformat(), pnl, exit_reason, exit_order_id, exit_order_status, trade_id))
                
                conn.commit()
                logger.info(f"✅ Trade #{trade_id} CLOSED: P&L ₹{pnl:.2f} ({exit_reason})")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error exiting trade: {e}")
    
    def check_15min_breakout(self):
        """Check for breakout signals from Super Pranni Monitor"""
        try:
            signal = self.monitor.check_all_breakouts()
            
            if signal:
                logger.info(f"🔥 SIGNAL: {signal.get('timeframe', 'N/A')} @ ₹{signal.get('level', 0):.2f} ({signal.get('probability', 0)}%)")
                logger.info(f"   Direction: {signal.get('direction', 'N/A')} | Type: {signal.get('type', 'N/A')}")
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking breakout: {e}")
            return None
    
    def is_market_hours(self):
        """Check if current time is within market hours (9:15 AM - 3:30 PM)"""
        now = datetime.now().time()
        market_open = time(9, 15)
        market_close = time(15, 30)
        return market_open <= now <= market_close
    
    async def run_trading_session(self):
        """Main trading loop"""
        try:
            logger.info("🚀 Starting trading session...")
            
            # Connect to Breeze
            if not self.connect_to_breeze():
                logger.error("❌ Failed to connect to Breeze")
                return
            
            iteration = 0
            
            while True:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"🔄 Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Check market hours
                if not self.is_market_hours():
                    logger.info("⏰ Market closed - waiting...")
                    await asyncio.sleep(60)
                    continue
                
                # Monitor open trades (always)
                await self.monitor_open_trades()
                
                # Check for new breakout signals
                signal = self.check_15min_breakout()
                
                if signal:
                    # Get current NIFTY price
                    nifty_price = signal['close_price']
                    
                    # Calculate strike
                    strike = self.calculate_nearest_strike(nifty_price)
                    
                    # Determine direction (signal already has 'CALL' or 'PUT')
                    direction = signal['direction']
                    
                    # Get entry premium
                    entry_premium = await self.get_option_premium(strike, direction)
                    
                    if entry_premium:
                        # Place order
                        await self.place_real_order(strike, direction, entry_premium, signal)
                
                # API usage stats
                stats = self.api_manager.get_usage_stats()
                logger.info(f"📊 API Usage: {stats['current_minute_usage']}/{self.api_manager.max_calls_per_minute} ({stats['usage_percentage']:.1f}%)")
                
                # Wait before next iteration
                await asyncio.sleep(15)  # Check every 15 seconds
                
        except KeyboardInterrupt:
            logger.info("\n⏹️ Trading session stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error in trading session: {e}", exc_info=True)
        finally:
            logger.info("👋 Trading session ended")


if __name__ == "__main__":
    trader = RealTrader()
    asyncio.run(trader.run_trading_session())
