"""Analyze the downloaded NIFTY data"""
import pandas as pd
import os

print("=" * 70)
print("NIFTY 5-Minute Data Analysis")
print("=" * 70)

# Load the data
data_file = "data/NIFTY_5min_20221024_20251023.csv"

if not os.path.exists(data_file):
    print(f"\n✗ File not found: {data_file}")
    exit(1)

df = pd.read_csv(data_file)
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values('datetime')

print(f"\n✓ Loaded {len(df):,} records")
print(f"✓ File size: {os.path.getsize(data_file) / (1024*1024):.2f} MB")

print("\n" + "=" * 70)
print("Data Overview:")
print("=" * 70)

print(f"\nDate Range:")
print(f"  Start: {df['datetime'].min()}")
print(f"  End:   {df['datetime'].max()}")
print(f"  Days:  {(df['datetime'].max() - df['datetime'].min()).days}")

print(f"\nPrice Range:")
print(f"  Highest: ₹{df['high'].max():,.2f}  ({df[df['high'] == df['high'].max()]['datetime'].iloc[0]})")
print(f"  Lowest:  ₹{df['low'].min():,.2f}   ({df[df['low'] == df['low'].min()]['datetime'].iloc[0]})")
print(f"  Current: ₹{df['close'].iloc[-1]:,.2f}")

print(f"\nVolume Statistics:")
print(f"  Total Volume: {df['volume'].sum():,.0f}")
print(f"  Avg Volume:   {df['volume'].mean():,.0f}")
print(f"  Max Volume:   {df['volume'].max():,.0f}")

print(f"\nPrice Statistics:")
print(f"  Mean Close:   ₹{df['close'].mean():,.2f}")
print(f"  Std Dev:      ₹{df['close'].std():,.2f}")
print(f"  Median Close: ₹{df['close'].median():,.2f}")

# Trading days analysis
df['date'] = df['datetime'].dt.date
trading_days = df['date'].nunique()
print(f"\nTrading Days:")
print(f"  Total: {trading_days}")
print(f"  Avg Candles per Day: {len(df) / trading_days:.1f}")

# Monthly breakdown
df['year_month'] = df['datetime'].dt.to_period('M')
monthly_stats = df.groupby('year_month').agg({
    'close': ['first', 'last', 'min', 'max', 'count'],
    'volume': 'sum'
})
monthly_stats.columns = ['Open', 'Close', 'Low', 'High', 'Candles', 'Volume']
monthly_stats['Change%'] = ((monthly_stats['Close'] - monthly_stats['Open']) / monthly_stats['Open'] * 100).round(2)

print("\n" + "=" * 70)
print("Monthly Breakdown (Last 12 months):")
print("=" * 70)
print(monthly_stats.tail(12).to_string())

# Recent data
print("\n" + "=" * 70)
print("Most Recent Data (Last 10 Candles):")
print("=" * 70)
print(df[['datetime', 'open', 'high', 'low', 'close', 'volume']].tail(10).to_string(index=False))

print("\n" + "=" * 70)
print("Data Quality Check:")
print("=" * 70)

# Check for missing values
missing = df.isnull().sum()
if missing.sum() == 0:
    print("✓ No missing values")
else:
    print("Missing values found:")
    print(missing[missing > 0])

# Check for duplicates
duplicates = df.duplicated(subset=['datetime']).sum()
if duplicates == 0:
    print("✓ No duplicate timestamps")
else:
    print(f"⚠ Found {duplicates} duplicate timestamps")

# Check data continuity (gaps)
df['time_diff'] = df['datetime'].diff()
expected_gap = pd.Timedelta(minutes=5)
large_gaps = df[df['time_diff'] > pd.Timedelta(hours=1)]

if len(large_gaps) > 0:
    print(f"\n⚠ Found {len(large_gaps)} gaps > 1 hour (likely non-trading hours/weekends)")
else:
    print("✓ No unusual gaps in data")

print("\n" + "=" * 70)
print("✓ Analysis Complete!")
print("=" * 70)
print(f"\nData file ready for backtesting: {data_file}")
print("You can use this data with your trading strategies!")
