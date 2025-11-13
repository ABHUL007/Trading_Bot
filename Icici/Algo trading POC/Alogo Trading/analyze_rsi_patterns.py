"""
Comprehensive RSI and Chart Behavior Analysis
Analyze RSI(14), returns before reversals/breakouts, and chart patterns
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)

# Create data directory
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

print("=" * 100)
print("RSI & CHART BEHAVIOR ANALYSIS - All Timeframes")
print("=" * 100)

# Load all data
print("\n✓ Loading data...")
df_15m = pd.read_csv(data_dir / "NIFTY_15min_20221024_20251023.csv", parse_dates=['datetime'])
df_1h = pd.read_csv(data_dir / "NIFTY_1hour_20221024_20251023.csv", parse_dates=['datetime'])
df_1d = pd.read_csv(data_dir / "NIFTY_1day_20221024_20251023.csv", parse_dates=['datetime'])

# Load event data
breakouts = pd.read_csv(data_dir / "NIFTY_breakouts_multi_timeframe.csv", parse_dates=['datetime'])
rejections = pd.read_csv(data_dir / "NIFTY_resistance_rejections_analysis.csv", parse_dates=['datetime'])
breakdowns = pd.read_csv(data_dir / "NIFTY_support_breakdowns_analysis.csv", parse_dates=['datetime'])
bounces = pd.read_csv(data_dir / "NIFTY_support_bounces_analysis.csv", parse_dates=['datetime'])

print(f"✓ Loaded 15-min: {len(df_15m)} candles")
print(f"✓ Loaded 1-hour: {len(df_1h)} candles")
print(f"✓ Loaded 1-day: {len(df_1d)} candles")
print(f"✓ Loaded {len(breakouts)} breakout events")
print(f"✓ Loaded {len(rejections)} rejection events")
print(f"✓ Loaded {len(breakdowns)} breakdown events")
print(f"✓ Loaded {len(bounces)} bounce events")


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_returns(df, periods=[1, 3, 5, 10, 20]):
    """Calculate returns over multiple periods"""
    for period in periods:
        df[f'return_{period}'] = df['close'].pct_change(period) * 100
    return df


def analyze_rsi_for_events(df_price, events_df, event_name, event_type):
    """
    Analyze RSI patterns for specific events
    event_type: 'breakout', 'rejection', 'breakdown', 'bounce'
    """
    print("\n" + "=" * 100)
    print(f"RSI ANALYSIS: {event_name}")
    print("=" * 100)
    
    # Map timeframe names
    tf_map = {'15-minute': df_15m, '1-hour': df_1h, '1-day': df_1d}
    
    all_analysis = []
    
    for tf_name, tf_df in [('15-minute', df_15m), ('1-hour', df_1h), ('1-day', df_1d)]:
        # Filter events for this timeframe
        tf_events = events_df[events_df['timeframe'] == tf_name].copy()
        
        if len(tf_events) == 0:
            continue
        
        print(f"\n{'-'*100}")
        print(f"Timeframe: {tf_name} - {len(tf_events)} events")
        print(f"{'-'*100}")
        
        # Calculate RSI if not present
        if 'rsi' not in tf_df.columns:
            tf_df['rsi'] = calculate_rsi(tf_df['close'], 14)
        
        # Calculate returns
        tf_df = calculate_returns(tf_df, [1, 3, 5, 10, 20])
        
        for idx, event in tf_events.iterrows():
            event_time = pd.to_datetime(event['datetime'])
            
            # Find the candle index
            candle_idx = tf_df[tf_df['datetime'] == event_time].index
            if len(candle_idx) == 0:
                continue
            
            candle_idx = candle_idx[0]
            
            # Get RSI at event
            rsi_at_event = tf_df.iloc[candle_idx]['rsi'] if candle_idx < len(tf_df) else None
            
            # Get RSI before event (1, 3, 5 candles before)
            rsi_1_before = tf_df.iloc[candle_idx - 1]['rsi'] if candle_idx >= 1 else None
            rsi_3_before = tf_df.iloc[candle_idx - 3]['rsi'] if candle_idx >= 3 else None
            rsi_5_before = tf_df.iloc[candle_idx - 5]['rsi'] if candle_idx >= 5 else None
            
            # Get returns before event
            return_1 = tf_df.iloc[candle_idx]['return_1'] if 'return_1' in tf_df.columns else None
            return_3 = tf_df.iloc[candle_idx]['return_3'] if 'return_3' in tf_df.columns else None
            return_5 = tf_df.iloc[candle_idx]['return_5'] if 'return_5' in tf_df.columns else None
            return_10 = tf_df.iloc[candle_idx]['return_10'] if 'return_10' in tf_df.columns else None
            return_20 = tf_df.iloc[candle_idx]['return_20'] if 'return_20' in tf_df.columns else None
            
            # Determine success based on event type
            if event_type == 'breakout':
                success_10 = event.get('hit_10', False)
                success_20 = event.get('hit_20', False)
                success_50 = event.get('hit_50', False)
            elif event_type == 'rejection':
                success_10 = event.get('drop_10', False)
                success_20 = event.get('drop_20', False)
                success_50 = event.get('drop_50', False)
            elif event_type == 'breakdown':
                success_10 = event.get('drop_10', False)
                success_20 = event.get('drop_20', False)
                success_50 = event.get('drop_50', False)
            elif event_type == 'bounce':
                success_10 = event.get('rally_10', False)
                success_20 = event.get('rally_20', False)
                success_50 = event.get('rally_50', False)
            else:
                success_10 = success_20 = success_50 = False
            
            all_analysis.append({
                'datetime': event_time,
                'timeframe': tf_name,
                'event_type': event_type,
                'rsi_at_event': rsi_at_event,
                'rsi_1_before': rsi_1_before,
                'rsi_3_before': rsi_3_before,
                'rsi_5_before': rsi_5_before,
                'rsi_change_1': rsi_at_event - rsi_1_before if rsi_1_before else None,
                'rsi_change_3': rsi_at_event - rsi_3_before if rsi_3_before else None,
                'return_1': return_1,
                'return_3': return_3,
                'return_5': return_5,
                'return_10': return_10,
                'return_20': return_20,
                'success_10': success_10,
                'success_20': success_20,
                'success_50': success_50,
                'price': event.get('breakout_price', event.get('candle_close', 0))
            })
        
        # Convert to DataFrame for analysis
        if len(all_analysis) > 0:
            analysis_df = pd.DataFrame(all_analysis)
            tf_analysis = analysis_df[analysis_df['timeframe'] == tf_name]
            
            if len(tf_analysis) > 0:
                print(f"\nRSI Statistics at Event:")
                print(f"  Mean RSI:        {tf_analysis['rsi_at_event'].mean():.2f}")
                print(f"  Median RSI:      {tf_analysis['rsi_at_event'].median():.2f}")
                print(f"  Min RSI:         {tf_analysis['rsi_at_event'].min():.2f}")
                print(f"  Max RSI:         {tf_analysis['rsi_at_event'].max():.2f}")
                print(f"  Std Dev:         {tf_analysis['rsi_at_event'].std():.2f}")
                
                # RSI ranges
                print(f"\nRSI Range Distribution:")
                oversold = (tf_analysis['rsi_at_event'] < 30).sum()
                neutral_low = ((tf_analysis['rsi_at_event'] >= 30) & (tf_analysis['rsi_at_event'] < 50)).sum()
                neutral_high = ((tf_analysis['rsi_at_event'] >= 50) & (tf_analysis['rsi_at_event'] < 70)).sum()
                overbought = (tf_analysis['rsi_at_event'] >= 70).sum()
                
                total = len(tf_analysis)
                print(f"  Oversold (<30):      {oversold:4d} ({oversold/total*100:5.1f}%)")
                print(f"  Neutral Low (30-50): {neutral_low:4d} ({neutral_low/total*100:5.1f}%)")
                print(f"  Neutral High (50-70):{neutral_high:4d} ({neutral_high/total*100:5.1f}%)")
                print(f"  Overbought (>70):    {overbought:4d} ({overbought/total*100:5.1f}%)")
                
                # Returns before event
                print(f"\nReturns Before Event:")
                print(f"  1-period return:  {tf_analysis['return_1'].mean():+.2f}% (median: {tf_analysis['return_1'].median():+.2f}%)")
                print(f"  3-period return:  {tf_analysis['return_3'].mean():+.2f}% (median: {tf_analysis['return_3'].median():+.2f}%)")
                print(f"  5-period return:  {tf_analysis['return_5'].mean():+.2f}% (median: {tf_analysis['return_5'].median():+.2f}%)")
                print(f"  10-period return: {tf_analysis['return_10'].mean():+.2f}% (median: {tf_analysis['return_10'].median():+.2f}%)")
                print(f"  20-period return: {tf_analysis['return_20'].mean():+.2f}% (median: {tf_analysis['return_20'].median():+.2f}%)")
                
                # Success rate by RSI range
                print(f"\nSuccess Rate by RSI Range:")
                for rsi_range, condition in [
                    ('Oversold (<30)', tf_analysis['rsi_at_event'] < 30),
                    ('Neutral Low (30-50)', (tf_analysis['rsi_at_event'] >= 30) & (tf_analysis['rsi_at_event'] < 50)),
                    ('Neutral High (50-70)', (tf_analysis['rsi_at_event'] >= 50) & (tf_analysis['rsi_at_event'] < 70)),
                    ('Overbought (>70)', tf_analysis['rsi_at_event'] >= 70)
                ]:
                    subset = tf_analysis[condition]
                    if len(subset) > 0:
                        success_10_rate = subset['success_10'].mean() * 100
                        success_20_rate = subset['success_20'].mean() * 100
                        success_50_rate = subset['success_50'].mean() * 100
                        print(f"  {rsi_range:20s} (n={len(subset):3d}): 10pts={success_10_rate:5.1f}%, 20pts={success_20_rate:5.1f}%, 50pts={success_50_rate:5.1f}%")
                
                # Success rate by return direction
                print(f"\nSuccess Rate by Prior Return (5-period):")
                for return_label, condition in [
                    ('Strong Negative (<-2%)', tf_analysis['return_5'] < -2),
                    ('Negative (-2% to 0%)', (tf_analysis['return_5'] >= -2) & (tf_analysis['return_5'] < 0)),
                    ('Positive (0% to +2%)', (tf_analysis['return_5'] >= 0) & (tf_analysis['return_5'] < 2)),
                    ('Strong Positive (>+2%)', tf_analysis['return_5'] >= 2)
                ]:
                    subset = tf_analysis[condition]
                    if len(subset) > 0:
                        success_10_rate = subset['success_10'].mean() * 100
                        success_20_rate = subset['success_20'].mean() * 100
                        print(f"  {return_label:25s} (n={len(subset):3d}): 10pts={success_10_rate:5.1f}%, 20pts={success_20_rate:5.1f}%")
    
    return pd.DataFrame(all_analysis) if all_analysis else None


# Analyze each event type
print("\n" + "=" * 100)
print("ANALYZING ALL EVENT TYPES ACROSS TIMEFRAMES")
print("=" * 100)

breakout_rsi = analyze_rsi_for_events(df_15m, breakouts, "RESISTANCE BREAKOUTS", "breakout")
rejection_rsi = analyze_rsi_for_events(df_15m, rejections, "RESISTANCE REJECTIONS", "rejection")
breakdown_rsi = analyze_rsi_for_events(df_15m, breakdowns, "SUPPORT BREAKDOWNS", "breakdown")
bounce_rsi = analyze_rsi_for_events(df_15m, bounces, "SUPPORT BOUNCES", "bounce")

# Combine all analyses
all_events = []
if breakout_rsi is not None:
    all_events.append(breakout_rsi)
if rejection_rsi is not None:
    all_events.append(rejection_rsi)
if breakdown_rsi is not None:
    all_events.append(breakdown_rsi)
if bounce_rsi is not None:
    all_events.append(bounce_rsi)

if len(all_events) > 0:
    combined_df = pd.concat(all_events, ignore_index=True)
    
    # Save combined analysis
    combined_df.to_csv(data_dir / "NIFTY_rsi_analysis_combined.csv", index=False)
    print(f"\n✓ Saved: {data_dir / 'NIFTY_rsi_analysis_combined.csv'}")
    
    # ML Analysis - Predict success using RSI and returns
    print("\n" + "=" * 100)
    print("MACHINE LEARNING: Predicting Success from RSI & Returns")
    print("=" * 100)
    
    # Prepare features
    feature_cols = ['rsi_at_event', 'rsi_1_before', 'rsi_change_1', 'return_1', 'return_3', 'return_5', 'return_10']
    X = combined_df[feature_cols].fillna(0)
    
    # Predict 10-point success
    y_10 = combined_df['success_10'].fillna(0).astype(int)
    
    if len(X) > 20 and y_10.sum() > 5:
        X_train, X_test, y_train, y_test = train_test_split(X, y_10, test_size=0.3, random_state=42)
        
        print(f"\nPredicting 10-Point Success:")
        print(f"  Total events: {len(X)}")
        print(f"  Successful: {y_10.sum()} ({y_10.mean()*100:.1f}%)")
        
        # Random Forest
        rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        rf.fit(X_train, y_train)
        rf_score = rf.score(X_test, y_test)
        
        # Gradient Boosting
        gb = GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
        gb.fit(X_train, y_train)
        gb_score = gb.score(X_test, y_test)
        
        print(f"\n  RandomForest Accuracy:     {rf_score*100:.1f}%")
        print(f"  GradientBoosting Accuracy: {gb_score*100:.1f}%")
        
        # Feature importance
        print(f"\n  Feature Importance (RandomForest):")
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': rf.feature_importances_
        }).sort_values('importance', ascending=False)
        
        for idx, row in feature_importance.iterrows():
            print(f"    {row['feature']:20s}: {row['importance']*100:5.1f}%")
    
    # Create visualizations
    print("\n" + "=" * 100)
    print("Creating Visualizations...")
    print("=" * 100)
    
    # Figure 1: RSI Distribution by Event Type
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('RSI Distribution by Event Type and Timeframe', fontsize=16, fontweight='bold')
    
    event_types = [('breakout', 'Resistance Breakout'), ('rejection', 'Resistance Rejection'), 
                   ('breakdown', 'Support Breakdown'), ('bounce', 'Support Bounce')]
    
    for idx, (event_type, title) in enumerate(event_types):
        ax = axes[idx // 2, idx % 2]
        event_data = combined_df[combined_df['event_type'] == event_type]
        
        for tf in ['15-minute', '1-hour', '1-day']:
            tf_data = event_data[event_data['timeframe'] == tf]
            if len(tf_data) > 0:
                ax.hist(tf_data['rsi_at_event'].dropna(), bins=20, alpha=0.5, label=tf)
        
        ax.axvline(30, color='red', linestyle='--', linewidth=1, label='Oversold')
        ax.axvline(70, color='green', linestyle='--', linewidth=1, label='Overbought')
        ax.set_xlabel('RSI Value')
        ax.set_ylabel('Frequency')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('rsi_distribution_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: rsi_distribution_analysis.png")
    
    # Figure 2: Success Rate vs RSI
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Success Rate vs RSI Level', fontsize=16, fontweight='bold')
    
    for idx, (event_type, title) in enumerate(event_types):
        ax = axes[idx // 2, idx % 2]
        event_data = combined_df[combined_df['event_type'] == event_type]
        
        if len(event_data) > 0:
            # Bin RSI into ranges
            bins = [0, 30, 40, 50, 60, 70, 100]
            labels = ['<30', '30-40', '40-50', '50-60', '60-70', '>70']
            event_data['rsi_bin'] = pd.cut(event_data['rsi_at_event'], bins=bins, labels=labels)
            
            success_by_rsi = event_data.groupby('rsi_bin')['success_10'].mean() * 100
            counts = event_data.groupby('rsi_bin').size()
            
            bars = ax.bar(range(len(success_by_rsi)), success_by_rsi.values, 
                         color=['red' if x < 80 else 'orange' if x < 90 else 'green' for x in success_by_rsi.values])
            ax.set_xticks(range(len(success_by_rsi)))
            ax.set_xticklabels(success_by_rsi.index)
            ax.set_xlabel('RSI Range')
            ax.set_ylabel('Success Rate (%)')
            ax.set_title(f'{title}\n(10-point target)')
            ax.axhline(80, color='blue', linestyle='--', linewidth=1, alpha=0.5)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add count labels
            for i, (bar, count) in enumerate(zip(bars, counts)):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'n={count}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('rsi_success_rate_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: rsi_success_rate_analysis.png")
    
    # Figure 3: Prior Returns vs Success
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Success Rate by Prior 5-Period Return', fontsize=16, fontweight='bold')
    
    for idx, (event_type, title) in enumerate(event_types):
        ax = axes[idx // 2, idx % 2]
        event_data = combined_df[combined_df['event_type'] == event_type]
        
        if len(event_data) > 0:
            # Bin returns
            bins = [-100, -2, -1, 0, 1, 2, 100]
            labels = ['<-2%', '-2 to -1%', '-1 to 0%', '0 to 1%', '1 to 2%', '>2%']
            event_data['return_bin'] = pd.cut(event_data['return_5'], bins=bins, labels=labels)
            
            success_by_return = event_data.groupby('return_bin')['success_10'].mean() * 100
            counts = event_data.groupby('return_bin').size()
            
            bars = ax.bar(range(len(success_by_return)), success_by_return.values,
                         color=['red' if x < 80 else 'orange' if x < 90 else 'green' for x in success_by_return.values])
            ax.set_xticks(range(len(success_by_return)))
            ax.set_xticklabels(success_by_return.index, rotation=45)
            ax.set_xlabel('5-Period Return Range')
            ax.set_ylabel('Success Rate (%)')
            ax.set_title(title)
            ax.axhline(80, color='blue', linestyle='--', linewidth=1, alpha=0.5)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add count labels
            for i, (bar, count) in enumerate(zip(bars, counts)):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'n={count}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('returns_success_rate_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: returns_success_rate_analysis.png")

print("\n" + "=" * 100)
print("✓ RSI & CHART BEHAVIOR ANALYSIS COMPLETE!")
print("=" * 100)
print("\nKey Files Generated:")
print("  1. NIFTY_rsi_analysis_combined.csv - Complete RSI analysis data")
print("  2. rsi_distribution_analysis.png - RSI distribution charts")
print("  3. rsi_success_rate_analysis.png - Success rate by RSI level")
print("  4. returns_success_rate_analysis.png - Success rate by prior returns")
print("=" * 100)
