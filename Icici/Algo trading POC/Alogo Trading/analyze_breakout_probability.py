"""Analyze probability of price gains after breaking resistance levels"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("Resistance Breakout Analysis - ML Probability Calculator")
print("=" * 80)

# Load data
print("\n✓ Loading data...")
price_data = pd.read_csv("data/NIFTY_15min_20221024_20251023.csv")
resistance_data = pd.read_csv("data/NIFTY_resistance_levels.csv")

price_data['datetime'] = pd.to_datetime(price_data['datetime'])
resistance_data['datetime'] = pd.to_datetime(resistance_data['datetime'])

price_data = price_data.sort_values('datetime').reset_index(drop=True)

print(f"✓ Loaded {len(price_data)} candles")
print(f"✓ Loaded {len(resistance_data)} resistance levels")

# Create features for each candle
print("\n" + "=" * 80)
print("Feature Engineering...")
print("=" * 80)

# Add technical indicators
def add_technical_indicators(df):
    """Add technical indicators to dataframe"""
    # Price changes
    df['price_change'] = df['close'] - df['open']
    df['price_change_pct'] = (df['close'] - df['open']) / df['open'] * 100
    df['candle_range'] = df['high'] - df['low']
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
    
    # Volume momentum
    df['volume_sma'] = df['volume'].rolling(window=10).mean()
    df['volume_ratio'] = df['volume'] / (df['volume_sma'] + 1)
    
    # Volatility
    df['volatility'] = df['close'].rolling(window=20).std()
    
    # Momentum
    df['momentum_5'] = df['close'] - df['close'].shift(5)
    df['momentum_10'] = df['close'] - df['close'].shift(10)
    
    return df

price_data = add_technical_indicators(price_data)
price_data = price_data.dropna().reset_index(drop=True)

print(f"✓ Added technical indicators")
print(f"✓ {len(price_data)} candles with features")

# Identify resistance breakout events
print("\n" + "=" * 80)
print("Identifying Resistance Breakouts...")
print("=" * 80)

breakout_events = []
tolerance_pct = 0.1  # 0.1% tolerance

for i in range(len(price_data) - 50):  # Need at least 50 candles ahead for analysis
    candle = price_data.iloc[i]
    
    # Find resistance levels near this candle's high
    nearby_resistance = resistance_data[
        (resistance_data['price'] >= candle['low'] - (candle['low'] * tolerance_pct / 100)) &
        (resistance_data['price'] <= candle['high'] + (candle['high'] * tolerance_pct / 100)) &
        (resistance_data['datetime'] < candle['datetime'])  # Only use historical resistance
    ]
    
    # Check if close is above any resistance level
    for _, res_level in nearby_resistance.iterrows():
        if candle['close'] > res_level['price']:
            # This is a breakout!
            
            # Calculate future price movements
            future_prices = price_data.iloc[i+1:i+51]['high'].values  # Next 50 candles
            
            # Calculate max gains in next candles
            max_gain = max(future_prices) - candle['close'] if len(future_prices) > 0 else 0
            
            # Check which targets were hit
            hit_10 = max_gain >= 10
            hit_20 = max_gain >= 20
            hit_30 = max_gain >= 30
            hit_50 = max_gain >= 50
            hit_100 = max_gain >= 100
            
            # Find how many candles it took to hit targets
            candles_to_10 = np.where(future_prices >= candle['close'] + 10)[0]
            candles_to_20 = np.where(future_prices >= candle['close'] + 20)[0]
            candles_to_30 = np.where(future_prices >= candle['close'] + 30)[0]
            candles_to_50 = np.where(future_prices >= candle['close'] + 50)[0]
            
            time_to_10 = candles_to_10[0] + 1 if len(candles_to_10) > 0 else None
            time_to_20 = candles_to_20[0] + 1 if len(candles_to_20) > 0 else None
            time_to_30 = candles_to_30[0] + 1 if len(candles_to_30) > 0 else None
            time_to_50 = candles_to_50[0] + 1 if len(candles_to_50) > 0 else None
            
            breakout_events.append({
                'datetime': candle['datetime'],
                'breakout_price': candle['close'],
                'resistance_level': res_level['price'],
                'resistance_strength': res_level['strength'],
                'resistance_hits': res_level['num_hits'],
                'resistance_reversals': res_level['num_reversals'],
                'candle_idx': i,
                'price_change_pct': candle['price_change_pct'],
                'candle_range': candle['candle_range'],
                'rsi': candle['rsi'],
                'volume_ratio': candle['volume_ratio'],
                'volatility': candle['volatility'],
                'momentum_5': candle['momentum_5'],
                'sma_5': candle['sma_5'],
                'sma_10': candle['sma_10'],
                'max_gain': max_gain,
                'hit_10': hit_10,
                'hit_20': hit_20,
                'hit_30': hit_30,
                'hit_50': hit_50,
                'hit_100': hit_100,
                'time_to_10': time_to_10,
                'time_to_20': time_to_20,
                'time_to_30': time_to_30,
                'time_to_50': time_to_50
            })

df_breakouts = pd.DataFrame(breakout_events)

print(f"\n✓ Found {len(df_breakouts)} resistance breakout events")

if len(df_breakouts) == 0:
    print("\n✗ No breakout events found. Cannot perform analysis.")
    exit(1)

# Basic statistics
print("\n" + "=" * 80)
print("Breakout Statistics:")
print("=" * 80)

print(f"\nTotal Breakouts: {len(df_breakouts)}")
print(f"\nTarget Hit Rates:")
print(f"  10 points:  {df_breakouts['hit_10'].sum()} / {len(df_breakouts)} = {df_breakouts['hit_10'].mean()*100:.1f}%")
print(f"  20 points:  {df_breakouts['hit_20'].sum()} / {len(df_breakouts)} = {df_breakouts['hit_20'].mean()*100:.1f}%")
print(f"  30 points:  {df_breakouts['hit_30'].sum()} / {len(df_breakouts)} = {df_breakouts['hit_30'].mean()*100:.1f}%")
print(f"  50 points:  {df_breakouts['hit_50'].sum()} / {len(df_breakouts)} = {df_breakouts['hit_50'].mean()*100:.1f}%")
print(f"  100 points: {df_breakouts['hit_100'].sum()} / {len(df_breakouts)} = {df_breakouts['hit_100'].mean()*100:.1f}%")

print(f"\nAverage Time to Target (when hit):")
if df_breakouts['time_to_10'].notna().sum() > 0:
    print(f"  10 points:  {df_breakouts['time_to_10'].mean():.1f} candles ({df_breakouts['time_to_10'].mean()*15:.0f} minutes)")
if df_breakouts['time_to_20'].notna().sum() > 0:
    print(f"  20 points:  {df_breakouts['time_to_20'].mean():.1f} candles ({df_breakouts['time_to_20'].mean()*15:.0f} minutes)")
if df_breakouts['time_to_30'].notna().sum() > 0:
    print(f"  30 points:  {df_breakouts['time_to_30'].mean():.1f} candles ({df_breakouts['time_to_30'].mean()*15:.0f} minutes)")
if df_breakouts['time_to_50'].notna().sum() > 0:
    print(f"  50 points:  {df_breakouts['time_to_50'].mean():.1f} candles ({df_breakouts['time_to_50'].mean()*15:.0f} minutes)")

# Analyze by resistance strength
print("\n" + "=" * 80)
print("Success Rate by Resistance Strength:")
print("=" * 80)

strength_analysis = df_breakouts.groupby('resistance_strength').agg({
    'hit_10': 'mean',
    'hit_20': 'mean',
    'hit_30': 'mean',
    'hit_50': 'mean',
    'hit_100': 'mean',
    'breakout_price': 'count'
})
strength_analysis.columns = ['10pts%', '20pts%', '30pts%', '50pts%', '100pts%', 'Count']
strength_analysis = strength_analysis * 100
strength_analysis['Count'] = strength_analysis['Count'] / 100  # Fix count column

print(strength_analysis.round(1))

# Machine Learning Models
print("\n" + "=" * 80)
print("Training Machine Learning Models...")
print("=" * 80)

# Prepare features for ML
feature_columns = ['price_change_pct', 'candle_range', 'rsi', 'volume_ratio', 
                   'volatility', 'momentum_5', 'resistance_hits', 'resistance_reversals']

# Encode resistance strength
strength_map = {'Weak': 0, 'Moderate': 1, 'Strong': 2, 'Very Strong': 3}
df_breakouts['resistance_strength_encoded'] = df_breakouts['resistance_strength'].map(strength_map)
feature_columns.append('resistance_strength_encoded')

X = df_breakouts[feature_columns].fillna(0)

# Train models for each target
results = {}

for target, target_name in [('hit_10', '10 points'), ('hit_20', '20 points'), 
                             ('hit_30', '30 points'), ('hit_50', '50 points')]:
    
    if df_breakouts[target].sum() < 10:  # Need at least 10 positive samples
        print(f"\n⚠ Skipping {target_name} - insufficient positive samples")
        continue
    
    y = df_breakouts[target]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    rf_model.fit(X_train_scaled, y_train)
    
    # Train Gradient Boosting
    gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
    gb_model.fit(X_train_scaled, y_train)
    
    # Evaluate
    rf_score = rf_model.score(X_test_scaled, y_test)
    gb_score = gb_model.score(X_test_scaled, y_test)
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    results[target_name] = {
        'rf_model': rf_model,
        'gb_model': gb_model,
        'scaler': scaler,
        'rf_accuracy': rf_score,
        'gb_accuracy': gb_score,
        'feature_importance': feature_importance,
        'baseline_prob': y.mean()
    }
    
    print(f"\n✓ {target_name}:")
    print(f"    Random Forest Accuracy: {rf_score*100:.1f}%")
    print(f"    Gradient Boosting Accuracy: {gb_score*100:.1f}%")
    print(f"    Baseline Probability: {y.mean()*100:.1f}%")

# Generate probability predictions for different scenarios
print("\n" + "=" * 80)
print("Probability Predictions for Different Scenarios:")
print("=" * 80)

scenarios = [
    {
        'name': 'Strong Resistance + Bullish Candle + High Volume',
        'features': [2.5, 50, 65, 1.5, 30, 20, 15, 3, 3]  # Strong uptrend
    },
    {
        'name': 'Weak Resistance + Small Candle + Normal Volume',
        'features': [0.5, 20, 55, 1.0, 20, 5, 5, 1, 0]  # Weak setup
    },
    {
        'name': 'Very Strong Resistance + Large Candle + High RSI',
        'features': [3.0, 70, 75, 2.0, 40, 30, 25, 5, 3]  # Strong but overbought
    },
    {
        'name': 'Moderate Resistance + Average Conditions',
        'features': [1.5, 35, 60, 1.2, 25, 15, 10, 3, 1]  # Average
    }
]

print("\nFeatures: [price_change_pct, candle_range, rsi, volume_ratio, volatility,")
print("          momentum_5, resistance_hits, resistance_reversals, resistance_strength]\n")

for scenario in scenarios:
    print(f"\n{scenario['name']}:")
    print("-" * 80)
    
    # Create feature array
    X_scenario = np.array([scenario['features']])
    
    for target_name, model_data in results.items():
        if model_data is None:
            continue
        
        X_scaled = model_data['scaler'].transform(X_scenario)
        
        # Get probability from both models
        rf_prob = model_data['rf_model'].predict_proba(X_scaled)[0][1] * 100
        gb_prob = model_data['gb_model'].predict_proba(X_scaled)[0][1] * 100
        avg_prob = (rf_prob + gb_prob) / 2
        
        print(f"  {target_name:15} - RF: {rf_prob:5.1f}%  |  GB: {gb_prob:5.1f}%  |  Avg: {avg_prob:5.1f}%")

# Save results
print("\n" + "=" * 80)
print("Saving Results...")
print("=" * 80)

df_breakouts.to_csv('data/NIFTY_resistance_breakouts_analysis.csv', index=False)
print("✓ Detailed breakout data saved to: data/NIFTY_resistance_breakouts_analysis.csv")

# Create summary report
summary = {
    'Total Breakouts': len(df_breakouts),
    '10pts Success Rate': f"{df_breakouts['hit_10'].mean()*100:.1f}%",
    '20pts Success Rate': f"{df_breakouts['hit_20'].mean()*100:.1f}%",
    '30pts Success Rate': f"{df_breakouts['hit_30'].mean()*100:.1f}%",
    '50pts Success Rate': f"{df_breakouts['hit_50'].mean()*100:.1f}%",
    '100pts Success Rate': f"{df_breakouts['hit_100'].mean()*100:.1f}%",
}

summary_df = pd.DataFrame([summary])
summary_df.to_csv('data/NIFTY_breakout_summary.csv', index=False)
print("✓ Summary saved to: data/NIFTY_breakout_summary.csv")

print("\n" + "=" * 80)
print("✓ Analysis Complete!")
print("=" * 80)
print("\nKey Insights:")
print(f"  • After breaking resistance, {df_breakouts['hit_10'].mean()*100:.1f}% chance of +10 points")
print(f"  • After breaking resistance, {df_breakouts['hit_20'].mean()*100:.1f}% chance of +20 points")
print(f"  • After breaking resistance, {df_breakouts['hit_30'].mean()*100:.1f}% chance of +30 points")
print(f"  • After breaking resistance, {df_breakouts['hit_50'].mean()*100:.1f}% chance of +50 points")
print(f"  • ML models achieved {list(results.values())[0]['rf_accuracy']*100:.1f}% accuracy on test data")
print("=" * 80)
