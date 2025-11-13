"""
ICICI Breeze WebSocket Data Collector
- Downloads historical 1-min and 5-min data for specific date
- Maintains live feed with 1-minute OHLC updates
- Aggregates 5-min → 15-min → 1-hour data automatically
- Saves to respective SQLite databases
"""

import asyncio
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from breeze_connect import BreezeConnect
import os
from dotenv import load_dotenv
import time as time_module
import logging
from logging.handlers import RotatingFileHandler

# Setup logging with file rotation
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler with UTF-8 encoding
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.stream.reconfigure(encoding='utf-8')
logger.addHandler(console_handler)

# File handler with rotation (10MB max, keep 5 backups) and UTF-8 encoding
file_handler = RotatingFileHandler('websocket_data_collector.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Prevent propagation to root logger
logger.propagate = False

class NiftyDataCollector:
    def __init__(self):
        """Initialize the data collector"""
        load_dotenv()
        
        self.api_key = os.getenv('ICICI_API_KEY')
        self.api_secret = os.getenv('ICICI_API_SECRET')
        self.session_token = os.getenv('ICICI_SESSION_TOKEN')
        
        # Database paths
        self.db_1min = 'NIFTY_1min_data.db'
        self.db_5min = 'NIFTY_5min_data.db'
        self.db_15min = 'NIFTY_15min_data.db'
        self.db_1hour = 'NIFTY_1hour_data.db'
        self.db_1day = 'NIFTY_1day_data.db'
        
        # Initialize Breeze connection
        self.breeze = BreezeConnect(api_key=self.api_key)
        
        logger.info("✅ NiftyDataCollector initialized")
    
    def connect_to_breeze(self):
        """Connect to ICICI Breeze API"""
        try:
            self.breeze.generate_session(
                api_secret=self.api_secret,
                session_token=self.session_token
            )
            logger.info("✅ Connected to ICICI Breeze API")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Breeze: {e}")
            return False
    
    def create_database_tables(self):
        """Create tables in all databases if they don't exist"""
        databases = [
            (self.db_1min, 'data_1min'),
            (self.db_5min, 'data_5min'),
            (self.db_15min, 'data_15min'),
            (self.db_1hour, 'data_1hour'),
            (self.db_1day, 'data_1day')
        ]
        
        for db_path, table_name in databases:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    datetime TEXT PRIMARY KEY,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER
                )
            ''')
            
            # Create index on datetime
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_datetime ON {table_name}(datetime)')
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Database ready: {db_path} ({table_name})")
    
    def save_to_database(self, df, db_path, table_name):
        """Save dataframe to database, avoiding duplicates"""
        if df.empty:
            logger.warning(f"⚠️ Empty dataframe, skipping save to {db_path}")
            return
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Insert each row, using INSERT OR REPLACE to handle duplicates
            inserted = 0
            updated = 0
            skipped = 0
            
            for _, row in df.iterrows():
                # FILTER: Only allow market hours (9:15 AM - 3:30 PM)
                dt_str = row['datetime']
                try:
                    dt = pd.to_datetime(dt_str)
                    hour = dt.hour
                    minute = dt.minute
                    
                    # Skip if before 9:15 AM or after 3:30 PM
                    if hour < 9 or (hour == 9 and minute < 15):
                        skipped += 1
                        continue
                    if hour > 15 or (hour == 15 and minute > 30):
                        skipped += 1
                        continue
                except:
                    pass  # If parsing fails, proceed anyway
                
                # Check if datetime already exists
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE datetime = ?", (row['datetime'],))
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # Replace existing record
                    cursor.execute(f"""
                        REPLACE INTO {table_name} (datetime, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (row['datetime'], row['open'], row['high'], row['low'], row['close'], row['volume']))
                    updated += 1
                else:
                    # Insert new record
                    cursor.execute(f"""
                        INSERT INTO {table_name} (datetime, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (row['datetime'], row['open'], row['high'], row['low'], row['close'], row['volume']))
                    inserted += 1
            
            conn.commit()
            conn.close()
            
            if skipped > 0:
                logger.info(f"✅ Saved to {db_path}: {inserted} new, {updated} updated, {skipped} skipped (outside market hours)")
            elif updated > 0:
                logger.info(f"✅ Saved to {db_path}: {inserted} new, {updated} updated")
            else:
                logger.info(f"✅ Saved {len(df)} rows to {db_path}")
                
        except Exception as e:
            logger.error(f"❌ Error saving to {db_path}: {e}")
    
    def download_historical_data(self, date_str, interval):
        """Download historical data for a specific date and interval"""
        try:
            # Parse date
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Set time range for the day
            from_datetime = target_date.replace(hour=9, minute=15)
            to_datetime = target_date.replace(hour=15, minute=30)
            
            logger.info(f"📥 Downloading {interval} data for {date_str}...")
            
            # Fetch historical data using correct parameters
            data = self.breeze.get_historical_data_v2(
                interval=interval,
                from_date=from_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                to_date=to_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                stock_code="NIFTY",
                exchange_code="NSE",
                product_type="cash",
                expiry_date="",
                right="",
                strike_price=""
            )
            
            if data and 'Success' in data:
                records = data['Success']
                
                if not records or len(records) == 0:
                    logger.warning(f"⚠️ No records in response for {date_str} {interval}")
                    return pd.DataFrame()
                
                # Convert to dataframe
                df = pd.DataFrame(records)
                
                logger.info(f"✅ Downloaded {len(df)} {interval} candles for {date_str}")
                logger.debug(f"Columns: {df.columns.tolist()}")
                
                # Select and rename columns
                if 'datetime' in df.columns:
                    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
                else:
                    logger.error(f"❌ Missing datetime column in response")
                    return pd.DataFrame()
                
                return df
            else:
                logger.warning(f"⚠️ No data returned for {date_str} {interval}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Error downloading historical data: {e}")
            return pd.DataFrame()
    
    def aggregate_5min_to_15min(self, df_5min):
        """Aggregate 5-minute data to 15-minute candles"""
        if df_5min.empty:
            return pd.DataFrame()
        
        try:
            df = df_5min.copy()
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
            
            # Resample to 15-minute intervals
            df_15min = df.resample('15T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            df_15min = df_15min.reset_index()
            df_15min['datetime'] = df_15min['datetime'].astype(str)
            
            logger.info(f"✅ Aggregated {len(df_5min)} → {len(df_15min)} (5min → 15min)")
            return df_15min
            
        except Exception as e:
            logger.error(f"❌ Error aggregating to 15min: {e}")
            return pd.DataFrame()
    
    def aggregate_15min_to_1hour(self, df_15min):
        """Aggregate 15-minute data to 1-hour candles"""
        if df_15min.empty:
            return pd.DataFrame()
        
        try:
            df = df_15min.copy()
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
            
            # Resample to 1-hour intervals
            df_1hour = df.resample('1H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            df_1hour = df_1hour.reset_index()
            df_1hour['datetime'] = df_1hour['datetime'].astype(str)
            
            logger.info(f"✅ Aggregated {len(df_15min)} → {len(df_1hour)} (15min → 1hour)")
            return df_1hour
            
        except Exception as e:
            logger.error(f"❌ Error aggregating to 1hour: {e}")
            return pd.DataFrame()
    
    def download_last_n_days_data(self, days=10):
        """Download last N days of data in batches for all timeframes"""
        try:
            today = datetime.now().date()
            current_time = datetime.now()
            
            # CLEAR ALL DATABASES FIRST
            if days > 100:  # Only clear if downloading large historical data
                logger.info(f"\n{'='*80}")
                logger.info(f"🗑️  CLEARING ALL DATABASES")
                logger.info(f"{'='*80}\n")
                
                for db_path, table_name in [
                    (self.db_5min, 'data_5min'),
                    (self.db_15min, 'data_15min'),
                    (self.db_1hour, 'data_1hour'),
                    (self.db_1day, 'data_1day')
                ]:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM {table_name}")
                    conn.commit()
                    count = cursor.rowcount
                    conn.close()
                    logger.info(f"✅ Cleared {table_name}: {count} records deleted")
            
            # =====================================================================
            # DOWNLOAD 5-MINUTE DATA
            # =====================================================================
            logger.info(f"\n{'='*80}")
            logger.info(f"📥 DOWNLOADING 5-MINUTE DATA (LAST {days} DAYS)")
            logger.info(f"{'='*80}\n")
            
            batch_days = 17  # Days per batch for 5-min data
            num_batches = (days + batch_days - 1) // batch_days
            
            all_5min_data = []
            
            for batch_num in range(num_batches):
                batch_end_days = batch_num * batch_days
                batch_start_days = min((batch_num + 1) * batch_days, days)
                
                from_date = today - timedelta(days=batch_start_days)
                to_date = today - timedelta(days=batch_end_days)
                
                from_datetime = datetime.combine(from_date, time(9, 15))
                to_datetime = datetime.combine(to_date, time(15, 30))
                
                logger.info(f"📦 Batch {batch_num + 1}/{num_batches}: {from_date} to {to_date}")
                
                try:
                    data_5min = self.breeze.get_historical_data_v2(
                        interval="5minute",
                        from_date=from_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                        to_date=to_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                        stock_code="NIFTY",
                        exchange_code="NSE",
                        product_type="cash",
                        expiry_date="",
                        right="",
                        strike_price=""
                    )
                    
                    if data_5min and 'Success' in data_5min and len(data_5min['Success']) > 0:
                        df_batch = pd.DataFrame(data_5min['Success'])
                        if 'datetime' in df_batch.columns:
                            df_batch = df_batch[['datetime', 'open', 'high', 'low', 'close', 'volume']]
                            logger.info(f"   ✅ Downloaded {len(df_batch)} candles")
                            all_5min_data.append(df_batch)
                    
                    time_module.sleep(1)
                    
                except Exception as e:
                    logger.error(f"   ❌ Error: {e}")
            
            # Save 5-min data
            if all_5min_data:
                df_5min = pd.concat(all_5min_data, ignore_index=True)
                df_5min['datetime'] = pd.to_datetime(df_5min['datetime'])
                df_5min = df_5min.drop_duplicates(subset=['datetime']).sort_values('datetime')
                df_5min['datetime'] = df_5min['datetime'].astype(str)
                
                logger.info(f"\n✅ Total 5-min candles: {len(df_5min)}")
                self.save_to_database(df_5min, self.db_5min, 'data_5min')
                
                # Aggregate to 15-min
                df_15min = self.aggregate_5min_to_15min(df_5min)
                if not df_15min.empty:
                    logger.info(f"✅ Aggregated to {len(df_15min)} 15-min candles")
                    self.save_to_database(df_15min, self.db_15min, 'data_15min')
            
            # =====================================================================
            # DOWNLOAD 1-HOUR DATA DIRECTLY FROM API
            # =====================================================================
            logger.info(f"\n{'='*80}")
            logger.info(f"📥 DOWNLOADING 1-HOUR DATA (LAST {days} DAYS)")
            logger.info(f"{'='*80}\n")
            
            # 1-hour: 1000 candles = ~167 days (6 hours per day)
            hour_batch_days = 167
            hour_num_batches = (days + hour_batch_days - 1) // hour_batch_days
            
            all_1hour_data = []
            
            for batch_num in range(hour_num_batches):
                batch_end_days = batch_num * hour_batch_days
                batch_start_days = min((batch_num + 1) * hour_batch_days, days)
                
                from_date = today - timedelta(days=batch_start_days)
                to_date = today - timedelta(days=batch_end_days)
                
                from_datetime = datetime.combine(from_date, time(9, 15))
                to_datetime = datetime.combine(to_date, time(15, 30))
                
                logger.info(f"📦 Batch {batch_num + 1}/{hour_num_batches}: {from_date} to {to_date}")
                
                try:
                    data_1hour = self.breeze.get_historical_data_v2(
                        interval="1hour",
                        from_date=from_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                        to_date=to_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                        stock_code="NIFTY",
                        exchange_code="NSE",
                        product_type="cash",
                        expiry_date="",
                        right="",
                        strike_price=""
                    )
                    
                    if data_1hour and 'Success' in data_1hour and len(data_1hour['Success']) > 0:
                        df_batch = pd.DataFrame(data_1hour['Success'])
                        if 'datetime' in df_batch.columns:
                            df_batch = df_batch[['datetime', 'open', 'high', 'low', 'close', 'volume']]
                            logger.info(f"   ✅ Downloaded {len(df_batch)} candles")
                            all_1hour_data.append(df_batch)
                    
                    time_module.sleep(1)
                    
                except Exception as e:
                    logger.error(f"   ❌ Error: {e}")
            
            # Save 1-hour data
            if all_1hour_data:
                df_1hour = pd.concat(all_1hour_data, ignore_index=True)
                df_1hour['datetime'] = pd.to_datetime(df_1hour['datetime'])
                df_1hour = df_1hour.drop_duplicates(subset=['datetime']).sort_values('datetime')
                df_1hour['datetime'] = df_1hour['datetime'].astype(str)
                
                logger.info(f"\n✅ Total 1-hour candles: {len(df_1hour)}")
                self.save_to_database(df_1hour, self.db_1hour, 'data_1hour')
            
            # =====================================================================
            # DOWNLOAD 1-DAY DATA DIRECTLY FROM API
            # =====================================================================
            logger.info(f"\n{'='*80}")
            logger.info(f"📥 DOWNLOADING 1-DAY DATA (LAST {days} DAYS)")
            logger.info(f"{'='*80}\n")
            
            # Daily data: can download all 1095 days in one batch (< 1000 candles)
            from_date = today - timedelta(days=days)
            to_date = today
            
            from_datetime = datetime.combine(from_date, time(9, 15))
            to_datetime = datetime.combine(to_date, time(15, 30))
            
            logger.info(f"� Single batch: {from_date} to {to_date}")
            
            try:
                data_1day = self.breeze.get_historical_data_v2(
                    interval="1day",
                    from_date=from_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    to_date=to_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    stock_code="NIFTY",
                    exchange_code="NSE",
                    product_type="cash",
                    expiry_date="",
                    right="",
                    strike_price=""
                )
                
                if data_1day and 'Success' in data_1day and len(data_1day['Success']) > 0:
                    df_1day = pd.DataFrame(data_1day['Success'])
                    if 'datetime' in df_1day.columns:
                        df_1day = df_1day[['datetime', 'open', 'high', 'low', 'close', 'volume']]
                        df_1day['datetime'] = pd.to_datetime(df_1day['datetime'])
                        df_1day = df_1day.drop_duplicates(subset=['datetime']).sort_values('datetime')
                        df_1day['datetime'] = df_1day['datetime'].astype(str)
                        
                        logger.info(f"   ✅ Downloaded {len(df_1day)} candles")
                        self.save_to_database(df_1day, self.db_1day, 'data_1day')
                
            except Exception as e:
                logger.info(f"   ❌ Error: {e}")
            
            logger.info(f"\n{'='*80}")
            logger.info("✅ ALL HISTORICAL DATA DOWNLOADED!")
            logger.info(f"{'='*80}\n")
                
        except Exception as e:
            logger.error(f"❌ Error in download_last_n_days_data: {e}")
            import traceback
            traceback.print_exc()
    
    def download_todays_historical_data(self):
        """Download today's data from 9:15 AM till current time"""
        try:
            today = datetime.now().date()
            current_time = datetime.now()
            
            # Start from 9:15 AM today
            from_datetime = datetime.combine(today, time(9, 15))
            
            # If current time is before 9:15 AM, no data to download
            if current_time < from_datetime:
                logger.info("⏰ Market not yet opened. No historical data to download.")
                return pd.DataFrame(), pd.DataFrame()
            
            to_datetime = current_time
            
            logger.info(f"📥 Downloading today's data from {from_datetime.strftime('%H:%M')} to {to_datetime.strftime('%H:%M')}...")
            
            # Download 1-minute data
            logger.info("📊 Downloading 1-minute data for today...")
            data_1min = self.breeze.get_historical_data_v2(
                interval="1minute",
                from_date=from_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                to_date=to_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                stock_code="NIFTY",
                exchange_code="NSE",
                product_type="cash",
                expiry_date="",
                right="",
                strike_price=""
            )
            
            df_1min = pd.DataFrame()
            if data_1min and 'Success' in data_1min and len(data_1min['Success']) > 0:
                df_1min = pd.DataFrame(data_1min['Success'])
                if 'datetime' in df_1min.columns:
                    df_1min = df_1min[['datetime', 'open', 'high', 'low', 'close', 'volume']]
                    logger.info(f"✅ Downloaded {len(df_1min)} 1-minute candles for today")
            
            # Download 5-minute data
            logger.info("📊 Downloading 5-minute data for today...")
            data_5min = self.breeze.get_historical_data_v2(
                interval="5minute",
                from_date=from_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                to_date=to_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                stock_code="NIFTY",
                exchange_code="NSE",
                product_type="cash",
                expiry_date="",
                right="",
                strike_price=""
            )
            
            df_5min = pd.DataFrame()
            if data_5min and 'Success' in data_5min and len(data_5min['Success']) > 0:
                df_5min = pd.DataFrame(data_5min['Success'])
                if 'datetime' in df_5min.columns:
                    df_5min = df_5min[['datetime', 'open', 'high', 'low', 'close', 'volume']]
                    logger.info(f"✅ Downloaded {len(df_5min)} 5-minute candles for today")
            
            return df_1min, df_5min
            
        except Exception as e:
            logger.error(f"❌ Error downloading today's historical data: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def aggregate_to_daily(self, df_1min, date_str):
        """Aggregate 1-minute data to daily candle"""
        if df_1min.empty:
            return pd.DataFrame()
        
        try:
            df = df_1min.copy()
            
            # Create daily candle from all 1-minute candles
            daily_candle = {
                'datetime': date_str,
                'open': df['open'].iloc[0],
                'high': df['high'].max(),
                'low': df['low'].min(),
                'close': df['close'].iloc[-1],
                'volume': df['volume'].sum()
            }
            
            df_daily = pd.DataFrame([daily_candle])
            
            logger.info(f"✅ Aggregated {len(df_1min)} 1-min candles → 1 daily candle")
            return df_daily
            
        except Exception as e:
            logger.error(f"❌ Error aggregating to daily: {e}")
            return pd.DataFrame()
    
    def download_and_save_historical(self, date_str='2025-10-27'):
        """Download historical data for specified date and save to databases"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📥 DOWNLOADING HISTORICAL DATA FOR {date_str}")
        logger.info(f"{'='*80}\n")
        
        # Download 1-minute data
        logger.info("📊 Step 1: Downloading 1-minute data...")
        df_1min = self.download_historical_data(date_str, '1minute')
        if not df_1min.empty:
            self.save_to_database(df_1min, self.db_1min, 'data_1min')
            
            # Aggregate to daily
            logger.info("\n📊 Step 2: Aggregating 1-min → Daily...")
            df_daily = self.aggregate_to_daily(df_1min, date_str)
            if not df_daily.empty:
                self.save_to_database(df_daily, self.db_1day, 'data_1day')
        
        # Download 5-minute data
        logger.info("\n📊 Step 3: Downloading 5-minute data...")
        df_5min = self.download_historical_data(date_str, '5minute')
        if not df_5min.empty:
            self.save_to_database(df_5min, self.db_5min, 'data_5min')
            
            # Aggregate to 15-minute
            logger.info("\n📊 Step 4: Aggregating 5-min → 15-min...")
            df_15min = self.aggregate_5min_to_15min(df_5min)
            if not df_15min.empty:
                self.save_to_database(df_15min, self.db_15min, 'data_15min')
                
                # Aggregate to 1-hour
                logger.info("\n📊 Step 5: Aggregating 15-min → 1-hour...")
                df_1hour = self.aggregate_15min_to_1hour(df_15min)
                if not df_1hour.empty:
                    self.save_to_database(df_1hour, self.db_1hour, 'data_1hour')
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ HISTORICAL DATA DOWNLOAD COMPLETE")
        logger.info(f"{'='*80}\n")
    
    def get_live_quote(self):
        """Get live quote for NIFTY"""
        try:
            quote = self.breeze.get_quotes(
                stock_code="NIFTY",
                exchange_code="NSE",
                expiry_date="",
                product_type="cash",
                right="",
                strike_price=""
            )
            
            if quote and 'Success' in quote:
                return quote['Success'][0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting live quote: {e}")
            return None
    
    def create_1min_candle_from_quote(self, quote, timestamp):
        """Create a 1-minute OHLC candle from quote data"""
        try:
            price = float(quote.get('ltp', 0))
            
            # For live data, we use LTP as all OHLC values
            # In production, you'd accumulate ticks within the minute
            candle = {
                'datetime': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': int(quote.get('volume', 0))
            }
            
            return pd.DataFrame([candle])
            
        except Exception as e:
            logger.error(f"❌ Error creating candle: {e}")
            return pd.DataFrame()
    
    def clean_duplicates_for_datetime(self, db_file, table_name, datetime_value):
        """Remove duplicates for a specific datetime, keeping only the first entry"""
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Delete duplicates, keep only the first (MIN rowid)
            cursor.execute(f"""
                DELETE FROM {table_name}
                WHERE datetime = ?
                AND rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM {table_name}
                    WHERE datetime = ?
                )
            """, (datetime_value, datetime_value))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted > 0:
                logger.info(f"🧹 Cleaned {deleted} duplicate(s) for {datetime_value}")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning duplicates: {e}")
    
    def aggregate_buffer_to_timeframe(self, buffer, minutes):
        """Aggregate buffer data to specific timeframe"""
        if len(buffer) < (minutes // 1):  # Not enough data
            return None
        
        try:
            df = pd.DataFrame(buffer[-minutes:])
            
            # Use FIRST candle's timestamp as the aggregated candle timestamp
            # This represents the START of the period
            candle_timestamp = df['datetime'].iloc[0]
            
            candle = {
                'datetime': candle_timestamp,
                'open': df['open'].iloc[0],
                'high': df['high'].max(),
                'low': df['low'].min(),
                'close': df['close'].iloc[-1],
                'volume': df['volume'].sum()
            }
            
            return pd.DataFrame([candle])
            
        except Exception as e:
            logger.error(f"❌ Error aggregating buffer: {e}")
            return None
    
    def aggregate_recent_1min_to_5min(self, current_time):
        """Aggregate last 5 minutes of 1-min data to 5-min candle"""
        try:
            # For 5-min candle at 9:30, we want data from 9:25 to 9:29 (not including 9:30)
            # The candle is labeled with the start time (9:25)
            end_time = current_time - timedelta(minutes=1)  # Up to previous minute
            start_time = current_time - timedelta(minutes=5)
            
            # Fetch 5 minutes of 1-min data
            conn = sqlite3.connect(self.db_1min)
            query = f"SELECT * FROM data_1min WHERE datetime >= ? AND datetime <= ? ORDER BY datetime"
            df = pd.read_sql_query(query, conn, params=(start_time.strftime('%Y-%m-%d %H:%M:%S'), 
                                                         end_time.strftime('%Y-%m-%d %H:%M:%S')))
            conn.close()
            
            if len(df) == 0:
                return
            
            # Create 5-min candle with timestamp = start of period
            candle = {
                'datetime': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'open': df['open'].iloc[0],
                'high': df['high'].max(),
                'low': df['low'].min(),
                'close': df['close'].iloc[-1],
                'volume': df['volume'].sum()
            }
            
            df_5min = pd.DataFrame([candle])
            self.save_to_database(df_5min, self.db_5min, 'data_5min')
            logger.info(f"📊 5-min candle: {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}")
            
        except Exception as e:
            logger.error(f"❌ Error aggregating 1min→5min: {e}")
    
    def aggregate_recent_5min_to_15min(self, current_time):
        """Aggregate last 15 minutes of 5-min data to 15-min candle"""
        try:
            # For 15-min candle at 12:30, we aggregate 12:15, 12:20, 12:25 (3 candles)
            # The candle is labeled with start time (12:15 for 12:15-12:29 period)
            # Since we run at X:30:30, the 12:30 5-min candle will be written but shouldn't be included
            # We want data from (current_time - 15min) to (current_time - 1min)
            
            end_time = current_time - timedelta(minutes=1)  # Up to previous minute (12:29 at 12:30)
            start_time = current_time - timedelta(minutes=15)  # Start 15 min ago (12:15 at 12:30)
            
            # Fetch 15 minutes of 5-min data (should be 3 candles: 12:15, 12:20, 12:25)
            conn = sqlite3.connect(self.db_5min)
            query = f"SELECT * FROM data_5min WHERE datetime >= ? AND datetime <= ? ORDER BY datetime"
            df = pd.read_sql_query(query, conn, params=(start_time.strftime('%Y-%m-%d %H:%M:%S'), 
                                                         end_time.strftime('%Y-%m-%d %H:%M:%S')))
            conn.close()
            
            logger.info(f"🔍 Looking for 5-min data from {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}")
            logger.info(f"📊 Found {len(df)} 5-min candles for 15-min aggregation")
            
            if len(df) < 3:  # Need at least 3 x 5-min candles
                logger.warning(f"⚠️ Only {len(df)} 5-min candles, need 3 for 15-min. Skipping aggregation.")
                return
            
            # Create 15-min candle with timestamp = start of period
            candle = {
                'datetime': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'open': df['open'].iloc[0],
                'high': df['high'].max(),
                'low': df['low'].min(),
                'close': df['close'].iloc[-1],
                'volume': df['volume'].sum()
            }
            
            df_15min = pd.DataFrame([candle])
            self.save_to_database(df_15min, self.db_15min, 'data_15min')
            logger.info(f"📈 15-min candle: {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}")
            
            # Clean duplicates after aggregation
            self.clean_duplicates_for_datetime(self.db_15min, 'data_15min', start_time.strftime('%Y-%m-%d %H:%M:%S'))
            
        except Exception as e:
            logger.error(f"❌ Error aggregating 5min→15min: {e}")
    
    def aggregate_recent_15min_to_1hour(self, current_time):
        """Aggregate last 1 hour of 15-min data to 1-hour candle"""
        try:
            # Market starts at 9:15, so 1-hour boundaries are: 9:15, 10:15, 11:15, 12:15, 13:15, 14:15, 15:15
            # For candle at 10:15, aggregate data from 9:15 to 10:14 (4 x 15-min candles)
            current_hour = current_time.hour
            current_min = current_time.minute
            
            # Only create 1-hour candles at X:15 (market hour boundaries)
            if current_min != 15:
                return
            
            # Start time is exactly 1 hour before (e.g., 10:15 -> 9:15)
            start_time = current_time - timedelta(hours=1)
            end_time = current_time - timedelta(minutes=1)  # Up to X:14
            
            # Fetch 60 minutes of 15-min data (should be 4 candles: X:15, X:30, X:45, X:00)
            conn = sqlite3.connect(self.db_15min)
            query = f"SELECT * FROM data_15min WHERE datetime >= ? AND datetime <= ? ORDER BY datetime"
            df = pd.read_sql_query(query, conn, params=(start_time.strftime('%Y-%m-%d %H:%M:%S'), 
                                                         end_time.strftime('%Y-%m-%d %H:%M:%S')))
            conn.close()
            
            if len(df) < 4:  # Need at least 4 x 15-min candles
                logger.debug(f"⚠️ Only {len(df)} 15-min candles for {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}, need 4 for 1-hour")
                return
            
            # Create 1-hour candle with timestamp = start time (e.g., 9:15 for 9:15-10:14 period)
            candle = {
                'datetime': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'open': df['open'].iloc[0],
                'high': df['high'].max(),
                'low': df['low'].min(),
                'close': df['close'].iloc[-1],
                'volume': df['volume'].sum()
            }
            
            df_1hour = pd.DataFrame([candle])
            self.save_to_database(df_1hour, self.db_1hour, 'data_1hour')
            logger.info(f"🕐 1-hour candle: {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}")
            
        except Exception as e:
            logger.error(f"❌ Error aggregating 15min→1hour: {e}")
    
    async def start_live_feed(self):
        """Start live data feed - fetches 5-min candles with 5-second delay"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔴 STARTING LIVE FEED (5-minute intervals with 3s delay for real-time trading)")
        logger.info(f"{'='*80}\n")
        
        last_5min = None
        
        while True:
            try:
                now = datetime.now()
                
                # Check if it's market hours (9:15 AM to 3:30 PM)
                market_open = time(9, 15)
                market_close = time(15, 30)
                current_time = now.time()
                
                if not (market_open <= current_time <= market_close):
                    await asyncio.sleep(60)  # Check every minute outside market hours
                    continue
                
                # Check if we're at a 5-minute boundary + 3 seconds for real-time trading
                # e.g., 9:15:03, 9:20:03, 9:25:03, etc.
                current_minute = now.minute
                current_second = now.second
                
                # 5-minute boundaries: 15, 20, 25, 30, 35, 40, 45, 50, 55, 00, 05, 10
                is_5min_boundary = (current_minute % 5 == 0) and (current_second == 3)
                
                if is_5min_boundary:
                    # Round to the 5-minute mark (remove the 3 seconds)
                    current_5min = now.replace(second=0, microsecond=0)
                    
                    # Avoid duplicate processing
                    if current_5min == last_5min:
                        await asyncio.sleep(1)
                        continue
                    
                    last_5min = current_5min
                    
                    logger.info(f"\n⏰ {current_5min.strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info(f"⏱️  Fetching 5-min candle (3-second delay for real-time trading)...")
                    
                    # The candle we want is the CURRENT completed 5-minute period
                    # At 14:15:03, we want the 14:15 candle that just completed
                    candle_time = current_5min
                    
                    # Download the just-completed 5-minute candle from API
                    from_datetime = candle_time
                    to_datetime = current_5min + timedelta(minutes=5) - timedelta(seconds=1)  # Up to end of candle
                    
                    try:
                        data = self.breeze.get_historical_data_v2(
                            interval="5minute",
                            from_date=from_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                            to_date=to_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                            stock_code="NIFTY",
                            exchange_code="NSE",
                            product_type="cash",
                            expiry_date="",
                            right="",
                            strike_price=""
                        )
                        
                        if data and 'Success' in data and len(data['Success']) > 0:
                            df_5min = pd.DataFrame(data['Success'])
                            if 'datetime' in df_5min.columns:
                                df_5min = df_5min[['datetime', 'open', 'high', 'low', 'close', 'volume']]
                                # Take only the last candle (most recent)
                                df_5min = df_5min.tail(1)
                                
                                logger.info(f"✅ Fetched 5-min candle for {candle_time.strftime('%H:%M')}")
                                logger.info(f"   O:{df_5min['open'].iloc[0]:.2f} H:{df_5min['high'].iloc[0]:.2f} L:{df_5min['low'].iloc[0]:.2f} C:{df_5min['close'].iloc[0]:.2f}")
                                
                                # Save to 5-min database
                                self.save_to_database(df_5min, self.db_5min, 'data_5min')
                                
                                # Clean duplicates for this specific candle
                                self.clean_duplicates_for_datetime(self.db_5min, 'data_5min', candle_time.strftime('%Y-%m-%d %H:%M:%S'))
                                
                                # Aggregate to 15-min at 15-minute boundaries (X:00, X:15, X:30, X:45)
                                # At 9:30:30, aggregate 9:15, 9:20, 9:25 → create 9:15 15-min candle
                                if current_minute in [0, 15, 30, 45]:
                                    logger.info(f"📊 Aggregating to 15-minute...")
                                    self.aggregate_recent_5min_to_15min(current_5min)
                                    
                                    # Aggregate to 1-hour at hour boundaries (X:15)
                                    if current_minute == 15:
                                        logger.info(f"🕐 Aggregating to 1-hour...")
                                        self.aggregate_recent_15min_to_1hour(current_5min)
                        else:
                            logger.warning(f"⚠️ No data returned for {candle_time.strftime('%H:%M')}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error fetching 5-min data: {e}")
                
                # Sleep until next second
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error in live feed: {e}")
                await asyncio.sleep(60)
    
    async def run(self, download_last_n_days=10, start_live=True):
        """Main run method"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 NIFTY DATA COLLECTOR")
        logger.info(f"{'='*80}\n")
        
        # Connect to Breeze
        if not self.connect_to_breeze():
            logger.error("❌ Failed to connect. Exiting...")
            return
        
        # Create database tables
        self.create_database_tables()
        
        # Check if we have recent data (data from today)
        conn = sqlite3.connect(self.db_5min)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM data_5min WHERE date(datetime) = date('now', 'localtime')")
        today_count = cursor.fetchone()[0]
        conn.close()
        
        # Only download if explicitly requested AND we don't have today's data
        if download_last_n_days > 0 and today_count == 0:
            logger.info(f"\n{'='*60}")
            logger.info(f"STEP 1: Downloading Last {download_last_n_days} Days Historical Data")
            logger.info(f"{'='*60}\n")
            self.download_last_n_days_data(days=download_last_n_days)
        elif today_count > 0:
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ EXISTING DATA FOUND: {today_count} 5-min candles for today")
            logger.info(f"📊 Skipping download, will use live feed to update")
            logger.info(f"{'='*60}\n")
        
        # Step 2: Start live feed if requested
        if start_live:
            logger.info(f"\n{'='*60}")
            logger.info(f"STEP 2: Starting Live Feed with 30-second delay")
            logger.info(f"{'='*60}\n")
            await self.start_live_feed()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ DATA COLLECTOR STOPPED")
        logger.info(f"{'='*80}\n")

# Main execution
async def main():
    collector = NiftyDataCollector()
    
    # Only today's data + live feed
    await collector.run(download_last_n_days=1, start_live=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        # Ensure any uncaught exceptions are logged and process exits non-zero
        logger.error("❌ Unhandled exception in websocket_data_collector main", exc_info=True)
        import traceback, sys
        logger.error(traceback.format_exc())
        sys.exit(1)
