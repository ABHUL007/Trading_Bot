#!/usr/bin/env python3
"""
Calculate and display multi-timeframe highs and lows
"""

import sqlite3
import os
from datetime import datetime, timedelta

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print("📊 MULTI-TIMEFRAME HIGHS & LOWS")
print("="*80 + "\n")

conn = sqlite3.connect('NIFTY_1day_data.db')

# Today's date
today = datetime(2025, 11, 12)

# Calculate date ranges
one_week_ago = today - timedelta(days=7)
two_weeks_ago = today - timedelta(days=14)
one_month_ago = today - timedelta(days=30)
three_months_ago = today - timedelta(days=90)

# Weekly High/Low (Last 7 days)
print("📅 WEEKLY HIGH/LOW (Last 7 Days)")
print("-" * 80)
weekly_data = conn.execute('''
    SELECT MIN(low) as week_low, MAX(high) as week_high, 
           COUNT(*) as days
    FROM data_1day 
    WHERE datetime >= ?
    AND datetime < ?
''', (one_week_ago.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()

if weekly_data and weekly_data[0]:
    print(f"   🔴 Weekly High:  ₹{weekly_data[1]:.2f}")
    print(f"   🟢 Weekly Low:   ₹{weekly_data[0]:.2f}")
    print(f"   📊 Trading Days: {weekly_data[2]}")
else:
    print("   ⚠️  Insufficient data for weekly range")

# Fortnightly High/Low (Last 14 days)
print(f"\n📅 FORTNIGHTLY HIGH/LOW (Last 14 Days)")
print("-" * 80)
fortnightly_data = conn.execute('''
    SELECT MIN(low) as fortnight_low, MAX(high) as fortnight_high,
           COUNT(*) as days
    FROM data_1day 
    WHERE datetime >= ?
    AND datetime < ?
''', (two_weeks_ago.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()

if fortnightly_data and fortnightly_data[0]:
    print(f"   🔴 Fortnightly High:  ₹{fortnightly_data[1]:.2f}")
    print(f"   🟢 Fortnightly Low:   ₹{fortnightly_data[0]:.2f}")
    print(f"   📊 Trading Days:      {fortnightly_data[2]}")
else:
    print("   ⚠️  Insufficient data for fortnightly range")

# Monthly High/Low (Last 30 days)
print(f"\n📅 MONTHLY HIGH/LOW (Last 30 Days)")
print("-" * 80)
monthly_data = conn.execute('''
    SELECT MIN(low) as month_low, MAX(high) as month_high,
           COUNT(*) as days
    FROM data_1day 
    WHERE datetime >= ?
    AND datetime < ?
''', (one_month_ago.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()

if monthly_data and monthly_data[0]:
    print(f"   🔴 Monthly High:  ₹{monthly_data[1]:.2f}")
    print(f"   🟢 Monthly Low:   ₹{monthly_data[0]:.2f}")
    print(f"   📊 Trading Days:  {monthly_data[2]}")
else:
    print("   ⚠️  Insufficient data for monthly range")

# 3-Month High/Low (Last 90 days)
print(f"\n📅 3-MONTH HIGH/LOW (Last 90 Days)")
print("-" * 80)
three_month_data = conn.execute('''
    SELECT MIN(low) as quarter_low, MAX(high) as quarter_high,
           COUNT(*) as days
    FROM data_1day 
    WHERE datetime >= ?
    AND datetime < ?
''', (three_months_ago.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))).fetchone()

if three_month_data and three_month_data[0]:
    print(f"   🔴 3-Month High:  ₹{three_month_data[1]:.2f}")
    print(f"   🟢 3-Month Low:   ₹{three_month_data[0]:.2f}")
    print(f"   📊 Trading Days:  {three_month_data[2]}")
else:
    print("   ⚠️  Insufficient data for 3-month range")

# Show all available data range
print(f"\n📊 AVAILABLE DATA RANGE")
print("-" * 80)
data_range = conn.execute('''
    SELECT MIN(datetime) as first_date, MAX(datetime) as last_date,
           COUNT(*) as total_days
    FROM data_1day
''').fetchone()

if data_range and data_range[0]:
    print(f"   First Date:   {data_range[0]}")
    print(f"   Last Date:    {data_range[1]}")
    print(f"   Total Days:   {data_range[2]}")
    
    # Show last 10 days for reference
    print(f"\n📈 LAST 10 DAYS REFERENCE:")
    print("-" * 80)
    last_10_days = conn.execute('''
        SELECT datetime, high, low, close
        FROM data_1day
        ORDER BY datetime DESC
        LIMIT 10
    ''').fetchall()
    
    for day in last_10_days:
        date_str = datetime.strptime(day[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %a')
        print(f"   {date_str} | H: ₹{day[1]:7.2f} | L: ₹{day[2]:7.2f} | C: ₹{day[3]:7.2f}")

conn.close()

print("\n" + "="*80)
print("💡 NOTE: If data is insufficient, download more historical data")
print("="*80 + "\n")
