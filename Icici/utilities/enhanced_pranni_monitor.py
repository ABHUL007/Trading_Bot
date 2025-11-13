"""
Enhanced Pranni Live Monitor with 5-Min Levels and 15-Min Candle Close Confirmation
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

class EnhancedPranniMonitor:
    def __init__(self):
        if not os.path.exists(DB_PATH_15MIN):
            raise FileNotFoundError(f"15-min Database not found: {DB_PATH_15MIN}")
        if not os.path.exists(DB_PATH_5MIN):
            raise FileNotFoundError(f"5-min Database not found: {DB_PATH_5MIN}")
            
        self.conn_15min = sqlite3.connect(DB_PATH_15MIN, check_same_thread=False)
        self.conn_5min = sqlite3.connect(DB_PATH_5MIN, check_same_thread=False)
        
        self.active_signals = []
        self.completed_trades = []
        self.levels = {}
        self.atr_14 = 0
        self.current_price = 0
        self.last_update = None
        self.last_candle_check = None
        
        # Initialize levels
        self.update_all_levels()
    
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
        """
        df_daily = pd.read_sql_query(query, self.conn_15min)
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        df_daily['prev_close'] = df_daily['close'].shift(1)
        df_daily['tr1'] = df_daily['high'] - df_daily['low']
        df_daily['tr2'] = abs(df_daily['high'] - df_daily['prev_close'])
        df_daily['tr3'] = abs(df_daily['low'] - df_daily['prev_close'])
        df_daily['true_range'] = df_daily[['tr1', 'tr2', 'tr3']].max(axis=1)
        self.atr_14 = df_daily['true_range'].rolling(window=14).mean().iloc[-1]
        return self.atr_14
    
    def is_15min_candle_closed(self):
        """Check if we're at the close of a 15-minute candle"""
        now = datetime.now()
        minute = now.minute
        
        # 15-minute candles close at: 15, 30, 45, 00
        candle_close_minutes = [0, 15, 30, 45]
        
        # Check if current minute is a candle close time
        # Allow 30-second buffer after candle close for data arrival
        if minute in candle_close_minutes:
            seconds = now.second
            if 0 <= seconds <= 30:  # Within 30 seconds after candle close
                return True
        
        return False
    
    def get_5min_session_levels(self):
        """Get 5-minute session high/low and opening range"""
        today = datetime.now().date()
        
        # Today's session high/low (all 5-min candles so far)
        session_query = f"""
        SELECT 
            MIN(low) as session_low, 
            MAX(high) as session_high,
            COUNT(*) as candle_count
        FROM data_5min 
        WHERE datetime LIKE '{today}%'
        """
        df_session = pd.read_sql_query(session_query, self.conn_5min)
        
        # Opening range (first 3 candles: 9:15, 9:20, 9:25) - use subquery for proper first 3
        opening_query = f"""
        SELECT 
            MIN(low) as opening_low, 
            MAX(high) as opening_high,
            COUNT(*) as opening_candles
        FROM (
            SELECT low, high
            FROM data_5min 
            WHERE datetime LIKE '{today}%'
            ORDER BY datetime 
            LIMIT 3
        )
        """
        df_opening = pd.read_sql_query(opening_query, self.conn_5min)
        
        # First candle only (9:15 AM candle for opening levels)
        first_candle_query = f"""
        SELECT low as first_low, high as first_high, open as first_open
        FROM data_5min 
        WHERE datetime LIKE '{today}%'
        ORDER BY datetime 
        LIMIT 1
        """
        df_first = pd.read_sql_query(first_candle_query, self.conn_5min)
        
        return {
            'session_high': df_session['session_high'].iloc[0] if not df_session.empty else 0,
            'session_low': df_session['session_low'].iloc[0] if not df_session.empty else 0,
            'opening_high': df_opening['opening_high'].iloc[0] if not df_opening.empty else 0,
            'opening_low': df_opening['opening_low'].iloc[0] if not df_opening.empty else 0,
            'first_candle_high': df_first['first_high'].iloc[0] if not df_first.empty else 0,
            'first_candle_low': df_first['first_low'].iloc[0] if not df_first.empty else 0,
            'first_candle_open': df_first['first_open'].iloc[0] if not df_first.empty else 0,
            'candle_count': df_session['candle_count'].iloc[0] if not df_session.empty else 0,
            'opening_candles': df_opening['opening_candles'].iloc[0] if not df_opening.empty else 0
        }
    
    def update_all_levels(self):
        """Update all timeframe levels including 5-minute levels"""
        today = datetime.now().date()
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        # Calculate ATR
        self.calculate_atr()
        
        # Get current price
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
        else:
            self.current_price = 25000
            self.last_update = datetime.now().isoformat()
        
        # Get 5-minute session levels
        session_levels = self.get_5min_session_levels()
        
        # Get previous day levels
        prev_day_query = f"""
        SELECT MIN(low) as low, MAX(high) as high
        FROM data_15min 
        WHERE datetime LIKE '{yesterday}%'
        """
        df_prev_day = pd.read_sql_query(prev_day_query, self.conn_15min)
        
        # Define all timeframe levels
        timeframes = {}
        
        # 5-Minute Levels (if market is open)
        if session_levels['candle_count'] > 0:
            # Opening range (first 3 candles: 9:15, 9:20, 9:25)
            if session_levels['opening_candles'] >= 1:
                timeframes['Opening Range (First 3 Candles)'] = {
                    'high': session_levels['opening_high'],
                    'low': session_levels['opening_low'],
                    'type': '5min_opening'
                }
            
            # First candle only (9:15 AM candle)
            if session_levels['first_candle_high'] > 0:
                timeframes['First Candle (9:15 AM)'] = {
                    'high': session_levels['first_candle_high'],
                    'low': session_levels['first_candle_low'],
                    'type': '5min_first_candle'
                }
            
            # Session range (all candles so far) - only if different from opening
            if (session_levels['session_high'] != session_levels['opening_high'] or 
                session_levels['session_low'] != session_levels['opening_low']):
                timeframes['Today Session Range'] = {
                    'high': session_levels['session_high'],
                    'low': session_levels['session_low'],
                    'type': '5min_session'
                }
        
        # Previous Day Levels
        if not df_prev_day.empty and df_prev_day['high'].iloc[0] is not None:
            timeframes['Previous Day'] = {
                'high': df_prev_day['high'].iloc[0],
                'low': df_prev_day['low'].iloc[0],
                'type': 'previous_day'
            }
        
        # Weekly/Monthly levels
        other_timeframes = {
            '1 Week': 7,
            '2 Weeks': 14,
            '1 Month': 30
        }
        
        for name, days in other_timeframes.items():
            start_date = (datetime.now() - timedelta(days=days)).date()
            query = f"""
            SELECT MIN(low) as low, MAX(high) as high
            FROM data_15min 
            WHERE datetime >= '{start_date}' AND datetime < '{today}'
            """
            df_level = pd.read_sql_query(query, self.conn_15min)
            
            if not df_level.empty and df_level['high'].iloc[0] is not None:
                timeframes[name] = {
                    'high': df_level['high'].iloc[0],
                    'low': df_level['low'].iloc[0],
                    'type': 'historical'
                }
        
        # Calculate distances and probabilities
        for name, level_data in timeframes.items():
            if 'high' in level_data and 'low' in level_data:
                high_dist_atr = (level_data['high'] - self.current_price) / self.atr_14
                low_dist_atr = (self.current_price - level_data['low']) / self.atr_14
                
                level_data.update({
                    'high_distance': level_data['high'] - self.current_price,
                    'low_distance': self.current_price - level_data['low'],
                    'high_dist_atr': high_dist_atr,
                    'low_dist_atr': low_dist_atr,
                    'high_probability': self._calculate_probability(abs(high_dist_atr)),
                    'low_probability': self._calculate_probability(abs(low_dist_atr)),
                    'high_broken': self.current_price > level_data['high'],
                    'low_broken': self.current_price < level_data['low']
                })
        
        self.levels = timeframes
    
    def _calculate_probability(self, dist_atr):
        """Calculate probability based on ATR distance"""
        if dist_atr < 0.25: return 85
        elif dist_atr < 0.5: return 70
        elif dist_atr < 1.0: return 45
        elif dist_atr < 1.5: return 25
        elif dist_atr < 2.0: return 12
        else: return 5
    
    def check_15min_candle_breakouts(self):
        """Check breakouts ONLY at 15-minute candle close"""
        # Only check at candle close times
        if not self.is_15min_candle_closed():
            return None
        
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
        
        # Don't check the same candle twice
        if self.last_candle_check == candle_time:
            return None
        
        self.last_candle_check = candle_time
        
        # Update levels with latest data
        self.update_all_levels()
        
        # Check each level for breakouts
        for timeframe, level_data in self.levels.items():
            if 'high' not in level_data or 'low' not in level_data:
                continue
                
            # Check HIGH breakout (candle CLOSED above level)
            if candle_close > level_data['high']:
                return {
                    'type': 'BREAKOUT',
                    'direction': 'CALL',
                    'timeframe': timeframe,
                    'level': level_data['high'],
                    'close_price': candle_close,
                    'candle_time': candle_time,
                    'level_type': level_data.get('type', 'unknown'),
                    'probability': level_data.get('high_probability', 50)
                }
            
            # Check LOW breakdown (candle CLOSED below level)
            if candle_close < level_data['low']:
                return {
                    'type': 'BREAKDOWN',
                    'direction': 'PUT',
                    'timeframe': timeframe,
                    'level': level_data['low'],
                    'close_price': candle_close,
                    'candle_time': candle_time,
                    'level_type': level_data.get('type', 'unknown'),
                    'probability': level_data.get('low_probability', 50)
                }
        
        return None
    
    def get_live_status(self):
        """Get current status with all levels"""
        self.update_all_levels()
        
        return {
            'current_price': self.current_price,
            'atr_14': self.atr_14,
            'last_update': self.last_update,
            'levels': self.levels,
            'is_candle_close_time': self.is_15min_candle_closed(),
            'next_candle_close': self._get_next_candle_close_time()
        }
    
    def _get_next_candle_close_time(self):
        """Get the next 15-minute candle close time"""
        now = datetime.now()
        current_minute = now.minute
        
        # Find next candle close minute
        close_minutes = [0, 15, 30, 45]
        next_close = None
        
        for minute in close_minutes:
            if minute > current_minute:
                next_close = minute
                break
        
        if next_close is None:
            # Next close is at the top of next hour
            next_hour = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
            return next_hour.strftime('%H:%M:%S')
        else:
            next_time = now.replace(minute=next_close, second=0, microsecond=0)
            return next_time.strftime('%H:%M:%S')

# Global enhanced monitor instance
enhanced_pranni_monitor = None

def get_enhanced_monitor():
    """Get or create enhanced monitor instance"""
    global enhanced_pranni_monitor
    if enhanced_pranni_monitor is None:
        enhanced_pranni_monitor = EnhancedPranniMonitor()
    return enhanced_pranni_monitor

if __name__ == "__main__":
    # Test the enhanced monitor
    monitor = EnhancedPranniMonitor()
    
    print("=" * 60)
    print("ENHANCED PRANNI MONITOR - 5MIN + 15MIN CANDLE CLOSE")
    print("=" * 60)
    
    status = monitor.get_live_status()
    
    print(f"Current Price: ₹{status['current_price']:.2f}")
    print(f"ATR (14): {status['atr_14']:.2f}")
    print(f"Is Candle Close Time: {status['is_candle_close_time']}")
    print(f"Next Candle Close: {status['next_candle_close']}")
    print()
    
    print("📊 All Levels:")
    for name, level_data in status['levels'].items():
        if 'high' in level_data:
            print(f"{name:>20}: H:{level_data['high']:>8.2f} L:{level_data['low']:>8.2f} "
                  f"(Type: {level_data.get('type', 'unknown')})")
    
    print("\n🔍 Checking for breakouts...")
    breakout = monitor.check_15min_candle_breakouts()
    if breakout:
        print(f"🚨 BREAKOUT DETECTED: {breakout}")
    else:
        print("📊 No breakouts at this time")