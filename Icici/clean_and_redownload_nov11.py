#!/usr/bin/env python3
"""
Clean Nov 11 data and re-download correctly
"""

import sqlite3
import sys
import os
from datetime import datetime

# Change to parent directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print("🗑️  CLEANING NOVEMBER 11, 2025 DATA")
print("="*80 + "\n")

# Delete from 5-min
conn = sqlite3.connect('NIFTY_5min_data.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM data_5min WHERE datetime LIKE '2025-11-11%'")
deleted_5min = cursor.rowcount
conn.commit()
conn.close()
print(f"✅ Deleted {deleted_5min} candles from NIFTY_5min_data.db")

# Delete from 15-min
conn = sqlite3.connect('NIFTY_15min_data.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM data_15min WHERE datetime LIKE '2025-11-11%'")
deleted_15min = cursor.rowcount
conn.commit()
conn.close()
print(f"✅ Deleted {deleted_15min} candles from NIFTY_15min_data.db")

# Delete from 1-day
conn = sqlite3.connect('NIFTY_1day_data.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM data_1day WHERE datetime LIKE '2025-11-11%'")
deleted_1day = cursor.rowcount
conn.commit()
conn.close()
print(f"✅ Deleted {deleted_1day} candle from NIFTY_1day_data.db")

print("\n" + "="*80)
print("📥 RE-DOWNLOADING NOVEMBER 11, 2025 DATA")
print("="*80 + "\n")

# Now use websocket collector to download
sys.path.append(os.path.join(os.path.dirname(__file__), 'Trading_System'))
from websocket_data_collector import NiftyDataCollector

collector = NiftyDataCollector()

if not collector.connect_to_breeze():
    print("❌ Failed to connect")
    exit(1)

# Download Nov 11 data
collector.download_and_save_historical(date_str='2025-11-11')

print("\n" + "="*80)
print("✅ DOWNLOAD COMPLETE - CHECKING DATA")
print("="*80 + "\n")

# Show 15-min data
conn = sqlite3.connect('NIFTY_15min_data.db')
candles_15min = conn.execute('''
    SELECT datetime, open, high, low, close 
    FROM data_15min 
    WHERE datetime LIKE '2025-11-11%'
    AND TIME(datetime) >= '09:15:00'
    AND TIME(datetime) <= '15:30:00'
    ORDER BY datetime
''').fetchall()
conn.close()

print(f"📊 15-MIN CANDLES (Total: {len(candles_15min)}):")
for i, row in enumerate(candles_15min, 1):
    print(f"   {i:2d}. {row[0]} | O: ₹{row[1]:7.2f}, H: ₹{row[2]:7.2f}, L: ₹{row[3]:7.2f}, C: ₹{row[4]:7.2f}")

if candles_15min:
    daily_open = candles_15min[0][1]
    daily_high = max(c[2] for c in candles_15min)
    daily_low = min(c[3] for c in candles_15min)
    daily_close = candles_15min[-1][4]
    
    print(f"\n" + "="*80)
    print(f"📈 NOVEMBER 11, 2025 DAILY LEVELS")
    print(f"="*80)
    print(f"   Open:  ₹{daily_open:.2f}")
    print(f"   High:  ₹{daily_high:.2f}  🔴 PDH for today")
    print(f"   Low:   ₹{daily_low:.2f}   🟢 PDL for today")
    print(f"   Close: ₹{daily_close:.2f}")
    print(f"="*80 + "\n")
