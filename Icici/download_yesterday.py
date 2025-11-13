#!/usr/bin/env python3
"""
Download Yesterday's Data using WebSocket Collector
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Change to parent directory for database access
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Trading_System.websocket_data_collector import NiftyDataCollector

# Get yesterday's date
yesterday = (datetime.now() - timedelta(days=1)).date()
yesterday_str = yesterday.strftime('%Y-%m-%d')

print(f"\n{'='*80}")
print(f"📅 DOWNLOADING DATA FOR: {yesterday_str} (Yesterday)")
print(f"{'='*80}\n")

# Initialize collector
collector = NiftyDataCollector()

# Connect to Breeze
if not collector.connect_to_breeze():
    print("❌ Failed to connect to Breeze API")
    sys.exit(1)

# Create tables
collector.create_database_tables()

# Download yesterday's data using the existing method
print(f"📥 Downloading all timeframes for {yesterday_str}...")
collector.download_and_save_historical(date_str=yesterday_str)

print(f"\n{'='*80}")
print(f"✅ DOWNLOAD COMPLETE!")
print(f"{'='*80}")
print(f"📊 Data saved to:")
print(f"   - NIFTY_5min_data.db")
print(f"   - NIFTY_15min_data.db")  
print(f"   - NIFTY_1hour_data.db")
print(f"   - NIFTY_1day_data.db")
print(f"\n✅ System ready for live trading!")
print(f"{'='*80}\n")
