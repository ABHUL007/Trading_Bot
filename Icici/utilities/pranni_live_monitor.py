"""
Pranni Live Breakout Monitor
Monitors real-time price and detects breakouts/breakdowns
Updates probabilities and targets dynamically
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os

# Get absolute path to database - file is in d:\Algo Trading\Icici\
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH_15MIN = os.path.join(BASE_DIR, 'NIFTY_15min_data.db')
DB_PATH_5MIN = os.path.join(BASE_DIR, 'NIFTY_5min_data.db')

print(f"Pranni Monitor 15min DB: {DB_PATH_15MIN}")
print(f"Pranni Monitor 5min DB: {DB_PATH_5MIN}")
print(f"15min DB Exists: {os.path.exists(DB_PATH_15MIN)}")
print(f"5min DB Exists: {os.path.exists(DB_PATH_5MIN)}")

class PranniLiveMonitor:
    def __init__(self):
        if not os.path.exists(DB_PATH_15MIN):
            raise FileNotFoundError(f"15min Database not found: {DB_PATH_15MIN}")
        if not os.path.exists(DB_PATH_5MIN):
            raise FileNotFoundError(f"5min Database not found: {DB_PATH_5MIN}")
        
        self.conn_15min = sqlite3.connect(DB_PATH_15MIN, check_same_thread=False)
        self.conn_5min = sqlite3.connect(DB_PATH_5MIN, check_same_thread=False)
        self.active_signals = []
        self.completed_trades = []
        self.levels = {}
        self.atr_14 = 0
        self.current_price = 0
        self.last_update = None
        
        # Initialize levels
        self.update_levels()
    
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
    
    def update_levels(self):
        """Update all key levels"""
        today = datetime.now().date()
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        # Get today's high/low (Previous Day for tomorrow) - use yesterday if today empty
        query_today = f"""
        SELECT MIN(low) as intraday_low, MAX(high) as intraday_high
        FROM data_15min 
        WHERE datetime LIKE '{yesterday}%'
        """
        df_today = pd.read_sql_query(query_today, self.conn_15min)
        
        if df_today.empty or df_today['intraday_high'].iloc[0] is None:
            # Fallback to day before yesterday
            day_before = (datetime.now() - timedelta(days=2)).date()
            query_today = f"""
            SELECT MIN(low) as intraday_low, MAX(high) as intraday_high
            FROM data_15min 
            WHERE datetime LIKE '{day_before}%'
            """
            df_today = pd.read_sql_query(query_today, self.conn_15min)
        
        # Get current price - use most recent available
        query_current = f"""
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
            self.current_price = 25000  # Fallback
            self.last_update = datetime.now().isoformat()
        
        # Calculate ATR
        self.calculate_atr()
        
        # Ensure we have valid data
        if df_today.empty or df_today['intraday_high'].iloc[0] is None:
            print("⚠️ No historical data available")
            return
        
        # Get today's opening high/low (FIRST candle only - 9:15 opening candle)
        opening_query = f"""
        SELECT high as opening_high, low as opening_low
        FROM data_15min 
        WHERE DATE(datetime) = '{datetime.now().date()}' 
        ORDER BY datetime 
        LIMIT 1
        """
        df_opening = pd.read_sql_query(opening_query, self.conn_15min)
        
        # Define timeframes
        timeframes = {
            'Previous Day': {
                'high': df_today['intraday_high'].iloc[0],
                'low': df_today['intraday_low'].iloc[0],
                'median': 62.65, 'p75': 130.35, 'max': 1198.45, 'time': 2.6
            },
            'Opening Range': {
                'high': df_opening['opening_high'].iloc[0] if not df_opening.empty else 0,
                'low': df_opening['opening_low'].iloc[0] if not df_opening.empty else 0,
                'median': 45.50, 'p75': 95.25, 'max': 450.00, 'time': 1.5
            }
        }
        
        # Add other timeframes
        other_timeframes = {
            '1 Week': (7, 58.47, 124.64, 1053.05, 2.5),
            '2 Weeks': (14, 60.77, 120.99, 1053.05, 2.5),
            '1 Month': (30, 46.55, 115.21, 349.00, 2.4),
            '3 Months': (90, 45.95, 101.39, 349.00, 2.4),
            '6 Months': (180, 42.35, 83.90, 236.80, 2.4),
            '1 Year': (365, 37.02, 81.18, 236.80, 2.4),
            '2 Years': (730, 37.02, 80.80, 236.80, 2.4)
        }
        
        today_dt = pd.to_datetime(today)
        for name, (days, median, p75, max_gain, time_hrs) in other_timeframes.items():
            lookback = (today_dt - timedelta(days=days)).strftime('%Y-%m-%d')
            query = f"""
            SELECT MAX(high) as high, MIN(low) as low
            FROM data_15min
            WHERE date(datetime) >= '{lookback}' 
            AND date(datetime) < '{today}'
            """
            df_level = pd.read_sql_query(query, self.conn_15min)
            timeframes[name] = {
                'high': df_level['high'].iloc[0],
                'low': df_level['low'].iloc[0],
                'median': median, 'p75': p75, 'max': max_gain, 'time': time_hrs
            }
        
        # Calculate probabilities for each level
        for name, level_data in timeframes.items():
            high_dist_atr = (level_data['high'] - self.current_price) / self.atr_14
            low_dist_atr = (self.current_price - level_data['low']) / self.atr_14
            
            level_data['high_distance'] = level_data['high'] - self.current_price
            level_data['low_distance'] = self.current_price - level_data['low']
            level_data['high_dist_atr'] = high_dist_atr
            level_data['low_dist_atr'] = low_dist_atr
            level_data['high_probability'] = self._calculate_probability(abs(high_dist_atr))
            level_data['low_probability'] = self._calculate_probability(abs(low_dist_atr))
            
            # Breakout/breakdown status
            level_data['high_broken'] = self.current_price > level_data['high']
            level_data['low_broken'] = self.current_price < level_data['low']
        
        self.levels = timeframes
    
    def _calculate_probability(self, dist_atr):
        """Calculate probability based on ATR distance"""
        if dist_atr < 0.25: return 85
        elif dist_atr < 0.5: return 70
        elif dist_atr < 1.0: return 45
        elif dist_atr < 1.5: return 25
        elif dist_atr < 2.0: return 12
        else: return 5
    
    def check_breakouts(self):
        """Check for new breakouts/breakdowns at candle close"""
        new_signals = []
        
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
            return new_signals
        
        candle_close = df_candle['close'].iloc[0]
        candle_time = df_candle['datetime'].iloc[0]
        
        # Check each level for breakouts/breakdowns
        for name, level_data in self.levels.items():
            # Check HIGH breakout - immediate entry after candle close above level
            if candle_close > level_data['high']:
                # Check if already signaled
                if not any(s['timeframe'] == name and s['direction'] == 'CALL' for s in self.active_signals):
                    # Create immediate ACTIVE signal at candle close
                    signal = self._create_signal(name, 'CALL', level_data, candle_close, candle_time)
                    self.active_signals.append(signal)
                    new_signals.append(signal)
            
            # Check LOW breakdown - immediate entry after candle close below level
            if candle_close < level_data['low']:
                # Check if already signaled
                if not any(s['timeframe'] == name and s['direction'] == 'PUT' for s in self.active_signals):
                    # Create immediate ACTIVE signal at candle close
                    signal = self._create_signal(name, 'PUT', level_data, candle_close, candle_time)
                    self.active_signals.append(signal)
                    new_signals.append(signal)
        
        return new_signals
    
    def _create_signal(self, timeframe, direction, level_data, entry_price, entry_time):
        """Create a new trading signal"""
        if direction == 'CALL':
            breakout_level = level_data['high']
            median_target = breakout_level + level_data['median']
            p75_target = breakout_level + level_data['p75']
            max_target = breakout_level + level_data['max']
        else:  # PUT
            breakout_level = level_data['low']
            median_target = breakout_level - level_data['median']
            p75_target = breakout_level - level_data['p75']
            max_target = breakout_level - level_data['max']
        
        signal = {
            'id': f"{timeframe}_{direction}_{entry_time}",
            'timeframe': timeframe,
            'direction': direction,
            'breakout_level': breakout_level,
            'entry_price': entry_price,
            'entry_time': entry_time,
            'median_target': median_target,
            'p75_target': p75_target,
            'max_target': max_target,
            'expected_time_hours': level_data['time'],
            'status': 'ACTIVE',
            'max_profit': 0,
            'current_profit': 0,
            'targets_hit': [],
            'probability': level_data['high_probability'] if direction == 'CALL' else level_data['low_probability']
        }
        
        return signal
    

    

    
    def update_active_signals(self):
        """Update all active signals with current price"""
        today = datetime.now().date()
        
        # Get all candles from today
        query = f"""
        SELECT datetime, high, low, close 
        FROM data_15min 
        WHERE date(datetime) = '{today}'
        ORDER BY datetime
        """
        df_candles = pd.read_sql_query(query, self.conn_15min)
        
        for signal in self.active_signals:
            if signal['status'] != 'ACTIVE':
                continue
            
            # Get candles after entry
            entry_time = pd.to_datetime(signal['entry_time'])
            future_candles = df_candles[pd.to_datetime(df_candles['datetime']) > entry_time]
            
            if future_candles.empty:
                continue
            
            if signal['direction'] == 'CALL':
                # Check highest price reached
                max_high = future_candles['high'].max()
                current_price = future_candles['close'].iloc[-1]
                
                signal['max_profit'] = max_high - signal['entry_price']
                signal['current_profit'] = current_price - signal['entry_price']
                
                # Check targets
                if max_high >= signal['max_target'] and 'max' not in signal['targets_hit']:
                    signal['targets_hit'].append('max')
                    signal['target_max_time'] = future_candles[future_candles['high'] >= signal['max_target']]['datetime'].iloc[0]
                
                if max_high >= signal['p75_target'] and '75th' not in signal['targets_hit']:
                    signal['targets_hit'].append('75th')
                    signal['target_p75_time'] = future_candles[future_candles['high'] >= signal['p75_target']]['datetime'].iloc[0]
                
                if max_high >= signal['median_target'] and 'median' not in signal['targets_hit']:
                    signal['targets_hit'].append('median')
                    signal['target_median_time'] = future_candles[future_candles['high'] >= signal['median_target']]['datetime'].iloc[0]
                
            else:  # PUT
                # Check lowest price reached
                min_low = future_candles['low'].min()
                current_price = future_candles['close'].iloc[-1]
                
                signal['max_profit'] = signal['entry_price'] - min_low
                signal['current_profit'] = signal['entry_price'] - current_price
                
                # Check targets
                if min_low <= signal['max_target'] and 'max' not in signal['targets_hit']:
                    signal['targets_hit'].append('max')
                    signal['target_max_time'] = future_candles[future_candles['low'] <= signal['max_target']]['datetime'].iloc[0]
                
                if min_low <= signal['p75_target'] and '75th' not in signal['targets_hit']:
                    signal['targets_hit'].append('75th')
                    signal['target_p75_time'] = future_candles[future_candles['low'] <= signal['p75_target']]['datetime'].iloc[0]
                
                if min_low <= signal['median_target'] and 'median' not in signal['targets_hit']:
                    signal['targets_hit'].append('median')
                    signal['target_median_time'] = future_candles[future_candles['low'] <= signal['median_target']]['datetime'].iloc[0]
    
    def get_live_status(self):
        """Get current status for display"""
        self.update_levels()
        self.update_active_signals()
        
        # Convert numpy types to Python native types for JSON serialization
        def to_native(val):
            """Convert numpy/pandas types to Python native types"""
            if hasattr(val, 'item'):
                return val.item()
            return val
        
        status = {
            'current_price': float(self.current_price) if self.current_price is not None else None,
            'last_update': self.last_update,
            'atr_14': float(self.atr_14) if self.atr_14 is not None else None,
            'levels': {},
            'active_signals': [],
            'completed_trades': self.completed_trades
        }
        
        # Format levels
        for name, level_data in self.levels.items():
            status['levels'][name] = {
                'high': float(level_data['high']),
                'low': float(level_data['low']),
                'high_distance': float(level_data['high_distance']),
                'low_distance': float(level_data['low_distance']),
                'high_probability': int(level_data['high_probability']),
                'low_probability': int(level_data['low_probability']),
                'high_broken': bool(level_data['high_broken']),
                'low_broken': bool(level_data['low_broken'])
            }
        

        
        # Format active signals
        for signal in self.active_signals:
            if signal['status'] == 'ACTIVE':
                status['active_signals'].append({
                    'timeframe': str(signal['timeframe']),
                    'direction': str(signal['direction']),
                    'entry_price': float(signal['entry_price']),
                    'entry_time': str(signal['entry_time']),
                    'median_target': float(signal['median_target']),
                    'p75_target': float(signal['p75_target']),
                    'max_target': float(signal['max_target']),
                    'current_profit': float(signal['current_profit']),
                    'max_profit': float(signal['max_profit']),
                    'targets_hit': [str(t) for t in signal['targets_hit']],
                    'probability': float(signal['probability'])
                })
        
        return status
    
    def close_signal(self, signal_id, reason='Manual'):
        """Close an active signal"""
        for signal in self.active_signals:
            if signal['id'] == signal_id and signal['status'] == 'ACTIVE':
                signal['status'] = 'CLOSED'
                signal['close_reason'] = reason
                signal['close_time'] = datetime.now().isoformat()
                self.completed_trades.append(signal)
                return True
        return False

# Global monitor instance
pranni_monitor = None

def get_monitor():
    """Get or create monitor instance"""
    global pranni_monitor
    if pranni_monitor is None:
        pranni_monitor = PranniLiveMonitor()
    return pranni_monitor

if __name__ == "__main__":
    # Test the monitor
    monitor = PranniLiveMonitor()
    
    print("=" * 60)
    print("PRANNI LIVE MONITOR - TEST RUN")
    print("=" * 60)
    print()
    
    # Get current status
    status = monitor.get_live_status()
    
    print(f"Current Price: ₹{status['current_price']:.2f}")
    print(f"ATR (14): {status['atr_14']:.2f}")
    print(f"Last Update: {status['last_update']}")
    print()
    
    print("KEY LEVELS STATUS:")
    print("-" * 60)
    for name, level in status['levels'].items():
        print(f"\n{name}:")
        print(f"  High: ₹{level['high']:.2f} ({level['high_distance']:+.2f} pts, {level['high_probability']}% prob) {'🔥 BROKEN' if level['high_broken'] else ''}")
        print(f"  Low:  ₹{level['low']:.2f} ({level['low_distance']:+.2f} pts, {level['low_probability']}% prob) {'🚨 BROKEN' if level['low_broken'] else ''}")
    
    # Check for new breakouts
    print("\n" + "=" * 60)
    print("CHECKING FOR BREAKOUTS...")
    print("=" * 60)
    new_signals = monitor.check_breakouts()
    
    if new_signals:
        print(f"\n🚨 {len(new_signals)} NEW SIGNAL(S) DETECTED!")
        for signal in new_signals:
            print(f"\n{signal['timeframe']} - {signal['direction']}")
            print(f"  Entry: ₹{signal['entry_price']:.2f} at {signal['entry_time']}")
            print(f"  Targets: {signal['median_target']:.2f} (median) | {signal['p75_target']:.2f} (75th) | {signal['max_target']:.2f} (max)")
            print(f"  Probability: {signal['probability']}%")
    else:
        print("\nNo new breakouts detected.")
    
    print("\n" + "=" * 60)
    print("ACTIVE SIGNALS:")
    print("=" * 60)
    if status['active_signals']:
        for signal in status['active_signals']:
            print(f"\n{signal['timeframe']} - {signal['direction']}")
            print(f"  Entry: ₹{signal['entry_price']:.2f}")
            print(f"  Current P/L: {signal['current_profit']:+.2f} pts (Max: {signal['max_profit']:+.2f} pts)")
            print(f"  Targets Hit: {', '.join(signal['targets_hit']) if signal['targets_hit'] else 'None yet'}")
            print(f"  Next Target: ₹{signal['median_target']:.2f} (median, 50% prob)")
    else:
        print("\nNo active signals.")
