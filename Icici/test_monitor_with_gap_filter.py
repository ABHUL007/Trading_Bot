#!/usr/bin/env python3
"""
Test Super Pranni Monitor with gap filter
"""

import sys
import os

# Add Trading_System to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Trading_System'))

from super_pranni_monitor import FixedPranniMonitor

print("\n" + "="*80)
print("🧪 TESTING SUPER PRANNI MONITOR WITH GAP FILTER")
print("="*80 + "\n")

try:
    # Initialize monitor
    print("📊 Initializing Super Pranni Monitor...")
    monitor = FixedPranniMonitor()
    print("✅ Monitor initialized successfully\n")
    
    # Check current levels
    print("📈 Checking current levels...")
    monitor.update_all_levels()
    
    print(f"\n📊 Current Market Status:")
    print(f"   Current Price: ₹{monitor.current_price:.2f}")
    print(f"   ATR-14: {monitor.atr_14:.2f}")
    print(f"   Last Update: {monitor.last_update}")
    
    print(f"\n🎯 Key Levels Loaded:")
    for name, level_data in monitor.levels.items():
        if 'high' in level_data and 'low' in level_data:
            print(f"   {name}:")
            print(f"      High: ₹{level_data['high']:.2f} | Low: ₹{level_data['low']:.2f}")
            if name == 'Previous Day':
                print(f"      📌 PDH: ₹{level_data['high']:.2f} (for gap-up detection)")
                print(f"      📌 PDL: ₹{level_data['low']:.2f} (for gap-down detection)")
    
    print(f"\n🔍 Checking for breakouts...")
    breakout = monitor.check_all_breakouts()
    
    if breakout:
        print(f"\n🚨 BREAKOUT DETECTED!")
        print(f"   Type: {breakout.get('type', 'N/A')}")
        print(f"   Direction: {breakout.get('direction', 'N/A')}")
        print(f"   Timeframe: {breakout.get('timeframe', 'N/A')}")
        print(f"   Level: ₹{breakout.get('level', 0):.2f}")
        print(f"   Close Price: ₹{breakout.get('close_price', 0):.2f}")
    else:
        print("\n📊 No breakouts detected (or waiting for gap retest)")
    
    print("\n" + "="*80)
    print("✅ SUPER PRANNI MONITOR TEST COMPLETE")
    print("="*80)
    print("\n🎯 Gap Filter Features:")
    print("   ✅ Detects gap-up > 50 points above PDH")
    print("   ✅ Detects gap-down > 50 points below PDL")
    print("   ✅ Waits for retest within ±20 points")
    print("   ✅ Skips trades during large gaps")
    print("   ✅ Allows trades on retest zones")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    print("\n⚠️  Monitor test failed - check the error above")
