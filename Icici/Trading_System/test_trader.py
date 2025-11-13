#!/usr/bin/env python3
"""Quick test of RealTrader option price fetching"""
import sys
sys.path.insert(0, r'd:\Algo Trading\Icici\Trading_System')
from real_trader import RealTrader
import asyncio

print("Testing RealTrader...")
trader = RealTrader()
print("✅ Trader initialized")

ok = trader.connect_to_breeze()
print(f"Breeze connected: {ok}")

async def test_fetch():
    print("\nFetching 25900 CALL price...")
    price = await trader.get_option_premium(25900, 'CALL')
    print(f"25900 CALL LTP: Rs.{price}")
    
    print("\nFetching 25800 PUT price...")
    price2 = await trader.get_option_premium(25800, 'PUT')
    print(f"25800 PUT LTP: Rs.{price2}")
    
    return price, price2

prices = asyncio.run(test_fetch())
print(f"\n✅ Option price fetch test PASSED - Got prices: {prices}")
