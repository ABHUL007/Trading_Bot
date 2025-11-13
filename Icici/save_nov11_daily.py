#!/usr/bin/env python3
"""
Save Nov 11 daily candle to database
"""

import sqlite3
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print("📊 CALCULATING NOV 11 DAILY CANDLE FROM 15-MIN DATA")
print("="*80 + "\n")

# Get all 15-min candles for Nov 11
conn = sqlite3.connect('NIFTY_15min_data.db')
candles = conn.execute('''
    SELECT datetime, open, high, low, close, volume
    FROM data_15min 
    WHERE date(datetime) = '2025-11-11'
    AND TIME(datetime) >= '09:15:00'
    AND TIME(datetime) <= '15:30:00'
    ORDER BY datetime
''').fetchall()
conn.close()

if not candles:
    print("❌ No 15-min candles found for Nov 11")
    exit(1)

print(f"✅ Found {len(candles)} candles")
print(f"   First: {candles[0][0]}")
print(f"   Last:  {candles[-1][0]}")

# Calculate daily OHLC
daily_open = candles[0][1]
daily_high = max(c[2] for c in candles)
daily_low = min(c[3] for c in candles)
daily_close = candles[-1][4]
daily_volume = sum(c[5] for c in candles)

print(f"\n📈 DAILY CANDLE:")
print(f"   Open:   ₹{daily_open:.2f}")
print(f"   High:   ₹{daily_high:.2f}  🔴 PDH")
print(f"   Low:    ₹{daily_low:.2f}   🟢 PDL")
print(f"   Close:  ₹{daily_close:.2f}")
print(f"   Volume: {daily_volume}")

# Save to database
conn = sqlite3.connect('NIFTY_1day_data.db')
cursor = conn.cursor()

# Check if Nov 11 already exists
existing = cursor.execute('''
    SELECT datetime FROM data_1day WHERE date(datetime) = '2025-11-11'
''').fetchone()

if existing:
    print(f"\n⚠️  Nov 11 data already exists, updating...")
    cursor.execute('''
        UPDATE data_1day 
        SET open=?, high=?, low=?, close=?, volume=?
        WHERE date(datetime) = '2025-11-11'
    ''', (daily_open, daily_high, daily_low, daily_close, daily_volume))
else:
    print(f"\n✅ Inserting new Nov 11 data...")
    cursor.execute('''
        INSERT INTO data_1day (datetime, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('2025-11-11 00:00:00', daily_open, daily_high, daily_low, daily_close, daily_volume))

conn.commit()
conn.close()

print(f"✅ Saved to NIFTY_1day_data.db")

# Verify
conn = sqlite3.connect('NIFTY_1day_data.db')
saved = conn.execute('''
    SELECT datetime, open, high, low, close 
    FROM data_1day 
    WHERE date(datetime) = '2025-11-11'
''').fetchone()
conn.close()

if saved:
    print(f"\n✅ VERIFICATION - Nov 11 data in database:")
    print(f"   {saved[0]} | O: ₹{saved[1]:.2f}, H: ₹{saved[2]:.2f}, L: ₹{saved[3]:.2f}, C: ₹{saved[4]:.2f}")
else:
    print(f"\n❌ Failed to save to database")

print("="*80 + "\n")
