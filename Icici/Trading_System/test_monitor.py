#!/usr/bin/env python3
"""Quick test of Super Pranni Monitor"""
import sys
sys.path.insert(0, r'd:\Algo Trading\Icici\Trading_System')
from super_pranni_monitor import FixedPranniMonitor

print("Testing Super Pranni Monitor...")
m = FixedPranniMonitor()
print("✅ Monitor initialized OK")

s = m.get_live_status()
print(f"\nCurrent Price: Rs.{s['current_price']:.2f}")
print(f"2-Week High: Rs.{s['levels'].get('2 Weeks', {}).get('high', 0):.2f}")
print(f"1-Month High: Rs.{s['levels'].get('1 Month', {}).get('high', 0):.2f}")

signal = m.check_all_breakouts()
print(f"\nSignal: {signal}")
if signal:
    print(f"  Type: {signal.get('type')}")
    print(f"  Direction: {signal.get('direction')}")
    print(f"  Level: {signal.get('level')}")
    print(f"  Timeframe: {signal.get('timeframe')}")

print("\n✅ Super Pranni Monitor test PASSED")
