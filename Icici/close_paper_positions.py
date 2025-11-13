#!/usr/bin/env python3
"""
Close all open paper trade positions to start fresh
"""

import sqlite3
import os
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

conn = sqlite3.connect('paper_trades.db')
cursor = conn.cursor()

print("\n" + "="*80)
print("🧹 CLOSING OLD PAPER TRADE POSITIONS")
print("="*80 + "\n")

# Get all open positions
open_positions = cursor.execute('''
    SELECT id, direction, strike, entry_premium, timestamp, quantity
    FROM real_trades 
    WHERE status = 'OPEN'
    ORDER BY timestamp DESC
''').fetchall()

if not open_positions:
    print("✅ No open positions found - Already clean")
else:
    print(f"Found {len(open_positions)} OPEN position(s):\n")
    for pos in open_positions:
        print(f"  ID: {pos[0]} | {pos[1]} | Strike: {pos[2]} | Entry: ₹{pos[3]:.2f} @ {pos[4]}")
    
    print(f"\n🔄 Marking all as CLOSED (Paper trades)...\n")
    
    # Update all open positions to CLOSED
    cursor.execute('''
        UPDATE real_trades 
        SET status = 'CLOSED',
            exit_timestamp = ?,
            exit_premium = 0,
            pnl = 0,
            exit_order_id = 'PAPER_TRADE_CLEANUP',
            exit_order_status = 'CLEANED',
            exit_reason = 'Paper trade cleanup for fresh start'
        WHERE status = 'OPEN'
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
    
    rows_updated = cursor.rowcount
    conn.commit()
    
    print(f"✅ Closed {rows_updated} position(s)")

conn.close()

print("\n" + "="*80)
print("✅ DATABASE CLEAN - READY FOR FRESH REAL TRADES")
print("="*80 + "\n")

# Verify
conn = sqlite3.connect('paper_trades.db')
remaining_open = conn.execute('SELECT COUNT(*) FROM real_trades WHERE status = "OPEN"').fetchone()[0]
conn.close()

if remaining_open == 0:
    print("✅ VERIFICATION: 0 open positions remaining")
else:
    print(f"⚠️  WARNING: {remaining_open} positions still open")

print("="*80 + "\n")
