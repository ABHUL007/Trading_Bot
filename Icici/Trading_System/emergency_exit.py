#!/usr/bin/env python3
"""
EMERGENCY EXIT SCRIPT
Manually close ALL open positions immediately
Use in case of bot failure or emergency situations
"""

import os
import sqlite3
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from breeze_connect import BreezeConnect

load_dotenv()

async def emergency_exit_all():
    """Close all open positions via Breeze API"""
    
    print("🚨 EMERGENCY EXIT SCRIPT")
    print("="*60)
    
    # Check if paper trading
    paper_trading = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    
    if paper_trading:
        print("⚠️ PAPER TRADING MODE - No real orders will be placed")
        print("   Change PAPER_TRADING=false in .env for live trading")
    else:
        print("💰 LIVE TRADING MODE - REAL ORDERS WILL BE PLACED")
        confirm = input("\n⚠️ Are you sure you want to close ALL positions? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Emergency exit cancelled")
            return
    
    print(f"\n🔌 Connecting to Breeze API...")
    
    try:
        # Connect to Breeze
        if not paper_trading:
            api_key = os.getenv('ICICI_API_KEY')
            api_secret = os.getenv('ICICI_API_SECRET')
            session_token = os.getenv('ICICI_SESSION_TOKEN')
            
            breeze = BreezeConnect(api_key=api_key)
            breeze.generate_session(api_secret=api_secret, session_token=session_token)
            print("✅ Connected to Breeze API")
        else:
            print("✅ Using simulated Breeze (paper trading)")
            breeze = type('MockBreeze', (), {
                'get_portfolio_positions': lambda: {'Success': []},
                'square_off': lambda *args, **kwargs: {'Success': {'order_id': f'EMERGENCY{datetime.now().strftime("%Y%m%d%H%M%S")}', 'message': 'Emergency exit simulated'}}
            })()
        
        # Get open positions from database
        conn = sqlite3.connect('paper_trades.db')
        cursor = conn.cursor()
        
        open_trades = cursor.execute('''
            SELECT id, strike, direction, entry_premium, quantity, order_id
            FROM real_trades 
            WHERE status = 'OPEN'
            ORDER BY timestamp DESC
        ''').fetchall()
        
        if not open_trades:
            print("\n✅ No open positions found in database")
            conn.close()
            return
        
        print(f"\n📊 Found {len(open_trades)} open position(s) in database:")
        for i, (trade_id, strike, direction, entry_prem, qty, order_id) in enumerate(open_trades, 1):
            print(f"   {i}. Trade #{trade_id}: {strike} {direction} @ ₹{entry_prem:.2f} (Order: {order_id})")
        
        print(f"\n🚪 Closing all positions...")
        
        # Get next Thursday expiry
        from datetime import timedelta
        today = datetime.now()
        days_ahead = 3 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        expiry = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%dT06:00:00.000Z")
        
        closed_count = 0
        
        for trade_id, strike, direction, entry_prem, qty, order_id in open_trades:
            try:
                option_type = "call" if direction == "CALL" else "put"
                
                print(f"\n   Closing Trade #{trade_id}: {strike} {direction}...")
                
                # Square off
                result = breeze.square_off(
                    exchange_code="NFO",
                    product="options",
                    stock_code="NIFTY",
                    expiry_date=expiry,
                    right=option_type,
                    strike_price=str(strike),
                    action="sell",
                    order_type="market",
                    validity="day",
                    stoploss="0",
                    quantity=str(qty),
                    price="0"
                )
                
                if result and 'Success' in result:
                    exit_order_id = result['Success']['order_id']
                    print(f"   ✅ Exit order placed: {exit_order_id}")
                    
                    # Update database
                    cursor.execute('''
                        UPDATE real_trades 
                        SET status = 'CLOSED',
                            exit_timestamp = ?,
                            exit_reason = 'EMERGENCY_EXIT',
                            exit_order_id = ?,
                            exit_order_status = 'Ordered'
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), exit_order_id, trade_id))
                    
                    conn.commit()
                    closed_count += 1
                else:
                    print(f"   ❌ Failed to close Trade #{trade_id}")
                
                await asyncio.sleep(1)  # Delay between orders
                
            except Exception as e:
                print(f"   ❌ Error closing Trade #{trade_id}: {e}")
        
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"✅ Emergency exit complete!")
        print(f"   Closed: {closed_count}/{len(open_trades)} positions")
        print(f"   Check Breeze console for order confirmations")
        
    except Exception as e:
        print(f"\n❌ Emergency exit failed: {e}")

if __name__ == "__main__":
    asyncio.run(emergency_exit_all())
