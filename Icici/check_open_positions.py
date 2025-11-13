#!/usr/bin/env python3
"""
Check open positions
"""

import sqlite3
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

conn = sqlite3.connect('paper_trades.db')

print("\n" + "="*80)
print("🔍 OPEN POSITIONS IN REAL_TRADES")
print("="*80 + "\n")

rows = conn.execute('''
    SELECT id, type, strike, entry_price, entry_time, quantity, 
           target_price, status, order_id, entry_order_status
    FROM real_trades 
    WHERE status = 'OPEN'
    ORDER BY entry_time DESC
''').fetchall()

if not rows:
    print("✅ No open positions - Clean slate for today")
else:
    print(f"⚠️  Found {len(rows)} OPEN position(s):\n")
    for i, row in enumerate(rows, 1):
        print(f"Position {i}:")
        print(f"  ID: {row[0]}")
        print(f"  Type: {row[1]}")
        print(f"  Strike: {row[2]}")
        print(f"  Entry Price: ₹{row[3]:.2f}")
        print(f"  Entry Time: {row[4]}")
        print(f"  Quantity: {row[5]}")
        print(f"  Target: ₹{row[6]:.2f}")
        print(f"  Status: {row[7]}")
        print(f"  Order ID: {row[8]}")
        print(f"  Entry Order Status: {row[9]}")
        print()

conn.close()

print("="*80)
print("💡 RECOMMENDATION:")
print("   If these are old test positions, mark them as CLOSED")
print("   or delete them before starting live trading")
print("="*80 + "\n")
