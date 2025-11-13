"""Multi-Timeframe Support/Resistance Analysis with ML Integration"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("=" * 90)
print("Multi-Timeframe Support & Resistance Analysis (15m, 1h, 1d)")
print("=" * 90)

# Load all timeframe data
print("\n✓ Loading data...")
df_15m = pd.read_csv("data/NIFTY_15min_20221024_20251023.csv")
df_1h = pd.read_csv("data/NIFTY_1hour_20221024_20251023.csv")
df_1d = pd.read_csv("data/NIFTY_1day_20221024_20251023.csv")

for df in [df_15m, df_1h, df_1d]:
    df['datetime'] = pd.to_datetime(df['datetime'])

print(f"✓ Loaded 15-min: {len(df_15m)} candles")
print(f"✓ Loaded 1-hour: {len(df_1h)} candles")
print(f"✓ Loaded 1-day: {len(df_1d)} candles")

# Add technical indicators
def add_technical_indicators(df):
    df['is_green'] = df['close'] > df['open']
    df['is_red'] = df['close'] < df['open']
    df['body_size'] = abs(df['close'] - df['open'])
    df['candle_range'] = df['high'] - df['low']
    df['price_change_pct'] = (df['close'] - df['open']) / df['open'] * 100
    df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
    
    # Moving averages
    df['sma_5'] = df['close'].rolling(window=5).mean()
    df['sma_10'] = df['close'].rolling(window=10).mean()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Volume
    df['volume_sma'] = df['volume'].rolling(window=10).mean()
    df['volume_ratio'] = df['volume'] / (df['volume_sma'] + 1)
    
    # Volatility
    df['volatility'] = df['close'].rolling(window=20).std()
    
    # Momentum
    df['momentum_5'] = df['close'] - df['close'].shift(5)
    df['momentum_10'] = df['close'] - df['close'].shift(10)
    
    return df

print("\n" + "=" * 90)
print("Finding Support & Resistance Levels for Each Timeframe...")
print("=" * 90)

def find_support_resistance(df, timeframe):
    """Find support and resistance levels"""
    support_levels = []
    resistance_levels = []
    
    for i in range(1, len(df)):
        prev_candle = df.iloc[i-1]
        curr_candle = df.iloc[i]
        
        # Resistance: Prior green, current red
        if prev_candle['is_green'] and curr_candle['is_red']:
            resistance_price = max(prev_candle['high'], curr_candle['high'])
            resistance_levels.append({
                'type': 'resistance',
                'price': resistance_price,
                'datetime': curr_candle['datetime'],
                'timeframe': timeframe,
                'candle_idx': i,
                'retracement_pct': ((resistance_price - curr_candle['close']) / resistance_price) * 100
            })
        
        # Support: Prior red, current green
        if prev_candle['is_red'] and curr_candle['is_green']:
            support_price = min(prev_candle['low'], curr_candle['low'])
            support_levels.append({
                'type': 'support',
                'price': support_price,
                'datetime': curr_candle['datetime'],
                'timeframe': timeframe,
                'candle_idx': i,
                'retracement_pct': ((curr_candle['close'] - support_price) / support_price) * 100
            })
    
    return pd.DataFrame(resistance_levels), pd.DataFrame(support_levels)

# Find levels for each timeframe
df_15m_with_indicators = add_technical_indicators(df_15m.copy())
df_1h_with_indicators = add_technical_indicators(df_1h.copy())
df_1d_with_indicators = add_technical_indicators(df_1d.copy())

res_15m, sup_15m = find_support_resistance(df_15m_with_indicators, '15m')
res_1h, sup_1h = find_support_resistance(df_1h_with_indicators, '1h')
res_1d, sup_1d = find_support_resistance(df_1d_with_indicators, '1d')

print(f"\n15-minute: {len(res_15m)} resistance, {len(sup_15m)} support")
print(f"1-hour:    {len(res_1h)} resistance, {len(sup_1h)} support")
print(f"1-day:     {len(res_1d)} resistance, {len(sup_1d)} support")

# Calculate strength for all levels
def calculate_strength(levels_df, df_price, tolerance_pct=0.15):
    """Calculate strength of each level based on hits and reversals"""
    strengthened_levels = []
    
    for idx, level in levels_df.iterrows():
        level_price = level['price']
        tolerance = level_price * (tolerance_pct / 100)
        
        if level['type'] == 'resistance':
            touches = df_price[
                (df_price['high'] >= level_price - tolerance) & 
                (df_price['high'] <= level_price + tolerance) &
                (df_price.index > level['candle_idx'])
            ]
        else:
            touches = df_price[
                (df_price['low'] >= level_price - tolerance) & 
                (df_price['low'] <= level_price + tolerance) &
                (df_price.index > level['candle_idx'])
            ]
        
        num_hits = len(touches)
        
        reversals = 0
        for touch_idx in touches.index[:10]:
            if touch_idx + 1 < len(df_price):
                if level['type'] == 'resistance':
                    if df_price.loc[touch_idx + 1, 'close'] < df_price.loc[touch_idx, 'close']:
                        reversals += 1
                else:
                    if df_price.loc[touch_idx + 1, 'close'] > df_price.loc[touch_idx, 'close']:
                        reversals += 1
        
        retracement_score = min(level['retracement_pct'] * 2, 30)
        hits_score = min(num_hits * 5, 40)
        reversal_score = min(reversals * 10, 30)
        strength_score = retracement_score + hits_score + reversal_score
        
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

print("\n" + "=" * 90)
print("Calculating Strength for All Levels...")
print("=" * 90)

# Calculate strength using 15m data for all timeframes (most granular)
df_15m_reset = df_15m_with_indicators.dropna().reset_index(drop=True)

res_15m_strength = calculate_strength(res_15m, df_15m_reset) if len(res_15m) > 0 else pd.DataFrame()
res_1h_strength = calculate_strength(res_1h, df_15m_reset) if len(res_1h) > 0 else pd.DataFrame()
res_1d_strength = calculate_strength(res_1d, df_15m_reset) if len(res_1d) > 0 else pd.DataFrame()

sup_15m_strength = calculate_strength(sup_15m, df_15m_reset) if len(sup_15m) > 0 else pd.DataFrame()
sup_1h_strength = calculate_strength(sup_1h, df_15m_reset) if len(sup_1h) > 0 else pd.DataFrame()
sup_1d_strength = calculate_strength(sup_1d, df_15m_reset) if len(sup_1d) > 0 else pd.DataFrame()

print("✓ Strength calculated for all timeframes")

# Combine all resistance and support levels
all_resistance = pd.concat([res_15m_strength, res_1h_strength, res_1d_strength], ignore_index=True)
all_support = pd.concat([sup_15m_strength, sup_1h_strength, sup_1d_strength], ignore_index=True)

print(f"\nTotal levels before deduplication:")
print(f"  Resistance: {len(all_resistance)}")
print(f"  Support: {len(all_support)}")

# Remove duplicates - keep higher timeframe levels
print("\n" + "=" * 90)
print("Removing Duplicate Levels (Keeping Higher Timeframe)...")
print("=" * 90)

def remove_duplicates(levels_df, tolerance_pct=0.1):
    """Remove duplicate levels, keeping higher timeframe"""
    if len(levels_df) == 0:
        return levels_df
    
    # Sort by price and timeframe priority (1d > 1h > 15m)
    timeframe_priority = {'1d': 3, '1h': 2, '15m': 1}
    levels_df['tf_priority'] = levels_df['timeframe'].map(timeframe_priority)
    levels_df = levels_df.sort_values(['price', 'tf_priority'], ascending=[True, False])
    
    unique_levels = []
    used_prices = []
    
    for idx, level in levels_df.iterrows():
        level_price = level['price']
        tolerance = level_price * (tolerance_pct / 100)
        
        # Check if this price is already covered
        is_duplicate = False
        for used_price in used_prices:
            if abs(level_price - used_price) <= tolerance:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_levels.append(level)
            used_prices.append(level_price)
    
    result_df = pd.DataFrame(unique_levels).drop('tf_priority', axis=1)
    return result_df.reset_index(drop=True)

resistance_unique = remove_duplicates(all_resistance)
support_unique = remove_duplicates(all_support)

print(f"\nAfter deduplication:")
print(f"  Resistance: {len(resistance_unique)} (removed {len(all_resistance) - len(resistance_unique)})")
print(f"  Support: {len(support_unique)} (removed {len(all_support) - len(support_unique)})")

# Show timeframe distribution
print(f"\nResistance by timeframe:")
print(resistance_unique['timeframe'].value_counts().to_string())
print(f"\nSupport by timeframe:")
print(support_unique['timeframe'].value_counts().to_string())

# Save deduplicated levels
resistance_unique.to_csv('data/NIFTY_resistance_multi_timeframe.csv', index=False)
support_unique.to_csv('data/NIFTY_support_multi_timeframe.csv', index=False)

print("\n✓ Saved deduplicated levels:")
print("  - data/NIFTY_resistance_multi_timeframe.csv")
print("  - data/NIFTY_support_multi_timeframe.csv")

# Now perform breakout analysis for each timeframe
print("\n" + "=" * 90)
print("Analyzing Breakout Probabilities for Each Timeframe...")
print("=" * 90)

def analyze_breakouts(df_price, resistance_levels, timeframe_name, candle_interval_mins):
    """Analyze breakout events and calculate probabilities"""
    print(f"\n{timeframe_name}:")
    print("-" * 90)
    
    breakout_events = []
    tolerance_pct = 0.15
    
    df_price_clean = df_price.dropna().reset_index(drop=True)
    lookforward = min(50, len(df_price_clean) // 10)
    
    for i in range(len(df_price_clean) - lookforward):
        candle = df_price_clean.iloc[i]
        
        nearby_resistance = resistance_levels[
            (resistance_levels['price'] >= candle['low'] - (candle['low'] * tolerance_pct / 100)) &
            (resistance_levels['price'] <= candle['high'] + (candle['high'] * tolerance_pct / 100)) &
            (resistance_levels['datetime'] < candle['datetime'])
        ]
        
        for _, res_level in nearby_resistance.iterrows():
            if candle['close'] > res_level['price']:
                future_prices = df_price_clean.iloc[i+1:i+1+lookforward]['high'].values
                
                if len(future_prices) == 0:
                    continue
                
                max_gain = max(future_prices) - candle['close']
                
                hit_10 = max_gain >= 10
                hit_20 = max_gain >= 20
                hit_30 = max_gain >= 30
                hit_50 = max_gain >= 50
                hit_100 = max_gain >= 100
                
                candles_to_10 = np.where(future_prices >= candle['close'] + 10)[0]
                candles_to_20 = np.where(future_prices >= candle['close'] + 20)[0]
                candles_to_30 = np.where(future_prices >= candle['close'] + 30)[0]
                candles_to_50 = np.where(future_prices >= candle['close'] + 50)[0]
                
                breakout_events.append({
                    'datetime': candle['datetime'],
                    'timeframe': timeframe_name,
                    'breakout_price': candle['close'],
                    'resistance_level': res_level['price'],
                    'resistance_strength': res_level['strength'],
                    'resistance_timeframe': res_level['timeframe'],
                    'resistance_hits': res_level['num_hits'],
                    'resistance_reversals': res_level['num_reversals'],
                    'price_change_pct': candle.get('price_change_pct', 0),
                    'candle_range': candle['candle_range'],
                    'rsi': candle.get('rsi', 50),
                    'volume_ratio': candle.get('volume_ratio', 1),
                    'volatility': candle.get('volatility', 0),
                    'momentum_5': candle.get('momentum_5', 0),
                    'max_gain': max_gain,
                    'hit_10': hit_10,
                    'hit_20': hit_20,
                    'hit_30': hit_30,
                    'hit_50': hit_50,
                    'hit_100': hit_100,
                    'time_to_10': (candles_to_10[0] + 1) * candle_interval_mins if len(candles_to_10) > 0 else None,
                    'time_to_20': (candles_to_20[0] + 1) * candle_interval_mins if len(candles_to_20) > 0 else None,
                    'time_to_30': (candles_to_30[0] + 1) * candle_interval_mins if len(candles_to_30) > 0 else None,
                    'time_to_50': (candles_to_50[0] + 1) * candle_interval_mins if len(candles_to_50) > 0 else None,
                })
    
    if len(breakout_events) == 0:
        print("  No breakout events found")
        return None
    
    df_breakouts = pd.DataFrame(breakout_events)
    
    print(f"  Found {len(df_breakouts)} breakout events")
    print(f"  Target Hit Rates:")
    print(f"    10 points:  {df_breakouts['hit_10'].mean()*100:.1f}%")
    print(f"    20 points:  {df_breakouts['hit_20'].mean()*100:.1f}%")
    print(f"    30 points:  {df_breakouts['hit_30'].mean()*100:.1f}%")
    print(f"    50 points:  {df_breakouts['hit_50'].mean()*100:.1f}%")
    print(f"    100 points: {df_breakouts['hit_100'].mean()*100:.1f}%")
    
    if df_breakouts['time_to_10'].notna().sum() > 0:
        print(f"  Avg Time to +10pts: {df_breakouts['time_to_10'].mean():.0f} minutes")
    if df_breakouts['time_to_20'].notna().sum() > 0:
        print(f"  Avg Time to +20pts: {df_breakouts['time_to_20'].mean():.0f} minutes")
    if df_breakouts['time_to_30'].notna().sum() > 0:
        print(f"  Avg Time to +30pts: {df_breakouts['time_to_30'].mean():.0f} minutes")
    if df_breakouts['time_to_50'].notna().sum() > 0:
        print(f"  Avg Time to +50pts: {df_breakouts['time_to_50'].mean():.0f} minutes")
    
    return df_breakouts

# Analyze each timeframe
breakouts_15m = analyze_breakouts(df_15m_with_indicators, resistance_unique, '15-minute', 15)
breakouts_1h = analyze_breakouts(df_1h_with_indicators, resistance_unique, '1-hour', 60)
breakouts_1d = analyze_breakouts(df_1d_with_indicators, resistance_unique, '1-day', 390)  # 6.5 trading hours

# Combine all breakouts
all_breakouts = pd.concat([
    df for df in [breakouts_15m, breakouts_1h, breakouts_1d] if df is not None
], ignore_index=True)

print(f"\n✓ Total breakout events across all timeframes: {len(all_breakouts)}")

# Save combined breakouts
all_breakouts.to_csv('data/NIFTY_breakouts_multi_timeframe.csv', index=False)
print("✓ Saved: data/NIFTY_breakouts_multi_timeframe.csv")

# Train integrated ML models
print("\n" + "=" * 90)
print("Training Integrated ML Models...")
print("=" * 90)

feature_columns = ['price_change_pct', 'candle_range', 'rsi', 'volume_ratio',
                   'volatility', 'momentum_5', 'resistance_hits', 'resistance_reversals']

# Encode categorical variables
strength_map = {'Weak': 0, 'Moderate': 1, 'Strong': 2, 'Very Strong': 3}
timeframe_map = {'15-minute': 1, '1-hour': 2, '1-day': 3}
res_timeframe_map = {'15m': 1, '1h': 2, '1d': 3}

all_breakouts['strength_encoded'] = all_breakouts['resistance_strength'].map(strength_map)
all_breakouts['timeframe_encoded'] = all_breakouts['timeframe'].map(timeframe_map)
all_breakouts['res_timeframe_encoded'] = all_breakouts['resistance_timeframe'].map(res_timeframe_map)

feature_columns.extend(['strength_encoded', 'timeframe_encoded', 'res_timeframe_encoded'])

X = all_breakouts[feature_columns].fillna(0)

ml_results = {}

for target, target_name in [('hit_10', '10pts'), ('hit_20', '20pts'),
                             ('hit_30', '30pts'), ('hit_50', '50pts')]:
    
    if all_breakouts[target].sum() < 10:
        continue
    
    y = all_breakouts[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    rf_model = RandomForestClassifier(n_estimators=150, random_state=42, max_depth=12)
    rf_model.fit(X_train_scaled, y_train)
    
    gb_model = GradientBoostingClassifier(n_estimators=150, random_state=42, max_depth=6)
    gb_model.fit(X_train_scaled, y_train)
    
    rf_score = rf_model.score(X_test_scaled, y_test)
    gb_score = gb_model.score(X_test_scaled, y_test)
    
    ml_results[target_name] = {
        'rf_model': rf_model,
        'gb_model': gb_model,
        'scaler': scaler,
        'rf_accuracy': rf_score,
        'gb_accuracy': gb_score,
        'baseline': y.mean()
    }
    
    print(f"\n{target_name}:")
    print(f"  RF Accuracy: {rf_score*100:.1f}%  |  GB Accuracy: {gb_score*100:.1f}%  |  Baseline: {y.mean()*100:.1f}%")

# Summary by timeframe
print("\n" + "=" * 90)
print("Summary by Timeframe:")
print("=" * 90)

for tf in ['15-minute', '1-hour', '1-day']:
    tf_data = all_breakouts[all_breakouts['timeframe'] == tf]
    if len(tf_data) > 0:
        print(f"\n{tf}:")
        print(f"  Breakouts: {len(tf_data)}")
        print(f"  +10pts: {tf_data['hit_10'].mean()*100:.1f}%  |  +20pts: {tf_data['hit_20'].mean()*100:.1f}%  |  +30pts: {tf_data['hit_30'].mean()*100:.1f}%  |  +50pts: {tf_data['hit_50'].mean()*100:.1f}%")

print("\n" + "=" * 90)
print("✓ Multi-Timeframe Analysis Complete!")
print("=" * 90)
print(f"\nKey Results:")
print(f"  • Unique Resistance Levels: {len(resistance_unique)}")
print(f"  • Unique Support Levels: {len(support_unique)}")
print(f"  • Total Breakout Events: {len(all_breakouts)}")
print(f"  • Overall +10pts Success: {all_breakouts['hit_10'].mean()*100:.1f}%")
print(f"  • Overall +20pts Success: {all_breakouts['hit_20'].mean()*100:.1f}%")
print(f"  • Overall +50pts Success: {all_breakouts['hit_50'].mean()*100:.1f}%")
print("=" * 90)
