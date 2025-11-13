import sqlite3
import time
from datetime import datetime

def monitor_fresh_breakouts():
    """Monitor for fresh breakouts in real-time"""
    
    print("🚨 FRESH BREAKOUT MONITOR STARTED")
    print("=" * 40)
    
    # Get opening levels
    conn5 = sqlite3.connect('NIFTY_5min_data.db')
    opening_data = conn5.execute("""
    SELECT high, low FROM data_5min 
    WHERE DATE(datetime) = '2025-11-07' AND TIME(datetime) = '09:15:00'
    """).fetchone()
    
    if not opening_data:
        print("❌ No opening levels found")
        return
        
    opening_high, opening_low = opening_data
    conn5.close()
    
    print(f"📊 Monitoring Levels:")
    print(f"   High: ₹{opening_high:,.2f} (CALL breakout)")
    print(f"   Low: ₹{opening_low:,.2f} (PUT breakdown)")
    print("=" * 40)
    
    last_candle_time = None
    
    while True:
        try:
            # Get latest 2 candles
            conn15 = sqlite3.connect('NIFTY_15min_data.db')
            candles = conn15.execute("""
            SELECT datetime, close FROM data_15min 
            WHERE DATE(datetime) = '2025-11-07'
            ORDER BY datetime DESC 
            LIMIT 2
            """).fetchall()
            conn15.close()
            
            if len(candles) >= 2:
                current_time, current_close = candles[0]
                prev_time, prev_close = candles[1]
                
                # Only check if we have a new candle
                if current_time != last_candle_time:
                    last_candle_time = current_time
                    
                    current_time_str = current_time.split(' ')[1][:5]
                    now = datetime.now().strftime('%H:%M:%S')
                    
                    print(f"[{now}] Checking {current_time_str}: ₹{current_close:,.2f}")
                    
                    # Check for FRESH HIGH BREAKOUT
                    if prev_close <= opening_high and current_close > opening_high:
                        print(f"🚨🚨 FRESH HIGH BREAKOUT! 🚨🚨")
                        print(f"   Time: {current_time_str}")
                        print(f"   Previous: ₹{prev_close:,.2f} ≤ ₹{opening_high:,.2f}")
                        print(f"   Current:  ₹{current_close:,.2f} > ₹{opening_high:,.2f}")
                        print(f"   🎯 CALL TRADE SIGNAL!")
                        print("=" * 40)
                    
                    # Check for FRESH LOW BREAKDOWN
                    elif prev_close >= opening_low and current_close < opening_low:
                        print(f"🚨🚨 FRESH LOW BREAKDOWN! 🚨🚨")
                        print(f"   Time: {current_time_str}")
                        print(f"   Previous: ₹{prev_close:,.2f} ≥ ₹{opening_low:,.2f}")
                        print(f"   Current:  ₹{current_close:,.2f} < ₹{opening_low:,.2f}")
                        print(f"   🎯 PUT TRADE SIGNAL!")
                        print("=" * 40)
                    
                    else:
                        # Show current status
                        if current_close > opening_high:
                            status = f"🔴 Above high (continuation)"
                        elif current_close < opening_low:
                            status = f"🔵 Below low (continuation)"
                        else:
                            status = f"⚪ In range"
                        print(f"   {status}")
            
            time.sleep(30)  # Check every 30 seconds
            
        except KeyboardInterrupt:
            print("\n👋 Monitor stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_fresh_breakouts()