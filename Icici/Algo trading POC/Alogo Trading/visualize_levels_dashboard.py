"""
Visualize All Support & Resistance Levels with Strength Analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime

def load_levels():
    """Load support and resistance levels"""
    try:
        resistance = pd.read_csv('data/NIFTY_resistance_multi_timeframe.csv')
        support = pd.read_csv('data/NIFTY_support_multi_timeframe.csv')
        
        # Load current price
        data_5m = pd.read_csv('data/NIFTY_5min_20221024_20251023.csv')
        current_price = data_5m.iloc[-1]['close']
        
        return resistance, support, current_price
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None, 0

def calculate_distance(levels, current_price):
    """Calculate distance from current price"""
    if 'resistance_level' in levels.columns:
        level_col = 'resistance_level'
    else:
        level_col = 'support_level'
    
    levels['distance_pts'] = levels[level_col] - current_price
    levels['distance_pct'] = (levels['distance_pts'] / current_price) * 100
    levels['abs_distance'] = abs(levels['distance_pts'])
    
    return levels

def generate_html_dashboard(resistance, support, current_price):
    """Generate HTML dashboard"""
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIFTY Support & Resistance Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        
        .current-price {{
            font-size: 3rem;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        
        .timestamp {{
            color: #666;
            font-size: 0.9rem;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}
        
        .card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        
        .card-header {{
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #f0f0f0;
        }}
        
        .resistance-header {{
            color: #e74c3c;
        }}
        
        .support-header {{
            color: #27ae60;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }}
        
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e9ecef;
            font-size: 0.9rem;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .level-value {{
            font-weight: bold;
            font-size: 1rem;
        }}
        
        .strength-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: bold;
            color: white;
        }}
        
        .strength-very-strong {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .strength-strong {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        
        .strength-moderate {{
            background: linear-gradient(135deg, #ffa17f 0%, #00bf8f 100%);
        }}
        
        .strength-weak {{
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            color: #333;
        }}
        
        .timeframe-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 5px;
            font-size: 0.7rem;
            font-weight: bold;
            margin-right: 5px;
        }}
        
        .tf-daily {{
            background: #e74c3c;
            color: white;
        }}
        
        .tf-hourly {{
            background: #3498db;
            color: white;
        }}
        
        .tf-15m {{
            background: #95a5a6;
            color: white;
        }}
        
        .distance-positive {{
            color: #e74c3c;
            font-weight: bold;
        }}
        
        .distance-negative {{
            color: #27ae60;
            font-weight: bold;
        }}
        
        .nearest-level {{
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%) !important;
            font-weight: bold;
        }}
        
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        
        .stat-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            color: #6c757d;
            margin-top: 5px;
        }}
        
        .legend {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }}
        
        .legend-title {{
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 NIFTY Support & Resistance Dashboard</h1>
            <div class="current-price">₹{current_price:,.2f}</div>
            <div class="timestamp">Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <!-- Statistics -->
        <div class="stats-row">
            <div class="stat-box">
                <div class="stat-value">{len(resistance)}</div>
                <div class="stat-label">Resistance Levels</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(support)}</div>
                <div class="stat-label">Support Levels</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(resistance[resistance['distance_pct'] < 2])}</div>
                <div class="stat-label">Near Resistance (2%)</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(support[support['distance_pct'] > -2])}</div>
                <div class="stat-label">Near Support (2%)</div>
            </div>
        </div>
        
        <!-- Dashboard Grid -->
        <div class="dashboard-grid">
            <!-- Resistance Levels -->
            <div class="card">
                <div class="card-header resistance-header">
                    🔴 Resistance Levels
                </div>
"""
    
    # Add resistance table
    resistance_sorted = resistance.sort_values('abs_distance').head(20)
    
    html += """
                <table>
                    <thead>
                        <tr>
                            <th>Level</th>
                            <th>Timeframe</th>
                            <th>Strength</th>
                            <th>Distance</th>
                            <th>Hits</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for idx, row in resistance_sorted.iterrows():
        is_nearest = idx == resistance_sorted.index[0]
        row_class = 'nearest-level' if is_nearest else ''
        
        # Determine timeframe badge
        tf = row['timeframe']
        if tf == '1d':
            tf_class = 'tf-daily'
            tf_label = 'Daily'
        elif tf == '1h':
            tf_class = 'tf-hourly'
            tf_label = '1 Hour'
        else:
            tf_class = 'tf-15m'
            tf_label = '15 Min'
        
        # Determine strength badge
        strength = row.get('resistance_strength', 'Very Strong')
        if strength == 'Very Strong':
            strength_class = 'strength-very-strong'
        elif strength == 'Strong':
            strength_class = 'strength-strong'
        elif strength == 'Moderate':
            strength_class = 'strength-moderate'
        else:
            strength_class = 'strength-weak'
        
        distance_class = 'distance-positive' if row['distance_pts'] > 0 else 'distance-negative'
        
        html += f"""
                        <tr class="{row_class}">
                            <td class="level-value">₹{row['resistance_level']:,.2f}</td>
                            <td><span class="timeframe-badge {tf_class}">{tf_label}</span></td>
                            <td><span class="strength-badge {strength_class}">{strength}</span></td>
                            <td class="{distance_class}">{row['distance_pts']:+.2f} pts ({row['distance_pct']:+.2f}%)</td>
                            <td>{int(row.get('resistance_hits', 0))}</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <!-- Support Levels -->
            <div class="card">
                <div class="card-header support-header">
                    🟢 Support Levels
                </div>
"""
    
    # Add support table
    support_sorted = support.sort_values('abs_distance').head(20)
    
    html += """
                <table>
                    <thead>
                        <tr>
                            <th>Level</th>
                            <th>Timeframe</th>
                            <th>Strength</th>
                            <th>Distance</th>
                            <th>Hits</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for idx, row in support_sorted.iterrows():
        is_nearest = idx == support_sorted.index[0]
        row_class = 'nearest-level' if is_nearest else ''
        
        # Determine timeframe badge
        tf = row['timeframe']
        if tf == '1d':
            tf_class = 'tf-daily'
            tf_label = 'Daily'
        elif tf == '1h':
            tf_class = 'tf-hourly'
            tf_label = '1 Hour'
        else:
            tf_class = 'tf-15m'
            tf_label = '15 Min'
        
        # Determine strength badge
        strength = row.get('support_strength', 'Very Strong')
        if strength == 'Very Strong':
            strength_class = 'strength-very-strong'
        elif strength == 'Strong':
            strength_class = 'strength-strong'
        elif strength == 'Moderate':
            strength_class = 'strength-moderate'
        else:
            strength_class = 'strength-weak'
        
        distance_class = 'distance-negative' if row['distance_pts'] < 0 else 'distance-positive'
        
        html += f"""
                        <tr class="{row_class}">
                            <td class="level-value">₹{row['support_level']:,.2f}</td>
                            <td><span class="timeframe-badge {tf_class}">{tf_label}</span></td>
                            <td><span class="strength-badge {strength_class}">{strength}</span></td>
                            <td class="{distance_class}">{row['distance_pts']:+.2f} pts ({row['distance_pct']:+.2f}%)</td>
                            <td>{int(row.get('support_hits', 0))}</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Legend -->
        <div class="card">
            <div class="legend">
                <div class="legend-title">Legend:</div>
                <div class="legend-item">
                    <span class="timeframe-badge tf-daily">Daily</span> High timeframe (stronger)
                </div>
                <div class="legend-item">
                    <span class="timeframe-badge tf-hourly">1 Hour</span> Medium timeframe
                </div>
                <div class="legend-item">
                    <span class="timeframe-badge tf-15m">15 Min</span> Low timeframe (weaker)
                </div>
                <div class="legend-item" style="margin-top: 10px;">
                    <span class="strength-badge strength-very-strong">Very Strong</span>
                    <span class="strength-badge strength-strong">Strong</span>
                    <span class="strength-badge strength-moderate">Moderate</span>
                    <span class="strength-badge strength-weak">Weak</span>
                </div>
                <div style="margin-top: 10px; font-size: 0.85rem; color: #6c757d;">
                    🟡 Highlighted row = Nearest level to current price
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html

def main():
    print("=" * 80)
    print("SUPPORT & RESISTANCE LEVELS DASHBOARD")
    print("=" * 80)
    
    # Load data
    print("\n📊 Loading levels...")
    resistance, support, current_price = load_levels()
    
    if resistance is None or support is None:
        print("❌ Failed to load data")
        return
    
    print(f"✓ Loaded {len(resistance)} resistance levels")
    print(f"✓ Loaded {len(support)} support levels")
    print(f"✓ Current Price: ₹{current_price:,.2f}")
    
    # Calculate distances
    resistance = calculate_distance(resistance, current_price)
    support = calculate_distance(support, current_price)
    
    # Find nearest levels
    nearest_resistance = resistance.loc[resistance['abs_distance'].idxmin()]
    nearest_support = support.loc[support['abs_distance'].idxmin()]
    
    print(f"\n🔴 Nearest Resistance: ₹{nearest_resistance['resistance_level']:,.2f} ({nearest_resistance['timeframe']}) - {nearest_resistance['distance_pts']:+.2f} pts")
    print(f"🟢 Nearest Support: ₹{nearest_support['support_level']:,.2f} ({nearest_support['timeframe']}) - {nearest_support['distance_pts']:+.2f} pts")
    
    # Generate HTML
    print("\n🌐 Generating HTML dashboard...")
    html = generate_html_dashboard(resistance, support, current_price)
    
    # Save to file
    output_file = 'levels_dashboard.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Saved to: {output_file}")
    
    # Open in browser
    import webbrowser
    import os
    abs_path = os.path.abspath(output_file)
    webbrowser.open('file://' + abs_path)
    
    print(f"\n✅ Dashboard opened in browser!")
    print("=" * 80)

if __name__ == '__main__':
    main()
