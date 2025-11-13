#!/usr/bin/env python3
"""
Import NIFTY 50 historical data from CSV and merge with existing database
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print("📥 IMPORTING NIFTY 50 HISTORICAL DATA FROM CSV")
print("="*80 + "\n")

# Read CSV file
csv_file = 'Nifty 50 Historical Data (1).csv'
print(f"📂 Reading {csv_file}...")

df_csv = pd.read_csv(csv_file)
print(f"✅ Loaded {len(df_csv):,} rows from CSV")

# Show sample data
print("\n📊 Sample CSV data:")
print(df_csv.head(3))

# Parse and clean data
print("\n🔧 Cleaning and parsing data...")

# Convert Date column (DD-MM-YYYY format)
df_csv['datetime'] = pd.to_datetime(df_csv['Date'], format='%d-%m-%Y')

# Clean numeric columns (remove commas and convert)
def clean_price(value):
    if pd.isna(value):
        return 0.0
    return float(str(value).replace(',', ''))

df_csv['open'] = df_csv['Open'].apply(clean_price)
df_csv['high'] = df_csv['High'].apply(clean_price)
df_csv['low'] = df_csv['Low'].apply(clean_price)
df_csv['close'] = df_csv['Price'].apply(clean_price)  # Price is the close

# Volume - convert M to actual number
def clean_volume(value):
    if pd.isna(value):
        return 0
    value_str = str(value).replace('M', '').replace(',', '')
    try:
        return int(float(value_str) * 1_000_000)
    except:
        return 0

df_csv['volume'] = df_csv['Vol.'].apply(clean_volume)

# Format datetime as string
df_csv['datetime'] = df_csv['datetime'].dt.strftime('%Y-%m-%d 00:00:00')

# Select only needed columns
df_csv = df_csv[['datetime', 'open', 'high', 'low', 'close', 'volume']]

print(f"✅ Cleaned {len(df_csv):,} records")
print(f"   Date range: {df_csv['datetime'].min()} to {df_csv['datetime'].max()}")

# Check existing database
conn = sqlite3.connect('NIFTY_1day_data.db')
existing_dates = pd.read_sql_query('SELECT datetime FROM data_1day', conn)
print(f"\n📊 Existing database has {len(existing_dates):,} records")
print(f"   Date range: {existing_dates['datetime'].min()} to {existing_dates['datetime'].max()}")

# Find missing dates (in CSV but not in database)
existing_dates_set = set(existing_dates['datetime'])
csv_dates_set = set(df_csv['datetime'])

missing_in_db = csv_dates_set - existing_dates_set
print(f"\n🔍 Found {len(missing_in_db):,} dates in CSV that are missing in database")

if len(missing_in_db) > 0:
    # Filter CSV to only missing dates
    df_missing = df_csv[df_csv['datetime'].isin(missing_in_db)].copy()
    df_missing = df_missing.sort_values('datetime')
    
    print(f"\n📥 Importing {len(df_missing):,} missing records...")
    print(f"   From: {df_missing['datetime'].min()}")
    print(f"   To:   {df_missing['datetime'].max()}")
    
    # Insert missing data
    df_missing.to_sql('data_1day', conn, if_exists='append', index=False)
    conn.commit()
    
    print(f"✅ Successfully imported {len(df_missing):,} records")
else:
    print("✅ No missing data - database is already up to date")

# Update existing records if CSV has different values
print("\n🔄 Checking for records to update...")
df_to_update = df_csv[df_csv['datetime'].isin(existing_dates_set)].copy()

if len(df_to_update) > 0:
    print(f"   Found {len(df_to_update):,} records that exist in both CSV and database")
    print("   Updating these records with CSV data...")
    
    cursor = conn.cursor()
    updated_count = 0
    
    for _, row in df_to_update.iterrows():
        cursor.execute('''
            UPDATE data_1day 
            SET open=?, high=?, low=?, close=?, volume=?
            WHERE datetime=?
        ''', (row['open'], row['high'], row['low'], row['close'], 
              row['volume'], row['datetime']))
        if cursor.rowcount > 0:
            updated_count += 1
    
    conn.commit()
    print(f"✅ Updated {updated_count:,} records")

conn.close()

# Verify final state
print("\n" + "="*80)
print("✅ FINAL DATABASE STATE")
print("="*80)
conn = sqlite3.connect('NIFTY_1day_data.db')
result = conn.execute('''
    SELECT MIN(datetime), MAX(datetime), COUNT(*) 
    FROM data_1day
    ORDER BY datetime
''').fetchone()
conn.close()

print(f"   First Date:  {result[0]}")
print(f"   Last Date:   {result[1]}")
print(f"   Total Days:  {result[2]:,}")

# Calculate data coverage
first_date = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
last_date = datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S')
years_of_data = (last_date - first_date).days / 365.25

print(f"   Coverage:    {years_of_data:.1f} years")
print("="*80 + "\n")
