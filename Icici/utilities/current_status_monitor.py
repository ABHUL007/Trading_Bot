import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os
import psutil
import time

def check_process_status():
    """Check if trading system processes are running"""
    print("🤖 PROCESS STATUS:")
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if any(script in cmdline for script in ['enhanced_safe_trader', 'websocket_data_collector']):
                    runtime = datetime.now() - datetime.fromtimestamp(proc.info['create_time'])
                    processes.append({
                        'pid': proc.info['pid'],
                        'script': cmdline.split('\\')[-1].replace('.py', ''),
                        'runtime': runtime
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if processes:
        for proc in processes:
            print(f"   ✅ {proc['script']} (PID: {proc['pid']}, Runtime: {str(proc['runtime']).split('.')[0]})")
    else:
        print("   ❌ No trading processes running!")
    
    return len(processes)

def check_database_health():
    """Check all database connections and recent updates"""
    print("\n💾 DATABASE HEALTH:")
    
    databases = {
        'NIFTY_5min_data.db': {'table': 'data_5min', 'type': '5min NIFTY data'},
        'NIFTY_15min_data.db': {'table': 'data_15min', 'type': '15min NIFTY data'},
        'options_data.db': {'table': 'options_data', 'type': 'Options data'},
        'paper_trades.db': {'table': 'paper_trades', 'type': 'Trading records'}
    }
    
    db_status = {}
    for db_name, info in databases.items():
        try:
            if os.path.exists(db_name):
                conn = sqlite3.connect(db_name)
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{info['table']}'")
                if cursor.fetchone():
                    # Get latest record
                    if db_name == 'options_data.db':
                        cursor.execute(f"SELECT COUNT(*), MAX(timestamp) FROM {info['table']} WHERE timestamp > datetime('now', '-5 minutes')")
                        count, latest = cursor.fetchone()
                        status = f"✅ {count} updates in 5min" if count > 0 else "⚠️ No recent updates"
                    else:
                        cursor.execute(f"SELECT datetime FROM {info['table']} ORDER BY datetime DESC LIMIT 1")
                        result = cursor.fetchone()
                        if result:
                            latest_time = result[0]
                            try:
                                latest_dt = datetime.strptime(latest_time, '%Y-%m-%d %H:%M:%S')
                                age_minutes = (datetime.now() - latest_dt).total_seconds() / 60
                                status = f"✅ Fresh ({age_minutes:.0f}min ago)" if age_minutes < 30 else f"⚠️ Stale ({age_minutes:.0f}min ago)"
                            except:
                                status = "⚠️ Invalid timestamp"
                        else:
                            status = "❌ No data"
                else:
                    status = "❌ Table missing"
                conn.close()
            else:
                status = "❌ DB missing"
                
            print(f"   {info['type']}: {status}")
            db_status[db_name] = status.startswith('✅')
            
        except Exception as e:
            print(f"   {info['type']}: ❌ Error - {str(e)[:50]}")
            db_status[db_name] = False
    
    return db_status

def check_current_status():
    """UPGRADED: Comprehensive trading system health check"""
    
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    
    print("🏥 COMPREHENSIVE TRADING SYSTEM HEALTH CHECK")
    print("=" * 65)
    print(f"🕐 Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    
    # Check if processes are running
    process_count = check_process_status()
    
    # Check database health
    db_status = check_database_health()
    
    # Check trading levels and signals
    print("\n📊 TRADING LEVELS & SIGNALS:")
    
    # Get opening range from 5min data
    today = current_time.strftime('%Y-%m-%d')
    
    try:
        conn5 = sqlite3.connect('NIFTY_5min_data.db')
        opening_query = f"""
        SELECT high, low FROM data_5min 
        WHERE DATE(datetime) = '{today}' AND TIME(datetime) = '09:15:00'
        """
        opening_data = pd.read_sql_query(opening_query, conn5)
        conn5.close()
        
        if not opening_data.empty:
            opening_high = opening_data['high'].iloc[0]
            opening_low = opening_data['low'].iloc[0]
            
            print(f"   Opening High: ₹{opening_high:,.2f} (CALL breakout level)")
            print(f"   Opening Low:  ₹{opening_low:,.2f} (PUT breakdown level)")
            
            # Get latest 15min data for current price
            conn15 = sqlite3.connect('NIFTY_15min_data.db')
            latest_query = """
            SELECT datetime, close FROM data_15min 
            WHERE DATE(datetime) = ? 
            ORDER BY datetime DESC LIMIT 2
            """
            latest_data = pd.read_sql_query(latest_query, conn15, params=[today])
            conn15.close()
            
            if len(latest_data) >= 2:
                current_candle = latest_data.iloc[0]
                prev_candle = latest_data.iloc[1]
                current_price = current_candle['close']
                prev_price = prev_candle['close']
                
                print(f"   Current Price: ₹{current_price:,.2f}")
                
                # Check for fresh breakout signals
                if prev_price <= opening_high and current_price > opening_high:
                    print(f"   🚨 FRESH CALL SIGNAL! (Fresh breakout above ₹{opening_high:,.2f})")
                elif prev_price >= opening_low and current_price < opening_low:
                    print(f"   🚨 FRESH PUT SIGNAL! (Fresh breakdown below ₹{opening_low:,.2f})")
                elif current_price > opening_high:
                    print(f"   🔴 Above high (continuation, no fresh signal)")
                elif current_price < opening_low:
                    print(f"   🔵 Below low (continuation, no fresh signal)")
                else:
                    print(f"   ⚪ In range (waiting for breakout)")
            else:
                print(f"   ⚠️ Insufficient 15min data for signal analysis")
        else:
            print(f"   ❌ No opening range data for today")
    except Exception as e:
        print(f"   ❌ Error checking trading levels: {str(e)[:50]}")
    
    # Check recent trades
    print(f"\n💼 RECENT TRADING ACTIVITY:")
    try:
        conn_trades = sqlite3.connect('paper_trades.db')
        trades_query = """
        SELECT timestamp, trade_type, entry_price 
        FROM paper_trades 
        WHERE DATE(timestamp) = ?
        ORDER BY timestamp DESC LIMIT 5
        """
        trades = pd.read_sql_query(trades_query, conn_trades, params=[today])
        conn_trades.close()
        
        if not trades.empty:
            print(f"   Today's trades ({len(trades)}):")
            for _, trade in trades.iterrows():
                time_str = trade['timestamp'].split(' ')[1][:5]
                print(f"     {time_str}: {trade['trade_type']} @ ₹{trade['entry_price']:,.2f}")
        else:
            print(f"   No trades executed today")
    except Exception as e:
        print(f"   ⚠️ Could not check trading activity: {str(e)[:30]}")
    
    # System health summary
    print(f"\n🏥 SYSTEM HEALTH SUMMARY:")
    healthy_components = sum([
        process_count >= 2,  # Both main processes running
        all(db_status.values()),  # All databases healthy
    ])
    
    if healthy_components == 2:
        print(f"   ✅ ALL SYSTEMS OPERATIONAL")
    elif healthy_components == 1:
        print(f"   ⚠️ PARTIAL SYSTEM ISSUES - Check above")
    else:
        print(f"   🚨 MAJOR SYSTEM ISSUES - Manual intervention required")
    
    if not latest_data.empty:
        print("🔍 Recent 15-Min Candles:")
        for _, row in latest_data.iterrows():
            time_str = row['datetime']
            if isinstance(time_str, str):
                time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                time_obj = time_obj.replace(tzinfo=ist)
            else:
                time_obj = time_str.replace(tzinfo=ist)
            
            print(f"   {time_obj.strftime('%H:%M')}: O:{row['open']:,.1f} H:{row['high']:,.1f} L:{row['low']:,.1f} C:{row['close']:,.1f}")
    
    # Check for fresh breakouts
    print("\n🚨 Fresh Breakout Analysis:")
    
    if not opening_data.empty and not latest_data.empty:
        current_price = latest_data.iloc[0]['close']
        
        # Check if we have at least 2 candles for comparison
        if len(latest_data) >= 2:
            current_candle = latest_data.iloc[0]
            prev_candle = latest_data.iloc[1]
            
            # Fresh high breakout check
            if prev_candle['close'] <= opening_high and current_candle['close'] > opening_high:
                time_str = current_candle['datetime']
                if isinstance(time_str, str):
                    time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    time_obj = time_obj.replace(tzinfo=ist)
                else:
                    time_obj = time_str.replace(tzinfo=ist)
                
                print(f"   ⚡ FRESH HIGH BREAKOUT DETECTED!")
                print(f"   Time: {time_obj.strftime('%H:%M')}")
                print(f"   Price: ₹{current_candle['close']:,.2f} > ₹{opening_high:,.2f}")
                print(f"   🎯 EXECUTE CALL TRADE NOW!")
                
            elif prev_candle['close'] >= opening_low and current_candle['close'] < opening_low:
                time_str = current_candle['datetime']
                if isinstance(time_str, str):
                    time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    time_obj = time_obj.replace(tzinfo=ist)
                else:
                    time_obj = time_str.replace(tzinfo=ist)
                
                print(f"   ⚡ FRESH LOW BREAKDOWN DETECTED!")
                print(f"   Time: {time_obj.strftime('%H:%M')}")
                print(f"   Price: ₹{current_candle['close']:,.2f} < ₹{opening_low:,.2f}")
                print(f"   🎯 EXECUTE PUT TRADE NOW!")
            else:
                print(f"   ✋ No fresh breakout detected")
                print(f"   Current: ₹{current_price:,.2f}")
                print(f"   Range: ₹{opening_low:,.2f} - ₹{opening_high:,.2f}")
        else:
            print("   ⏳ Need more candle data for fresh breakout analysis")
    
    conn.close()
    conn15.close()
    
    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    check_current_status()