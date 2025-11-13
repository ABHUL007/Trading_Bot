"""
Tomorrow's Market Prediction Based on Current Position
Uses: Resistance/Support levels, RSI, and historical patterns
Analyzes: Breakouts, Breakdowns, Rejections, Bounces
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Load data
data_dir = Path("data")

# Load price data
df_15m = pd.read_csv(data_dir / "NIFTY_15min_20221024_20251023.csv", parse_dates=['datetime'])
df_1h = pd.read_csv(data_dir / "NIFTY_1hour_20221024_20251023.csv", parse_dates=['datetime'])
df_1d = pd.read_csv(data_dir / "NIFTY_1day_20221024_20251023.csv", parse_dates=['datetime'])

# Load S/R levels
resistance_df = pd.read_csv(data_dir / "NIFTY_resistance_multi_timeframe.csv")
support_df = pd.read_csv(data_dir / "NIFTY_support_multi_timeframe.csv")

# Load RSI analysis
rsi_analysis = pd.read_csv(data_dir / "NIFTY_rsi_analysis_combined.csv")

# Calculate RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Get current market state
current_price = df_15m['close'].iloc[-1]
current_rsi_15m = calculate_rsi(df_15m['close']).iloc[-1]
current_rsi_1h = calculate_rsi(df_1h['close']).iloc[-1]
current_rsi_1d = calculate_rsi(df_1d['close']).iloc[-1]

# Find nearby levels
price_range = current_price * 0.015  # 1.5% range

nearby_resistance = resistance_df[
    (resistance_df['price'] >= current_price) &
    (resistance_df['price'] <= current_price + price_range)
].sort_values('price').head(10)

nearby_support = support_df[
    (support_df['price'] <= current_price) &
    (support_df['price'] >= current_price - price_range)
].sort_values('price', ascending=False).head(10)

print("=" * 120)
print("TOMORROW'S MARKET PREDICTION - Based on Current Conditions & Historical Patterns")
print("=" * 120)

print(f"\n📊 CURRENT MARKET STATE (as of {df_15m['datetime'].iloc[-1]})")
print("-" * 120)
print(f"  Current Price:     ₹{current_price:,.2f}")
print(f"  RSI (15-min):      {current_rsi_15m:.2f} {'🔴 OVERBOUGHT' if current_rsi_15m >= 70 else '🟢 OVERSOLD' if current_rsi_15m <= 30 else '⚪ NEUTRAL'}")
print(f"  RSI (1-hour):      {current_rsi_1h:.2f} {'🔴 OVERBOUGHT' if current_rsi_1h >= 70 else '🟢 OVERSOLD' if current_rsi_1h <= 30 else '⚪ NEUTRAL'}")
print(f"  RSI (Daily):       {current_rsi_1d:.2f} {'🔴 OVERBOUGHT' if current_rsi_1d >= 70 else '🟢 OVERSOLD' if current_rsi_1d <= 30 else '⚪ NEUTRAL'}")

# Calculate distances to nearest levels
if len(nearby_resistance) > 0:
    nearest_resistance = nearby_resistance.iloc[0]
    dist_to_resistance = ((nearest_resistance['price'] - current_price) / current_price) * 100
    print(f"\n  Nearest Resistance: ₹{nearest_resistance['price']:,.2f} ({nearest_resistance['timeframe']}) - {dist_to_resistance:.2f}% away")
    print(f"    Strength: {nearest_resistance['strength']}, Hits: {nearest_resistance['num_hits']}")

if len(nearby_support) > 0:
    nearest_support = nearby_support.iloc[0]
    dist_to_support = ((current_price - nearest_support['price']) / current_price) * 100
    print(f"  Nearest Support:    ₹{nearest_support['price']:,.2f} ({nearest_support['timeframe']}) - {dist_to_support:.2f}% away")
    print(f"    Strength: {nearest_support['strength']}, Hits: {nearest_support['num_hits']}")

print("\n" + "=" * 120)
print("SCENARIO 1: IF MARKET GOES UP TOMORROW (BULLISH MOVE)")
print("=" * 120)

if len(nearby_resistance) > 0:
    for idx, res in nearby_resistance.iterrows():
        dist_pct = ((res['price'] - current_price) / current_price) * 100
        
        print(f"\n📈 Approaching Resistance: ₹{res['price']:,.2f} ({res['timeframe']}) - {dist_pct:.2f}% away")
        print("-" * 120)
        
        # Get historical probabilities for this timeframe
        tf_map = {'15m': '15-minute', '1h': '1-hour', '1d': '1-day'}
        tf_full = tf_map.get(res['timeframe'], res['timeframe'])
        
        # SCENARIO A: BREAKOUT (close above resistance)
        breakout_data = rsi_analysis[
            (rsi_analysis['event_type'] == 'breakout') & 
            (rsi_analysis['timeframe'] == tf_full)
        ]
        
        if len(breakout_data) > 0:
            print(f"\n  🟢 SCENARIO A: Price BREAKS ABOVE ₹{res['price']:,.2f}")
            
            # If RSI is overbought
            if current_rsi_1h >= 70 or current_rsi_1d >= 70:
                breakout_overbought = breakout_data[breakout_data['rsi_at_event'] >= 70]
                if len(breakout_overbought) > 0:
                    print(f"     With OVERBOUGHT RSI (≥70) - {len(breakout_overbought)} historical cases:")
                    print(f"       ✓ +10pts success: {breakout_overbought['success_10'].mean()*100:5.1f}%")
                    print(f"       ✓ +20pts success: {breakout_overbought['success_20'].mean()*100:5.1f}%")
                    print(f"       ✓ +50pts success: {breakout_overbought['success_50'].mean()*100:5.1f}%")
                    print(f"       → Median gain: {breakout_overbought['return_5'].mean():+.2f}% (5-period)")
                    
                    if breakout_overbought['success_10'].mean() >= 0.95:
                        print(f"       💡 STRONG MOMENTUM - Even with overbought RSI, breakout succeeds {breakout_overbought['success_10'].mean()*100:.0f}%!")
            
            # If RSI is neutral/oversold
            else:
                breakout_normal = breakout_data[breakout_data['rsi_at_event'] < 70]
                if len(breakout_normal) > 0:
                    print(f"     With NEUTRAL/OVERSOLD RSI (<70) - {len(breakout_normal)} historical cases:")
                    print(f"       ✓ +10pts success: {breakout_normal['success_10'].mean()*100:5.1f}%")
                    print(f"       ✓ +20pts success: {breakout_normal['success_20'].mean()*100:5.1f}%")
                    print(f"       ✓ +50pts success: {breakout_normal['success_50'].mean()*100:5.1f}%")
                    print(f"       → Median gain: {breakout_normal['return_5'].mean():+.2f}% (5-period)")
                    
                    if breakout_normal['success_10'].mean() >= 0.90:
                        print(f"       💡 EXCELLENT - Fresh RSI with breakout = {breakout_normal['success_10'].mean()*100:.0f}% success!")
        
        # SCENARIO B: REJECTION (touches resistance but closes below)
        rejection_data = rsi_analysis[
            (rsi_analysis['event_type'] == 'rejection') & 
            (rsi_analysis['timeframe'] == tf_full)
        ]
        
        if len(rejection_data) > 0:
            print(f"\n  🔴 SCENARIO B: Price TOUCHES but REJECTS at ₹{res['price']:,.2f}")
            
            # If RSI is overbought - BEST SHORT SIGNAL
            if current_rsi_1h >= 70 or current_rsi_1d >= 70:
                rejection_overbought = rejection_data[rejection_data['rsi_at_event'] >= 70]
                if len(rejection_overbought) > 0:
                    print(f"     With OVERBOUGHT RSI (≥70) - {len(rejection_overbought)} historical cases:")
                    print(f"       ✓ -10pts drop: {rejection_overbought['success_10'].mean()*100:5.1f}%")
                    print(f"       ✓ -20pts drop: {rejection_overbought['success_20'].mean()*100:5.1f}%")
                    print(f"       ✓ -50pts drop: {rejection_overbought['success_50'].mean()*100:5.1f}%")
                    print(f"       → Median prior return: {rejection_overbought['return_5'].mean():+.2f}%")
                    
                    if rejection_overbought['success_10'].mean() >= 0.85:
                        print(f"       🚨 HIGH PROBABILITY SHORT - Overbought rejection = {rejection_overbought['success_10'].mean()*100:.0f}% drop!")
            
            # If RSI is oversold - rejection less reliable
            elif current_rsi_1h <= 30 or current_rsi_1d <= 30:
                rejection_oversold = rejection_data[rejection_data['rsi_at_event'] <= 30]
                if len(rejection_oversold) > 0:
                    print(f"     With OVERSOLD RSI (≤30) - {len(rejection_oversold)} historical cases:")
                    print(f"       ✓ -10pts drop: {rejection_oversold['success_10'].mean()*100:5.1f}%")
                    print(f"       ✓ -20pts drop: {rejection_oversold['success_20'].mean()*100:5.1f}%")
                    print(f"       💡 Oversold RSI often leads to eventual breakout after rejection")

print("\n" + "=" * 120)
print("SCENARIO 2: IF MARKET GOES DOWN TOMORROW (BEARISH MOVE)")
print("=" * 120)

if len(nearby_support) > 0:
    for idx, sup in nearby_support.iterrows():
        dist_pct = ((current_price - sup['price']) / current_price) * 100
        
        print(f"\n📉 Approaching Support: ₹{sup['price']:,.2f} ({sup['timeframe']}) - {dist_pct:.2f}% away")
        print("-" * 120)
        
        tf_map = {'15m': '15-minute', '1h': '1-hour', '1d': '1-day'}
        tf_full = tf_map.get(sup['timeframe'], sup['timeframe'])
        
        # SCENARIO A: BREAKDOWN (close below support)
        breakdown_data = rsi_analysis[
            (rsi_analysis['event_type'] == 'breakdown') & 
            (rsi_analysis['timeframe'] == tf_full)
        ]
        
        if len(breakdown_data) > 0:
            print(f"\n  🔴 SCENARIO A: Price BREAKS BELOW ₹{sup['price']:,.2f}")
            
            # If RSI is oversold - extreme selling
            if current_rsi_1h <= 30 or current_rsi_1d <= 30:
                breakdown_oversold = breakdown_data[breakdown_data['rsi_at_event'] <= 30]
                if len(breakdown_oversold) > 0:
                    print(f"     With OVERSOLD RSI (≤30) - {len(breakdown_oversold)} historical cases:")
                    print(f"       ✓ -10pts drop: {breakdown_oversold['success_10'].mean()*100:5.1f}%")
                    print(f"       ✓ -20pts drop: {breakdown_oversold['success_20'].mean()*100:5.1f}%")
                    print(f"       ✓ -50pts drop: {breakdown_oversold['success_50'].mean()*100:5.1f}%")
                    print(f"       → Median prior return: {breakdown_oversold['return_5'].mean():+.2f}%")
                    
                    if breakdown_oversold['success_10'].mean() >= 0.90:
                        print(f"       🚨 PANIC SELLING - Oversold breakdown = {breakdown_oversold['success_10'].mean()*100:.0f}% further drop!")
                    else:
                        print(f"       💡 CAUTION - Oversold can lead to exhaustion/bounce soon")
            
            # If RSI is overbought/neutral
            else:
                breakdown_normal = breakdown_data[breakdown_data['rsi_at_event'] >= 30]
                if len(breakdown_normal) > 0:
                    print(f"     With NEUTRAL/OVERBOUGHT RSI (≥30) - {len(breakdown_normal)} historical cases:")
                    print(f"       ✓ -10pts drop: {breakdown_normal['success_10'].mean()*100:5.1f}%")
                    print(f"       ✓ -20pts drop: {breakdown_normal['success_20'].mean()*100:5.1f}%")
                    print(f"       ✓ -50pts drop: {breakdown_normal['success_50'].mean()*100:5.1f}%")
                    
                    if breakdown_normal['success_10'].mean() >= 0.90:
                        print(f"       💡 CLEAR BREAKDOWN - Fresh selling pressure with {breakdown_normal['success_10'].mean()*100:.0f}% success!")
        
        # SCENARIO B: BOUNCE (touches support but closes above)
        bounce_data = rsi_analysis[
            (rsi_analysis['event_type'] == 'bounce') & 
            (rsi_analysis['timeframe'] == tf_full)
        ]
        
        if len(bounce_data) > 0:
            print(f"\n  🟢 SCENARIO B: Price TOUCHES but BOUNCES at ₹{sup['price']:,.2f}")
            
            # If RSI is oversold - BEST BUY SIGNAL
            if current_rsi_1h <= 30 or current_rsi_1d <= 30:
                bounce_oversold = bounce_data[bounce_data['rsi_at_event'] <= 30]
                if len(bounce_oversold) > 0:
                    print(f"     With OVERSOLD RSI (≤30) - {len(bounce_oversold)} historical cases:")
                    print(f"       ✓ +10pts rally: {bounce_oversold['success_10'].mean()*100:5.1f}%")
                    print(f"       ✓ +20pts rally: {bounce_oversold['success_20'].mean()*100:5.1f}%")
                    print(f"       ✓ +50pts rally: {bounce_oversold['success_50'].mean()*100:5.1f}%")
                    print(f"       → Median prior return: {bounce_oversold['return_5'].mean():+.2f}%")
                    
                    if bounce_oversold['success_10'].mean() >= 0.90:
                        print(f"       🎯 EXCELLENT BUY - Oversold bounce = {bounce_oversold['success_10'].mean()*100:.0f}% rally!")
            
            # If RSI is overbought
            elif current_rsi_1h >= 70 or current_rsi_1d >= 70:
                bounce_overbought = bounce_data[bounce_data['rsi_at_event'] >= 70]
                if len(bounce_overbought) > 0:
                    print(f"     With OVERBOUGHT RSI (≥70) - {len(bounce_overbought)} historical cases:")
                    print(f"       ✓ +10pts rally: {bounce_overbought['success_10'].mean()*100:5.1f}%")
                    print(f"       ✓ +20pts rally: {bounce_overbought['success_20'].mean()*100:5.1f}%")
                    print(f"       💡 Overbought bounce still works but momentum may fade")

# Summary recommendations
print("\n" + "=" * 120)
print("📋 TOMORROW'S TRADING PLAN - HIGHEST PROBABILITY SETUPS")
print("=" * 120)

print("\n🎯 PRIMARY SETUPS (>90% Success Rate):")
print("-" * 120)

signals = []

# Check for oversold bounce setup
if current_rsi_1h <= 30 or current_rsi_1d <= 30:
    if len(nearby_support) > 0:
        nearest_sup = nearby_support.iloc[0]
        bounce_tf = rsi_analysis[
            (rsi_analysis['event_type'] == 'bounce') & 
            (rsi_analysis['timeframe'] == tf_map.get(nearest_sup['timeframe'], nearest_sup['timeframe'])) &
            (rsi_analysis['rsi_at_event'] <= 30)
        ]
        if len(bounce_tf) > 0 and bounce_tf['success_10'].mean() >= 0.90:
            signals.append(f"🟢 BUY if price touches ₹{nearest_sup['price']:,.2f} and holds (RSI oversold)")
            signals.append(f"   → Target: +10pts ({bounce_tf['success_10'].mean()*100:.0f}% probability)")
            signals.append(f"   → Extended target: +20pts ({bounce_tf['success_20'].mean()*100:.0f}% probability)")

# Check for overbought rejection setup
if current_rsi_1h >= 70 or current_rsi_1d >= 70:
    if len(nearby_resistance) > 0:
        nearest_res = nearby_resistance.iloc[0]
        rejection_tf = rsi_analysis[
            (rsi_analysis['event_type'] == 'rejection') & 
            (rsi_analysis['timeframe'] == tf_map.get(nearest_res['timeframe'], nearest_res['timeframe'])) &
            (rsi_analysis['rsi_at_event'] >= 70)
        ]
        if len(rejection_tf) > 0 and rejection_tf['success_10'].mean() >= 0.80:
            signals.append(f"🔴 SELL/SHORT if price rejects at ₹{nearest_res['price']:,.2f} (RSI overbought)")
            signals.append(f"   → Target: -10pts ({rejection_tf['success_10'].mean()*100:.0f}% probability)")
            signals.append(f"   → Extended target: -20pts ({rejection_tf['success_20'].mean()*100:.0f}% probability)")

# Check for breakout setup
if current_rsi_1h < 70 and len(nearby_resistance) > 0:
    nearest_res = nearby_resistance.iloc[0]
    breakout_tf = rsi_analysis[
        (rsi_analysis['event_type'] == 'breakout') & 
        (rsi_analysis['timeframe'] == tf_map.get(nearest_res['timeframe'], nearest_res['timeframe']))
    ]
    if len(breakout_tf) > 0 and breakout_tf['success_10'].mean() >= 0.90:
        signals.append(f"🟢 BUY on breakout above ₹{nearest_res['price']:,.2f} (Fresh RSI)")
        signals.append(f"   → Target: +10pts ({breakout_tf['success_10'].mean()*100:.0f}% probability)")

# Check for breakdown setup
if current_rsi_1h > 30 and len(nearby_support) > 0:
    nearest_sup = nearby_support.iloc[0]
    breakdown_tf = rsi_analysis[
        (rsi_analysis['event_type'] == 'breakdown') & 
        (rsi_analysis['timeframe'] == tf_map.get(nearest_sup['timeframe'], nearest_sup['timeframe']))
    ]
    if len(breakdown_tf) > 0 and breakdown_tf['success_10'].mean() >= 0.90:
        signals.append(f"🔴 SELL on breakdown below ₹{nearest_sup['price']:,.2f}")
        signals.append(f"   → Target: -10pts ({breakdown_tf['success_10'].mean()*100:.0f}% probability)")

if signals:
    for signal in signals:
        print(signal)
else:
    print("⚪ No high-probability setups at current levels. Wait for price to reach key levels.")

print("\n⚠️  RISK MANAGEMENT:")
print("-" * 120)
print("  • Entry: Only take trades at exact support/resistance levels")
print("  • Stop Loss: Place 15-20 points beyond the level")
print("  • Position Size: Risk only 1-2% per trade")
print("  • Confirmation: Wait for candle close to confirm pattern")
print("  • Best Timeframe: 1-hour signals have highest success rate")

print("\n" + "=" * 120)
print("✓ Analysis Complete!")
print("=" * 120)
