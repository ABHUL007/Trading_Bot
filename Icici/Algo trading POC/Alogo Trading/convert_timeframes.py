"""Convert 5-minute NIFTY data to different timeframes"""
import pandas as pd
import os

print("=" * 70)
print("NIFTY Data Timeframe Conversion")
print("=" * 70)

# Load 5-minute data
input_file = "data/NIFTY_5min_20221024_20251023.csv"

print(f"\n✓ Loading 5-minute data from: {input_file}")
df = pd.read_csv(input_file)
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values('datetime')

print(f"✓ Loaded {len(df):,} 5-minute candles")

# Set datetime as index for resampling
df.set_index('datetime', inplace=True)

print("\n" + "=" * 70)
print("Converting to Different Timeframes...")
print("=" * 70)

# Function to resample OHLCV data
def resample_ohlcv(df, rule, label):
    """Resample OHLCV data to specified timeframe"""
    resampled = df.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'stock_code': 'first',
        'exchange_code': 'first'
    }).dropna()
    
    return resampled

# 1. Convert to 15-minute
print("\n1. Creating 15-minute dataset...")
df_15min = resample_ohlcv(df, '15min', '15-minute')
output_15min = "data/NIFTY_15min_20221024_20251023.csv"
df_15min.to_csv(output_15min)
print(f"   ✓ {len(df_15min):,} candles saved to: {output_15min}")
print(f"   Date range: {df_15min.index.min()} to {df_15min.index.max()}")

# 2. Convert to 1-hour using custom grouping (market hours: 9:15 AM - 3:30 PM)
print("\n2. Creating 1-hour dataset...")
df_reset = df.reset_index()

# Create hour group based on market time
# Trading starts at 9:15 AM, hourly candles: 9:15-10:15, 10:15-11:15, etc.
# Last candle 3:15-3:30 is only 15 minutes
def get_hour_group(dt):
    hour = dt.hour
    minute = dt.minute
    
    # Calculate minutes since market open (9:15 AM)
    market_open = 9 * 60 + 15  # 9:15 AM in minutes
    current_time = hour * 60 + minute
    minutes_since_open = current_time - market_open
    
    if minutes_since_open < 0:
        # Before market open
        return None
    elif minutes_since_open < 60:
        # 9:15 - 10:15 (first hour)
        return pd.Timestamp.combine(dt.date(), pd.Timestamp('09:15:00').time())
    elif minutes_since_open < 120:
        # 10:15 - 11:15 (second hour)
        return pd.Timestamp.combine(dt.date(), pd.Timestamp('10:15:00').time())
    elif minutes_since_open < 180:
        # 11:15 - 12:15 (third hour)
        return pd.Timestamp.combine(dt.date(), pd.Timestamp('11:15:00').time())
    elif minutes_since_open < 240:
        # 12:15 - 13:15 (fourth hour)
        return pd.Timestamp.combine(dt.date(), pd.Timestamp('12:15:00').time())
    elif minutes_since_open < 300:
        # 13:15 - 14:15 (fifth hour)
        return pd.Timestamp.combine(dt.date(), pd.Timestamp('13:15:00').time())
    elif minutes_since_open < 360:
        # 14:15 - 15:15 (sixth hour)
        return pd.Timestamp.combine(dt.date(), pd.Timestamp('14:15:00').time())
    else:
        # 15:15 - 15:30 (last 15 minutes)
        return pd.Timestamp.combine(dt.date(), pd.Timestamp('15:15:00').time())

df_reset['hour_group'] = df_reset['datetime'].apply(get_hour_group)

# Remove any None values (before market open)
df_reset = df_reset[df_reset['hour_group'].notna()]

# Group by hour_group and aggregate
df_1hour = df_reset.groupby('hour_group').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum',
    'stock_code': 'first',
    'exchange_code': 'first'
}).reset_index()

df_1hour.rename(columns={'hour_group': 'datetime'}, inplace=True)
df_1hour.set_index('datetime', inplace=True)

output_1hour = "data/NIFTY_1hour_20221024_20251023.csv"
df_1hour.to_csv(output_1hour)
print(f"   ✓ {len(df_1hour):,} candles saved to: {output_1hour}")
print(f"   Date range: {df_1hour.index.min()} to {df_1hour.index.max()}")
print(f"   Note: Hourly candles start at 9:15 AM, last candle (3:15 PM) is 15 minutes")

# 3. Convert to 1-day using date-based grouping (better for partial trading days)
print("\n3. Creating 1-day dataset...")
df_reset = df.reset_index()
df_reset['date'] = df_reset['datetime'].dt.date

# Group by date and aggregate
df_1day = df_reset.groupby('date').agg({
    'datetime': 'first',  # Use first datetime for the day
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum',
    'stock_code': 'first',
    'exchange_code': 'first'
}).reset_index(drop=True)

# Set datetime as index and ensure it's date only
df_1day['datetime'] = pd.to_datetime(df_1day['datetime'].dt.date)
df_1day.set_index('datetime', inplace=True)

output_1day = "data/NIFTY_1day_20221024_20251023.csv"
df_1day.to_csv(output_1day)
print(f"   ✓ {len(df_1day):,} candles saved to: {output_1day}")
print(f"   Date range: {df_1day.index.min()} to {df_1day.index.max()}")

# Summary comparison
print("\n" + "=" * 70)
print("Summary Comparison:")
print("=" * 70)

summary = pd.DataFrame({
    'Timeframe': ['5-minute', '15-minute', '1-hour', '1-day'],
    'Candles': [len(df), len(df_15min), len(df_1hour), len(df_1day)],
    'File': [
        input_file.split('/')[-1],
        output_15min.split('/')[-1],
        output_1hour.split('/')[-1],
        output_1day.split('/')[-1]
    ],
    'Size (KB)': [
        os.path.getsize(input_file) / 1024,
        os.path.getsize(output_15min) / 1024,
        os.path.getsize(output_1hour) / 1024,
        os.path.getsize(output_1day) / 1024
    ]
})

print(summary.to_string(index=False))

# Show sample data from each timeframe
print("\n" + "=" * 70)
print("Sample Data - Latest 5 Candles from Each Timeframe:")
print("=" * 70)

print("\n15-Minute Data:")
print(df_15min[['open', 'high', 'low', 'close', 'volume']].tail(5).to_string())

print("\n1-Hour Data:")
print(df_1hour[['open', 'high', 'low', 'close', 'volume']].tail(5).to_string())

print("\n1-Day Data:")
print(df_1day[['open', 'high', 'low', 'close', 'volume']].tail(5).to_string())

# Price comparison
print("\n" + "=" * 70)
print("Price Statistics Comparison:")
print("=" * 70)

stats = pd.DataFrame({
    'Timeframe': ['5-min', '15-min', '1-hour', '1-day'],
    'Highest': [df['high'].max(), df_15min['high'].max(), df_1hour['high'].max(), df_1day['high'].max()],
    'Lowest': [df['low'].min(), df_15min['low'].min(), df_1hour['low'].min(), df_1day['low'].min()],
    'Avg Close': [df['close'].mean(), df_15min['close'].mean(), df_1hour['close'].mean(), df_1day['close'].mean()],
    'Current': [df['close'].iloc[-1], df_15min['close'].iloc[-1], df_1hour['close'].iloc[-1], df_1day['close'].iloc[-1]]
})

print(stats.to_string(index=False, float_format=lambda x: f'₹{x:,.2f}'))

print("\n" + "=" * 70)
print("✓ Conversion Complete!")
print("=" * 70)
print("\nAll datasets are ready in the 'data' folder:")
print("  • 5-minute:  6,536 candles")
print("  • 15-minute: " + f"{len(df_15min):,} candles")
print("  • 1-hour:    " + f"{len(df_1hour):,} candles")
print("  • 1-day:     " + f"{len(df_1day):,} candles")
print("\nYou can use these for backtesting different strategies!")
print("=" * 70)
