import sqlite3
from datetime import datetime

print("\n" + "="*80)
print("📊 DATABASE STATUS CHECK")
print("="*80 + "\n")

# Check 5-min data
print("📈 NIFTY_5min_data.db:")
conn = sqlite3.connect('../NIFTY_5min_data.db')
result = conn.execute('''
    SELECT date(datetime) as date, COUNT(*) as cnt, 
           MIN(datetime) as first, MAX(datetime) as last,
           MIN(low) as low, MAX(high) as high
    FROM data_5min 
    GROUP BY date(datetime) 
    ORDER BY date DESC 
    LIMIT 5
''').fetchall()

if result:
    for row in result:
        print(f"   {row[0]} - {row[1]} candles | {row[2]} to {row[3]} | Low: ₹{row[4]:.2f}, High: ₹{row[5]:.2f}")
else:
    print("   ❌ No data found")
conn.close()

# Check 15-min data
print("\n📈 NIFTY_15min_data.db:")
conn = sqlite3.connect('../NIFTY_15min_data.db')
result = conn.execute('''
    SELECT date(datetime) as date, COUNT(*) as cnt, 
           MIN(datetime) as first, MAX(datetime) as last,
           MIN(low) as low, MAX(high) as high
    FROM data_15min 
    GROUP BY date(datetime) 
    ORDER BY date DESC 
    LIMIT 5
''').fetchall()

if result:
    for row in result:
        print(f"   {row[0]} - {row[1]} candles | {row[2]} to {row[3]} | Low: ₹{row[4]:.2f}, High: ₹{row[5]:.2f}")
else:
    print("   ❌ No data found")
conn.close()

# Check daily data
print("\n📈 NIFTY_1day_data.db:")
conn = sqlite3.connect('../NIFTY_1day_data.db')
result = conn.execute('''
    SELECT datetime, open, high, low, close 
    FROM data_1day 
    ORDER BY datetime DESC 
    LIMIT 5
''').fetchall()

if result:
    for row in result:
        date = row[0].split('T')[0] if 'T' in row[0] else row[0]
        print(f"   {date} | O: ₹{row[1]:.2f}, H: ₹{row[2]:.2f}, L: ₹{row[3]:.2f}, C: ₹{row[4]:.2f}")
        if result.index(row) == 0:
            print(f"   🔴 PDH (Previous Day High): ₹{row[2]:.2f}")
            print(f"   🟢 PDL (Previous Day Low):  ₹{row[3]:.2f}")
else:
    print("   ❌ No data found")
conn.close()

print("\n" + "="*80)
print("✅ Status check complete")
print("="*80 + "\n")
