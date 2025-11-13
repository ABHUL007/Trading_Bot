import sqlite3

conn = sqlite3.connect('NIFTY_15min_data.db')

print("\n" + "="*80)
print("📊 15-MIN CANDLES FOR NOVEMBER 11, 2025")
print("="*80 + "\n")

candles = conn.execute('''
    SELECT datetime, open, high, low, close 
    FROM data_15min 
    WHERE datetime LIKE '2025-11-11%' 
    ORDER BY datetime
''').fetchall()

print(f"Total candles: {len(candles)}\n")

for i, c in enumerate(candles, 1):
    time = c[0].split()[1] if ' ' in c[0] else c[0]
    print(f"{i:2}. {time} | O: {c[1]:8.2f} H: {c[2]:8.2f} L: {c[3]:8.2f} C: {c[4]:8.2f}")

print("\n" + "="*80)
print("SUMMARY:")
print(f"🔴 Highest High: ₹{max(c[2] for c in candles):.2f}")
print(f"🟢 Lowest Low:   ₹{min(c[3] for c in candles):.2f}")
print(f"📊 Close:        ₹{candles[-1][4]:.2f}")
print("="*80 + "\n")

# Check if data is within market hours (9:15 AM - 3:30 PM)
market_start = "09:15:00"
market_end = "15:30:00"
outside_hours = [c for c in candles if c[0].split()[1] < market_start or c[0].split()[1] > market_end]

if outside_hours:
    print("⚠️ CANDLES OUTSIDE MARKET HOURS (9:15 AM - 3:30 PM):")
    for c in outside_hours:
        print(f"   {c[0]}")
else:
    print("✅ All candles within market hours (9:15 AM - 3:30 PM)")

conn.close()
