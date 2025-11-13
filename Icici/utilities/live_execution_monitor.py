#!/usr/bin/env python3
"""Live execution monitor - watch the bot execute trade in real-time."""

import time
import sqlite3
from datetime import datetime

def live_execution_monitor():
    print('🚨 LIVE TRADE EXECUTION MONITOR')
    print('⏰ Watching for 13:15 candle completion...')
    print('=' * 50)
    
    start_time = datetime.now()
    
    while True:
        now = datetime.now()
        elapsed = (now - start_time).total_seconds()
        
        # Check if we're past 13:15
        if now.hour == 13 and now.minute >= 15:
            print(f'\n🎯 13:15 CANDLE COMPLETED! Checking execution...')
            
            # Check if new 15-min candle exists
            conn = sqlite3.connect('NIFTY_15min_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT datetime, close FROM data_15min WHERE datetime = "2025-11-07 13:15:00"')
            new_candle = cursor.fetchone()
            
            if new_candle:
                candle_time, candle_close = new_candle
                print(f'✅ New candle found: {candle_time} Close: ₹{candle_close:.2f}')
                
                if candle_close > 25438.50:
                    print(f'🚨 BREAKOUT CONFIRMED! ₹{candle_close:.2f} > ₹25438.50')
                    print(f'✅ Bot should execute CALL trade within next 3-5 seconds!')
                    
                    # Check for trade execution
                    time.sleep(10)  # Wait for trade
                    
                    conn_trades = sqlite3.connect('paper_trades.db')
                    cursor_trades = conn_trades.cursor()
                    cursor_trades.execute('SELECT * FROM paper_trades WHERE timestamp > datetime("now", "-2 minutes") ORDER BY timestamp DESC LIMIT 1')
                    recent_trade = cursor_trades.fetchone()
                    
                    if recent_trade:
                        print(f'🎉 TRADE EXECUTED!')
                        print(f'   Details: {recent_trade}')
                    else:
                        print(f'⚠️ No trade found - checking confluence score...')
                    
                    conn_trades.close()
                else:
                    print(f'❌ Candle closed below breakout level')
                
                conn.close()
                break
            else:
                print(f'⏳ Waiting for 13:15 candle data...')
                conn.close()
                time.sleep(5)
        
        elif now.hour == 13 and now.minute < 15:
            seconds_left = (15 - now.minute) * 60 - now.second
            print(f'\r⏳ {seconds_left:3d}s until 13:15 candle completion...', end='', flush=True)
            time.sleep(1)
        
        elif elapsed > 300:  # 5 minutes max
            print('\n⏰ Monitor timeout')
            break
        
        else:
            break

if __name__ == "__main__":
    live_execution_monitor()