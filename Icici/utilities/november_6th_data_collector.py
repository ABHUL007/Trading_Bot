#!/usr/bin/env python3
"""
NOVEMBER 6TH DATA COLLECTOR WITH DUPLICATE REMOVAL
==================================================
- Downloads November 6th, 2025 5-minute data via websocket
- Saves to database with duplicate removal
- Aggregates to 15-min, 1-hour, and daily timeframes
- Comprehensive data cleaning and validation
"""

import asyncio
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from websocket_data_collector import NiftyDataCollector
import logging
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class November6thDataProcessor:
    def __init__(self):
        """Initialize the November 6th data processor"""
        self.collector = NiftyDataCollector()
        self.target_date = '2025-11-06'
        
        # Database paths
        self.db_5min = 'NIFTY_5min_data.db'
        self.db_15min = 'NIFTY_15min_data.db'
        self.db_1hour = 'NIFTY_1hour_data.db'
        self.db_1day = 'NIFTY_1day_data.db'
        
        logger.info("✅ November 6th Data Processor initialized")
    
    def connect_and_setup(self):
        """Connect to API and setup databases"""
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP 1: Connecting to ICICI Breeze API")
        logger.info(f"{'='*60}")
        
        if not self.collector.connect_to_breeze():
            logger.error("❌ Failed to connect to Breeze API")
            return False
        
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP 2: Setting up databases")
        logger.info(f"{'='*60}")
        
        self.collector.create_database_tables()
        return True
    
    def remove_duplicates_from_db(self, db_path, table_name):
        """Remove duplicate entries from database"""
        logger.info(f"🧹 Removing duplicates from {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count duplicates before removal
        cursor.execute(f"""
            SELECT datetime, COUNT(*) as count 
            FROM {table_name} 
            GROUP BY datetime 
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            logger.info(f"   Found {len(duplicates)} duplicate datetime entries")
            
            # Remove duplicates, keeping only the first occurrence
            cursor.execute(f"""
                DELETE FROM {table_name} 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) 
                    FROM {table_name} 
                    GROUP BY datetime
                )
            """)
            
            removed_count = cursor.rowcount
            logger.info(f"   ✅ Removed {removed_count} duplicate records")
        else:
            logger.info(f"   ✅ No duplicates found")
        
        # Get final count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        final_count = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        logger.info(f"   📊 Final record count: {final_count}")
        return final_count
    
    def download_november_6th_data(self):
        """Download November 6th 5-minute data"""
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP 3: Downloading November 6th, 2025 Data")
        logger.info(f"{'='*60}")
        
        try:
            # Download 5-minute data for November 6th
            df_5min = self.collector.download_historical_data(self.target_date, '5minute')
            
            if df_5min is not None and not df_5min.empty:
                logger.info(f"✅ Downloaded {len(df_5min)} 5-minute candles")
                
                # Save to database
                self.collector.save_to_database(df_5min, self.db_5min, 'data_5min')
                
                # Remove duplicates
                self.remove_duplicates_from_db(self.db_5min, 'data_5min')
                
                return True
            else:
                logger.error("❌ No data received for November 6th")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error downloading November 6th data: {e}")
            return False
    
    def aggregate_to_15min(self):
        """Aggregate 5-min data to 15-min"""
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP 4: Aggregating to 15-minute timeframe")
        logger.info(f"{'='*60}")
        
        try:
            # Read 5-min data for November 6th
            conn = sqlite3.connect(self.db_5min)
            query = f"""
                SELECT * FROM data_5min 
                WHERE datetime LIKE '{self.target_date}%' 
                ORDER BY datetime
            """
            df_5min = pd.read_sql_query(query, conn)
            conn.close()
            
            if df_5min.empty:
                logger.error("❌ No 5-minute data found for aggregation")
                return False
            
            # Convert datetime and set as index
            df_5min['datetime'] = pd.to_datetime(df_5min['datetime'])
            df_5min.set_index('datetime', inplace=True)
            
            # Aggregate to 15-minute OHLCV
            df_15min = df_5min.resample('15T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # Reset index and format datetime
            df_15min.reset_index(inplace=True)
            df_15min['datetime'] = df_15min['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"✅ Aggregated {len(df_5min)} → {len(df_15min)} candles (5min → 15min)")
            
            # Save to database
            self.collector.save_to_database(df_15min, self.db_15min, 'data_15min')
            
            # Remove duplicates
            self.remove_duplicates_from_db(self.db_15min, 'data_15min')
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error aggregating to 15-min: {e}")
            return False
    
    def aggregate_to_1hour(self):
        """Aggregate 15-min data to 1-hour"""
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP 5: Aggregating to 1-hour timeframe")
        logger.info(f"{'='*60}")
        
        try:
            # Read 15-min data for November 6th
            conn = sqlite3.connect(self.db_15min)
            query = f"""
                SELECT * FROM data_15min 
                WHERE datetime LIKE '{self.target_date}%' 
                ORDER BY datetime
            """
            df_15min = pd.read_sql_query(query, conn)
            conn.close()
            
            if df_15min.empty:
                logger.error("❌ No 15-minute data found for aggregation")
                return False
            
            # Convert datetime and set as index
            df_15min['datetime'] = pd.to_datetime(df_15min['datetime'])
            df_15min.set_index('datetime', inplace=True)
            
            # Aggregate to 1-hour OHLCV
            df_1hour = df_15min.resample('1H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # Reset index and format datetime
            df_1hour.reset_index(inplace=True)
            df_1hour['datetime'] = df_1hour['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"✅ Aggregated {len(df_15min)} → {len(df_1hour)} candles (15min → 1hour)")
            
            # Save to database
            self.collector.save_to_database(df_1hour, self.db_1hour, 'data_1hour')
            
            # Remove duplicates
            self.remove_duplicates_from_db(self.db_1hour, 'data_1hour')
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error aggregating to 1-hour: {e}")
            return False
    
    def create_daily_data(self):
        """Create daily data from 1-hour data"""
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP 6: Creating daily data")
        logger.info(f"{'='*60}")
        
        try:
            # Read 1-hour data for November 6th
            conn = sqlite3.connect(self.db_1hour)
            query = f"""
                SELECT * FROM data_1hour 
                WHERE datetime LIKE '{self.target_date}%' 
                ORDER BY datetime
            """
            df_1hour = pd.read_sql_query(query, conn)
            conn.close()
            
            if df_1hour.empty:
                logger.error("❌ No 1-hour data found for daily aggregation")
                return False
            
            # Convert datetime and set as index
            df_1hour['datetime'] = pd.to_datetime(df_1hour['datetime'])
            df_1hour.set_index('datetime', inplace=True)
            
            # Aggregate to daily OHLCV
            df_1day = df_1hour.resample('1D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # Reset index and format datetime
            df_1day.reset_index(inplace=True)
            df_1day['datetime'] = df_1day['datetime'].dt.strftime('%Y-%m-%d')
            
            logger.info(f"✅ Created daily data: {len(df_1day)} day(s)")
            logger.info(f"   📊 November 6th Summary:")
            if len(df_1day) > 0:
                day_data = df_1day.iloc[0]
                logger.info(f"      Open: ₹{day_data['open']:.2f}")
                logger.info(f"      High: ₹{day_data['high']:.2f}")
                logger.info(f"      Low: ₹{day_data['low']:.2f}")
                logger.info(f"      Close: ₹{day_data['close']:.2f}")
                logger.info(f"      Volume: {day_data['volume']:,}")
            
            # Save to database
            self.collector.save_to_database(df_1day, self.db_1day, 'data_1day')
            
            # Remove duplicates
            self.remove_duplicates_from_db(self.db_1day, 'data_1day')
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating daily data: {e}")
            return False
    
    def validate_data_integrity(self):
        """Validate data integrity across all timeframes"""
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP 7: Validating data integrity")
        logger.info(f"{'='*60}")
        
        databases = [
            (self.db_5min, 'data_5min', '5-minute'),
            (self.db_15min, 'data_15min', '15-minute'),
            (self.db_1hour, 'data_1hour', '1-hour'),
            (self.db_1day, 'data_1day', 'daily')
        ]
        
        for db_path, table_name, timeframe in databases:
            try:
                conn = sqlite3.connect(db_path)
                
                # Count records for November 6th
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE datetime LIKE '{self.target_date}%'
                """)
                count = cursor.fetchone()[0]
                
                # Get sample data
                if count > 0:
                    cursor.execute(f"""
                        SELECT datetime, open, high, low, close, volume 
                        FROM {table_name} 
                        WHERE datetime LIKE '{self.target_date}%' 
                        ORDER BY datetime 
                        LIMIT 1
                    """)
                    sample = cursor.fetchone()
                    
                    logger.info(f"✅ {timeframe:>10}: {count:>3} records | Sample: {sample[0]} O:{sample[1]:.2f} H:{sample[2]:.2f} L:{sample[3]:.2f} C:{sample[4]:.2f}")
                else:
                    logger.warning(f"⚠️ {timeframe:>10}: {count:>3} records")
                
                conn.close()
                
            except Exception as e:
                logger.error(f"❌ Error validating {timeframe}: {e}")
        
        logger.info(f"\n✅ Data integrity validation complete!")
    
    async def run_complete_collection(self):
        """Run the complete November 6th data collection process"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 STARTING NOVEMBER 6TH DATA COLLECTION WITH DUPLICATE REMOVAL")
        logger.info(f"{'='*80}")
        
        try:
            # Step 1: Connect and setup
            if not self.connect_and_setup():
                return False
            
            # Step 2: Download November 6th data
            if not self.download_november_6th_data():
                return False
            
            # Step 3: Aggregate to 15-min
            if not self.aggregate_to_15min():
                return False
            
            # Step 4: Aggregate to 1-hour
            if not self.aggregate_to_1hour():
                return False
            
            # Step 5: Create daily data
            if not self.create_daily_data():
                return False
            
            # Step 6: Validate integrity
            self.validate_data_integrity()
            
            logger.info(f"\n{'='*80}")
            logger.info(f"🎉 NOVEMBER 6TH DATA COLLECTION COMPLETED SUCCESSFULLY!")
            logger.info(f"{'='*80}")
            logger.info(f"📂 Data saved to databases:")
            logger.info(f"   • {self.db_5min} (5-minute)")
            logger.info(f"   • {self.db_15min} (15-minute)")
            logger.info(f"   • {self.db_1hour} (1-hour)")
            logger.info(f"   • {self.db_1day} (daily)")
            logger.info(f"🧹 All duplicates removed from all timeframes")
            logger.info(f"{'='*80}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fatal error during data collection: {e}")
            return False

# Main execution
async def main():
    processor = November6thDataProcessor()
    await processor.run_complete_collection()

if __name__ == "__main__":
    asyncio.run(main())