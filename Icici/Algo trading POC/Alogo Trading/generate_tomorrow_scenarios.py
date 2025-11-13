"""
Generate Tomorrow's Market Scenarios with All Trading Ideas
Combines all analysis to show what could happen tomorrow
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

def load_all_data():
    """Load all analysis data"""
    try:
        # Load resistance data
        resistance_breakout = pd.read_csv('data/NIFTY_breakouts_multi_timeframe.csv')
        resistance_rejection = pd.read_csv('data/NIFTY_resistance_rejections_analysis.csv')
        
        # Load support data
        support_bounce = pd.read_csv('data/NIFTY_support_bounces_analysis.csv')
        support_breakdown = pd.read_csv('data/NIFTY_support_breakdowns_analysis.csv')
        
        # Load 5-min data for current price
        data_5m = pd.read_csv('data/NIFTY_5min_20221024_20251023.csv')
        data_5m['datetime'] = pd.to_datetime(data_5m['datetime'])
        
        return {
            'resistance_breakout': resistance_breakout,
            'resistance_rejection': resistance_rejection,
            'support_bounce': support_bounce,
            'support_breakdown': support_breakdown,
            'current_price': data_5m.iloc[-1]['close'],
            'current_time': data_5m.iloc[-1]['datetime'],
            'latest_candle': data_5m.iloc[-1]
        }
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def calculate_rsi(data, period=14):
    """Calculate RSI"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_current_rsi():
    """Get current RSI for all timeframes"""
    try:
        # 15-min RSI
        data_15m = pd.read_csv('data/NIFTY_15min_20221024_20251023.csv')
        data_15m['rsi'] = calculate_rsi(data_15m['close'])
        rsi_15m = data_15m['rsi'].iloc[-1]
        
        # 1-hour RSI
        data_1h = pd.read_csv('data/NIFTY_1hour_20221024_20251023.csv')
        data_1h['rsi'] = calculate_rsi(data_1h['close'])
        rsi_1h = data_1h['rsi'].iloc[-1]
        
        # Daily RSI
        data_1d = pd.read_csv('data/NIFTY_1day_20221024_20251023.csv')
        data_1d['rsi'] = calculate_rsi(data_1d['close'])
        rsi_daily = data_1d['rsi'].iloc[-1]
        
        return {
            '15m': rsi_15m,
            '1h': rsi_1h,
            'daily': rsi_daily
        }
    except Exception as e:
        print(f"Error calculating RSI: {e}")
        return {'15m': 50, '1h': 50, 'daily': 50}

def generate_scenarios(data):
    """Generate all possible scenarios for tomorrow"""
    
    current_price = data['current_price']
    rsi = get_current_rsi()
    
    scenarios = []
    
    # Get nearest resistance levels (within 2%)
    resistance_breakout = data['resistance_breakout'].copy()
    resistance_breakout['distance_pct'] = ((resistance_breakout['resistance_level'] - current_price) / current_price) * 100
    nearest_resistance = resistance_breakout[
        (resistance_breakout['distance_pct'] > -0.5) & 
        (resistance_breakout['distance_pct'] < 2.0)
    ].sort_values('distance_pct').head(5)
    
    # Get nearest support levels (within 2%)
    support_bounce = data['support_bounce'].copy()
    support_bounce['distance_pct'] = ((support_bounce['support_level'] - current_price) / current_price) * 100
    nearest_support = support_bounce[
        (support_bounce['distance_pct'] < 0.5) & 
        (support_bounce['distance_pct'] > -2.0)
    ].sort_values('distance_pct', ascending=False).head(5)
    
    # BULLISH SCENARIOS - If market goes UP
    for idx, row in nearest_resistance.iterrows():
        level = row['resistance_level']
        timeframe = row['timeframe']
        distance = level - current_price
        
        # Get rejection data for this level
        rejection_data = data['resistance_rejection'][
            (data['resistance_rejection']['resistance_level'] == level) &
            (data['resistance_rejection']['timeframe'] == timeframe)
        ]
        
        # Determine optimal targets based on historical data
        # Use most probable target based on hit rates
        if row['hit_50'] > 0.75:
            target_main = level + 50
            target_label = '50pts'
            target_prob = row['hit_50'] * 100
        elif row['hit_30'] > 0.80:
            target_main = level + 30
            target_label = '30pts'
            target_prob = row['hit_30'] * 100
        elif row['hit_20'] > 0.85:
            target_main = level + 20
            target_label = '20pts'
            target_prob = row['hit_20'] * 100
        else:
            target_main = level + 10
            target_label = '10pts'
            target_prob = row['hit_10'] * 100
        
        # Calculate optimal stop loss (max 10 points)
        stop_loss_pts = 10
        stop_loss = level - stop_loss_pts
        
        # Calculate expected value with actual targets
        target_pts = target_main - level
        expected_value = (target_prob/100 * target_pts) - ((1 - target_prob/100) * stop_loss_pts)
        
        # RSI-based condition enhancement
        rsi_boost = ''
        if timeframe == '1-hour' and rsi['1h'] > 70:
            rsi_boost = ' (RSI >70: Momentum Override)'
            target_prob = min(99.5, target_prob * 1.02)  # Slight boost
        elif timeframe == '1-hour' and rsi['1h'] < 30:
            rsi_boost = ' (RSI <30: Weak Breakout)'
            
        # Scenario 1: BREAKOUT
        breakout_scenario = {
            'scenario_id': f'BULL_BREAKOUT_{level}',
            'direction': 'BULLISH',
            'type': 'BREAKOUT',
            'level': level,
            'timeframe': timeframe,
            'distance_pts': distance,
            'distance_pct': (distance / current_price) * 100,
            'entry': level,
            'stop_loss': stop_loss,
            'stop_loss_pts': stop_loss_pts,
            'target_conservative': level + 10,
            'target_main': target_main,
            'target_label': target_label,
            'target_aggressive': level + 100 if row['hit_100'] > 0.60 else level + 50,
            'probability_10pts': row['hit_10'] * 100,
            'probability_20pts': row['hit_20'] * 100,
            'probability_30pts': row['hit_30'] * 100,
            'probability_50pts': row['hit_50'] * 100,
            'probability_target': target_prob,
            'expected_value': expected_value,
            'risk_reward': target_pts / stop_loss_pts,
            'rsi_condition': 'FAVORABLE' if rsi['15m'] > 70 else 'NEUTRAL' if rsi['15m'] > 50 else 'WEAK',
            'rsi_boost': rsi_boost,
            'confidence': 'HIGH' if target_prob > 90 else 'MEDIUM' if target_prob > 75 else 'LOW',
            'description': f"Breakout above ₹{level:.2f} → Target: ₹{target_main:.2f} ({target_label}) @ {target_prob:.1f}% probability{rsi_boost}"
        }
        scenarios.append(breakout_scenario)
        
        # Scenario 2: REJECTION
        if len(rejection_data) > 0:
            rej_row = rejection_data.iloc[0]
            
            # Determine best target for rejection
            if rej_row['drop_50'] > 0.70:
                target_main = level - 50
                target_label = '50pts drop'
                target_prob = rej_row['drop_50'] * 100
            elif rej_row['drop_30'] > 0.75:
                target_main = level - 30
                target_label = '30pts drop'
                target_prob = rej_row['drop_30'] * 100
            elif rej_row['drop_20'] > 0.80:
                target_main = level - 20
                target_label = '20pts drop'
                target_prob = rej_row['drop_20'] * 100
            else:
                target_main = level - 10
                target_label = '10pts drop'
                target_prob = rej_row['drop_10'] * 100
            
            # Stop loss max 10 points
            stop_loss_pts = 10
            stop_loss = level + stop_loss_pts
            
            # Expected value
            target_pts = abs(target_main - level)
            expected_value = (target_prob/100 * target_pts) - ((1 - target_prob/100) * stop_loss_pts)
            
            # RSI-based enhancement
            rsi_boost = ''
            if rsi['15m'] >= 70 or rsi['1h'] >= 70:
                rsi_boost = ' (RSI ≥70: High Reversal Probability)'
                target_prob = min(99.5, target_prob * 1.05)
            
            rejection_scenario = {
                'scenario_id': f'BEAR_REJECTION_{level}',
                'direction': 'BEARISH',
                'type': 'REJECTION',
                'level': level,
                'timeframe': timeframe,
                'distance_pts': distance,
                'distance_pct': (distance / current_price) * 100,
                'entry': level,
                'stop_loss': stop_loss,
                'stop_loss_pts': stop_loss_pts,
                'target_conservative': level - 10,
                'target_main': target_main,
                'target_label': target_label,
                'target_aggressive': level - 100 if rej_row['drop_100'] > 0.50 else level - 50,
                'probability_10pts': rej_row['drop_10'] * 100,
                'probability_20pts': rej_row['drop_20'] * 100,
                'probability_30pts': rej_row['drop_30'] * 100,
                'probability_50pts': rej_row['drop_50'] * 100,
                'probability_target': target_prob,
                'expected_value': expected_value,
                'risk_reward': target_pts / stop_loss_pts,
                'rsi_condition': 'FAVORABLE' if rsi['15m'] >= 70 else 'NEUTRAL',
                'rsi_boost': rsi_boost,
                'confidence': 'HIGH' if target_prob > 85 else 'MEDIUM' if target_prob > 70 else 'LOW',
                'description': f"Rejection at ₹{level:.2f} → Target: ₹{target_main:.2f} ({target_label}) @ {target_prob:.1f}% probability{rsi_boost}"
            }
            scenarios.append(rejection_scenario)
    
    # BEARISH SCENARIOS - If market goes DOWN
    for idx, row in nearest_support.iterrows():
        level = row['support_level']
        timeframe = row['timeframe']
        distance = current_price - level
        
        # Get breakdown data for this level
        breakdown_data = data['support_breakdown'][
            (data['support_breakdown']['support_level'] == level) &
            (data['support_breakdown']['timeframe'] == timeframe)
        ]
        
        # Determine optimal target for bounce
        if row['rally_50'] > 0.85:
            target_main = level + 50
            target_label = '50pts rally'
            target_prob = row['rally_50'] * 100
        elif row['rally_30'] > 0.85:
            target_main = level + 30
            target_label = '30pts rally'
            target_prob = row['rally_30'] * 100
        elif row['rally_20'] > 0.90:
            target_main = level + 20
            target_label = '20pts rally'
            target_prob = row['rally_20'] * 100
        else:
            target_main = level + 10
            target_label = '10pts rally'
            target_prob = row['rally_10'] * 100
        
        # Stop loss max 10 points
        stop_loss_pts = 10
        stop_loss = level - stop_loss_pts
        
        # Expected value
        target_pts = target_main - level
        expected_value = (target_prob/100 * target_pts) - ((1 - target_prob/100) * stop_loss_pts)
        
        # RSI-based enhancement
        rsi_boost = ''
        if rsi['15m'] <= 30 or rsi['1h'] <= 30:
            rsi_boost = ' (RSI ≤30: Perfect Buy Signal!)'
            target_prob = min(100, target_prob * 1.05)
        
        # Scenario 3: BOUNCE
        bounce_scenario = {
            'scenario_id': f'BULL_BOUNCE_{level}',
            'direction': 'BULLISH',
            'type': 'BOUNCE',
            'level': level,
            'timeframe': timeframe,
            'distance_pts': -distance,
            'distance_pct': (-distance / current_price) * 100,
            'entry': level,
            'stop_loss': stop_loss,
            'stop_loss_pts': stop_loss_pts,
            'target_conservative': level + 10,
            'target_main': target_main,
            'target_label': target_label,
            'target_aggressive': level + 100 if row['rally_100'] > 0.70 else level + 50,
            'probability_10pts': row['rally_10'] * 100,
            'probability_20pts': row['rally_20'] * 100,
            'probability_30pts': row['rally_30'] * 100,
            'probability_50pts': row['rally_50'] * 100,
            'probability_target': target_prob,
            'expected_value': expected_value,
            'risk_reward': target_pts / stop_loss_pts,
            'rsi_condition': 'FAVORABLE' if rsi['15m'] < 30 else 'NEUTRAL' if rsi['15m'] < 50 else 'WEAK',
            'rsi_boost': rsi_boost,
            'confidence': 'HIGH' if target_prob > 90 else 'MEDIUM' if target_prob > 75 else 'LOW',
            'description': f"Bounce from ₹{level:.2f} → Target: ₹{target_main:.2f} ({target_label}) @ {target_prob:.1f}% probability{rsi_boost}"
        }
        scenarios.append(bounce_scenario)
        
        # Scenario 4: BREAKDOWN
        if len(breakdown_data) > 0:
            bd_row = breakdown_data.iloc[0]
            
            # Determine best target for breakdown
            if bd_row['drop_50'] > 0.80:
                target_main = level - 50
                target_label = '50pts drop'
                target_prob = bd_row['drop_50'] * 100
            elif bd_row['drop_30'] > 0.85:
                target_main = level - 30
                target_label = '30pts drop'
                target_prob = bd_row['drop_30'] * 100
            elif bd_row['drop_20'] > 0.90:
                target_main = level - 20
                target_label = '20pts drop'
                target_prob = bd_row['drop_20'] * 100
            else:
                target_main = level - 10
                target_label = '10pts drop'
                target_prob = bd_row['drop_10'] * 100
            
            # Stop loss max 10 points
            stop_loss_pts = 10
            stop_loss = level + stop_loss_pts
            
            # Expected value
            target_pts = abs(target_main - level)
            expected_value = (target_prob/100 * target_pts) - ((1 - target_prob/100) * stop_loss_pts)
            
            # RSI-based enhancement
            rsi_boost = ''
            if rsi['15m'] <= 30 or rsi['daily'] <= 30:
                rsi_boost = ' (RSI ≤30: Panic Selling Likely)'
                target_prob = min(99.5, target_prob * 1.03)
            
            breakdown_scenario = {
                'scenario_id': f'BEAR_BREAKDOWN_{level}',
                'direction': 'BEARISH',
                'type': 'BREAKDOWN',
                'level': level,
                'timeframe': timeframe,
                'distance_pts': -distance,
                'distance_pct': (-distance / current_price) * 100,
                'entry': level,
                'stop_loss': stop_loss,
                'stop_loss_pts': stop_loss_pts,
                'target_conservative': level - 10,
                'target_main': target_main,
                'target_label': target_label,
                'target_aggressive': level - 100 if bd_row['drop_100'] > 0.75 else level - 50,
                'probability_10pts': bd_row['drop_10'] * 100,
                'probability_20pts': bd_row['drop_20'] * 100,
                'probability_30pts': bd_row['drop_30'] * 100,
                'probability_50pts': bd_row['drop_50'] * 100,
                'probability_target': target_prob,
                'expected_value': expected_value,
                'risk_reward': target_pts / stop_loss_pts,
                'rsi_condition': 'FAVORABLE' if rsi['15m'] < 30 else 'NEUTRAL',
                'rsi_boost': rsi_boost,
                'confidence': 'HIGH' if target_prob > 90 else 'MEDIUM' if target_prob > 80 else 'LOW',
                'description': f"Breakdown below ₹{level:.2f} → Target: ₹{target_main:.2f} ({target_label}) @ {target_prob:.1f}% probability{rsi_boost}"
            }
            scenarios.append(breakdown_scenario)
    
    # Remove duplicate levels - keep only the best scenario per level
    unique_scenarios = {}
    for scenario in scenarios:
        level_key = f"{scenario['level']:.2f}_{scenario['type']}"
        if level_key not in unique_scenarios:
            unique_scenarios[level_key] = scenario
        else:
            # Keep the one with higher expected value
            if scenario['expected_value'] > unique_scenarios[level_key]['expected_value']:
                unique_scenarios[level_key] = scenario
    
    scenarios = list(unique_scenarios.values())
    
    # Sort by expected value
    scenarios.sort(key=lambda x: x['expected_value'], reverse=True)
    
    # Further filter to remove very close levels (within 5 points)
    filtered_scenarios = []
    used_levels = set()
    
    for scenario in scenarios:
        level = scenario['level']
        # Check if any used level is within 5 points
        is_too_close = any(abs(level - used_level) < 5 for used_level in used_levels)
        
        if not is_too_close:
            filtered_scenarios.append(scenario)
            used_levels.add(level)
            
            # Stop after we have enough diverse scenarios
            if len(filtered_scenarios) >= 20:
                break
    
    return filtered_scenarios, rsi

def generate_market_summary(data, scenarios, rsi):
    """Generate market summary and recommendations"""
    
    current_price = data['current_price']
    
    # Determine market bias
    if rsi['15m'] > 70 and rsi['daily'] > 70:
        bias = 'OVERBOUGHT'
        bias_color = 'danger'
    elif rsi['15m'] < 30 and rsi['daily'] < 30:
        bias = 'OVERSOLD'
        bias_color = 'success'
    elif rsi['15m'] > 50:
        bias = 'BULLISH'
        bias_color = 'success'
    else:
        bias = 'BEARISH'
        bias_color = 'danger'
    
    # Get best scenarios
    best_bullish = [s for s in scenarios if s['direction'] == 'BULLISH'][:3]
    best_bearish = [s for s in scenarios if s['direction'] == 'BEARISH'][:3]
    
    summary = {
        'current_price': current_price,
        'current_time': str(data['current_time']),
        'rsi': rsi,
        'market_bias': bias,
        'bias_color': bias_color,
        'total_scenarios': len(scenarios),
        'best_bullish_scenarios': best_bullish,
        'best_bearish_scenarios': best_bearish,
        'top_recommendation': scenarios[0] if scenarios else None
    }
    
    return summary

def main():
    print("=" * 100)
    print("TOMORROW'S MARKET SCENARIOS - COMPREHENSIVE ANALYSIS")
    print("=" * 100)
    
    # Load data
    print("\n📊 Loading all analysis data...")
    data = load_all_data()
    
    if not data:
        print("❌ Failed to load data")
        return
    
    print(f"✓ Current Price: ₹{data['current_price']:.2f}")
    print(f"✓ Last Update: {data['current_time']}")
    
    # Generate scenarios
    print("\n🎯 Generating all possible scenarios...")
    scenarios, rsi = generate_scenarios(data)
    
    print(f"✓ Generated {len(scenarios)} scenarios")
    print(f"\n📈 RSI Conditions:")
    print(f"   15-min: {rsi['15m']:.2f}")
    print(f"   1-hour: {rsi['1h']:.2f}")
    print(f"   Daily:  {rsi['daily']:.2f}")
    
    # Generate summary
    summary = generate_market_summary(data, scenarios, rsi)
    
    # Convert numpy types to Python types for JSON serialization
    def convert_to_json_serializable(obj):
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_json_serializable(i) for i in obj]
        return obj
    
    # Save to JSON for web app
    output = {
        'summary': convert_to_json_serializable(summary),
        'scenarios': convert_to_json_serializable(scenarios),
        'generated_at': datetime.now().isoformat()
    }
    
    with open('data/tomorrow_scenarios.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Saved to: data/tomorrow_scenarios.json")
    
    # Display top scenarios
    print("\n" + "=" * 100)
    print("TOP 5 TRADING OPPORTUNITIES FOR TOMORROW")
    print("=" * 100)
    
    for i, scenario in enumerate(scenarios[:5], 1):
        print(f"\n#{i} - {scenario['type']} at ₹{scenario['level']:.2f} ({scenario['timeframe']})")
        print(f"    Direction: {scenario['direction']}")
        print(f"    Distance: {scenario['distance_pts']:.2f} pts ({scenario['distance_pct']:.2f}%)")
        print(f"    Entry: ₹{scenario['entry']:.2f} | SL: ₹{scenario['stop_loss']:.2f} (Max {scenario['stop_loss_pts']} pts)")
        print(f"    Target: ₹{scenario['target_main']:.2f} ({scenario['target_label']})")
        print(f"    Probability: {scenario['probability_target']:.1f}%")
        print(f"    Risk:Reward = 1:{scenario['risk_reward']:.2f}")
        print(f"    Expected Value: +{scenario['expected_value']:.2f} pts per trade")
        print(f"    Confidence: {scenario['confidence']}")
        print(f"    💡 {scenario['description']}")
    
    print("\n" + "=" * 100)
    print("✅ Analysis Complete! Use this data in the trading dashboard.")
    print("=" * 100)

if __name__ == '__main__':
    main()
