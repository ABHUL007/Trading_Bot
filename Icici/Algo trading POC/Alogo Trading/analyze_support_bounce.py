"""Analyze Support Bounce Probability - When price touches but holds support"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("=" * 90)
print("Support Bounce Analysis - Bullish Reversal Probability")
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
print("Identifying Support Bounce Events...")
print("=" * 90)

def analyze_support_bounces(df_price, support_df, timeframe):
    """Analyze when price touches support but closes above it (bounce/reversal)"""
    bounces = []
    
    for idx, support in support_df.iterrows():
        support_price = support['price']
        support_date = support['datetime']
        tolerance = support_price * 0.0015  # 0.15% tolerance
        
        # Find candles after support was identified
        future_candles = df_price[df_price['datetime'] > support_date].copy()
        
        for i in range(len(future_candles)):
            candle = future_candles.iloc[i]
            
            # Bounce: Low touches/goes below support BUT close is above support (bullish reversal)
            if candle['low'] <= support_price + tolerance and candle['close'] > support_price:
                
                # Calculate bounce characteristics
                bounce_distance = candle['close'] - support_price
                bounce_pct = (bounce_distance / support_price) * 100
                close_above_pct = ((candle['close'] - support_price) / support_price) * 100
                
                # Lower wick size (shows rejection of lower prices)
                lower_wick = min(candle['open'], candle['close']) - candle['low']
                wick_ratio = lower_wick / (candle['high'] - candle['low']) if candle['high'] != candle['low'] else 0
                
                # Look ahead for rally targets
                remaining = future_candles.iloc[i+1:i+101] if i+1 < len(future_candles) else pd.DataFrame()
                
                if len(remaining) > 0:
                    # Check if rally continues (bullish continuation)
                    next_candle_higher = remaining.iloc[0]['close'] > candle['close'] if len(remaining) > 0 else False
                    next_3_higher = remaining.iloc[2]['close'] > candle['close'] if len(remaining) >= 3 else False
                    next_5_higher = remaining.iloc[4]['close'] > candle['close'] if len(remaining) >= 5 else False
                    
                    # Maximum rally after bounce
                    max_rally = remaining['high'].max() - candle['close']
                    
                    # Rally target achievements
                    rally_10 = max_rally >= 10
                    rally_20 = max_rally >= 20
                    rally_30 = max_rally >= 30
                    rally_50 = max_rally >= 50
                    rally_100 = max_rally >= 100
                    
                    # Time to reach rally targets
                    def time_to_target(target):
                        for j, r in remaining.iterrows():
                            if r['high'] - candle['close'] >= target:
                                return (r['datetime'] - candle['datetime']).total_seconds() / 60
                        return np.nan
                    
                    time_to_10 = time_to_target(10) if rally_10 else np.nan
                    time_to_20 = time_to_target(20) if rally_20 else np.nan
                    time_to_30 = time_to_target(30) if rally_30 else np.nan
                    time_to_50 = time_to_target(50) if rally_50 else np.nan
                    
                    bounces.append({
                        'datetime': candle['datetime'],
                        'timeframe': timeframe,
                        'candle_close': candle['close'],
                        'candle_low': candle['low'],
                        'support_level': support_price,
                        'support_strength': support['strength'],
                        'support_timeframe': support['timeframe'],
                        'support_hits': support['num_hits'],
                        'support_reversals': support['num_reversals'],
                        'bounce_distance': bounce_distance,
                        'bounce_pct': bounce_pct,
                        'close_above_pct': close_above_pct,
                        'lower_wick': lower_wick,
                        'wick_ratio': wick_ratio,
                        'price_change_pct': ((candle['close'] - candle['open']) / candle['open']) * 100,
                        'candle_range': candle['high'] - candle['low'],
                        'body_size': abs(candle['close'] - candle['open']),
                        'rsi': candle.get('rsi', 50),
                        'volume_ratio': candle.get('volume_ratio', 1),
                        'volatility': candle.get('volatility', 0),
                        'momentum_5': candle.get('momentum_5', 0),
                        'max_rally': max_rally,
                        'next_candle_higher': next_candle_higher,
                        'next_3_higher': next_3_higher,
                        'next_5_higher': next_5_higher,
                        'rally_10': rally_10,
                        'rally_20': rally_20,
                        'rally_30': rally_30,
                        'rally_50': rally_50,
                        'rally_100': rally_100,
                        'time_to_10': time_to_10,
                        'time_to_20': time_to_20,
                        'time_to_30': time_to_30,
                        'time_to_50': time_to_50,
                    })
                
                break  # Only first bounce per support level
    
    return pd.DataFrame(bounces)

# Analyze bounces for each timeframe
bounces_15m = analyze_support_bounces(df_15m, support_levels, '15-minute')
bounces_1h = analyze_support_bounces(df_1h, support_levels, '1-hour')
bounces_1d = analyze_support_bounces(df_1d, support_levels, '1-day')

# Display results
for tf_name, df_bnc in [('15-minute', bounces_15m), ('1-hour', bounces_1h), ('1-day', bounces_1d)]:
    print(f"\n{tf_name}:")
    print("-" * 90)
    if len(df_bnc) > 0:
        print(f"  Found {len(df_bnc)} support bounce events")
        print(f"\n  Reversal Probabilities:")
        print(f"    Next candle higher:    {df_bnc['next_candle_higher'].mean()*100:.1f}%")
        print(f"    Next 3 candles higher: {df_bnc['next_3_higher'].mean()*100:.1f}%")
        print(f"    Next 5 candles higher: {df_bnc['next_5_higher'].mean()*100:.1f}%")
        
        print(f"\n  Rally Target Hit Rates:")
        print(f"    10 points rally:  {df_bnc['rally_10'].mean()*100:.1f}%")
        print(f"    20 points rally:  {df_bnc['rally_20'].mean()*100:.1f}%")
        print(f"    30 points rally:  {df_bnc['rally_30'].mean()*100:.1f}%")
        print(f"    50 points rally:  {df_bnc['rally_50'].mean()*100:.1f}%")
        print(f"    100 points rally: {df_bnc['rally_100'].mean()*100:.1f}%")
        
        print(f"\n  Avg Time to Rally Targets:")
        print(f"    +10pts: {df_bnc['time_to_10'].mean():.0f} minutes")
        print(f"    +20pts: {df_bnc['time_to_20'].mean():.0f} minutes")
        print(f"    +30pts: {df_bnc['time_to_30'].mean():.0f} minutes")
        print(f"    +50pts: {df_bnc['time_to_50'].mean():.0f} minutes")

# Combine all timeframes
all_bounces = pd.concat([bounces_15m, bounces_1h, bounces_1d], ignore_index=True)

print(f"\n✓ Total bounce events across all timeframes: {len(all_bounces)}")

# Save results
all_bounces.to_csv('data/NIFTY_support_bounces_analysis.csv', index=False)
print(f"✓ Saved: data/NIFTY_support_bounces_analysis.csv")

# Analysis by support strength
print("\n" + "=" * 90)
print("Reversal Probability by Support Strength:")
print("=" * 90)

strength_analysis = all_bounces.groupby('support_strength').agg({
    'next_candle_higher': 'mean',
    'next_3_higher': 'mean',
    'next_5_higher': 'mean',
    'rally_10': 'mean',
    'rally_20': 'mean',
    'rally_30': 'mean',
    'rally_50': 'mean',
    'support_level': 'count'
}).round(3)

strength_analysis.columns = ['Next Candle↑', 'Next 3↑', 'Next 5↑', '+10pts', '+20pts', '+30pts', '+50pts', 'Count']
print(strength_analysis.to_string())

# Analysis by lower wick size
print("\n" + "=" * 90)
print("Reversal Probability by Lower Wick Size:")
print("=" * 90)

all_bounces['wick_category'] = pd.cut(all_bounces['wick_ratio'] * 100, 
                                       bins=[0, 30, 50, 70, 100],
                                       labels=['Small (<30%)', 'Medium (30-50%)', 'Large (50-70%)', 'Very Large (>70%)'])

wick_analysis = all_bounces.groupby('wick_category', observed=True).agg({
    'next_candle_higher': 'mean',
    'rally_10': 'mean',
    'rally_20': 'mean',
    'rally_30': 'mean',
    'support_level': 'count'
}).round(3)

wick_analysis.columns = ['Next Candle↑', '+10pts', '+20pts', '+30pts', 'Count']
print(wick_analysis.to_string())

# ML Models
print("\n" + "=" * 90)
print("Training ML Models for Bounce Reversal Prediction...")
print("=" * 90)

if len(all_bounces) > 50:
    # Prepare features
    feature_cols = ['bounce_pct', 'close_above_pct', 'wick_ratio', 'price_change_pct', 'candle_range', 
                    'body_size', 'rsi', 'volume_ratio', 'volatility', 'support_hits', 
                    'support_reversals']
    
    # Encode categorical variables
    all_bounces['strength_encoded'] = all_bounces['support_strength'].map({
        'Weak': 1, 'Moderate': 2, 'Strong': 3, 'Very Strong': 4
    })
    all_bounces['timeframe_encoded'] = all_bounces['timeframe'].map({
        '15-minute': 1, '1-hour': 2, '1-day': 3
    })
    all_bounces['sup_timeframe_encoded'] = all_bounces['support_timeframe'].map({
        '15m': 1, '1h': 2, '1d': 3
    })
    
    feature_cols.extend(['strength_encoded', 'timeframe_encoded', 'sup_timeframe_encoded'])
    
    X = all_bounces[feature_cols].fillna(0)
    
    # Train models for different targets
    targets = [
        ('next_candle_higher', 'Next Candle Up'),
        ('next_3_higher', 'Next 3 Higher'),
        ('rally_10', '+10pts'),
        ('rally_20', '+20pts'),
        ('rally_30', '+30pts')
    ]
    
    for target_col, target_name in targets:
        y = all_bounces[target_col].astype(int)
        
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
    tf_data = all_bounces[all_bounces['timeframe'] == tf]
    if len(tf_data) > 0:
        summary_data.append({
            'Timeframe': tf,
            'Bounces': len(tf_data),
            'Next↑': f"{tf_data['next_candle_higher'].mean()*100:.1f}%",
            'Next3↑': f"{tf_data['next_3_higher'].mean()*100:.1f}%",
            '+10pts': f"{tf_data['rally_10'].mean()*100:.1f}%",
            '+20pts': f"{tf_data['rally_20'].mean()*100:.1f}%",
            '+30pts': f"{tf_data['rally_30'].mean()*100:.1f}%",
            '+50pts': f"{tf_data['rally_50'].mean()*100:.1f}%",
            'Avg Time +10pts': f"{tf_data['time_to_10'].mean():.0f}m"
        })

summary_df = pd.DataFrame(summary_data)
print(summary_df.to_string(index=False))

print("\n" + "=" * 90)
print("✓ Support Bounce Analysis Complete!")
print("=" * 90)

print("\nKey Insights:")
print(f"  • When low touches support but closes above, {all_bounces['next_candle_higher'].mean()*100:.1f}% chance next candle is higher")
print(f"  • {all_bounces['rally_10'].mean()*100:.1f}% probability of +10 point rally after bounce")
print(f"  • {all_bounces['rally_20'].mean()*100:.1f}% probability of +20 point rally after bounce")
print(f"  • Stronger support = Higher reversal probability")
print(f"  • Larger lower wick = Stronger bounce signal")
print("=" * 90)
