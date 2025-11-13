"""Download missing historical data for NIFTY from ICICI Breeze (April-Sept 2024)"""
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from breeze_connect import BreezeConnect
import time

print("=" * 70)
print("Downloading Missing NIFTY Data (April - September 2024)")
print("=" * 70)

# Load credentials
load_dotenv()
api_key = os.getenv('ICICI_API_KEY')
api_secret = os.getenv('ICICI_API_SECRET')
session_token = os.getenv('ICICI_SESSION_TOKEN')

print("\n✓ Credentials loaded")

# Initialize Breeze
breeze = BreezeConnect(api_key=api_key)
breeze.generate_session(api_secret=api_secret, session_token=session_token)

print("✓ Connected to ICICI Breeze")

# Parameters
symbol = "NIFTY"
exchange = "NSE"
interval = "5minute"

# Load existing data
existing_data = pd.read_csv("data/NIFTY_5min_20221024_20251023.csv")
existing_data['datetime'] = pd.to_datetime(existing_data['datetime'])

print(f"\n✓ Loaded existing data: {len(existing_data)} candles")
print(f"  Date range: {existing_data['datetime'].min()} to {existing_data['datetime'].max()}")

# Download missing periods
print("\n" + "=" * 70)
print("Downloading Missing Data...")
print("=" * 70)

all_new_data = []

# Split into monthly chunks to avoid API limits
date_ranges = [
    ("2024-04-19", "2024-04-30"),
    ("2024-05-01", "2024-05-31"),
    ("2024-06-01", "2024-06-30"),
    ("2024-07-01", "2024-07-31"),
    ("2024-08-01", "2024-08-31"),
    ("2024-09-01", "2024-09-26"),
]

for start_str, end_str in date_ranges:
    print(f"\nDownloading: {start_str} to {end_str}")
    
    try:
        response = breeze.get_historical_data_v2(
            interval=interval,
            from_date=f"{start_str}T07:00:00.000Z",
            to_date=f"{end_str}T18:00:00.000Z",
            stock_code=symbol,
            exchange_code=exchange,
            product_type="cash"
        )
        
        if response and response.get('Success'):
            chunk_data = response['Success']
            if chunk_data:
                df_chunk = pd.DataFrame(chunk_data)
                df_chunk['datetime'] = pd.to_datetime(df_chunk['datetime'])
                
                # Rename columns to match existing format
                df_chunk = df_chunk.rename(columns={
                    'stock_code': 'symbol'
                })
                
                all_new_data.append(df_chunk)
                print(f"  ✓ Downloaded {len(df_chunk)} candles")
            else:
                print(f"  ⚠ No data available for this period")
        else:
            print(f"  ✗ Failed to download: {response}")
        
        # Rate limiting
        time.sleep(1)
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        continue

if all_new_data:
    # Combine new data
    df_new = pd.concat(all_new_data, ignore_index=True)
    df_new = df_new.sort_values('datetime').drop_duplicates(subset=['datetime'])
    
    print(f"\n✓ Downloaded {len(df_new)} new candles")
    print(f"  Date range: {df_new['datetime'].min()} to {df_new['datetime'].max()}")
    
    # Combine with existing data
    df_combined = pd.concat([existing_data, df_new], ignore_index=True)
    df_combined = df_combined.sort_values('datetime').drop_duplicates(subset=['datetime'])
    
    print(f"\n✓ Combined data: {len(df_combined)} total candles")
    print(f"  Date range: {df_combined['datetime'].min()} to {df_combined['datetime'].max()}")
    
    # Save
    output_file = "data/NIFTY_5min_20221024_20251023.csv"
    df_combined.to_csv(output_file, index=False)
    
    print(f"\n✓ Saved updated data to: {output_file}")
    
    # Check for remaining gaps
    df_combined['date'] = df_combined['datetime'].dt.date
    dates = df_combined['date'].unique()
    print(f"\n✓ Total unique trading days: {len(dates)}")
    
    # Show data distribution by month
    df_combined['month'] = df_combined['datetime'].dt.to_period('M')
    print("\nData distribution by month:")
    print(df_combined.groupby('month').size().tail(20))
    
else:
    print("\n✗ No new data was downloaded")

print("\n" + "=" * 70)
print("Download Complete!")
print("=" * 70)
