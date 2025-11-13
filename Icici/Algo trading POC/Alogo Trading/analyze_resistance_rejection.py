"""Analyze probability of reversal when candle rejects resistance (high > resistance, close < resistance)"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("=" * 90)
print("Resistance Rejection Analysis - Reversal Probability")
print("=" * 90)

# Load data
print("\n✓ Loading data...")
df_15m = pd.read_csv("data/NIFTY_15min_20221024_20251023.csv")
df_1h = pd.read_csv("data/NIFTY_1hour_20221024_20251023.csv")
df_1d = pd.read_csv("data/NIFTY_1day_20221024_20251023.csv")
resistance_data = pd.read_csv("data/NIFTY_resistance_multi_timeframe.csv")

for df in [df_15m, df_1h, df_1d, resistance_data]:
    df['datetime'] = pd.to_datetime(df['datetime'])

print(f"✓ Loaded 15-min: {len(df_15m)} candles")
print(f"✓ Loaded 1-hour: {len(df_1h)} candles")
print(f"✓ Loaded 1-day: {len(df_1d)} candles")
print(f"✓ Loaded {len(resistance_data)} resistance levels")

# Add technical indicators
def add_technical_indicators(df):
    df['price_change_pct'] = (df['close'] - df['open']) / df['open'] * 100
    df['candle_range'] = df['high'] - df['low']
    df['body_size'] = abs(df['close'] - df['open'])
    df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
    df['wick_ratio'] = df['upper_wick'] / (df['candle_range'] + 0.01)
    
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
    
    return df

print("\n" + "=" * 90)
print("Identifying Resistance Rejection Events...")
print("=" * 90)

def analyze_resistance_rejection(df_price, resistance_levels, timeframe_name, candle_interval_mins):
    """Identify when candle high > resistance but close < resistance (rejection)"""
    print(f"\n{timeframe_name}:")
    print("-" * 90)
    
    df_price_clean = df_price.dropna().reset_index(drop=True)
    rejection_events = []
    tolerance_pct = 0.15
    lookforward = min(50, len(df_price_clean) // 10)
    
    for i in range(len(df_price_clean) - lookforward):
        candle = df_price_clean.iloc[i]
        
        # Find resistance levels near this candle
        nearby_resistance = resistance_levels[
            (resistance_levels['price'] >= candle['low'] - (candle['low'] * tolerance_pct / 100)) &
            (resistance_levels['price'] <= candle['high'] + (candle['high'] * tolerance_pct / 100)) &
            (resistance_levels['datetime'] < candle['datetime'])
        ]
        
        for _, res_level in nearby_resistance.iterrows():
            # Check for rejection: high touches/breaks resistance but close is below
            if candle['high'] >= res_level['price'] and candle['close'] < res_level['price']:
                # This is a rejection!
                
                # Calculate future price movements (downward)
                future_lows = df_price_clean.iloc[i+1:i+1+lookforward]['low'].values
                future_closes = df_price_clean.iloc[i+1:i+1+lookforward]['close'].values
                
                if len(future_lows) == 0:
                    continue
                
                # Calculate maximum downward movement
                max_drop = candle['close'] - min(future_lows)
                
                # Check if price dropped (reversal)
                drop_10 = max_drop >= 10
                drop_20 = max_drop >= 20
                drop_30 = max_drop >= 30
                drop_50 = max_drop >= 50
                drop_100 = max_drop >= 100
                
                # Check if next candle closed lower (immediate reversal)
                next_candle_lower = future_closes[0] < candle['close'] if len(future_closes) > 0 else False
                
                # Check if next 3 candles trend lower
                next_3_lower = np.mean(future_closes[:min(3, len(future_closes))]) < candle['close'] if len(future_closes) > 0 else False
                
                # Check if next 5 candles trend lower
                next_5_lower = np.mean(future_closes[:min(5, len(future_closes))]) < candle['close'] if len(future_closes) > 0 else False
                
                # Find time to hit drop targets
                candles_to_10 = np.where(future_lows <= candle['close'] - 10)[0]
                candles_to_20 = np.where(future_lows <= candle['close'] - 20)[0]
                candles_to_30 = np.where(future_lows <= candle['close'] - 30)[0]
                candles_to_50 = np.where(future_lows <= candle['close'] - 50)[0]
                
                # Calculate rejection strength (how far high was above resistance vs where it closed)
                rejection_distance = candle['high'] - res_level['price']
                rejection_pct = (rejection_distance / res_level['price']) * 100
                close_distance_below = res_level['price'] - candle['close']
                close_distance_pct = (close_distance_below / res_level['price']) * 100
                
                rejection_events.append({
                    'datetime': candle['datetime'],
                    'timeframe': timeframe_name,
                    'candle_close': candle['close'],
                    'candle_high': candle['high'],
                    'resistance_level': res_level['price'],
                    'resistance_strength': res_level['strength'],
                    'resistance_timeframe': res_level['timeframe'],
                    'resistance_hits': res_level['num_hits'],
                    'resistance_reversals': res_level['num_reversals'],
                    'rejection_distance': rejection_distance,
                    'rejection_pct': rejection_pct,
                    'close_below_pct': close_distance_pct,
                    'upper_wick': candle['upper_wick'],
                    'wick_ratio': candle['wick_ratio'],
                    'price_change_pct': candle.get('price_change_pct', 0),
                    'candle_range': candle['candle_range'],
                    'body_size': candle['body_size'],
                    'rsi': candle.get('rsi', 50),
                    'volume_ratio': candle.get('volume_ratio', 1),
                    'volatility': candle.get('volatility', 0),
                    'momentum_5': candle.get('momentum_5', 0),
                    'max_drop': max_drop,
                    'next_candle_lower': next_candle_lower,
                    'next_3_lower': next_3_lower,
                    'next_5_lower': next_5_lower,
                    'drop_10': drop_10,
                    'drop_20': drop_20,
                    'drop_30': drop_30,
                    'drop_50': drop_50,
                    'drop_100': drop_100,
                    'time_to_10': (candles_to_10[0] + 1) * candle_interval_mins if len(candles_to_10) > 0 else None,
                    'time_to_20': (candles_to_20[0] + 1) * candle_interval_mins if len(candles_to_20) > 0 else None,
                    'time_to_30': (candles_to_30[0] + 1) * candle_interval_mins if len(candles_to_30) > 0 else None,
                    'time_to_50': (candles_to_50[0] + 1) * candle_interval_mins if len(candles_to_50) > 0 else None,
                })
    
    if len(rejection_events) == 0:
        print("  No rejection events found")
        return None
    
    df_rejections = pd.DataFrame(rejection_events)
    
    print(f"  Found {len(df_rejections)} resistance rejection events")
    print(f"  \n  Reversal Probabilities:")
    print(f"    Next candle lower:    {df_rejections['next_candle_lower'].mean()*100:.1f}%")
    print(f"    Next 3 candles lower: {df_rejections['next_3_lower'].mean()*100:.1f}%")
    print(f"    Next 5 candles lower: {df_rejections['next_5_lower'].mean()*100:.1f}%")
    print(f"  \n  Drop Target Hit Rates:")
    print(f"    10 points drop:  {df_rejections['drop_10'].mean()*100:.1f}%")
    print(f"    20 points drop:  {df_rejections['drop_20'].mean()*100:.1f}%")
    print(f"    30 points drop:  {df_rejections['drop_30'].mean()*100:.1f}%")
    print(f"    50 points drop:  {df_rejections['drop_50'].mean()*100:.1f}%")
    print(f"    100 points drop: {df_rejections['drop_100'].mean()*100:.1f}%")
    
    if df_rejections['time_to_10'].notna().sum() > 0:
        print(f"  \n  Avg Time to Drop Targets:")
        print(f"    -10pts: {df_rejections['time_to_10'].mean():.0f} minutes")
        if df_rejections['time_to_20'].notna().sum() > 0:
            print(f"    -20pts: {df_rejections['time_to_20'].mean():.0f} minutes")
        if df_rejections['time_to_30'].notna().sum() > 0:
            print(f"    -30pts: {df_rejections['time_to_30'].mean():.0f} minutes")
        if df_rejections['time_to_50'].notna().sum() > 0:
            print(f"    -50pts: {df_rejections['time_to_50'].mean():.0f} minutes")
    
    return df_rejections

# Add indicators
df_15m = add_technical_indicators(df_15m)
df_1h = add_technical_indicators(df_1h)
df_1d = add_technical_indicators(df_1d)

# Analyze each timeframe
rejections_15m = analyze_resistance_rejection(df_15m, resistance_data, '15-minute', 15)
rejections_1h = analyze_resistance_rejection(df_1h, resistance_data, '1-hour', 60)
rejections_1d = analyze_resistance_rejection(df_1d, resistance_data, '1-day', 390)

# Combine all rejections
all_rejections = pd.concat([
    df for df in [rejections_15m, rejections_1h, rejections_1d] if df is not None
], ignore_index=True)

print(f"\n✓ Total rejection events across all timeframes: {len(all_rejections)}")

# Save results
all_rejections.to_csv('data/NIFTY_resistance_rejections_analysis.csv', index=False)
print("✓ Saved: data/NIFTY_resistance_rejections_analysis.csv")

# Analyze by resistance strength
print("\n" + "=" * 90)
print("Reversal Probability by Resistance Strength:")
print("=" * 90)

strength_analysis = all_rejections.groupby('resistance_strength').agg({
    'next_candle_lower': 'mean',
    'next_3_lower': 'mean',
    'next_5_lower': 'mean',
    'drop_10': 'mean',
    'drop_20': 'mean',
    'drop_30': 'mean',
    'drop_50': 'mean',
    'candle_close': 'count'
})
strength_analysis.columns = ['Next Candle↓', 'Next 3↓', 'Next 5↓', '-10pts', '-20pts', '-30pts', '-50pts', 'Count']
strength_analysis = strength_analysis * 100
strength_analysis['Count'] = strength_analysis['Count'] / 100

print("\n" + strength_analysis.round(1).to_string())

# Analyze by wick characteristics
print("\n" + "=" * 90)
print("Reversal Probability by Upper Wick Size:")
print("=" * 90)

# Categorize by wick ratio
all_rejections['wick_category'] = pd.cut(all_rejections['wick_ratio'], 
                                          bins=[0, 0.3, 0.5, 0.7, 1.0],
                                          labels=['Small (<30%)', 'Medium (30-50%)', 'Large (50-70%)', 'Very Large (>70%)'])

wick_analysis = all_rejections.groupby('wick_category').agg({
    'next_candle_lower': 'mean',
    'drop_10': 'mean',
    'drop_20': 'mean',
    'drop_30': 'mean',
    'candle_close': 'count'
})
wick_analysis.columns = ['Next Candle↓', '-10pts', '-20pts', '-30pts', 'Count']
wick_analysis = wick_analysis * 100
wick_analysis['Count'] = wick_analysis['Count'] / 100

print("\n" + wick_analysis.round(1).to_string())

# Train ML models
print("\n" + "=" * 90)
print("Training ML Models for Reversal Prediction...")
print("=" * 90)

feature_columns = ['rejection_pct', 'close_below_pct', 'wick_ratio', 'price_change_pct',
                   'candle_range', 'body_size', 'rsi', 'volume_ratio', 'volatility',
                   'resistance_hits', 'resistance_reversals']

# Encode categorical variables
strength_map = {'Weak': 0, 'Moderate': 1, 'Strong': 2, 'Very Strong': 3}
timeframe_map = {'15-minute': 1, '1-hour': 2, '1-day': 3}
res_timeframe_map = {'15m': 1, '1h': 2, '1d': 3}

all_rejections['strength_encoded'] = all_rejections['resistance_strength'].map(strength_map)
all_rejections['timeframe_encoded'] = all_rejections['timeframe'].map(timeframe_map)
all_rejections['res_timeframe_encoded'] = all_rejections['resistance_timeframe'].map(res_timeframe_map)

feature_columns.extend(['strength_encoded', 'timeframe_encoded', 'res_timeframe_encoded'])

X = all_rejections[feature_columns].fillna(0)

ml_results = {}

for target, target_name in [('next_candle_lower', 'Next Candle Down'), 
                             ('next_3_lower', 'Next 3 Lower'),
                             ('drop_10', '-10pts'), 
                             ('drop_20', '-20pts'),
                             ('drop_30', '-30pts')]:
    
    if all_rejections[target].sum() < 10:
        continue
    
    y = all_rejections[target]
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
    print(f"  RF: {rf_score*100:.1f}%  |  GB: {gb_score*100:.1f}%  |  Baseline: {y.mean()*100:.1f}%")

# Summary by timeframe
print("\n" + "=" * 90)
print("Summary by Timeframe:")
print("=" * 90)

summary_data = []
for tf in ['15-minute', '1-hour', '1-day']:
    tf_data = all_rejections[all_rejections['timeframe'] == tf]
    if len(tf_data) > 0:
        summary_data.append({
            'Timeframe': tf,
            'Rejections': len(tf_data),
            'Next↓': f"{tf_data['next_candle_lower'].mean()*100:.1f}%",
            'Next3↓': f"{tf_data['next_3_lower'].mean()*100:.1f}%",
            '-10pts': f"{tf_data['drop_10'].mean()*100:.1f}%",
            '-20pts': f"{tf_data['drop_20'].mean()*100:.1f}%",
            '-30pts': f"{tf_data['drop_30'].mean()*100:.1f}%",
            '-50pts': f"{tf_data['drop_50'].mean()*100:.1f}%",
            'Avg Time -10pts': f"{tf_data['time_to_10'].mean():.0f}m" if tf_data['time_to_10'].notna().sum() > 0 else 'N/A'
        })

summary_df = pd.DataFrame(summary_data)
print("\n" + summary_df.to_string(index=False))

# Scenario predictions
print("\n" + "=" * 90)
print("Reversal Probability for Different Scenarios:")
print("=" * 90)

scenarios = [
    {
        'name': 'Strong Resistance + Large Upper Wick + High RSI',
        'features': [0.5, 0.3, 0.8, -1.5, 50, 10, 75, 1.2, 30, 20, 5, 3, 1, 3]  # Bearish setup
    },
    {
        'name': 'Weak Resistance + Small Wick + Normal RSI',
        'features': [0.2, 0.1, 0.3, 0.5, 30, 15, 55, 1.0, 20, 5, 2, 0, 1, 1]  # Weak rejection
    },
    {
        'name': 'Very Strong Resistance + Very Large Wick + Overbought',
        'features': [0.8, 0.5, 0.9, -2.0, 70, 15, 80, 1.5, 40, 30, 8, 3, 2, 3]  # Very bearish
    },
]

print("\nFeatures: [rejection_pct, close_below_pct, wick_ratio, price_change_pct, candle_range,")
print("          body_size, rsi, volume_ratio, volatility, resistance_hits, resistance_reversals,")
print("          strength_encoded, timeframe_encoded, res_timeframe_encoded]\n")

for scenario in scenarios:
    print(f"\n{scenario['name']}:")
    print("-" * 90)
    
    X_scenario = np.array([scenario['features']])
    
    for target_name, model_data in ml_results.items():
        X_scaled = model_data['scaler'].transform(X_scenario)
        rf_prob = model_data['rf_model'].predict_proba(X_scaled)[0][1] * 100
        gb_prob = model_data['gb_model'].predict_proba(X_scaled)[0][1] * 100
        avg_prob = (rf_prob + gb_prob) / 2
        
        print(f"  {target_name:20} - RF: {rf_prob:5.1f}%  |  GB: {gb_prob:5.1f}%  |  Avg: {avg_prob:5.1f}%")

print("\n" + "=" * 90)
print("✓ Resistance Rejection Analysis Complete!")
print("=" * 90)

print("\nKey Insights:")
print(f"  • When high > resistance but close < resistance, {all_rejections['next_candle_lower'].mean()*100:.1f}% chance next candle is lower")
print(f"  • {all_rejections['drop_10'].mean()*100:.1f}% probability of -10 point drop after rejection")
print(f"  • {all_rejections['drop_20'].mean()*100:.1f}% probability of -20 point drop after rejection")
print(f"  • Stronger resistance = Higher reversal probability")
print(f"  • Larger upper wick = Stronger rejection signal")
print(f"  • ML models achieved {list(ml_results.values())[0]['gb_accuracy']*100:.1f}% accuracy")
print("=" * 90)
