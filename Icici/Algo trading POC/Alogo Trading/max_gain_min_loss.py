"""
Maximum Gain with Minimum Loss Analysis
Risk-Reward Scenarios for Tomorrow's Market
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Load data
data_dir = Path("data")

df_15m = pd.read_csv(data_dir / "NIFTY_15min_20221024_20251023.csv", parse_dates=['datetime'])
df_1h = pd.read_csv(data_dir / "NIFTY_1hour_20221024_20251023.csv", parse_dates=['datetime'])
df_1d = pd.read_csv(data_dir / "NIFTY_1day_20221024_20251023.csv", parse_dates=['datetime'])

resistance_df = pd.read_csv(data_dir / "NIFTY_resistance_multi_timeframe.csv")
support_df = pd.read_csv(data_dir / "NIFTY_support_multi_timeframe.csv")
rsi_analysis = pd.read_csv(data_dir / "NIFTY_rsi_analysis_combined.csv")

# Calculate RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Current state
current_price = df_15m['close'].iloc[-1]
current_rsi_15m = calculate_rsi(df_15m['close']).iloc[-1]
current_rsi_1h = calculate_rsi(df_1h['close']).iloc[-1]
current_rsi_1d = calculate_rsi(df_1d['close']).iloc[-1]

# Find nearby levels
price_range = current_price * 0.02

nearby_resistance = resistance_df[
    (resistance_df['price'] >= current_price) &
    (resistance_df['price'] <= current_price + price_range)
].sort_values('price').head(5)

nearby_support = support_df[
    (support_df['price'] <= current_price) &
    (support_df['price'] >= current_price - price_range)
].sort_values('price', ascending=False).head(5)

print("=" * 130)
print("MAXIMUM GAIN WITH MINIMUM LOSS - SCENARIO ANALYSIS")
print("=" * 130)

print(f"\n📊 CURRENT MARKET STATE")
print("-" * 130)
print(f"  Price: ₹{current_price:,.2f}")
print(f"  RSI 15m: {current_rsi_15m:.2f} | RSI 1h: {current_rsi_1h:.2f} | RSI Daily: {current_rsi_1d:.2f}")

if len(nearby_resistance) > 0:
    print(f"  Nearest Resistance: ₹{nearby_resistance.iloc[0]['price']:,.2f} ({nearby_resistance.iloc[0]['timeframe']})")
if len(nearby_support) > 0:
    print(f"  Nearest Support: ₹{nearby_support.iloc[0]['price']:,.2f} ({nearby_support.iloc[0]['timeframe']})")

# Analyze each scenario
scenarios = []

tf_map = {'15m': '15-minute', '1h': '1-hour', '1d': '1-day'}

print("\n" + "=" * 130)
print("BULLISH SCENARIOS - MARKET GOES UP")
print("=" * 130)

scenario_num = 1

for idx, res in nearby_resistance.iterrows():
    dist_pct = ((res['price'] - current_price) / current_price) * 100
    dist_pts = res['price'] - current_price
    
    tf_full = tf_map.get(res['timeframe'], res['timeframe'])
    
    # SCENARIO: Breakout above resistance
    breakout_data = rsi_analysis[
        (rsi_analysis['event_type'] == 'breakout') & 
        (rsi_analysis['timeframe'] == tf_full)
    ]
    
    if len(breakout_data) > 0:
        # Calculate statistics
        avg_gain = breakout_data['return_5'].mean()
        median_gain = breakout_data['return_5'].median()
        max_gain = breakout_data['return_5'].max()
        min_gain = breakout_data['return_5'].min()
        
        # Success probabilities
        prob_10 = breakout_data['success_10'].mean() * 100
        prob_20 = breakout_data['success_20'].mean() * 100
        prob_50 = breakout_data['success_50'].mean() * 100
        prob_100 = breakout_data['success_100'].mean() * 100 if 'success_100' in breakout_data.columns else 0
        
        # Calculate potential gain in rupees
        potential_10 = current_price + 10
        potential_20 = current_price + 20
        potential_50 = current_price + 50
        potential_100 = current_price + 100
        
        # Risk (if breakout fails)
        risk_data = rsi_analysis[
            (rsi_analysis['event_type'] == 'rejection') & 
            (rsi_analysis['timeframe'] == tf_full)
        ]
        
        if len(risk_data) > 0:
            avg_loss = risk_data['return_5'].mean()
            worst_loss = risk_data['return_5'].min()
            prob_loss_10 = risk_data['success_10'].mean() * 100  # Probability of -10pts drop
        else:
            avg_loss = -0.5
            worst_loss = -2.0
            prob_loss_10 = 50
        
        print(f"\n{'='*130}")
        print(f"SCENARIO #{scenario_num}: BREAKOUT ABOVE ₹{res['price']:,.2f} ({res['timeframe']})")
        print(f"{'='*130}")
        print(f"Entry Level: ₹{res['price']:,.2f} (Wait for candle to close above)")
        print(f"Distance from current: +{dist_pts:.2f} pts ({dist_pct:+.2f}%)")
        
        print(f"\n{'POTENTIAL GAINS:':<40} {'Probability':<15} {'Target Price':<20} {'Gain':<15}")
        print("-" * 130)
        print(f"{'Target +10 points':<40} {prob_10:>6.1f}% {f'₹{potential_10:,.2f}':>19} {'+₹10/lot':<15}")
        print(f"{'Target +20 points':<40} {prob_20:>6.1f}% {f'₹{potential_20:,.2f}':>19} {'+₹20/lot':<15}")
        print(f"{'Target +50 points':<40} {prob_50:>6.1f}% {f'₹{potential_50:,.2f}':>19} {'+₹50/lot':<15}")
        if prob_100 > 0:
            print(f"{'Target +100 points':<40} {prob_100:>6.1f}% {f'₹{potential_100:,.2f}':>19} {'+₹100/lot':<15}")
        
        print(f"\n{'Historical Returns (5-period):':<40}")
        print(f"{'  Average gain:':<40} {avg_gain:>6.2f}%")
        print(f"{'  Median gain:':<40} {median_gain:>6.2f}%")
        print(f"{'  Best case:':<40} {max_gain:>6.2f}%")
        print(f"{'  Worst case:':<40} {min_gain:>6.2f}%")
        
        print(f"\n{'RISK ANALYSIS (If Breakout Fails - Rejection):':<40}")
        print(f"{'  Probability of reversal:':<40} {prob_loss_10:>6.1f}%")
        print(f"{'  Average loss if rejected:':<40} {avg_loss:>6.2f}%")
        print(f"{'  Worst historical loss:':<40} {worst_loss:>6.2f}%")
        
        # Risk-Reward Ratio
        risk_points = 15  # Typical stop loss
        reward_points_conservative = 10
        reward_points_aggressive = 50
        
        rr_conservative = reward_points_conservative / risk_points
        rr_aggressive = reward_points_aggressive / risk_points
        
        print(f"\n{'RISK-REWARD SETUP:':<40}")
        print(f"{'  Stop Loss:':<40} ₹{res['price'] - risk_points:,.2f} (-{risk_points} pts)")
        print(f"{'  Conservative Target (+10pts):':<40} Risk:Reward = 1:{rr_conservative:.2f} | Success: {prob_10:.1f}%")
        print(f"{'  Aggressive Target (+50pts):':<40} Risk:Reward = 1:{rr_aggressive:.2f} | Success: {prob_50:.1f}%")
        
        # Expected Value calculation
        ev_conservative = (prob_10/100 * 10) - ((100-prob_10)/100 * risk_points)
        ev_aggressive = (prob_50/100 * 50) - ((100-prob_50)/100 * risk_points)
        
        print(f"\n{'EXPECTED VALUE PER TRADE:':<40}")
        print(f"{'  Conservative (+10pts target):':<40} {ev_conservative:>+6.2f} pts per trade")
        print(f"{'  Aggressive (+50pts target):':<40} {ev_aggressive:>+6.2f} pts per trade")
        
        if ev_conservative > 5:
            print(f"\n  💰 EXCELLENT TRADE - Positive expected value of {ev_conservative:.1f} pts!")
        
        # Lot size recommendation
        if res['strength'] in ['Very Strong', 'Strong']:
            print(f"\n  ⭐ {res['strength']} resistance - Trade with HIGHER confidence")
        
        scenarios.append({
            'scenario': f"Breakout above {res['price']:.2f}",
            'type': 'BULLISH',
            'entry': res['price'],
            'stop_loss': res['price'] - risk_points,
            'target_conservative': res['price'] + 10,
            'target_aggressive': res['price'] + 50,
            'prob_success': prob_10,
            'expected_value': ev_conservative,
            'risk_reward': rr_conservative,
            'max_gain_pct': max_gain,
            'avg_loss_pct': avg_loss
        })
        
        scenario_num += 1

print("\n" + "=" * 130)
print("BEARISH SCENARIOS - MARKET GOES DOWN")
print("=" * 130)

for idx, sup in nearby_support.iterrows():
    dist_pct = ((current_price - sup['price']) / current_price) * 100
    dist_pts = current_price - sup['price']
    
    tf_full = tf_map.get(sup['timeframe'], sup['timeframe'])
    
    # SCENARIO: Breakdown below support
    breakdown_data = rsi_analysis[
        (rsi_analysis['event_type'] == 'breakdown') & 
        (rsi_analysis['timeframe'] == tf_full)
    ]
    
    if len(breakdown_data) > 0:
        # Calculate statistics
        avg_drop = breakdown_data['return_5'].mean()
        median_drop = breakdown_data['return_5'].median()
        max_drop = breakdown_data['return_5'].min()  # Most negative
        min_drop = breakdown_data['return_5'].max()  # Least negative
        
        # Success probabilities
        prob_10 = breakdown_data['success_10'].mean() * 100
        prob_20 = breakdown_data['success_20'].mean() * 100
        prob_50 = breakdown_data['success_50'].mean() * 100
        
        # Calculate potential profit in rupees
        potential_10 = current_price - 10
        potential_20 = current_price - 20
        potential_50 = current_price - 50
        
        # Risk (if breakdown fails - bounce)
        risk_data = rsi_analysis[
            (rsi_analysis['event_type'] == 'bounce') & 
            (rsi_analysis['timeframe'] == tf_full)
        ]
        
        if len(risk_data) > 0:
            avg_bounce = risk_data['return_5'].mean()
            worst_bounce = risk_data['return_5'].max()
            prob_bounce_10 = risk_data['success_10'].mean() * 100
        else:
            avg_bounce = 0.5
            worst_bounce = 2.0
            prob_bounce_10 = 50
        
        print(f"\n{'='*130}")
        print(f"SCENARIO #{scenario_num}: BREAKDOWN BELOW ₹{sup['price']:,.2f} ({sup['timeframe']})")
        print(f"{'='*130}")
        print(f"Entry Level: ₹{sup['price']:,.2f} (Wait for candle to close below)")
        print(f"Distance from current: -{dist_pts:.2f} pts ({dist_pct:+.2f}%)")
        
        print(f"\n{'POTENTIAL GAINS (SHORT POSITION):':<40} {'Probability':<15} {'Target Price':<20} {'Gain':<15}")
        print("-" * 130)
        print(f"{'Target -10 points':<40} {prob_10:>6.1f}% {f'₹{potential_10:,.2f}':>19} {'+₹10/lot':<15}")
        print(f"{'Target -20 points':<40} {prob_20:>6.1f}% {f'₹{potential_20:,.2f}':>19} {'+₹20/lot':<15}")
        print(f"{'Target -50 points':<40} {prob_50:>6.1f}% {f'₹{potential_50:,.2f}':>19} {'+₹50/lot':<15}")
        
        print(f"\n{'Historical Returns (5-period):':<40}")
        print(f"{'  Average drop:':<40} {avg_drop:>6.2f}%")
        print(f"{'  Median drop:':<40} {median_drop:>6.2f}%")
        print(f"{'  Best case (max drop):':<40} {max_drop:>6.2f}%")
        print(f"{'  Worst case (min drop):':<40} {min_drop:>6.2f}%")
        
        print(f"\n{'RISK ANALYSIS (If Breakdown Fails - Bounce):':<40}")
        print(f"{'  Probability of bounce:':<40} {prob_bounce_10:>6.1f}%")
        print(f"{'  Average bounce if fails:':<40} {avg_bounce:>6.2f}%")
        print(f"{'  Worst historical bounce:':<40} {worst_bounce:>6.2f}%")
        
        # Risk-Reward Ratio
        risk_points = 15
        reward_points_conservative = 10
        reward_points_aggressive = 50
        
        rr_conservative = reward_points_conservative / risk_points
        rr_aggressive = reward_points_aggressive / risk_points
        
        print(f"\n{'RISK-REWARD SETUP (SHORT):':<40}")
        print(f"{'  Stop Loss:':<40} ₹{sup['price'] + risk_points:,.2f} (+{risk_points} pts)")
        print(f"{'  Conservative Target (-10pts):':<40} Risk:Reward = 1:{rr_conservative:.2f} | Success: {prob_10:.1f}%")
        print(f"{'  Aggressive Target (-50pts):':<40} Risk:Reward = 1:{rr_aggressive:.2f} | Success: {prob_50:.1f}%")
        
        # Expected Value
        ev_conservative = (prob_10/100 * 10) - ((100-prob_10)/100 * risk_points)
        ev_aggressive = (prob_50/100 * 50) - ((100-prob_50)/100 * risk_points)
        
        print(f"\n{'EXPECTED VALUE PER TRADE (SHORT):':<40}")
        print(f"{'  Conservative (-10pts target):':<40} {ev_conservative:>+6.2f} pts per trade")
        print(f"{'  Aggressive (-50pts target):':<40} {ev_aggressive:>+6.2f} pts per trade")
        
        if ev_conservative > 5:
            print(f"\n  💰 EXCELLENT SHORT - Positive expected value of {ev_conservative:.1f} pts!")
        
        if sup['strength'] in ['Very Strong', 'Strong']:
            print(f"\n  ⭐ {sup['strength']} support - Breakdown has HIGHER impact if it breaks")
        
        scenarios.append({
            'scenario': f"Breakdown below {sup['price']:.2f}",
            'type': 'BEARISH',
            'entry': sup['price'],
            'stop_loss': sup['price'] + risk_points,
            'target_conservative': sup['price'] - 10,
            'target_aggressive': sup['price'] - 50,
            'prob_success': prob_10,
            'expected_value': ev_conservative,
            'risk_reward': rr_conservative,
            'max_gain_pct': abs(max_drop),
            'avg_loss_pct': avg_bounce
        })
        
        scenario_num += 1

# Summary table
print("\n" + "=" * 130)
print("SUMMARY - BEST RISK-REWARD SCENARIOS")
print("=" * 130)

scenarios_df = pd.DataFrame(scenarios)
scenarios_df = scenarios_df.sort_values('expected_value', ascending=False)

print(f"\n{'Rank':<6} {'Scenario':<35} {'Type':<10} {'Entry':<12} {'Target':<12} {'Success%':<10} {'Exp.Value':<12} {'Risk:Reward'}")
print("-" * 130)

for rank, (idx, row) in enumerate(scenarios_df.head(10).iterrows(), 1):
    print(f"{rank:<6} {row['scenario']:<35} {row['type']:<10} ₹{row['entry']:>9,.2f} ₹{row['target_conservative']:>9,.2f} "
          f"{row['prob_success']:>8.1f}% {row['expected_value']:>+10.2f}pts  1:{row['risk_reward']:.2f}")

print("\n" + "=" * 130)
print("OPTIMAL TRADING STRATEGY")
print("=" * 130)

best_scenario = scenarios_df.iloc[0]

print(f"\n🎯 HIGHEST EXPECTED VALUE TRADE:")
print(f"  Scenario: {best_scenario['scenario']}")
print(f"  Type: {best_scenario['type']}")
print(f"  Entry: ₹{best_scenario['entry']:,.2f}")
print(f"  Stop Loss: ₹{best_scenario['stop_loss']:,.2f}")
print(f"  Target: ₹{best_scenario['target_conservative']:,.2f} (Conservative) | ₹{best_scenario['target_aggressive']:,.2f} (Aggressive)")
print(f"  Success Probability: {best_scenario['prob_success']:.1f}%")
print(f"  Expected Value: {best_scenario['expected_value']:+.2f} pts per trade")
print(f"  Risk:Reward Ratio: 1:{best_scenario['risk_reward']:.2f}")

print(f"\n💡 POSITION SIZING:")
lot_size_50 = 50  # NIFTY lot size
capital = 100000  # Example capital

risk_per_trade = 0.02  # 2% risk
risk_amount = capital * risk_per_trade
risk_points = abs(best_scenario['entry'] - best_scenario['stop_loss'])
lots = int(risk_amount / (risk_points * lot_size_50))

print(f"  With ₹{capital:,} capital and 2% risk per trade:")
print(f"  → Risk per trade: ₹{risk_amount:,.0f}")
print(f"  → Risk per lot: {risk_points:.1f} pts × {lot_size_50} = ₹{risk_points * lot_size_50:,.0f}")
print(f"  → Recommended lots: {lots}")
print(f"  → Potential profit (conservative): ₹{lots * 10 * lot_size_50:,.0f}")
print(f"  → Potential loss (if wrong): ₹{lots * risk_points * lot_size_50:,.0f}")

print("\n" + "=" * 130)
print("✓ ANALYSIS COMPLETE - Trade with discipline and proper risk management!")
print("=" * 130)
