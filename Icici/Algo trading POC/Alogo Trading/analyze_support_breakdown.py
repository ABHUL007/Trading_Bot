"""Analyze Support Breakdown Probability - When price breaks below support"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("=" * 90)
print("Support Breakdown Analysis - Bearish Continuation Probability")
print("=" * 90)

# Load data
print("\n✓ Loading data...")
df_15m = pd.read_csv("data/NIFTY_15min_20221024_20251023.csv")
df_1h = pd.read_csv("data/NIFTY_1hour_20221024_20251023.csv")
df_1d = pd.read_csv("data/NIFTY_1day_20221024_20251023.csv")
support_levels = pd.read_csv("data/NIFTY_support_multi_timeframe.csv")

for df in [df_15m, df_1h, df_1d, support_levels]:
    df['datetime'] = pd.to_datetime(df['datetime'])

print(f"✓ Loaded 15-min: {len(df_15m)} candles")
print(f"✓ Loaded 1-hour: {len(df_1h)} candles")
print(f"✓ Loaded 1-day: {len(df_1d)} candles")
print(f"✓ Loaded {len(support_levels)} support levels")

# Technical indicators
def add_technical_indicators(df):
    df['rsi'] = 100 - (100 / (1 + (df['close'].diff().clip(lower=0).rolling(14).mean() / 
                                     (-df['close'].diff().clip(upper=0).rolling(14).mean() + 1e-10))))
    df['volume_sma'] = df['volume'].rolling(10).mean()
    df['volume_ratio'] = df['volume'] / (df['volume_sma'] + 1)
    df['volatility'] = df['close'].rolling(20).std()
    df['momentum_5'] = df['close'] - df['close'].shift(5)
    return df

df_15m = add_technical_indicators(df_15m)
df_1h = add_technical_indicators(df_1h)
df_1d = add_technical_indicators(df_1d)

print("\n" + "=" * 90)
print("Identifying Support Breakdown Events...")
print("=" * 90)

def analyze_support_breakdowns(df_price, support_df, timeframe):
    """Analyze when price closes below support (breakdown)"""
    breakdowns = []
    
    for idx, support in support_df.iterrows():
        support_price = support['price']
        support_date = support['datetime']
        tolerance = support_price * 0.001  # 0.1% tolerance
        
        # Find candles after support was identified
        future_candles = df_price[df_price['datetime'] > support_date].copy()
        
        for i in range(len(future_candles)):
            candle = future_candles.iloc[i]
            
            # Breakdown: Close below support (bearish)
            if candle['close'] < support_price - tolerance:
                
                # Calculate how far below support
                breakdown_distance = support_price - candle['close']
                breakdown_pct = (breakdown_distance / support_price) * 100
                
                # Look ahead for drop targets
                remaining = future_candles.iloc[i+1:i+101] if i+1 < len(future_candles) else pd.DataFrame()
                
                if len(remaining) > 0:
                    # Check if drop continues (bearish continuation)
                    next_candle_lower = remaining.iloc[0]['close'] < candle['close'] if len(remaining) > 0 else False
                    next_3_lower = remaining.iloc[2]['close'] < candle['close'] if len(remaining) >= 3 else False
                    next_5_lower = remaining.iloc[4]['close'] < candle['close'] if len(remaining) >= 5 else False
                    
                    # Maximum drop after breakdown
                    max_drop = candle['close'] - remaining['low'].min()
                    
                    # Drop target achievements
                    drop_10 = max_drop >= 10
                    drop_20 = max_drop >= 20
                    drop_30 = max_drop >= 30
                    drop_50 = max_drop >= 50
                    drop_100 = max_drop >= 100
                    
                    # Time to reach drop targets
                    def time_to_target(target):
                        for j, r in remaining.iterrows():
                            if candle['close'] - r['low'] >= target:
                                return (r['datetime'] - candle['datetime']).total_seconds() / 60
                        return np.nan
                    
                    time_to_10 = time_to_target(10) if drop_10 else np.nan
                    time_to_20 = time_to_target(20) if drop_20 else np.nan
                    time_to_30 = time_to_target(30) if drop_30 else np.nan
                    time_to_50 = time_to_target(50) if drop_50 else np.nan
                    
                    breakdowns.append({
                        'datetime': candle['datetime'],
                        'timeframe': timeframe,
                        'candle_close': candle['close'],
                        'candle_low': candle['low'],
                        'support_level': support_price,
                        'support_strength': support['strength'],
                        'support_timeframe': support['timeframe'],
                        'support_hits': support['num_hits'],
                        'support_reversals': support['num_reversals'],
                        'breakdown_distance': breakdown_distance,
                        'breakdown_pct': breakdown_pct,
                        'close_below_pct': ((support_price - candle['close']) / support_price) * 100,
                        'lower_wick': candle['low'] - min(candle['open'], candle['close']),
                        'price_change_pct': ((candle['close'] - candle['open']) / candle['open']) * 100,
                        'candle_range': candle['high'] - candle['low'],
                        'body_size': abs(candle['close'] - candle['open']),
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
                        'time_to_10': time_to_10,
                        'time_to_20': time_to_20,
                        'time_to_30': time_to_30,
                        'time_to_50': time_to_50,
                    })
                
                break  # Only first breakdown per support level
    
    return pd.DataFrame(breakdowns)

# Analyze breakdowns for each timeframe
breakdowns_15m = analyze_support_breakdowns(df_15m, support_levels, '15-minute')
breakdowns_1h = analyze_support_breakdowns(df_1h, support_levels, '1-hour')
breakdowns_1d = analyze_support_breakdowns(df_1d, support_levels, '1-day')

# Display results
for tf_name, df_bd in [('15-minute', breakdowns_15m), ('1-hour', breakdowns_1h), ('1-day', breakdowns_1d)]:
    print(f"\n{tf_name}:")
    print("-" * 90)
    if len(df_bd) > 0:
        print(f"  Found {len(df_bd)} support breakdown events")
        print(f"\n  Continuation Probabilities:")
        print(f"    Next candle lower:    {df_bd['next_candle_lower'].mean()*100:.1f}%")
        print(f"    Next 3 candles lower: {df_bd['next_3_lower'].mean()*100:.1f}%")
        print(f"    Next 5 candles lower: {df_bd['next_5_lower'].mean()*100:.1f}%")
        
        print(f"\n  Drop Target Hit Rates:")
        print(f"    10 points drop:  {df_bd['drop_10'].mean()*100:.1f}%")
        print(f"    20 points drop:  {df_bd['drop_20'].mean()*100:.1f}%")
        print(f"    30 points drop:  {df_bd['drop_30'].mean()*100:.1f}%")
        print(f"    50 points drop:  {df_bd['drop_50'].mean()*100:.1f}%")
        print(f"    100 points drop: {df_bd['drop_100'].mean()*100:.1f}%")
        
        print(f"\n  Avg Time to Drop Targets:")
        print(f"    -10pts: {df_bd['time_to_10'].mean():.0f} minutes")
        print(f"    -20pts: {df_bd['time_to_20'].mean():.0f} minutes")
        print(f"    -30pts: {df_bd['time_to_30'].mean():.0f} minutes")
        print(f"    -50pts: {df_bd['time_to_50'].mean():.0f} minutes")

# Combine all timeframes
all_breakdowns = pd.concat([breakdowns_15m, breakdowns_1h, breakdowns_1d], ignore_index=True)

print(f"\n✓ Total breakdown events across all timeframes: {len(all_breakdowns)}")

# Save results
all_breakdowns.to_csv('data/NIFTY_support_breakdowns_analysis.csv', index=False)
print(f"✓ Saved: data/NIFTY_support_breakdowns_analysis.csv")

# Analysis by support strength
print("\n" + "=" * 90)
print("Continuation Probability by Support Strength:")
print("=" * 90)

strength_analysis = all_breakdowns.groupby('support_strength').agg({
    'next_candle_lower': 'mean',
    'next_3_lower': 'mean',
    'next_5_lower': 'mean',
    'drop_10': 'mean',
    'drop_20': 'mean',
    'drop_30': 'mean',
    'drop_50': 'mean',
    'support_level': 'count'
}).round(3)

strength_analysis.columns = ['Next Candle↓', 'Next 3↓', 'Next 5↓', '-10pts', '-20pts', '-30pts', '-50pts', 'Count']
print(strength_analysis.to_string())

# ML Models
print("\n" + "=" * 90)
print("Training ML Models for Breakdown Continuation Prediction...")
print("=" * 90)

if len(all_breakdowns) > 50:
    # Prepare features
    feature_cols = ['breakdown_pct', 'close_below_pct', 'price_change_pct', 'candle_range', 
                    'body_size', 'rsi', 'volume_ratio', 'volatility', 'support_hits', 
                    'support_reversals']
    
    # Encode categorical variables
    all_breakdowns['strength_encoded'] = all_breakdowns['support_strength'].map({
        'Weak': 1, 'Moderate': 2, 'Strong': 3, 'Very Strong': 4
    })
    all_breakdowns['timeframe_encoded'] = all_breakdowns['timeframe'].map({
        '15-minute': 1, '1-hour': 2, '1-day': 3
    })
    all_breakdowns['sup_timeframe_encoded'] = all_breakdowns['support_timeframe'].map({
        '15m': 1, '1h': 2, '1d': 3
    })
    
    feature_cols.extend(['strength_encoded', 'timeframe_encoded', 'sup_timeframe_encoded'])
    
    X = all_breakdowns[feature_cols].fillna(0)
    
    # Train models for different targets
    targets = [
        ('next_candle_lower', 'Next Candle Down'),
        ('next_3_lower', 'Next 3 Lower'),
        ('drop_10', '-10pts'),
        ('drop_20', '-20pts'),
        ('drop_30', '-30pts')
    ]
    
    for target_col, target_name in targets:
        y = all_breakdowns[target_col].astype(int)
        
        if len(y.unique()) > 1:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
            gb = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
            
            rf.fit(X_train_scaled, y_train)
            gb.fit(X_train_scaled, y_train)
            
            rf_acc = rf.score(X_test_scaled, y_test) * 100
            gb_acc = gb.score(X_test_scaled, y_test) * 100
            baseline = y.mean() * 100
            
            print(f"\n{target_name}:")
            print(f"  RF: {rf_acc:.1f}%  |  GB: {gb_acc:.1f}%  |  Baseline: {baseline:.1f}%")

# Summary
print("\n" + "=" * 90)
print("Summary by Timeframe:")
print("=" * 90)

summary_data = []
for tf in ['15-minute', '1-hour', '1-day']:
    tf_data = all_breakdowns[all_breakdowns['timeframe'] == tf]
    if len(tf_data) > 0:
        summary_data.append({
            'Timeframe': tf,
            'Breakdowns': len(tf_data),
            'Next↓': f"{tf_data['next_candle_lower'].mean()*100:.1f}%",
            'Next3↓': f"{tf_data['next_3_lower'].mean()*100:.1f}%",
            '-10pts': f"{tf_data['drop_10'].mean()*100:.1f}%",
            '-20pts': f"{tf_data['drop_20'].mean()*100:.1f}%",
            '-30pts': f"{tf_data['drop_30'].mean()*100:.1f}%",
            '-50pts': f"{tf_data['drop_50'].mean()*100:.1f}%",
            'Avg Time -10pts': f"{tf_data['time_to_10'].mean():.0f}m"
        })

summary_df = pd.DataFrame(summary_data)
print(summary_df.to_string(index=False))

print("\n" + "=" * 90)
print("✓ Support Breakdown Analysis Complete!")
print("=" * 90)

print("\nKey Insights:")
print(f"  • When price closes below support, {all_breakdowns['next_candle_lower'].mean()*100:.1f}% chance next candle is lower")
print(f"  • {all_breakdowns['drop_10'].mean()*100:.1f}% probability of -10 point drop after breakdown")
print(f"  • {all_breakdowns['drop_20'].mean()*100:.1f}% probability of -20 point drop after breakdown")
print(f"  • Stronger support = Higher breakdown continuation probability")
print("=" * 90)
