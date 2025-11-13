#!/usr/bin/env python3
"""
Calculate and save November 11, 2025 daily candle from 5-min data
"""

import sqlite3
from datetime import datetime

print("\n" + "="*80)
print("📊 CALCULATING NOV 11, 2025 DAILY CANDLE")
print("="*80 + "\n")

# Get Nov 11 5-min data
conn_5min = sqlite3.connect('NIFTY_5min_data.db')
candles = conn_5min.execute('''
    SELECT datetime, open, high, low, close, volume
    FROM data_5min
    WHERE datetime LIKE '2025-11-11%'
    AND TIME(datetime) >= '09:15:00'
    AND TIME(datetime) <= '15:30:00'
    ORDER BY datetime
''').fetchall()
conn_5min.close()

if not candles:
    print("❌ No 5-min data found for Nov 11, 2025")
    exit(1)

print(f"📊 Found {len(candles)} 5-min candles for Nov 11, 2025")
print(f"   First: {candles[0][0]}")
print(f"   Last:  {candles[-1][0]}")

# Calculate daily OHLC
daily_open = candles[0][1]  # First candle's open
daily_high = max(c[2] for c in candles)  # Highest high
daily_low = min(c[3] for c in candles)   # Lowest low
daily_close = candles[-1][4]  # Last candle's close
daily_volume = sum(c[5] for c in candles)  # Total volume

print(f"\n📈 NOVEMBER 11, 2025 DAILY CANDLE:")
print(f"   Open:   ₹{daily_open:.2f}")
print(f"   High:   ₹{daily_high:.2f}  🔴 (This is PDH for today)")
print(f"   Low:    ₹{daily_low:.2f}   🟢 (This is PDL for today)")
print(f"   Close:  ₹{daily_close:.2f}")
print(f"   Volume: {daily_volume:,}")

# Save to daily database
conn_daily = sqlite3.connect('NIFTY_1day_data.db')
cursor = conn_daily.cursor()

cursor.execute('''
    INSERT OR REPLACE INTO data_1day (datetime, open, high, low, close, volume)
    VALUES (?, ?, ?, ?, ?, ?)
''', (
    '2025-11-11 00:00:00',
    daily_open,
    daily_high,
    daily_low,
    daily_close,
    daily_volume
))

conn_daily.commit()
conn_daily.close()

print(f"\n✅ Saved to NIFTY_1day_data.db")

print("\n" + "="*80)
print("🎯 TODAY'S TRADING LEVELS (Nov 12, 2025)")
print("="*80)
print(f"🔴 PDH (Previous Day High): ₹{daily_high:.2f}")
print(f"🟢 PDL (Previous Day Low):  ₹{daily_low:.2f}")
print("="*80 + "\n")
