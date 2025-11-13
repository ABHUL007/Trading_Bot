#!/usr/bin/env python3
"""
Setup script to rename safe_trades to real_trades and add real trading columns
"""

import sqlite3

def setup_real_trades_database():
    conn = sqlite3.connect('paper_trades.db')
    cursor = conn.cursor()
    
    try:
        # Rename table
        print("📊 Renaming safe_trades to real_trades...")
        cursor.execute('ALTER TABLE safe_trades RENAME TO real_trades')
        conn.commit()
        print("✅ Table renamed successfully")
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("ℹ️ real_trades table already exists")
        else:
            print(f"⚠️ Error renaming table: {e}")
    
    # Add new columns for real trading
    columns_to_add = [
        ('order_id', 'TEXT'),
        ('entry_order_status', 'TEXT'),
        ('exit_order_id', 'TEXT'),
        ('exit_order_status', 'TEXT'),
        ('sl_candle_count', 'INTEGER DEFAULT 0'),
        ('last_sl_check_time', 'TEXT')
    ]
    
    print("\n📊 Adding real trading columns...")
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE real_trades ADD COLUMN {col_name} {col_type}')
            conn.commit()
            print(f"✅ Added column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"ℹ️ Column {col_name} already exists")
            else:
                print(f"⚠️ Error adding {col_name}: {e}")
    
    # Show final schema
    print("\n📊 Final Schema for real_trades:")
    cursor.execute('PRAGMA table_info(real_trades)')
    columns = cursor.fetchall()
    
    for col in columns:
        print(f"  {col[1]:25} {col[2]:15} {'NOT NULL' if col[3] else ''} {f'DEFAULT {col[4]}' if col[4] else ''}")
    
    conn.close()
    print("\n✅ Database setup complete!")

if __name__ == "__main__":
    setup_real_trades_database()
