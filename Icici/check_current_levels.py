#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Trading_System'))

from super_pranni_monitor import FixedPranniMonitor

print("\n" + "="*80)
print("🎯 CHECKING CURRENT LEVELS")
print("="*80 + "\n")

monitor = FixedPranniMonitor()
monitor.update_all_levels()

print(f"Current Price: ₹{monitor.current_price:.2f}\n")

if monitor.levels:
    for name, level_data in monitor.levels.items():
        if 'high' in level_data and 'low' in level_data:
            print(f"📊 {name}:")
            print(f"   High: ₹{level_data['high']:.2f}")
            print(f"   Low:  ₹{level_data['low']:.2f}")
            print(f"   Type: {level_data.get('type', 'N/A')}\n")
else:
    print("⚠️  No levels found")

print("="*80)
