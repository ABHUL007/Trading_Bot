#!/usr/bin/env python3
"""
QUICK DAILY STARTUP - TODAY'S DATA ONLY
======================================== 
- Only checks for today's missing data
- Fast startup for daily trading
- Uses existing START_TRADING.bat
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
import subprocess
from websocket_data_collector import NiftyDataCollector
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickDailyStartup:
    def __init__(self):
        load_dotenv()
        self.today = datetime.now().date()
        self.today_str = self.today.strftime('%Y-%m-%d')
        
        logger.info("✅ Quick Daily Startup initialized")
    
    def check_todays_data_only(self):
        """Check if we have today's data"""
        logger.info(f"\n🔍 CHECKING TODAY'S DATA ({self.today_str})")
        logger.info("=" * 50)
        
        missing_today = False
        
        # Check 5-minute data for today
        try:
            if os.path.exists('NIFTY_5min_data.db'):
                conn = sqlite3.connect('NIFTY_5min_data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM data_5min WHERE datetime LIKE ?", (f"{self.today_str}%",))
                count = cursor.fetchone()[0]
                conn.close()
                
                if count == 0:
                    logger.warning(f"⚠️ No data for today ({self.today_str})")
                    missing_today = True
                else:
                    logger.info(f"✅ Today's data exists: {count} 5-min candles")
            else:
                logger.warning("⚠️ 5-min database not found")
                missing_today = True
                
        except Exception as e:
            logger.error(f"❌ Error checking today's data: {e}")
            missing_today = True
        
        return missing_today
    
    async def download_todays_data_only(self):
        """Download only today's data if missing"""
        logger.info(f"\n📥 DOWNLOADING TODAY'S DATA ({self.today_str})")
        logger.info("=" * 50)
        
        try:
            collector = NiftyDataCollector()
            
            if not collector.connect_to_breeze():
                logger.error("❌ Failed to connect to ICICI Breeze API")
                return False
            
            collector.create_database_tables()
            
            # Download today's 5-minute data
            df_5min = collector.download_historical_data(self.today_str, '5minute')
            
            if df_5min is not None and not df_5min.empty:
                logger.info(f"✅ Downloaded {len(df_5min)} candles for today")
                
                # Save and aggregate
                collector.save_to_database(df_5min, 'NIFTY_5min_data.db', 'data_5min')
                
                # Quick aggregation for today only
                df_5min_copy = df_5min.copy()
                df_5min_copy['datetime'] = pd.to_datetime(df_5min_copy['datetime'])
                df_5min_copy.set_index('datetime', inplace=True)
                
                # 15-min
                df_15min = df_5min_copy.resample('15min').agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
                }).dropna()
                df_15min.reset_index(inplace=True)
                df_15min['datetime'] = df_15min['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
                collector.save_to_database(df_15min, 'NIFTY_15min_data.db', 'data_15min')
                
                # 1-hour
                df_1hour = df_5min_copy.resample('1h').agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
                }).dropna()
                df_1hour.reset_index(inplace=True)
                df_1hour['datetime'] = df_1hour['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
                collector.save_to_database(df_1hour, 'NIFTY_1hour_data.db', 'data_1hour')
                
                logger.info("✅ Today's data updated in all timeframes")
                return True
            else:
                logger.warning("⚠️ No data available for today (market might be closed)")
                return True  # Continue anyway
                
        except Exception as e:
            logger.error(f"❌ Error downloading today's data: {e}")
            return False
    
    def start_existing_trading_system(self):
        """Start the existing START_TRADING.bat"""
        logger.info(f"\n🚀 STARTING EXISTING TRADING SYSTEM")
        logger.info("=" * 50)
        
        try:
            # Check if START_TRADING.bat exists
            if os.path.exists('START_TRADING.bat'):
                logger.info("✅ Found START_TRADING.bat - executing...")
                
                # Run START_TRADING.bat
                subprocess.Popen(['START_TRADING.bat'], shell=True)
                
                logger.info("✅ START_TRADING.bat launched successfully")
                logger.info("🔄 Trading system components are starting in separate windows")
                return True
            else:
                logger.error("❌ START_TRADING.bat not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting trading system: {e}")
            return False
    
    async def quick_startup(self):
        """Run quick daily startup"""
        logger.info(f"\n{'='*60}")
        logger.info(f"⚡ QUICK DAILY STARTUP - {self.today_str}")
        logger.info(f"{'='*60}")
        
        try:
            # Step 1: Check if we need today's data
            need_todays_data = self.check_todays_data_only()
            
            # Step 2: Download today's data if needed
            if need_todays_data:
                success = await self.download_todays_data_only()
                if not success:
                    logger.error("❌ Failed to download today's data")
                    logger.info("⚡ Continuing with startup anyway...")
            
            # Step 3: Start existing trading system
            if self.start_existing_trading_system():
                logger.info(f"\n{'='*60}")
                logger.info(f"🎉 QUICK STARTUP COMPLETED!")
                logger.info(f"🎯 Trading system is now starting...")
                logger.info(f"📊 Check the opened windows for:")
                logger.info(f"   • WebSocket Data Collector")
                logger.info(f"   • Enhanced Safe Trader") 
                logger.info(f"   • Options Data Collector")
                logger.info(f"{'='*60}")
                return True
            else:
                logger.error("❌ Failed to start trading system")
                return False
                
        except Exception as e:
            logger.error(f"❌ Quick startup failed: {e}")
            return False

async def main():
    startup = QuickDailyStartup()
    success = await startup.quick_startup()
    
    if success:
        logger.info("\n✅ Ready for trading! Keep this window open for monitoring.")
    else:
        logger.error("❌ Startup failed!")
    
    return success

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())