#!/usr/bin/env python3
"""
Download Yesterday's Historical Data
- Downloads 5-min data for yesterday
- Aggregates to 15-min
- Downloads daily data for yesterday
- Ensures PDH/PDL levels are available
"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from breeze_connect import BreezeConnect
import sqlite3
import pandas as pd
import time as time_module

# Get yesterday's date
yesterday = (datetime.now() - timedelta(days=1)).date()
print(f"\n{'='*80}")
print(f"📅 DOWNLOADING DATA FOR: {yesterday.strftime('%Y-%m-%d')} (Yesterday)")
print(f"{'='*80}\n")

# Initialize Breeze
api_key = os.getenv('ICICI_API_KEY')
api_secret = os.getenv('ICICI_API_SECRET')
session_token = os.getenv('ICICI_SESSION_TOKEN')

if not all([api_key, api_secret, session_token]):
    print("❌ Error: Missing ICICI credentials in .env file")
    print("   Required: ICICI_API_KEY, ICICI_API_SECRET, ICICI_SESSION_TOKEN")
    sys.exit(1)

print("🔌 Connecting to Breeze API...")
breeze = BreezeConnect(api_key=api_key)

try:
    breeze.generate_session(api_secret=api_secret, session_token=session_token)
    print("✅ Connected to Breeze API\n")
except Exception as e:
    print(f"❌ Failed to connect to Breeze: {e}")
    sys.exit(1)

# Database paths (in parent directory)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
DB_5MIN = os.path.join(PARENT_DIR, 'NIFTY_5min_data.db')
DB_15MIN = os.path.join(PARENT_DIR, 'NIFTY_15min_data.db')
DB_1DAY = os.path.join(PARENT_DIR, 'NIFTY_1day_data.db')


def download_5min_data():
    """Download yesterday's 5-minute data"""
    print("📊 Downloading 5-minute data...")
    
    try:
        # Breeze API call for 5-minute data
        from_date = yesterday.strftime('%Y-%m-%d') + "T00:00:00.000Z"
        to_date = yesterday.strftime('%Y-%m-%d') + "T23:59:59.000Z"
        
        response = breeze.get_historical_data_v2(
            interval="5minute",
            from_date=from_date,
            to_date=to_date,
            stock_code="NIFTY",
            exchange_code="NFO",
            product_type="futures",
            expiry_date="",
            right="",
            strike_price=""
        )
        
        if not response or 'Success' not in response:
            print(f"❌ Failed to get 5-min data: {response}")
            return False
        
        data = response['Success']
        
        if not data:
            print("⚠️ No 5-minute data returned")
            return False
        
        print(f"✅ Downloaded {len(data)} 5-minute candles")
        
        # Save to database
        conn = sqlite3.connect(DB_5MIN)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_5min (
                datetime TEXT PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER
            )
        ''')
        
        # Insert data
        saved_count = 0
        for candle in data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO data_5min (datetime, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    candle['datetime'],
                    candle['open'],
                    candle['high'],
                    candle['low'],
                    candle['close'],
                    candle.get('volume', 0)
                ))
                saved_count += 1
            except Exception as e:
                print(f"⚠️ Error saving candle: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Saved {saved_count} candles to NIFTY_5min_data.db\n")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading 5-min data: {e}\n")
        return False


def aggregate_to_15min():
    """Aggregate 5-minute data to 15-minute"""
    print("📊 Aggregating to 15-minute data...")
    
    try:
        conn_5min = sqlite3.connect(DB_5MIN)
        
        # Get yesterday's 5-min data
        query = f"""
        SELECT datetime, open, high, low, close, volume
        FROM data_5min
        WHERE datetime LIKE '{yesterday.strftime('%Y-%m-%d')}%'
        ORDER BY datetime
        """
        
        df = pd.read_sql_query(query, conn_5min)
        conn_5min.close()
        
        if df.empty:
            print("⚠️ No 5-minute data found to aggregate\n")
            return False
        
        print(f"📊 Found {len(df)} 5-minute candles")
        
        # Convert to datetime and aggregate
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        # Aggregate to 15-min
        df_15min = df.resample('15min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        if df_15min.empty:
            print("⚠️ Failed to aggregate to 15-minute\n")
            return False
        
        print(f"✅ Aggregated to {len(df_15min)} 15-minute candles")
        
        # Save to database
        conn_15min = sqlite3.connect(DB_15MIN)
        cursor = conn_15min.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_15min (
                datetime TEXT PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER
            )
        ''')
        
        # Insert data
        df_15min.reset_index(inplace=True)
        saved_count = 0
        
        for _, row in df_15min.iterrows():
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO data_15min (datetime, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    row['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    int(row['volume'])
                ))
                saved_count += 1
            except Exception as e:
                print(f"⚠️ Error saving 15-min candle: {e}")
        
        conn_15min.commit()
        conn_15min.close()
        
        print(f"✅ Saved {saved_count} candles to NIFTY_15min_data.db\n")
        return True
        
    except Exception as e:
        print(f"❌ Error aggregating to 15-min: {e}\n")
        return False


def download_daily_data():
    """Download yesterday's daily data for PDH/PDL"""
    print("📊 Downloading daily data for PDH/PDL...")
    
    try:
        # Breeze API call for daily data
        from_date = yesterday.strftime('%Y-%m-%d') + "T00:00:00.000Z"
        to_date = yesterday.strftime('%Y-%m-%d') + "T23:59:59.000Z"
        
        response = breeze.get_historical_data_v2(
            interval="1day",
            from_date=from_date,
            to_date=to_date,
            stock_code="NIFTY",
            exchange_code="NFO",
            product_type="futures",
            expiry_date="",
            right="",
            strike_price=""
        )
        
        if not response or 'Success' not in response:
            print(f"❌ Failed to get daily data: {response}")
            return False
        
        data = response['Success']
        
        if not data:
            print("⚠️ No daily data returned")
            return False
        
        print(f"✅ Downloaded {len(data)} daily candle(s)")
        
        # Save to database
        conn = sqlite3.connect(DB_1DAY)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_1day (
                datetime TEXT PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER
            )
        ''')
        
        # Insert data
        saved_count = 0
        pdh = None
        pdl = None
        
        for candle in data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO data_1day (datetime, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    candle['datetime'],
                    candle['open'],
                    candle['high'],
                    candle['low'],
                    candle['close'],
                    candle.get('volume', 0)
                ))
                saved_count += 1
                pdh = candle['high']
                pdl = candle['low']
            except Exception as e:
                print(f"⚠️ Error saving daily candle: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Saved {saved_count} candle(s) to NIFTY_1day_data.db")
        
        if pdh and pdl:
            print(f"\n{'='*80}")
            print(f"📊 PREVIOUS DAY HIGH (PDH): ₹{pdh:.2f}")
            print(f"📊 PREVIOUS DAY LOW (PDL):  ₹{pdl:.2f}")
            print(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading daily data: {e}\n")
        return False


def main():
    """Main execution"""
    print("🚀 Starting data download process...\n")
    
    success_count = 0
    
    # Step 1: Download 5-minute data
    if download_5min_data():
        success_count += 1
    
    # Wait 2 seconds between API calls
    time_module.sleep(2)
    
    # Step 2: Aggregate to 15-minute
    if aggregate_to_15min():
        success_count += 1
    
    # Wait 2 seconds before next API call
    time_module.sleep(2)
    
    # Step 3: Download daily data
    if download_daily_data():
        success_count += 1
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 DOWNLOAD SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Completed: {success_count}/3 tasks")
    
    if success_count == 3:
        print(f"🎉 All data downloaded successfully!")
        print(f"\n📁 Data saved to:")
        print(f"   - {DB_5MIN}")
        print(f"   - {DB_15MIN}")
        print(f"   - {DB_1DAY}")
        print(f"\n✅ System ready for live trading!")
    else:
        print(f"⚠️ Some tasks failed. Check errors above.")
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
