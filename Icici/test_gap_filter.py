#!/usr/bin/env python3
"""
Test gap filter logic
"""

# Simulate gap scenarios
scenarios = [
    {
        'name': 'Normal Day - No Gap',
        'prev_day_high': 25713.80,
        'prev_day_low': 25450.85,
        'opening_price': 25700.00,
        'current_price': 25720.00
    },
    {
        'name': 'Small Gap-Up - Trade Allowed',
        'prev_day_high': 25713.80,
        'prev_day_low': 25450.85,
        'opening_price': 25750.00,  # +36 points (< 50)
        'current_price': 25760.00
    },
    {
        'name': 'Large Gap-Up - Wait for Retest',
        'prev_day_high': 25713.80,
        'prev_day_low': 25450.85,
        'opening_price': 25850.00,  # +136 points (> 50)
        'current_price': 25870.00
    },
    {
        'name': 'Large Gap-Up - Retest Success',
        'prev_day_high': 25713.80,
        'prev_day_low': 25450.85,
        'opening_price': 25850.00,  # +136 points (> 50)
        'current_price': 25720.00   # Retesting PDH (within ±20)
    },
    {
        'name': 'Large Gap-Down - Wait for Retest',
        'prev_day_high': 25713.80,
        'prev_day_low': 25450.85,
        'opening_price': 25350.00,  # -100 points below PDL (> 50)
        'current_price': 25320.00
    },
    {
        'name': 'Large Gap-Down - Retest Success',
        'prev_day_high': 25713.80,
        'prev_day_low': 25450.85,
        'opening_price': 25350.00,  # -100 points below PDL (> 50)
        'current_price': 25460.00   # Retesting PDL (within ±20)
    }
]

print("\n" + "="*80)
print("🧪 GAP FILTER LOGIC TEST")
print("="*80 + "\n")

for scenario in scenarios:
    print(f"📊 {scenario['name']}")
    print("-" * 80)
    
    pdh = scenario['prev_day_high']
    pdl = scenario['prev_day_low']
    opening = scenario['opening_price']
    current = scenario['current_price']
    
    print(f"   PDH: ₹{pdh:.2f} | PDL: ₹{pdl:.2f}")
    print(f"   Opening: ₹{opening:.2f} | Current: ₹{current:.2f}")
    
    # Calculate gaps
    gap_up_size = opening - pdh
    gap_down_size = pdl - opening
    
    gap_up_detected = gap_up_size > 50
    gap_down_detected = gap_down_size > 50
    
    # Check retest zones
    in_pdh_retest = (pdh - 20 <= current <= pdh + 20)
    in_pdl_retest = (pdl - 20 <= current <= pdl + 20)
    
    if gap_up_detected:
        print(f"   ⚠️  GAP-UP: +{gap_up_size:.2f} points above PDH")
        if in_pdh_retest:
            print(f"   ✅ IN RETEST ZONE: Price ₹{current:.2f} near PDH ₹{pdh:.2f}")
            print(f"   🎯 ACTION: TRADE ALLOWED on PDH breakout")
        else:
            print(f"   🚫 NOT IN RETEST ZONE: Price ₹{current:.2f} vs PDH ₹{pdh:.2f}")
            print(f"   🎯 ACTION: SKIP TRADE - Wait for retest")
    
    elif gap_down_detected:
        print(f"   ⚠️  GAP-DOWN: -{gap_down_size:.2f} points below PDL")
        if in_pdl_retest:
            print(f"   ✅ IN RETEST ZONE: Price ₹{current:.2f} near PDL ₹{pdl:.2f}")
            print(f"   🎯 ACTION: TRADE ALLOWED on PDL breakdown")
        else:
            print(f"   🚫 NOT IN RETEST ZONE: Price ₹{current:.2f} vs PDL ₹{pdl:.2f}")
            print(f"   🎯 ACTION: SKIP TRADE - Wait for retest")
    
    else:
        print(f"   ✅ NO SIGNIFICANT GAP")
        print(f"   🎯 ACTION: NORMAL TRADING - Check for breakouts")
    
    print()

print("="*80)
print("✅ TEST COMPLETE")
print("="*80 + "\n")
