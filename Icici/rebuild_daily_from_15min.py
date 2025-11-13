#!/usr/bin/env python3
"""
Build daily database from 15-min historical data
"""

import sqlite3
import os
from datetime import datetime
import pandas as pd

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print("📊 BUILDING DAILY DATABASE FROM 15-MIN DATA")
print("="*80 + "\n")

# Read all 15-min data
conn_15min = sqlite3.connect('NIFTY_15min_data.db')
print("📥 Loading 15-min data...")
df_15min = pd.read_sql_query('''
    SELECT datetime, open, high, low, close, volume 
    FROM data_15min 
    ORDER BY datetime
''', conn_15min)
conn_15min.close()

print(f"✅ Loaded {len(df_15min):,} 15-min candles")
print(f"   From: {df_15min['datetime'].min()}")
print(f"   To:   {df_15min['datetime'].max()}")

# Convert datetime to pandas datetime
df_15min['datetime'] = pd.to_datetime(df_15min['datetime'])

# Extract date only
df_15min['date'] = df_15min['datetime'].dt.date

# Group by date and aggregate
print("\n📊 Aggregating to daily candles...")
daily_data = df_15min.groupby('date').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).reset_index()

# Convert date back to datetime string
daily_data['datetime'] = pd.to_datetime(daily_data['date']).dt.strftime('%Y-%m-%d 00:00:00')
daily_data = daily_data[['datetime', 'open', 'high', 'low', 'close', 'volume']]

print(f"✅ Created {len(daily_data):,} daily candles")

# Save to database
conn_daily = sqlite3.connect('NIFTY_1day_data.db')
cursor = conn_daily.cursor()

# Clear existing data
cursor.execute('DELETE FROM data_1day')
print("\n🗑️  Cleared existing daily data")

# Insert new data
daily_data.to_sql('data_1day', conn_daily, if_exists='append', index=False)
conn_daily.commit()
conn_daily.close()

print(f"✅ Saved {len(daily_data):,} daily candles to NIFTY_1day_data.db")

# Verify
conn_daily = sqlite3.connect('NIFTY_1day_data.db')
result = conn_daily.execute('''
    SELECT MIN(datetime), MAX(datetime), COUNT(*) 
    FROM data_1day
''').fetchone()
conn_daily.close()

print("\n" + "="*80)
print("✅ VERIFICATION")
print("="*80)
print(f"   First Date: {result[0]}")
print(f"   Last Date:  {result[1]}")
print(f"   Total Days: {result[2]:,}")
print("="*80 + "\n")
