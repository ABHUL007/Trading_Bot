#!/usr/bin/env python3
"""
Check if bot is ready to trade today (Nov 12, 2025)
"""

import sqlite3
import os
from datetime import datetime
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print("🔍 TRADING READINESS CHECK - NOVEMBER 12, 2025")
print("="*80 + "\n")

# Check 1: PDH/PDL from Nov 11
print("📊 CHECK 1: Previous Day High/Low (PDH/PDL)")
print("-" * 80)
conn = sqlite3.connect('NIFTY_1day_data.db')
nov11_data = conn.execute('''
    SELECT datetime, open, high, low, close 
    FROM data_1day 
    WHERE date(datetime) = '2025-11-11'
''').fetchone()
conn.close()

if nov11_data:
    print(f"✅ Nov 11 Daily Data Found:")
    print(f"   Date:  {nov11_data[0]}")
    print(f"   Open:  ₹{nov11_data[1]:.2f}")
    print(f"   High:  ₹{nov11_data[2]:.2f}  🔴 PDH (Previous Day High)")
    print(f"   Low:   ₹{nov11_data[3]:.2f}  🟢 PDL (Previous Day Low)")
    print(f"   Close: ₹{nov11_data[4]:.2f}")
    pdh = nov11_data[2]
    pdl = nov11_data[3]
else:
    print("❌ Nov 11 data NOT FOUND - Cannot trade without PDH/PDL")
    pdh = None
    pdl = None

# Check 2: 15-min candles for Nov 11
print(f"\n📊 CHECK 2: 15-Minute Candles for Super Pranni Signals")
print("-" * 80)
conn = sqlite3.connect('NIFTY_15min_data.db')
candles_15min = conn.execute('''
    SELECT COUNT(*) 
    FROM data_15min 
    WHERE date(datetime) = '2025-11-11'
    AND TIME(datetime) >= '09:15:00'
    AND TIME(datetime) <= '15:30:00'
''').fetchone()[0]
conn.close()

if candles_15min >= 24:  # Expect ~25 candles
    print(f"✅ {candles_15min} candles found (Expected: 25)")
else:
    print(f"⚠️  Only {candles_15min} candles found (Expected: 25) - May affect signal quality")

# Check 3: 5-min candles for stop-loss
print(f"\n📊 CHECK 3: 5-Minute Candles for Stop-Loss Monitoring")
print("-" * 80)
conn = sqlite3.connect('NIFTY_5min_data.db')
candles_5min = conn.execute('''
    SELECT COUNT(*) 
    FROM data_5min 
    WHERE date(datetime) = '2025-11-11'
    AND TIME(datetime) >= '09:15:00'
    AND TIME(datetime) <= '15:30:00'
''').fetchone()[0]
conn.close()

if candles_5min >= 74:  # Expect ~75 candles
    print(f"✅ {candles_5min} candles found (Expected: 75)")
else:
    print(f"⚠️  Only {candles_5min} candles found (Expected: 75) - May affect stop-loss")

# Check 4: Real trades database
print(f"\n📊 CHECK 4: Real Trades Database")
print("-" * 80)
conn = sqlite3.connect('paper_trades.db')
cursor = conn.cursor()

# Check if real_trades table exists
table_exists = cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='real_trades'
''').fetchone()

if table_exists:
    print("✅ real_trades table exists")
    
    # Check columns
    columns = cursor.execute("PRAGMA table_info(real_trades)").fetchall()
    column_names = [col[1] for col in columns]
    
    required_columns = ['order_id', 'entry_order_status', 'exit_order_id', 
                       'exit_order_status', 'sl_candle_count', 'last_sl_check_time']
    
    missing = [col for col in required_columns if col not in column_names]
    if not missing:
        print(f"✅ All {len(column_names)} columns present (including order tracking)")
    else:
        print(f"⚠️  Missing columns: {', '.join(missing)}")
    
    # Check for any open trades
    open_trades = cursor.execute("SELECT COUNT(*) FROM real_trades WHERE status = 'OPEN'").fetchone()[0]
    if open_trades > 0:
        print(f"⚠️  {open_trades} OPEN position(s) found - will be monitored")
    else:
        print(f"✅ No open positions - ready for fresh signals")
else:
    print("❌ real_trades table NOT FOUND")

conn.close()

# Check 5: .env file
print(f"\n📊 CHECK 5: Configuration (.env file)")
print("-" * 80)
if os.path.exists('.env'):
    print("✅ .env file exists")
    with open('.env', 'r') as f:
        content = f.read()
        has_api_key = 'ICICI_API_KEY=' in content and content.split('ICICI_API_KEY=')[1].split('\n')[0].strip() != ''
        has_api_secret = 'ICICI_API_SECRET=' in content and content.split('ICICI_API_SECRET=')[1].split('\n')[0].strip() != ''
        has_session = 'ICICI_SESSION_TOKEN=' in content and content.split('ICICI_SESSION_TOKEN=')[1].split('\n')[0].strip() != ''
        has_paper_mode = 'PAPER_TRADING=' in content
        
        if has_api_key and has_api_secret:
            print("✅ API credentials configured")
        else:
            print("❌ API credentials missing")
        
        if has_session:
            print("✅ Session token configured")
        else:
            print("❌ Session token missing")
        
        if has_paper_mode:
            paper_mode = content.split('PAPER_TRADING=')[1].split('\n')[0].strip().lower()
            if paper_mode == 'true':
                print("⚠️  PAPER_TRADING=true (No real orders will be placed)")
            else:
                print("🔴 PAPER_TRADING=false (REAL ORDERS WILL BE PLACED)")
else:
    print("❌ .env file NOT FOUND")

# Check 6: Trading system files
print(f"\n📊 CHECK 6: Trading System Files")
print("-" * 80)
required_files = [
    ('Trading_System/real_trader.py', 'Main trading bot'),
    ('Trading_System/websocket_data_collector.py', 'Data collector'),
    ('Trading_System/super_pranni_monitor.py', 'Signal detector'),
    ('Trading_System/start_trading_system.py', 'System launcher'),
    ('Trading_System/START_TRADING_SYSTEM.bat', 'Windows launcher')
]

all_files_exist = True
for file_path, description in required_files:
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
    else:
        print(f"❌ MISSING: {description}: {file_path}")
        all_files_exist = False

# Final verdict
print("\n" + "="*80)
print("🎯 FINAL READINESS STATUS")
print("="*80)

if pdh and pdl and candles_15min >= 24 and candles_5min >= 74 and table_exists and all_files_exist:
    print("✅ ALL SYSTEMS GO - READY TO TRADE")
    print(f"\n📋 Quick Start:")
    print(f"   1. Run: Trading_System\\START_TRADING_SYSTEM.bat")
    print(f"   2. Bot will use PDH: ₹{pdh:.2f}, PDL: ₹{pdl:.2f}")
    print(f"   3. Watch for Super Pranni breakout signals")
    print(f"   4. Monitor logs: trading_system.log, real_trader.log")
    print("\n⚠️  IMPORTANT: Check PAPER_TRADING setting in .env before starting!")
else:
    print("❌ NOT READY - Please fix issues above")

print("="*80 + "\n")
