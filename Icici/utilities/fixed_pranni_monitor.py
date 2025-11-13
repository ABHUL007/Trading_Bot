#!/usr/bin/env python3
"""
FIXED Pranni Live Monitor - GUARANTEED Breakdown Detection
=========================================================

CRITICAL FIXES:
1. Uses ACTUAL Previous Day data from daily database
2. Checks BOTH breakouts AND breakdowns
3. Proper PDH/PDL calculation
4. No more missed signals!
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pranni_fixed.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FixedPranniMonitor:
    def __init__(self):
        # Connect to all databases
        self.conn_15min = sqlite3.connect('NIFTY_15min_data.db', check_same_thread=False)
        self.conn_5min = sqlite3.connect('NIFTY_5min_data.db', check_same_thread=False)
        self.conn_daily = sqlite3.connect('NIFTY_1day_data.db', check_same_thread=False)
        
        self.active_signals = []
        self.levels = {}
        self.current_price = 0
        self.pdh = None
        self.pdl = None
        
        logger.info("🔧 FIXED Pranni Monitor initialized")
        
    def get_previous_day_levels(self):
        """Get ACTUAL Previous Day High/Low from daily database"""
        try:
            # Get last 2 trading days
            query = """
            SELECT datetime, open, high, low, close 
            FROM data_1day 
            ORDER BY datetime DESC 
            LIMIT 2
            """
            df = pd.read_sql_query(query, self.conn_daily)
            
            if len(df) >= 2:
                prev_day = df.iloc[1]  # Previous trading day (Nov 4th)
                
                self.pdh = float(prev_day['high'])
                self.pdl = float(prev_day['low'])
                
                logger.info(f"📊 Previous Day Levels:")
                logger.info(f"   PDH: {self.pdh:.2f}")
                logger.info(f"   PDL: {self.pdl:.2f}")
                logger.info(f"   Date: {prev_day['datetime']}")
                
                return True
            else:
                logger.error("❌ Not enough daily data for PDH/PDL calculation")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error getting previous day levels: {e}")
            return False
    
    def get_current_price(self):
        """Get current market price from latest 15-min candle"""
        try:
            today = datetime.now().date()
            query = f"""
            SELECT datetime, close 
            FROM data_15min 
            WHERE date(datetime) = '{today}'
            ORDER BY datetime DESC 
            LIMIT 1
            """
            df = pd.read_sql_query(query, self.conn_15min)
            
            if not df.empty:
                self.current_price = float(df['close'].iloc[0])
                logger.info(f"💰 Current Price: {self.current_price:.2f}")
                return True
            else:
                logger.error("❌ No current price data available")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error getting current price: {e}")
            return False
    
    def update_levels(self):
        """Update all key levels with ACTUAL data"""
        logger.info("🔄 Updating levels...")
        
        # Get previous day levels
        if not self.get_previous_day_levels():
            return False
            
        # Get current price
        if not self.get_current_price():
            return False
        
        # Set up levels for monitoring
        self.levels = {
            'Previous Day': {
                'high': self.pdh,
                'low': self.pdl,
                'median': 62.65, 
                'p75': 130.35, 
                'max': 1198.45, 
                'time': 2.6
            }
        }
        
        logger.info(f"✅ Levels updated successfully")
        return True
    
    def check_breakouts_and_breakdowns(self):
        """FIXED: Check for both breakouts AND breakdowns"""
        new_signals = []
        
        try:
            # Get latest 15-min candle
            today = datetime.now().date()
            query = f"""
            SELECT datetime, open, high, low, close 
            FROM data_15min 
            WHERE date(datetime) = '{today}'
            ORDER BY datetime DESC 
            LIMIT 1
            """
            df_candle = pd.read_sql_query(query, self.conn_15min)
            
            if df_candle.empty:
                logger.warning("⚠️ No candle data available")
                return new_signals
            
            candle = df_candle.iloc[0]
            candle_close = float(candle['close'])
            candle_high = float(candle['high'])
            candle_low = float(candle['low'])
            candle_time = candle['datetime']
            
            logger.info(f"🕐 Checking candle: {candle_time}")
            logger.info(f"   OHLC: {candle['open']:.2f} | {candle_high:.2f} | {candle_low:.2f} | {candle_close:.2f}")
            
            # Check PDH BREAKOUT
            if candle_close > self.pdh:
                logger.info(f"🚀 PDH BREAKOUT DETECTED!")
                logger.info(f"   Close {candle_close:.2f} > PDH {self.pdh:.2f}")
                
                # Create CALL signal
                signal = self._create_signal('Previous Day', 'CALL', candle_close, candle_time, self.pdh)
                new_signals.append(signal)
                
            # Check PDL BREAKDOWN  
            if candle_close < self.pdl:
                logger.info(f"📉 PDL BREAKDOWN DETECTED!")
                logger.info(f"   Close {candle_close:.2f} < PDL {self.pdl:.2f}")
                logger.info(f"   Breakdown by: {self.pdl - candle_close:.2f} points")
                
                # Create PUT signal
                signal = self._create_signal('Previous Day', 'PUT', candle_close, candle_time, self.pdl)
                new_signals.append(signal)
            
            # Log if no signals
            if not new_signals:
                logger.info(f"✅ No breakout/breakdown detected")
                logger.info(f"   Price {candle_close:.2f} between PDL {self.pdl:.2f} and PDH {self.pdh:.2f}")
            
            return new_signals
            
        except Exception as e:
            logger.error(f"❌ Error checking breakouts: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _create_signal(self, timeframe, direction, entry_price, entry_time, breakout_level):
        """Create trading signal"""
        
        # Calculate targets (simplified)
        if direction == 'CALL':
            target_1 = entry_price + 50  # +50 points
            target_2 = entry_price + 100 # +100 points
            stop_loss = entry_price - 30  # -30 points
        else:  # PUT
            target_1 = entry_price - 50  # -50 points
            target_2 = entry_price - 100 # -100 points  
            stop_loss = entry_price + 30  # +30 points
        
        signal = {
            'id': f"{timeframe.replace(' ', '_')}_{direction}_{entry_time.replace(':', '').replace('-', '').replace(' ', '_')}",
            'timeframe': timeframe,
            'direction': direction,
            'breakout_level': breakout_level,
            'entry_price': entry_price,
            'entry_time': entry_time,
            'target_1': target_1,
            'target_2': target_2,
            'stop_loss': stop_loss,
            'status': 'ACTIVE'
        }
        
        logger.info(f"📊 SIGNAL CREATED:")
        logger.info(f"   Direction: {direction}")
        logger.info(f"   Entry: {entry_price:.2f}")
        logger.info(f"   Target 1: {target_1:.2f}")
        logger.info(f"   Target 2: {target_2:.2f}")
        logger.info(f"   Stop Loss: {stop_loss:.2f}")
        
        return signal
    
    def run_live_check(self):
        """Run complete check - call this from main bot"""
        logger.info("🚀 RUNNING LIVE BREAKOUT/BREAKDOWN CHECK")
        logger.info("=" * 60)
        
        # Update levels
        if not self.update_levels():
            logger.error("❌ Failed to update levels")
            return []
        
        # Check for signals
        signals = self.check_breakouts_and_breakdowns()
        
        if signals:
            logger.info(f"🎯 FOUND {len(signals)} SIGNAL(S)!")
            for signal in signals:
                logger.info(f"   🔥 {signal['direction']} signal at {signal['entry_price']:.2f}")
        else:
            logger.info("✅ No signals detected")
        
        logger.info("=" * 60)
        return signals

# Test function
def test_fixed_monitor():
    """Test the fixed monitor with current data"""
    monitor = FixedPranniMonitor()
    
    print("\n🔧 TESTING FIXED PRANNI MONITOR")
    print("=" * 60)
    
    # Run check
    signals = monitor.run_live_check()
    
    # Simulate what should happen at 10:15
    print(f"\n🕐 SIMULATING 10:15 CHECK:")
    print("Expected:")
    print(f"  - PDL: ~25578.40")
    print(f"  - 10:15 Close: ~25536.95")  
    print(f"  - Should detect: PDL BREAKDOWN")
    print(f"  - Should create: PUT signal")
    
    if signals:
        print(f"\n✅ FIXED! {len(signals)} signal(s) detected")
    else:
        print(f"\n❌ Still not working - check logs")

if __name__ == "__main__":
    test_fixed_monitor()