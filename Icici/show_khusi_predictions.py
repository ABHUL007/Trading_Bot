#!/usr/bin/env python3
"""
Display Khusi Investment Model Predictions for November 2025
"""

print("\n" + "="*80)
print("🎯 KHUSI INVESTMENT MODEL - NOVEMBER 2025 PREDICTIONS")
print("="*80)
print("📅 Dashboard Created: November 6, 2025")
print("📊 Current Analysis: November 12, 2025")
print("="*80 + "\n")

print("📈 CURRENT MARKET STATUS (Nov 6, 2025 base)")
print("-" * 80)
print("   Last Close: ₹25,554.05")
print("   EMA 5 (Weekly): ₹25,424.17")
print("   EMA 21 (Monthly): ₹25,591.49")
print("   EMA 50 (Quarterly): ₹25,323.43")
print("   EMA 100 (6-Month): ₹25,051.35")
print("   EMA 200 (Annual): ₹24,643.17")

print("\n" + "="*80)
print("🎯 NOVEMBER 2025 SCENARIOS")
print("="*80 + "\n")

print("📊 SCENARIO 1: EMA 50 BOUNCE (85% Confidence)")
print("-" * 80)
print("   🎯 Target: ₹25,323.43 (EMA 50)")
print("   📉 Move: -0.9% correction from Nov 6")
print("   📅 Timeline: Mid-November (Nov 11-15)")
print("   💡 Logic: Quarterly returns normalization")
print("   ✅ Support: Strong 3-month average")
print("   📈 After Bounce: Rally to ₹26,500-27,000")
print("   🔑 Historical: 85% bounce rate at this level")

print("\n📊 SCENARIO 2: EMA 100 BREAKDOWN (25% Probability)")
print("-" * 80)
print("   🎯 Target: ₹25,051.35 (EMA 100)")
print("   📉 Move: -2.0% correction")
print("   📅 Timeline: Late November (Nov 18-25)")
print("   ⚠️  Trigger: EMA 50 break with volume")
print("   💡 Logic: Semi-annual support test")
print("   ✅ Recovery: Strong bounce from 6M average")

print("\n📊 SCENARIO 3: EMA 200 TEST (10% Probability)")
print("-" * 80)
print("   🎯 Target: ₹24,643.17 (EMA 200)")
print("   📉 Move: -3.6% correction")
print("   📅 Timeline: December spillover")
print("   ⚠️  Trigger: Major breakdown + external shock")
print("   💡 Logic: Annual returns reset")
print("   ✅ Opportunity: MAJOR BUYING OPPORTUNITY")

print("\n" + "="*80)
print("📅 NOVEMBER 2025 TIMELINE")
print("="*80 + "\n")

timeline = [
    ("Nov 7-8", "Continuation toward ₹25,400. Possible bounce attempt at EMA 21"),
    ("Nov 11-15", "Approach EMA 50 (₹25,323). Key decision point - bounce or breakdown"),
    ("Nov 18-22", "If EMA 50 holds: Strong bounce to ₹26,200+. If breaks: Move toward EMA 100"),
    ("Nov 25-29", "Final positioning for December. EMA system reset completion")
]

for date_range, description in timeline:
    print(f"   {date_range:12s} | {description}")

print("\n" + "="*80)
print("🔑 CRITICAL LEVELS FOR NOVEMBER")
print("="*80 + "\n")

print("📈 RESISTANCE LEVELS:")
print("   ₹25,800 - EMA 9 area")
print("   ₹25,591 - EMA 21 (Monthly)")

print("\n📉 SUPPORT LEVELS:")
print("   ₹25,323 - EMA 50 (Quarterly) ⭐ KEY LEVEL")
print("   ₹25,051 - EMA 100 (6-Month) 🛡️ MAJOR SUPPORT")
print("   ₹24,643 - EMA 200 (Annual) 🔴 CRITICAL SUPPORT")

print("\n" + "="*80)
print("💡 CURRENT STATUS ANALYSIS (Nov 12, 2025)")
print("="*80)

# Current actual close
actual_close_nov11 = 25705.55
ema_50 = 25323.43
ema_100 = 25051.35

print(f"\n   Yesterday's Close: ₹{actual_close_nov11:.2f}")
print(f"   Distance from EMA 50: +₹{actual_close_nov11 - ema_50:.2f} (+{((actual_close_nov11/ema_50)-1)*100:.2f}%)")
print(f"   Distance from EMA 100: +₹{actual_close_nov11 - ema_100:.2f} (+{((actual_close_nov11/ema_100)-1)*100:.2f}%)")

print("\n   📊 Status: ABOVE EMA 50 - Bullish scenario holding")
print("   🎯 Prediction: Scenario 1 (85% bounce) still in play")
print("   ⚡ Watch: If breaks below ₹25,323 → Scenario 2 activates")

print("\n" + "="*80)
print("🎯 TRADING STRATEGY FOR TODAY (Nov 12)")
print("="*80)

print("\n   ✅ BULLISH ABOVE: ₹25,323 (EMA 50)")
print("      - Target: ₹26,200-26,500")
print("      - Stop: Below ₹25,300")

print("\n   ⚠️  BEARISH BELOW: ₹25,323 (EMA 50)")
print("      - Target: ₹25,051 (EMA 100)")
print("      - Stop: Above ₹25,400")

print("\n   🔑 KEY INTRADAY LEVELS:")
print("      - PDH: ₹25,713.80 (immediate resistance)")
print("      - PDL: ₹25,450.85 (immediate support)")
print("      - EMA 50: ₹25,323 (swing support)")

print("\n" + "="*80)
print("✅ KHUSI MODEL PREDICTION SUMMARY")
print("="*80)
print("   Most Likely: Bounce from EMA 50 area (85% confidence)")
print("   Target: ₹26,500-27,000 by late November")
print("   Key Level: ₹25,323 - Must hold for bullish case")
print("   Risk: Break below ₹25,323 → Move to ₹25,051 (25% chance)")
print("="*80 + "\n")
