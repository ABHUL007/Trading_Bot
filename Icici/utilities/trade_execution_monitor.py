#!/usr/bin/env python3
"""
COMPREHENSIVE TRADE EXECUTION MONITOR
Shows EXACTLY when and how bot will execute trades
"""

import sqlite3
from datetime import datetime, timedelta
from super_pranni_monitor import FixedPranniMonitor

def check_trade_execution_status():
    print('🎯 REAL-TIME TRADE EXECUTION MONITOR')
    print('=' * 60)
    
    # 1. Get current market data
    conn = sqlite3.connect('NIFTY_5min_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT datetime, close FROM data_5min ORDER BY datetime DESC LIMIT 1')
    current_data = cursor.fetchone()
    current_time, current_price = current_data
    conn.close()
    
    print(f'📊 CURRENT STATUS:')
    print(f'   Time: {current_time}')
    print(f'   NIFTY: ₹{current_price:,.2f}')
    
    # 2. Check opening range levels
    monitor = FixedPranniMonitor()
    levels = monitor.get_all_trading_levels()
    
    if 'Opening Range' in levels:
        opening_high = levels['Opening Range']['high']
        opening_low = levels['Opening Range']['low']
        
        print(f'\n🎯 OPENING 5-MIN RANGE (TRIGGER LEVELS):')
        print(f'   High: ₹{opening_high:.2f} (CALL above this)')
        print(f'   Low:  ₹{opening_low:.2f} (PUT below this)')
        
        # Determine signal
        if current_price > opening_high:
            signal = "CALL"
            breakout_amount = current_price - opening_high
            print(f'\n🚨 SIGNAL: {signal} (+₹{breakout_amount:.2f} breakout)')
        elif current_price < opening_low:
            signal = "PUT" 
            breakdown_amount = opening_low - current_price
            print(f'\n🚨 SIGNAL: {signal} (-₹{breakdown_amount:.2f} breakdown)')
        else:
            signal = "WAIT"
            print(f'\n⏳ SIGNAL: {signal} (Inside range)')
        
        # 3. Check 15-minute candle timing
        conn15 = sqlite3.connect('NIFTY_15min_data.db')
        cursor15 = conn15.cursor()
        cursor15.execute('SELECT datetime, close FROM data_15min ORDER BY datetime DESC LIMIT 1')
        last_15min = cursor15.fetchone()
        candle_time, candle_close = last_15min
        conn15.close()
        
        candle_dt = datetime.strptime(candle_time, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        minutes_old = (now - candle_dt).total_seconds() / 60
        
        print(f'\n⏰ 15-MINUTE CANDLE STATUS:')
        print(f'   Last candle: {candle_time}')
        print(f'   Close: ₹{candle_close:.2f}')
        print(f'   Age: {minutes_old:.1f} minutes old')
        
        # Next candle timing
        next_candle = candle_dt + timedelta(minutes=15)
        wait_minutes = (next_candle - now).total_seconds() / 60
        
        if wait_minutes > 0:
            print(f'   Next candle: {next_candle.strftime("%H:%M:%S")} (in {wait_minutes:.1f} min)')
            trade_window = f"{next_candle.strftime('%H:%M')}-{(next_candle + timedelta(minutes=5)).strftime('%H:%M')}"
            print(f'   Trade window: {trade_window}')
        else:
            print('   ⚠️ Next candle overdue!')
        
        # 4. Execute condition check
        print(f'\n🔍 TRADE EXECUTION CONDITIONS:')
        conditions = []
        
        # Condition 1: Valid signal
        if signal != "WAIT":
            conditions.append(f"✅ Signal: {signal} breakout detected")
            will_execute_signal = True
        else:
            conditions.append(f"❌ Signal: Waiting for breakout")
            will_execute_signal = False
        
        # Condition 2: Fresh candle
        if minutes_old <= 5:
            conditions.append(f"✅ Timing: Fresh candle ({minutes_old:.1f}m old)")
            will_execute_timing = True
        else:
            conditions.append(f"❌ Timing: Candle too old ({minutes_old:.1f}m > 5m)")
            will_execute_timing = False
        
        # Condition 3: 15-min candle breakout
        if signal == "CALL" and candle_close > opening_high:
            conditions.append(f"✅ Breakout: 15m candle closed above ₹{opening_high:.2f}")
            will_execute_breakout = True
        elif signal == "PUT" and candle_close < opening_low:
            conditions.append(f"✅ Breakdown: 15m candle closed below ₹{opening_low:.2f}")
            will_execute_breakout = True
        else:
            conditions.append(f"❌ Breakout: 15m candle needs to close through level")
            will_execute_breakout = False
        
        for condition in conditions:
            print(f'   {condition}')
        
        # Final execution decision
        will_execute = will_execute_signal and will_execute_timing and will_execute_breakout
        
        print(f'\n🎯 EXECUTION DECISION:')
        if will_execute:
            print(f'   ✅ WILL EXECUTE {signal} TRADE')
            print(f'   📋 All conditions met - bot will trade automatically')
        else:
            if not will_execute_signal:
                print(f'   ⏳ WAITING for opening range breakout')
            elif not will_execute_timing:
                print(f'   ⏳ WAITING for fresh 15-minute candle')
            else:
                print(f'   ⏳ WAITING for 15m candle to close through level')
        
        # 5. Next execution opportunity
        print(f'\n🕐 NEXT EXECUTION OPPORTUNITIES:')
        current_hour = now.hour
        current_minute = now.minute
        
        # Calculate next 15-minute intervals
        next_intervals = []
        for h in range(current_hour, 16):  # Till market close
            for m in [0, 15, 30, 45]:
                if h == current_hour and m <= current_minute:
                    continue
                if h == 15 and m > 30:  # Market closes at 15:30
                    break
                next_intervals.append(f"{h:02d}:{m:02d}")
                if len(next_intervals) >= 3:
                    break
            if len(next_intervals) >= 3:
                break
        
        for i, interval in enumerate(next_intervals):
            print(f'   {i+1}. {interval} (Trade window: {interval}-{(datetime.strptime(interval, "%H:%M") + timedelta(minutes=5)).strftime("%H:%M")})')
    
    else:
        print('❌ No Opening Range data available')

if __name__ == "__main__":
    check_trade_execution_status()