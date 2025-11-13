"""Find Support and Resistance levels in 15-minute NIFTY data"""
import pandas as pd
import numpy as np

print("=" * 80)
print("NIFTY Support & Resistance Analysis (15-Minute Data)")
print("=" * 80)

# Load 15-minute data
input_file = "data/NIFTY_15min_20221024_20251023.csv"
print(f"\n✓ Loading data from: {input_file}")

df = pd.read_csv(input_file)
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values('datetime').reset_index(drop=True)

print(f"✓ Loaded {len(df):,} candles")

# Determine candle color
df['is_green'] = df['close'] > df['open']
df['is_red'] = df['close'] < df['open']
df['body_size'] = abs(df['close'] - df['open'])
df['candle_range'] = df['high'] - df['low']

print("\n" + "=" * 80)
print("Identifying Support and Resistance Levels...")
print("=" * 80)

# Lists to store support and resistance levels
resistance_levels = []
support_levels = []

# Iterate through candles to find support/resistance
for i in range(1, len(df)):
    prev_candle = df.iloc[i-1]
    curr_candle = df.iloc[i]
    
    # Condition 1: Prior green, current red = RESISTANCE
    if prev_candle['is_green'] and curr_candle['is_red']:
        resistance_price = max(prev_candle['high'], curr_candle['high'])
        resistance_levels.append({
            'type': 'resistance',
            'price': resistance_price,
            'datetime': curr_candle['datetime'],
            'prev_candle_idx': i-1,
            'curr_candle_idx': i,
            'prev_high': prev_candle['high'],
            'curr_high': curr_candle['high'],
            'prev_close': prev_candle['close'],
            'curr_close': curr_candle['close'],
            'retracement_pct': ((resistance_price - curr_candle['close']) / resistance_price) * 100
        })
    
    # Condition 2: Prior red, current green = SUPPORT
    if prev_candle['is_red'] and curr_candle['is_green']:
        support_price = min(prev_candle['low'], curr_candle['low'])
        support_levels.append({
            'type': 'support',
            'price': support_price,
            'datetime': curr_candle['datetime'],
            'prev_candle_idx': i-1,
            'curr_candle_idx': i,
            'prev_low': prev_candle['low'],
            'curr_low': curr_candle['low'],
            'prev_close': prev_candle['close'],
            'curr_close': curr_candle['close'],
            'retracement_pct': ((curr_candle['close'] - support_price) / support_price) * 100
        })

print(f"\n✓ Found {len(resistance_levels)} resistance levels")
print(f"✓ Found {len(support_levels)} support levels")

# Convert to DataFrames
df_resistance = pd.DataFrame(resistance_levels)
df_support = pd.DataFrame(support_levels)

# Calculate strength based on hits and reversals
def calculate_strength(levels_df, df_price, tolerance_pct=0.1):
    """Calculate strength of each level based on hits and reversals"""
    
    strengthened_levels = []
    
    for idx, level in levels_df.iterrows():
        level_price = level['price']
        tolerance = level_price * (tolerance_pct / 100)
        
        # Find all candles that touched this level (within tolerance)
        if level['type'] == 'resistance':
            # Check highs that touched resistance
            touches = df_price[
                (df_price['high'] >= level_price - tolerance) & 
                (df_price['high'] <= level_price + tolerance) &
                (df_price.index > level['curr_candle_idx'])
            ]
        else:  # support
            # Check lows that touched support
            touches = df_price[
                (df_price['low'] >= level_price - tolerance) & 
                (df_price['low'] <= level_price + tolerance) &
                (df_price.index > level['curr_candle_idx'])
            ]
        
        num_hits = len(touches)
        
        # Count reversals (touches followed by opposite direction move)
        reversals = 0
        for touch_idx in touches.index[:10]:  # Check first 10 touches
            if touch_idx + 1 < len(df_price):
                if level['type'] == 'resistance':
                    # Reversal = price went down after touching resistance
                    if df_price.loc[touch_idx + 1, 'close'] < df_price.loc[touch_idx, 'close']:
                        reversals += 1
                else:  # support
                    # Reversal = price went up after touching support
                    if df_price.loc[touch_idx + 1, 'close'] > df_price.loc[touch_idx, 'close']:
                        reversals += 1
        
        # Calculate strength score
        # Factors: retracement %, number of hits, number of reversals
        retracement_score = min(level['retracement_pct'] * 2, 30)  # Max 30 points
        hits_score = min(num_hits * 5, 40)  # Max 40 points
        reversal_score = min(reversals * 10, 30)  # Max 30 points
        
        strength_score = retracement_score + hits_score + reversal_score
        
        # Classify strength
        if strength_score >= 70:
            strength = "Very Strong"
        elif strength_score >= 50:
            strength = "Strong"
        elif strength_score >= 30:
            strength = "Moderate"
        else:
            strength = "Weak"
        
        strengthened_levels.append({
            **level,
            'num_hits': num_hits,
            'num_reversals': reversals,
            'strength_score': round(strength_score, 2),
            'strength': strength
        })
    
    return pd.DataFrame(strengthened_levels)

print("\n" + "=" * 80)
print("Calculating Strength of Levels...")
print("=" * 80)

# Calculate strength for resistance and support
df_resistance_strength = calculate_strength(df_resistance, df, tolerance_pct=0.1)
df_support_strength = calculate_strength(df_support, df, tolerance_pct=0.1)

# Sort by strength score
df_resistance_strength = df_resistance_strength.sort_values('strength_score', ascending=False)
df_support_strength = df_support_strength.sort_values('strength_score', ascending=False)

print(f"\n✓ Strength analysis complete")

# Display top resistance levels
print("\n" + "=" * 80)
print("TOP 20 RESISTANCE LEVELS (Strongest First)")
print("=" * 80)

if len(df_resistance_strength) > 0:
    top_resistance = df_resistance_strength.head(20)[['datetime', 'price', 'retracement_pct', 'num_hits', 'num_reversals', 'strength_score', 'strength']]
    top_resistance['datetime'] = top_resistance['datetime'].dt.strftime('%Y-%m-%d %H:%M')
    top_resistance['price'] = top_resistance['price'].apply(lambda x: f"₹{x:,.2f}")
    top_resistance['retracement_pct'] = top_resistance['retracement_pct'].apply(lambda x: f"{x:.2f}%")
    print(top_resistance.to_string(index=False))
else:
    print("No resistance levels found")

# Display top support levels
print("\n" + "=" * 80)
print("TOP 20 SUPPORT LEVELS (Strongest First)")
print("=" * 80)

if len(df_support_strength) > 0:
    top_support = df_support_strength.head(20)[['datetime', 'price', 'retracement_pct', 'num_hits', 'num_reversals', 'strength_score', 'strength']]
    top_support['datetime'] = top_support['datetime'].dt.strftime('%Y-%m-%d %H:%M')
    top_support['price'] = top_support['price'].apply(lambda x: f"₹{x:,.2f}")
    top_support['retracement_pct'] = top_support['retracement_pct'].apply(lambda x: f"{x:.2f}%")
    print(top_support.to_string(index=False))
else:
    print("No support levels found")

# Key levels near current price
current_price = df['close'].iloc[-1]
price_range = current_price * 0.02  # 2% range

print("\n" + "=" * 80)
print(f"KEY LEVELS NEAR CURRENT PRICE (₹{current_price:,.2f})")
print("=" * 80)

# Nearby resistance
nearby_resistance = df_resistance_strength[
    (df_resistance_strength['price'] >= current_price) &
    (df_resistance_strength['price'] <= current_price + price_range)
].sort_values('price')

if len(nearby_resistance) > 0:
    print("\nNEARBY RESISTANCE LEVELS (Above Current Price):")
    nearby_res_display = nearby_resistance[['price', 'retracement_pct', 'num_hits', 'num_reversals', 'strength_score', 'strength']].head(10)
    nearby_res_display['price'] = nearby_res_display['price'].apply(lambda x: f"₹{x:,.2f}")
    nearby_res_display['retracement_pct'] = nearby_res_display['retracement_pct'].apply(lambda x: f"{x:.2f}%")
    print(nearby_res_display.to_string(index=False))
else:
    print("\nNo nearby resistance levels found")

# Nearby support
nearby_support = df_support_strength[
    (df_support_strength['price'] <= current_price) &
    (df_support_strength['price'] >= current_price - price_range)
].sort_values('price', ascending=False)

if len(nearby_support) > 0:
    print("\nNEARBY SUPPORT LEVELS (Below Current Price):")
    nearby_sup_display = nearby_support[['price', 'retracement_pct', 'num_hits', 'num_reversals', 'strength_score', 'strength']].head(10)
    nearby_sup_display['price'] = nearby_sup_display['price'].apply(lambda x: f"₹{x:,.2f}")
    nearby_sup_display['retracement_pct'] = nearby_sup_display['retracement_pct'].apply(lambda x: f"{x:.2f}%")
    print(nearby_sup_display.to_string(index=False))
else:
    print("\nNo nearby support levels found")

# Save to CSV
print("\n" + "=" * 80)
print("Saving Results...")
print("=" * 80)

resistance_output = "data/NIFTY_resistance_levels.csv"
support_output = "data/NIFTY_support_levels.csv"

df_resistance_strength.to_csv(resistance_output, index=False)
df_support_strength.to_csv(support_output, index=False)

print(f"\n✓ Resistance levels saved to: {resistance_output}")
print(f"✓ Support levels saved to: {support_output}")

# Summary statistics
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

print(f"\nTotal Resistance Levels: {len(df_resistance_strength)}")
print(f"  Very Strong: {len(df_resistance_strength[df_resistance_strength['strength'] == 'Very Strong'])}")
print(f"  Strong:      {len(df_resistance_strength[df_resistance_strength['strength'] == 'Strong'])}")
print(f"  Moderate:    {len(df_resistance_strength[df_resistance_strength['strength'] == 'Moderate'])}")
print(f"  Weak:        {len(df_resistance_strength[df_resistance_strength['strength'] == 'Weak'])}")

print(f"\nTotal Support Levels: {len(df_support_strength)}")
print(f"  Very Strong: {len(df_support_strength[df_support_strength['strength'] == 'Very Strong'])}")
print(f"  Strong:      {len(df_support_strength[df_support_strength['strength'] == 'Strong'])}")
print(f"  Moderate:    {len(df_support_strength[df_support_strength['strength'] == 'Moderate'])}")
print(f"  Weak:        {len(df_support_strength[df_support_strength['strength'] == 'Weak'])}")

print("\n" + "=" * 80)
print("✓ Analysis Complete!")
print("=" * 80)
