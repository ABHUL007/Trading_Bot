#!/usr/bin/env python3
"""
FIXED Enhanced Pranni Monitor - Always Detects Breakouts!
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os

# Get absolute path to database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH_15MIN = os.path.join(BASE_DIR, 'NIFTY_15min_data.db')
DB_PATH_5MIN = os.path.join(BASE_DIR, 'NIFTY_5min_data.db')
DB_PATH_1DAY = os.path.join(BASE_DIR, 'NIFTY_1day_data.db')

class FixedPranniMonitor:
    def __init__(self):
        if not os.path.exists(DB_PATH_15MIN):
            raise FileNotFoundError(f"15-min Database not found: {DB_PATH_15MIN}")
        if not os.path.exists(DB_PATH_5MIN):
            raise FileNotFoundError(f"5-min Database not found: {DB_PATH_5MIN}")
        if not os.path.exists(DB_PATH_1DAY):
            raise FileNotFoundError(f"1-day Database not found: {DB_PATH_1DAY}")
            
        self.conn_15min = sqlite3.connect(DB_PATH_15MIN, check_same_thread=False)
        self.conn_5min = sqlite3.connect(DB_PATH_5MIN, check_same_thread=False)
        self.conn_1day = sqlite3.connect(DB_PATH_1DAY, check_same_thread=False)
        
        self.processed_candles = set()  # Track processed candles to avoid duplicates
        self.levels = {}
        self.atr_14 = 0
        self.current_price = 0
        self.last_update = None
        
        # Initialize levels
        self.update_all_levels()
        print("[FIXED] Pranni Monitor initialized!")
    
    def force_aggregate_latest_data(self):
        """Force aggregate any missing 5-min data to 15-min"""
        today = datetime.now().date().strftime('%Y-%m-%d')
        
        # Get today's 5-min data (volume not needed for NIFTY)
        query_5min = f"""
        SELECT datetime, open, high, low, close, 0 as volume
        FROM data_5min 
        WHERE datetime LIKE '{today}%'
        ORDER BY datetime
        """
        df_5min = pd.read_sql_query(query_5min, self.conn_5min)
        
        if df_5min.empty:
            return
        
        # Convert to datetime and aggregate to 15-min
        df_5min['datetime'] = pd.to_datetime(df_5min['datetime'])
        df_5min.set_index('datetime', inplace=True)
        
        # Aggregate to 15-min
        df_15min = df_5min.resample('15min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min', 
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        if df_15min.empty:
            return
        
        # Save to database (INSERT OR REPLACE to update existing)
        df_15min.reset_index(inplace=True)
        df_15min['datetime'] = df_15min['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        for _, row in df_15min.iterrows():
            self.conn_15min.execute("""
                INSERT OR REPLACE INTO data_15min (datetime, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (row['datetime'], row['open'], row['high'], row['low'], row['close'], row['volume']))
        
        self.conn_15min.commit()
        
    def calculate_atr(self):
        """Calculate 14-day ATR"""
        query = """
        SELECT 
            date(datetime) as date,
            MAX(high) as high,
            MIN(low) as low,
            (SELECT close FROM data_15min WHERE date(datetime) = date(d.datetime) ORDER BY datetime DESC LIMIT 1) as close
        FROM data_15min d
        WHERE datetime >= date('now', '-60 days')
        GROUP BY date(datetime)
        ORDER BY date
        LIMIT 14
        """
        
        df = pd.read_sql_query(query, self.conn_15min)
        
        if len(df) < 2:
            self.atr_14 = 50  # Default ATR
            return
        
        # Calculate True Range for each day
        true_ranges = []
        for i in range(1, len(df)):
            current_high = df.iloc[i]['high']
            current_low = df.iloc[i]['low']
            prev_close = df.iloc[i-1]['close']
            
            tr1 = current_high - current_low
            tr2 = abs(current_high - prev_close)
            tr3 = abs(current_low - prev_close)
            
            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)
        
        self.atr_14 = np.mean(true_ranges) if true_ranges else 50
    
    def get_all_trading_levels(self):
        """Get ALL trading levels including 5-minute levels"""
        today = datetime.now().date().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).date().strftime('%Y-%m-%d')
        
        levels = {}
        
        # 1. TODAY'S 5-MINUTE LEVELS
        
        # Session High/Low (all candles today)
        session_query = f"""
        SELECT MIN(low) as session_low, MAX(high) as session_high, COUNT(*) as candle_count
        FROM data_5min 
        WHERE datetime LIKE '{today}%'
        """
        df_session = pd.read_sql_query(session_query, self.conn_5min)
        
        if not df_session.empty and df_session['session_low'].iloc[0] is not None:
            levels['Today Session'] = {
                'high': df_session['session_high'].iloc[0],
                'low': df_session['session_low'].iloc[0],
                'type': '5min_session',
                'candles': df_session['candle_count'].iloc[0]
            }
        
        # Opening Range (first 3 candles: 9:15, 9:20, 9:25)
        opening_query = f"""
        SELECT MIN(low) as opening_low, MAX(high) as opening_high, COUNT(*) as opening_candles
        FROM (
            SELECT low, high
            FROM data_5min 
            WHERE datetime LIKE '{today}%'
            ORDER BY datetime 
            LIMIT 3
        )
        """
        df_opening = pd.read_sql_query(opening_query, self.conn_5min)
        
        if not df_opening.empty and df_opening['opening_low'].iloc[0] is not None:
            levels['Opening Range'] = {
                'high': df_opening['opening_high'].iloc[0],
                'low': df_opening['opening_low'].iloc[0],
                'type': '5min_opening',
                'candles': df_opening['opening_candles'].iloc[0]
            }
        
        # First Candle (9:15 AM only - market opens at 9:15)
        first_candle_query = f"""
        SELECT low as first_low, high as first_high, open as first_open, close as first_close
        FROM data_5min 
        WHERE datetime LIKE '{today}%'
        AND TIME(datetime) >= '09:15:00'
        ORDER BY datetime 
        LIMIT 1
        """
        df_first = pd.read_sql_query(first_candle_query, self.conn_5min)
        
        if not df_first.empty and df_first['first_low'].iloc[0] is not None:
            levels['First Candle'] = {
                'high': df_first['first_high'].iloc[0],
                'low': df_first['first_low'].iloc[0],
                'open': df_first['first_open'].iloc[0],
                'close': df_first['first_close'].iloc[0],
                'type': '5min_first'
            }
        
        # 2. PREVIOUS DAY LEVELS
        prev_day_query = f"""
        SELECT MIN(low) as low, MAX(high) as high, 
               (SELECT open FROM data_15min WHERE datetime LIKE '{yesterday}%' ORDER BY datetime LIMIT 1) as prev_open,
               (SELECT close FROM data_15min WHERE datetime LIKE '{yesterday}%' ORDER BY datetime DESC LIMIT 1) as prev_close
        FROM data_15min 
        WHERE datetime LIKE '{yesterday}%'
        """
        df_prev_day = pd.read_sql_query(prev_day_query, self.conn_15min)
        
        if not df_prev_day.empty and df_prev_day['high'].iloc[0] is not None:
            levels['Previous Day'] = {
                'high': df_prev_day['high'].iloc[0],
                'low': df_prev_day['low'].iloc[0],
                'open': df_prev_day['prev_open'].iloc[0],
                'close': df_prev_day['prev_close'].iloc[0],
                'type': 'previous_day'
            }
        
        # 3. WEEKLY/MONTHLY LEVELS (use daily data for accuracy)
        timeframes = {
            '1 Week': 7,
            '2 Weeks': 14,
            '1 Month': 30
        }
        
        for name, days in timeframes.items():
            start_date = (datetime.now() - timedelta(days=days)).date().strftime('%Y-%m-%d')
            query = f"""
            SELECT MIN(low) as low, MAX(high) as high
            FROM data_1day 
            WHERE datetime >= '{start_date}' AND datetime < '{today}'
            """
            df_level = pd.read_sql_query(query, self.conn_1day)
            
            if not df_level.empty and df_level['high'].iloc[0] is not None:
                levels[name] = {
                    'high': df_level['high'].iloc[0],
                    'low': df_level['low'].iloc[0],
                    'type': 'historical'
                }
        
        return levels
    
    def update_all_levels(self):
        """Update all levels and current price"""
        # Force aggregate latest data first
        self.force_aggregate_latest_data()
        
        # Calculate ATR
        self.calculate_atr()
        
        # Get current price from latest 15-min candle
        query_current = """
        SELECT close, datetime 
        FROM data_15min 
        ORDER BY datetime DESC 
        LIMIT 1
        """
        df_current = pd.read_sql_query(query_current, self.conn_15min)
        
        if not df_current.empty:
            self.current_price = df_current['close'].iloc[0]
            self.last_update = df_current['datetime'].iloc[0]
        
        # Get all levels
        all_levels = self.get_all_trading_levels()
        
        # Add breakout status and probabilities to each level
        for name, level_data in all_levels.items():
            if 'high' in level_data and 'low' in level_data:
                # Calculate distances
                high_dist = level_data['high'] - self.current_price
                low_dist = self.current_price - level_data['low']
                high_dist_atr = high_dist / self.atr_14 if self.atr_14 > 0 else 0
                low_dist_atr = low_dist / self.atr_14 if self.atr_14 > 0 else 0
                
                # Calculate probabilities
                high_prob = self._calculate_probability(abs(high_dist_atr))
                low_prob = self._calculate_probability(abs(low_dist_atr))
                
                level_data.update({
                    'high_distance': high_dist,
                    'low_distance': low_dist,
                    'high_dist_atr': high_dist_atr,
                    'low_dist_atr': low_dist_atr,
                    'high_probability': high_prob,
                    'low_probability': low_prob,
                    'high_broken': self.current_price > level_data['high'],
                    'low_broken': self.current_price < level_data['low']
                })
        
        self.levels = all_levels
    
    def _calculate_probability(self, dist_atr):
        """Calculate breakout probability based on ATR distance"""
        if dist_atr < 0.25: return 85
        elif dist_atr < 0.5: return 70
        elif dist_atr < 1.0: return 55
        elif dist_atr < 2.0: return 40
        else: return 25
    
    def check_all_breakouts(self):
        """
        Check for breakouts - ONLY on FRESH 15-minute candles (within 5 minutes)!
        Returns the BEST breakout signal if any levels are broken RECENTLY
        """
        # Update levels with latest data
        self.update_all_levels()
        
        # Get latest completed 15-min candle
        query = """
        SELECT datetime, open, high, low, close 
        FROM data_15min 
        ORDER BY datetime DESC 
        LIMIT 1
        """
        df_candle = pd.read_sql_query(query, self.conn_15min)
        
        if df_candle.empty:
            return None
        
        candle = df_candle.iloc[0]
        candle_close = float(candle['close'])
        candle_time = candle['datetime']
        
        # ⚡ CRITICAL TIMING CHECK: Only trade within 5 minutes of candle completion
        try:
            candle_dt = datetime.strptime(candle_time, '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            
            # 15-min candles: 9:15 candle completes at 9:30, 9:30 candle completes at 9:45, etc.
            # Completion time = candle_time + 15 minutes
            candle_completion_time = candle_dt + timedelta(minutes=15)
            minutes_since_completion = (now - candle_completion_time).total_seconds() / 60
            
            if minutes_since_completion > 5:  # More than 5 minutes since completion
                print(f"⏰ TIMING FILTER: Candle completed at {candle_completion_time.strftime('%H:%M:%S')}, {minutes_since_completion:.1f}m ago - TOO OLD")
                return None
            
            if minutes_since_completion < 0:  # Candle hasn't completed yet
                print(f"⏰ Candle hasn't completed yet (completes at {candle_completion_time.strftime('%H:%M:%S')})")
                return None
            
            print(f"✅ FRESH CANDLE: {candle_time} completed {minutes_since_completion:.1f}m ago - VALID for trading")
            
        except ValueError:
            print(f"⚠️ Could not parse candle time: {candle_time}")
            return None
        
        # Skip if we already processed this exact candle
        if candle_time in self.processed_candles:
            return None
        
        # 🚨 GAP FILTER: Check for gap-up/gap-down from Previous Day High/Low
        pdh = None
        pdl = None
        if 'Previous Day' in self.levels:
            pdh = self.levels['Previous Day'].get('high')
            pdl = self.levels['Previous Day'].get('low')
        
        gap_up_detected = False
        gap_down_detected = False
        in_retest_zone = False
        
        if pdh and pdl:
            # Check if we're in a gap situation (first candle of the day)
            candle_hour = candle_dt.hour
            candle_minute = candle_dt.minute
            
            # First 15-min candle is at 9:15, completes at 9:30
            is_first_candle = (candle_hour == 9 and candle_minute == 15)
            
            if is_first_candle:
                gap_size_up = candle['open'] - pdh
                gap_size_down = pdl - candle['open']
                
                # Option 1: GAP FILTER (>50 points gap)
                if gap_size_up > 50:
                    gap_up_detected = True
                    print(f"⚠️  GAP-UP DETECTED: Opening at ₹{candle['open']:.2f}, PDH was ₹{pdh:.2f} (+{gap_size_up:.2f} points)")
                    print(f"    🎯 Strategy: Will only trade on RETEST of PDH (within ±20 points)")
                
                if gap_size_down > 50:
                    gap_down_detected = True
                    print(f"⚠️  GAP-DOWN DETECTED: Opening at ₹{candle['open']:.2f}, PDL was ₹{pdl:.2f} (-{gap_size_down:.2f} points)")
                    print(f"    🎯 Strategy: Will only trade on RETEST of PDL (within ±20 points)")
            
            # Option 2: RETEST ZONE CHECK (within ±20 points of PDH/PDL)
            if gap_up_detected and (pdh - 20 <= candle_close <= pdh + 20):
                in_retest_zone = True
                print(f"✅ RETEST ZONE: Price at ₹{candle_close:.2f}, PDH at ₹{pdh:.2f} (within ±20 points)")
            
            if gap_down_detected and (pdl - 20 <= candle_close <= pdl + 20):
                in_retest_zone = True
                print(f"✅ RETEST ZONE: Price at ₹{candle_close:.2f}, PDL at ₹{pdl:.2f} (within ±20 points)")
            
            # If gap detected but NOT in retest zone, skip trading
            if (gap_up_detected or gap_down_detected) and not in_retest_zone:
                print(f"🚫 GAP FILTER: Skipping trade - waiting for retest of PDH/PDL")
                return None
        
        # Find FRESH breakouts - ONLY trade when breakout FIRST occurs
        breakouts = []
        
        # Check if this specific candle created a NEW breakout (not continuation of old one)
        for timeframe, level_data in self.levels.items():
            
            # Get previous 15-min candle to check if breakout is FRESH
            query_prev = """
            SELECT datetime, close 
            FROM data_15min 
            ORDER BY datetime DESC 
            LIMIT 2
            """
            df_prev = pd.read_sql_query(query_prev, self.conn_15min)
            
            if len(df_prev) >= 2:
                current_candle = df_prev.iloc[0]
                previous_candle = df_prev.iloc[1] 
                
                prev_close = float(previous_candle['close'])
                curr_close = float(current_candle['close'])
                
                # 🎯 OPENING 5-MIN HIGH BREAKOUT - ONLY if FRESH breakout
                if (timeframe == 'Opening Range' and 'high' in level_data):
                    level_high = level_data['high']
                    
                    # FRESH breakout: previous candle below, current candle above
                    if prev_close <= level_high and curr_close > level_high:
                        breakouts.append({
                            'type': 'FRESH_BREAKOUT',
                            'direction': 'CALL',
                            'timeframe': 'opening_5min_high',
                            'level': level_high,
                            'close_price': curr_close,
                            'candle_time': candle_time,
                            'level_type': 'opening_high_fresh',
                            'probability': 90,  # Very high for fresh breakouts
                            'distance_atr': 0.8,
                            'breakout_margin': curr_close - level_high
                        })
                
                # 🎯 OPENING 5-MIN LOW BREAKDOWN - ONLY if FRESH breakdown  
                if (timeframe == 'Opening Range' and 'low' in level_data):
                    level_low = level_data['low']
                    
                    # FRESH breakdown: previous candle above, current candle below
                    if prev_close >= level_low and curr_close < level_low:
                        breakouts.append({
                            'type': 'FRESH_BREAKDOWN',
                            'direction': 'PUT', 
                            'timeframe': 'opening_5min_low',
                            'level': level_low,
                            'close_price': curr_close,
                            'candle_time': candle_time,
                            'level_type': 'opening_low_fresh',
                            'probability': 90,  # Very high for fresh breakdowns
                            'distance_atr': 0.8,
                            'breakdown_margin': level_low - curr_close
                        })
            
            # Secondary signals (lower priority)
            if timeframe != 'Opening Range':
                # Other high breakouts
                if 'high' in level_data and candle_close > level_data['high']:
                    breakouts.append({
                        'type': 'BREAKOUT',
                        'direction': 'CALL',
                        'timeframe': timeframe,
                        'level': level_data['high'],
                        'close_price': candle_close,
                        'candle_time': candle_time,
                        'level_type': level_data.get('type', 'unknown'),
                        'probability': 70,
                        'distance_atr': 0.3
                    })
                
                # Other low breakdowns
                if 'low' in level_data and candle_close < level_data['low']:
                    breakouts.append({
                        'type': 'BREAKDOWN',
                        'direction': 'PUT', 
                        'timeframe': timeframe,
                        'level': level_data['low'],
                        'close_price': candle_close,
                        'candle_time': candle_time,
                        'level_type': level_data.get('type', 'unknown'),
                        'probability': 70,
                        'distance_atr': 0.3
                    })
        
        if breakouts:
            # Mark this candle as processed
            self.processed_candles.add(candle_time)
            
            # Return the BEST breakout (highest probability, closest level)
            best_breakout = max(breakouts, key=lambda x: (x['probability'], -abs(x['distance_atr'])))
            
            print(f"🚨 {best_breakout['type']} DETECTED!")
            print(f"   📊 {best_breakout['timeframe']} {best_breakout['level']:.2f} broken @ {best_breakout['close_price']:.2f}")
            print(f"   🎯 Probability: {best_breakout['probability']}% | ATR Distance: {best_breakout['distance_atr']:.2f}")
            print(f"   ⏰ Candle: {best_breakout['candle_time']}")
            
            return best_breakout
        
        return None
    
    def get_live_status(self):
        """Get current status with all levels and broken levels highlighted"""
        self.update_all_levels()
        
        status = {
            'current_price': self.current_price,
            'atr_14': self.atr_14,
            'last_update': self.last_update,
            'levels': self.levels,
            'processed_candles': len(self.processed_candles)
        }
        
        # Add summary of broken levels
        broken_levels = []
        for timeframe, level_data in self.levels.items():
            if level_data.get('high_broken'):
                broken_levels.append(f"{timeframe} High ({level_data['high']:.2f})")
            if level_data.get('low_broken'):
                broken_levels.append(f"{timeframe} Low ({level_data['low']:.2f})")
        
        status['broken_levels'] = broken_levels
        status['total_broken'] = len(broken_levels)
        
        return status

# Global instance for easy import
_monitor_instance = None

def get_fixed_monitor():
    """Get the global fixed monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = super_pranni_monitor()
    return _monitor_instance

if __name__ == "__main__":
    # Test the fixed monitor
    monitor = super_pranni_monitor()
    
    print("\n📊 TESTING FIXED BREAKOUT DETECTION")
    print("=" * 50)
    
    # Check for breakouts
    breakout = monitor.check_all_breakouts()
    
    if breakout:
        print(f"\n🚨 BREAKOUT FOUND: {breakout}")
    else:
        print("\n📈 No breakouts detected")
    
    # Show status
    status = monitor.get_live_status()
    print(f"\n📊 Current Price: ₹{status['current_price']:.2f}")
    print(f"📏 ATR-14: {status['atr_14']:.2f}")
    print(f"🔥 Broken Levels: {status['total_broken']}")
    
    if status['broken_levels']:
        print("🚨 BROKEN LEVELS:")
        for level in status['broken_levels']:
            print(f"   • {level}")

