"""Download historical 5-minute data for NIFTY from ICICI Breeze"""
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from breeze_connect import BreezeConnect
import time

print("=" * 70)
print("NIFTY 5-Minute Historical Data Download")
print("=" * 70)

# Load credentials
load_dotenv()
api_key = os.getenv('ICICI_API_KEY')
api_secret = os.getenv('ICICI_API_SECRET')
session_token = os.getenv('ICICI_SESSION_TOKEN')

print("\n✓ Credentials loaded")
print(f"  API Key: {api_key[:15]}...")
print(f"  Session Token: {session_token}")

# Initialize Breeze
breeze = BreezeConnect(api_key=api_key)
breeze.generate_session(api_secret=api_secret, session_token=session_token)

print("\n✓ Connected to ICICI Breeze")

# Parameters for NIFTY cash segment
symbol = "NIFTY"
exchange = "NSE"
interval = "5minute"

# Calculate date range (3 years back from today)
end_date = datetime.now()
start_date = end_date - timedelta(days=3*365)

print("\n" + "=" * 70)
print("Download Parameters:")
print("=" * 70)
print(f"Symbol: {symbol}")
print(f"Exchange: {exchange}")
print(f"Interval: {interval}")
print(f"Start Date: {start_date.strftime('%Y-%m-%d')}")
print(f"End Date: {end_date.strftime('%Y-%m-%d')}")

# ICICI API has limits on data per request, so we'll split into chunks
# Download in 6-month chunks to avoid API limits
all_data = []
chunk_size_days = 180  # 6 months

current_start = start_date
chunk_num = 1

print("\n" + "=" * 70)
print("Downloading Data in Chunks...")
print("=" * 70)

while current_start < end_date:
    current_end = min(current_start + timedelta(days=chunk_size_days), end_date)
    
    print(f"\nChunk {chunk_num}: {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}")
    
    try:
        # Format dates for Breeze API
        from_date_str = current_start.strftime("%Y-%m-%dT00:00:00.000Z")
        to_date_str = current_end.strftime("%Y-%m-%dT23:59:59.000Z")
        
        # Get historical data
        response = breeze.get_historical_data_v2(
            interval=interval,
            from_date=from_date_str,
            to_date=to_date_str,
            stock_code=symbol,
            exchange_code=exchange,
            product_type="cash"
        )
        
        if response and response.get('Status') == 200:
            success_data = response.get('Success', [])
            if success_data:
                print(f"  ✓ Downloaded {len(success_data)} candles")
                all_data.extend(success_data)
            else:
                print(f"  ⚠ No data for this period")
        else:
            error_msg = response.get('Error', 'Unknown error') if response else 'No response'
            print(f"  ✗ Error: {error_msg}")
        
        chunk_num += 1
        current_start = current_end + timedelta(days=1)
        
        # Rate limiting - wait 1 second between requests
        time.sleep(1)
        
    except Exception as e:
        print(f"  ✗ Error downloading chunk: {e}")
        # Continue with next chunk
        current_start = current_end + timedelta(days=1)
        chunk_num += 1
        time.sleep(1)

print("\n" + "=" * 70)
print("Processing Data...")
print("=" * 70)

if all_data:
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    
    print(f"\n✓ Total records downloaded: {len(df)}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst few records:")
    print(df.head())
    
    # Save to CSV
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f"{output_dir}/NIFTY_5min_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n✓ Data saved to: {output_file}")
    
    # Show summary statistics
    print("\n" + "=" * 70)
    print("Data Summary:")
    print("=" * 70)
    
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        print(f"Date Range: {df['datetime'].min()} to {df['datetime'].max()}")
    
    if 'close' in df.columns:
        print(f"\nPrice Statistics:")
        print(f"  Highest Close: ₹{df['close'].max():,.2f}")
        print(f"  Lowest Close: ₹{df['close'].min():,.2f}")
        print(f"  Average Close: ₹{df['close'].mean():,.2f}")
    
    # Save to Parquet format (more efficient for large datasets)
    parquet_file = f"{output_dir}/NIFTY_5min_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.parquet"
    df.to_parquet(parquet_file, index=False)
    print(f"\n✓ Data also saved to Parquet format: {parquet_file}")
    
    print("\n" + "=" * 70)
    print("✓ DOWNLOAD COMPLETE!")
    print("=" * 70)
    
else:
    print("\n✗ No data was downloaded. Possible reasons:")
    print("  1. Market holidays during the period")
    print("  2. API access restrictions")
    print("  3. Symbol format incorrect")
    print("  4. Session token expired")
    print("\n" + "=" * 70)
