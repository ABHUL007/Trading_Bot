"""
Analyze price movement when 15-min candle crosses resistance/support from higher timeframes
Calculate median/mode distance and probability using ML models
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from scipy import stats

# Create data directory
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

print("=" * 90)
print("Cross-Timeframe Breakout/Breakdown Analysis")
print("=" * 90)

# Load data
print("\n✓ Loading data...")
df_15m = pd.read_csv(data_dir / "NIFTY_15min_20221024_20251023.csv", parse_dates=['datetime'])
df_1h = pd.read_csv(data_dir / "NIFTY_1hour_20221024_20251023.csv", parse_dates=['datetime'])
df_1d = pd.read_csv(data_dir / "NIFTY_1day_20221024_20251023.csv", parse_dates=['datetime'])

resistance_df = pd.read_csv(data_dir / "NIFTY_resistance_multi_timeframe.csv")
support_df = pd.read_csv(data_dir / "NIFTY_support_multi_timeframe.csv")

print(f"✓ Loaded 15-min: {len(df_15m)} candles")
print(f"✓ Loaded 1-hour: {len(df_1h)} candles")
print(f"✓ Loaded 1-day: {len(df_1d)} candles")
print(f"✓ Loaded {len(resistance_df)} resistance levels")
print(f"✓ Loaded {len(support_df)} support levels")

# Separate resistance by timeframe
resistance_1h = resistance_df[resistance_df['timeframe'] == '1h']['price'].values
resistance_1d = resistance_df[resistance_df['timeframe'] == '1d']['price'].values

# Separate support by timeframe
support_1h = support_df[support_df['timeframe'] == '1h']['price'].values
support_1d = support_df[support_df['timeframe'] == '1d']['price'].values

print(f"\n✓ 1-hour resistance levels: {len(resistance_1h)}")
print(f"✓ Daily resistance levels: {len(resistance_1d)}")
print(f"✓ 1-hour support levels: {len(support_1h)}")
print(f"✓ Daily support levels: {len(support_1d)}")


def find_nearest_level(price, levels, tolerance=0.001):
    """Find nearest resistance/support level within tolerance"""
    if len(levels) == 0:
        return None
    
    distances = np.abs(levels - price)
    min_dist_idx = np.argmin(distances)
    
    if distances[min_dist_idx] / price <= tolerance:
        return levels[min_dist_idx]
    return None


def analyze_breakout_moves(df_15m, levels, level_name, is_resistance=True):
    """Analyze price movement after 15-min candle closes above/below higher timeframe level"""
    
    events = []
    
    for i in range(1, len(df_15m) - 50):  # Need future data to calculate moves
        current = df_15m.iloc[i]
        prev = df_15m.iloc[i-1]
        
        # Check if crossed the level
        if is_resistance:
            # Previous close below, current close above resistance
            crossed_level = find_nearest_level(current['close'], levels, tolerance=0.002)
            if crossed_level is None:
                continue
            
            if prev['close'] < crossed_level and current['close'] > crossed_level:
                breakout_price = current['close']
                
                # Calculate future moves
                future_highs = [df_15m.iloc[i+j]['high'] for j in range(1, min(51, len(df_15m)-i))]
                future_lows = [df_15m.iloc[i+j]['low'] for j in range(1, min(51, len(df_15m)-i))]
                
                if len(future_highs) == 0:
                    continue
                
                max_high = max(future_highs)
                max_gain = max_high - breakout_price
                
                # Calculate how far it actually moved upward
                peak_gain = max_gain
                
                # Check if it hit specific targets
                hit_10 = any(h >= breakout_price + 10 for h in future_highs)
                hit_20 = any(h >= breakout_price + 20 for h in future_highs)
                hit_30 = any(h >= breakout_price + 30 for h in future_highs)
                hit_50 = any(h >= breakout_price + 50 for h in future_highs)
                hit_100 = any(h >= breakout_price + 100 for h in future_highs)
                
                # Time to reach targets
                time_10 = next((j*15 for j in range(len(future_highs)) if future_highs[j] >= breakout_price + 10), None)
                time_20 = next((j*15 for j in range(len(future_highs)) if future_highs[j] >= breakout_price + 20), None)
                time_30 = next((j*15 for j in range(len(future_highs)) if future_highs[j] >= breakout_price + 30), None)
                time_50 = next((j*15 for j in range(len(future_highs)) if future_highs[j] >= breakout_price + 50), None)
                
                # Calculate distance from resistance
                distance_from_level = abs(breakout_price - crossed_level)
                
                events.append({
                    'datetime': current['datetime'],
                    'resistance_level': crossed_level,
                    'breakout_price': breakout_price,
                    'distance_from_level': distance_from_level,
                    'peak_gain': peak_gain,
                    'max_gain_50candles': peak_gain,
                    'hit_10pts': hit_10,
                    'hit_20pts': hit_20,
                    'hit_30pts': hit_30,
                    'hit_50pts': hit_50,
                    'hit_100pts': hit_100,
                    'time_to_10pts': time_10,
                    'time_to_20pts': time_20,
                    'time_to_30pts': time_30,
                    'time_to_50pts': time_50,
                    'candle_body': abs(current['close'] - current['open']),
                    'upper_wick': current['high'] - max(current['open'], current['close']),
                    'volume': current['volume'] if 'volume' in current else 0
                })
        else:
            # Support breakdown - previous close above, current close below
            crossed_level = find_nearest_level(current['close'], levels, tolerance=0.002)
            if crossed_level is None:
                continue
            
            if prev['close'] > crossed_level and current['close'] < crossed_level:
                breakdown_price = current['close']
                
                # Calculate future moves (downward)
                future_lows = [df_15m.iloc[i+j]['low'] for j in range(1, min(51, len(df_15m)-i))]
                future_highs = [df_15m.iloc[i+j]['high'] for j in range(1, min(51, len(df_15m)-i))]
                
                if len(future_lows) == 0:
                    continue
                
                min_low = min(future_lows)
                max_drop = breakdown_price - min_low
                
                peak_drop = max_drop
                
                # Check if it hit specific targets (downward)
                hit_10 = any(l <= breakdown_price - 10 for l in future_lows)
                hit_20 = any(l <= breakdown_price - 20 for l in future_lows)
                hit_30 = any(l <= breakdown_price - 30 for l in future_lows)
                hit_50 = any(l <= breakdown_price - 50 for l in future_lows)
                hit_100 = any(l <= breakdown_price - 100 for l in future_lows)
                
                # Time to reach targets
                time_10 = next((j*15 for j in range(len(future_lows)) if future_lows[j] <= breakdown_price - 10), None)
                time_20 = next((j*15 for j in range(len(future_lows)) if future_lows[j] <= breakdown_price - 20), None)
                time_30 = next((j*15 for j in range(len(future_lows)) if future_lows[j] <= breakdown_price - 30), None)
                time_50 = next((j*15 for j in range(len(future_lows)) if future_lows[j] <= breakdown_price - 50), None)
                
                distance_from_level = abs(breakdown_price - crossed_level)
                
                events.append({
                    'datetime': current['datetime'],
                    'support_level': crossed_level,
                    'breakdown_price': breakdown_price,
                    'distance_from_level': distance_from_level,
                    'peak_drop': peak_drop,
                    'max_drop_50candles': peak_drop,
                    'hit_10pts': hit_10,
                    'hit_20pts': hit_20,
                    'hit_30pts': hit_30,
                    'hit_50pts': hit_50,
                    'hit_100pts': hit_100,
                    'time_to_10pts': time_10,
                    'time_to_20pts': time_20,
                    'time_to_30pts': time_30,
                    'time_to_50pts': time_50,
                    'candle_body': abs(current['close'] - current['open']),
                    'lower_wick': min(current['open'], current['close']) - current['low'],
                    'volume': current['volume'] if 'volume' in current else 0
                })
    
    if len(events) == 0:
        return None
    
    df = pd.DataFrame(events)
    
    print("\n" + "=" * 90)
    print(f"{level_name} - {'Resistance Breakout' if is_resistance else 'Support Breakdown'} Analysis")
    print("=" * 90)
    print(f"\n✓ Found {len(df)} events where 15-min candle closed {'above' if is_resistance else 'below'} {level_name}")
    
    if is_resistance:
        print(f"\n{'Statistic':<20} {'Value':>15}")
        print("-" * 40)
        print(f"{'Median Gain:':<20} {df['peak_gain'].median():>14.2f} pts")
        print(f"{'Mode Gain:':<20} {stats.mode(df['peak_gain'].round(0), keepdims=True)[0][0]:>14.0f} pts")
        print(f"{'Mean Gain:':<20} {df['peak_gain'].mean():>14.2f} pts")
        print(f"{'Max Gain:':<20} {df['peak_gain'].max():>14.2f} pts")
        print(f"{'Min Gain:':<20} {df['peak_gain'].min():>14.2f} pts")
        
        print(f"\n{'Target Hit Probabilities:'}")
        print("-" * 40)
        print(f"{'10 points:':<20} {df['hit_10pts'].mean()*100:>13.1f}%")
        print(f"{'20 points:':<20} {df['hit_20pts'].mean()*100:>13.1f}%")
        print(f"{'30 points:':<20} {df['hit_30pts'].mean()*100:>13.1f}%")
        print(f"{'50 points:':<20} {df['hit_50pts'].mean()*100:>13.1f}%")
        print(f"{'100 points:':<20} {df['hit_100pts'].mean()*100:>13.1f}%")
        
        print(f"\n{'Average Time to Target (minutes):'}")
        print("-" * 40)
        if df['time_to_10pts'].notna().any():
            print(f"{'10 points:':<20} {df['time_to_10pts'].mean():>13.0f}m")
        if df['time_to_20pts'].notna().any():
            print(f"{'20 points:':<20} {df['time_to_20pts'].mean():>13.0f}m")
        if df['time_to_30pts'].notna().any():
            print(f"{'30 points:':<20} {df['time_to_30pts'].mean():>13.0f}m")
        if df['time_to_50pts'].notna().any():
            print(f"{'50 points:':<20} {df['time_to_50pts'].mean():>13.0f}m")
    else:
        print(f"\n{'Statistic':<20} {'Value':>15}")
        print("-" * 40)
        print(f"{'Median Drop:':<20} {df['peak_drop'].median():>14.2f} pts")
        print(f"{'Mode Drop:':<20} {stats.mode(df['peak_drop'].round(0), keepdims=True)[0][0]:>14.0f} pts")
        print(f"{'Mean Drop:':<20} {df['peak_drop'].mean():>14.2f} pts")
        print(f"{'Max Drop:':<20} {df['peak_drop'].max():>14.2f} pts")
        print(f"{'Min Drop:':<20} {df['peak_drop'].min():>14.2f} pts")
        
        print(f"\n{'Target Hit Probabilities:'}")
        print("-" * 40)
        print(f"{'10 points drop:':<20} {df['hit_10pts'].mean()*100:>13.1f}%")
        print(f"{'20 points drop:':<20} {df['hit_20pts'].mean()*100:>13.1f}%")
        print(f"{'30 points drop:':<20} {df['hit_30pts'].mean()*100:>13.1f}%")
        print(f"{'50 points drop:':<20} {df['hit_50pts'].mean()*100:>13.1f}%")
        print(f"{'100 points drop:':<20} {df['hit_100pts'].mean()*100:>13.1f}%")
        
        print(f"\n{'Average Time to Target (minutes):'}")
        print("-" * 40)
        if df['time_to_10pts'].notna().any():
            print(f"{'10 points drop:':<20} {df['time_to_10pts'].mean():>13.0f}m")
        if df['time_to_20pts'].notna().any():
            print(f"{'20 points drop:':<20} {df['time_to_20pts'].mean():>13.0f}m")
        if df['time_to_30pts'].notna().any():
            print(f"{'30 points drop:':<20} {df['time_to_30pts'].mean():>13.0f}m")
        if df['time_to_50pts'].notna().any():
            print(f"{'50 points drop:':<20} {df['time_to_50pts'].mean():>13.0f}m")
    
    # ML Model for predicting peak gain/drop
    print(f"\n{'Training ML Models for Movement Prediction:'}")
    print("-" * 90)
    
    features = ['distance_from_level', 'candle_body']
    if is_resistance:
        features.append('upper_wick')
        target_col = 'peak_gain'
    else:
        features.append('lower_wick')
        target_col = 'peak_drop'
    
    X = df[features].fillna(0)
    y = df[target_col]
    
    if len(X) > 10:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        
        # Random Forest
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        rf_score = rf.score(X_test, y_test)
        rf_pred = rf.predict(X_test)
        
        # Gradient Boosting
        gb = GradientBoostingRegressor(n_estimators=100, random_state=42)
        gb.fit(X_train, y_train)
        gb_score = gb.score(X_test, y_test)
        gb_pred = gb.predict(X_test)
        
        print(f"{'Model':<25} {'R² Score':>15} {'Predicted Median':>20}")
        print("-" * 90)
        print(f"{'Random Forest':<25} {rf_score:>14.1%} {np.median(rf_pred):>19.2f} pts")
        print(f"{'Gradient Boosting':<25} {gb_score:>14.1%} {np.median(gb_pred):>19.2f} pts")
        print(f"{'Actual Median':<25} {'':<15} {y.median():>19.2f} pts")
    
    return df


# Analyze all scenarios
print("\n" + "=" * 90)
print("15-MIN CANDLE CROSSING 1-HOUR RESISTANCE")
print("=" * 90)
df_15m_cross_1h_resistance = analyze_breakout_moves(df_15m, resistance_1h, "1-Hour Resistance", is_resistance=True)

print("\n" + "=" * 90)
print("15-MIN CANDLE CROSSING DAILY RESISTANCE")
print("=" * 90)
df_15m_cross_1d_resistance = analyze_breakout_moves(df_15m, resistance_1d, "Daily Resistance", is_resistance=True)

print("\n" + "=" * 90)
print("15-MIN CANDLE BREAKING 1-HOUR SUPPORT")
print("=" * 90)
df_15m_cross_1h_support = analyze_breakout_moves(df_15m, support_1h, "1-Hour Support", is_resistance=False)

print("\n" + "=" * 90)
print("15-MIN CANDLE BREAKING DAILY SUPPORT")
print("=" * 90)
df_15m_cross_1d_support = analyze_breakout_moves(df_15m, support_1d, "Daily Support", is_resistance=False)

# Save results
if df_15m_cross_1h_resistance is not None:
    df_15m_cross_1h_resistance.to_csv(data_dir / "NIFTY_15m_cross_1h_resistance.csv", index=False)
    print(f"\n✓ Saved: {data_dir / 'NIFTY_15m_cross_1h_resistance.csv'}")

if df_15m_cross_1d_resistance is not None:
    df_15m_cross_1d_resistance.to_csv(data_dir / "NIFTY_15m_cross_1d_resistance.csv", index=False)
    print(f"✓ Saved: {data_dir / 'NIFTY_15m_cross_1d_resistance.csv'}")

if df_15m_cross_1h_support is not None:
    df_15m_cross_1h_support.to_csv(data_dir / "NIFTY_15m_cross_1h_support.csv", index=False)
    print(f"✓ Saved: {data_dir / 'NIFTY_15m_cross_1h_support.csv'}")

if df_15m_cross_1d_support is not None:
    df_15m_cross_1d_support.to_csv(data_dir / "NIFTY_15m_cross_1d_support.csv", index=False)
    print(f"✓ Saved: {data_dir / 'NIFTY_15m_cross_1d_support.csv'}")

print("\n" + "=" * 90)
print("✓ Cross-Timeframe Analysis Complete!")
print("=" * 90)
