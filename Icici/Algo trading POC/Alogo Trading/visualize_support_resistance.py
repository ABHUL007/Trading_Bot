"""Interactive web app to visualize Support and Resistance levels"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser
import os

print("=" * 70)
print("Loading Support & Resistance Data...")
print("=" * 70)

# Load data
price_data = pd.read_csv("data/NIFTY_15min_20221024_20251023.csv")
resistance_data = pd.read_csv("data/NIFTY_resistance_levels.csv")
support_data = pd.read_csv("data/NIFTY_support_levels.csv")

price_data['datetime'] = pd.to_datetime(price_data['datetime'])
resistance_data['datetime'] = pd.to_datetime(resistance_data['datetime'])
support_data['datetime'] = pd.to_datetime(support_data['datetime'])

print(f"✓ Loaded {len(price_data)} price candles")
print(f"✓ Loaded {len(resistance_data)} resistance levels")
print(f"✓ Loaded {len(support_data)} support levels")

# Filter for recent data (last 90 days)
recent_data = price_data.tail(500)
current_price = recent_data['close'].iloc[-1]

# Get strong levels near current price
price_range = current_price * 0.05  # 5% range

strong_resistance = resistance_data[
    (resistance_data['strength'].isin(['Very Strong', 'Strong'])) &
    (resistance_data['price'] >= current_price) &
    (resistance_data['price'] <= current_price + price_range)
].sort_values('strength_score', ascending=False).head(10)

strong_support = support_data[
    (support_data['strength'].isin(['Very Strong', 'Strong'])) &
    (support_data['price'] <= current_price) &
    (support_data['price'] >= current_price - price_range)
].sort_values('strength_score', ascending=False).head(10)

print(f"\n✓ Found {len(strong_resistance)} strong resistance levels nearby")
print(f"✓ Found {len(strong_support)} strong support levels nearby")

print("\n" + "=" * 70)
print("Creating Interactive Chart...")
print("=" * 70)

# Create candlestick chart
fig = go.Figure()

# Add candlestick
fig.add_trace(go.Candlestick(
    x=recent_data['datetime'],
    open=recent_data['open'],
    high=recent_data['high'],
    low=recent_data['low'],
    close=recent_data['close'],
    name='NIFTY',
    increasing_line_color='green',
    decreasing_line_color='red'
))

# Add resistance levels
for idx, level in strong_resistance.iterrows():
    color = 'rgba(255, 0, 0, 0.7)' if level['strength'] == 'Very Strong' else 'rgba(255, 100, 100, 0.5)'
    line_width = 2 if level['strength'] == 'Very Strong' else 1
    
    fig.add_hline(
        y=level['price'],
        line_dash="dash",
        line_color=color,
        line_width=line_width,
        annotation_text=f"R: ₹{level['price']:.2f} ({level['num_hits']} hits)",
        annotation_position="right"
    )

# Add support levels
for idx, level in strong_support.iterrows():
    color = 'rgba(0, 255, 0, 0.7)' if level['strength'] == 'Very Strong' else 'rgba(100, 255, 100, 0.5)'
    line_width = 2 if level['strength'] == 'Very Strong' else 1
    
    fig.add_hline(
        y=level['price'],
        line_dash="dash",
        line_color=color,
        line_width=line_width,
        annotation_text=f"S: ₹{level['price']:.2f} ({level['num_hits']} hits)",
        annotation_position="right"
    )

# Update layout
fig.update_layout(
    title={
        'text': f'NIFTY Support & Resistance Levels<br>Current Price: ₹{current_price:,.2f}',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 20}
    },
    xaxis_title='Date',
    yaxis_title='Price (₹)',
    template='plotly_dark',
    height=800,
    hovermode='x unified',
    xaxis_rangeslider_visible=False
)

# Save to HTML
output_file = "support_resistance_chart.html"
fig.write_html(output_file)

print(f"\n✓ Chart saved to: {output_file}")

# Create detailed HTML report
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NIFTY Support & Resistance Analysis</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #1a1a1a;
            color: #ffffff;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: #4CAF50;
            margin-bottom: 10px;
        }}
        .current-price {{
            text-align: center;
            font-size: 24px;
            color: #2196F3;
            margin-bottom: 30px;
        }}
        .section {{
            margin: 30px 0;
            background-color: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        h2 {{
            color: #FF9800;
            border-bottom: 2px solid #FF9800;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #333;
            color: #FFF;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #444;
        }}
        tr:hover {{
            background-color: #333;
        }}
        .very-strong {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .strong {{
            color: #8BC34A;
        }}
        .moderate {{
            color: #FFC107;
        }}
        .weak {{
            color: #9E9E9E;
        }}
        .resistance {{
            background-color: rgba(255, 0, 0, 0.1);
        }}
        .support {{
            background-color: rgba(0, 255, 0, 0.1);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .stat-box {{
            background-color: #333;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .stat-label {{
            color: #999;
            margin-top: 10px;
        }}
        .chart-container {{
            margin: 30px 0;
            text-align: center;
        }}
        .chart-link {{
            display: inline-block;
            background-color: #2196F3;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-size: 18px;
            transition: background-color 0.3s;
        }}
        .chart-link:hover {{
            background-color: #1976D2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 NIFTY Support & Resistance Analysis</h1>
        <div class="current-price">Current Price: ₹{current_price:,.2f}</div>
        
        <div class="chart-container">
            <a href="{output_file}" target="_blank" class="chart-link">📈 View Interactive Chart</a>
        </div>
        
        <div class="section">
            <h2>📈 Summary Statistics</h2>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value">{len(resistance_data)}</div>
                    <div class="stat-label">Total Resistance Levels</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{len(support_data)}</div>
                    <div class="stat-label">Total Support Levels</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{len(strong_resistance)}</div>
                    <div class="stat-label">Nearby Resistance</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{len(strong_support)}</div>
                    <div class="stat-label">Nearby Support</div>
                </div>
            </div>
        </div>
        
        <div class="section resistance">
            <h2>🔴 Top Resistance Levels (Above Current Price)</h2>
            <table>
                <tr>
                    <th>Price</th>
                    <th>Distance</th>
                    <th>Retracement %</th>
                    <th>Hits</th>
                    <th>Reversals</th>
                    <th>Strength Score</th>
                    <th>Strength</th>
                    <th>Date Identified</th>
                </tr>
"""

for idx, level in strong_resistance.iterrows():
    distance = ((level['price'] - current_price) / current_price) * 100
    strength_class = level['strength'].lower().replace(' ', '-')
    html_content += f"""
                <tr>
                    <td>₹{level['price']:,.2f}</td>
                    <td>+{distance:.2f}%</td>
                    <td>{level['retracement_pct']:.2f}%</td>
                    <td>{level['num_hits']}</td>
                    <td>{level['num_reversals']}</td>
                    <td>{level['strength_score']:.2f}</td>
                    <td class="{strength_class}">{level['strength']}</td>
                    <td>{level['datetime'].strftime('%Y-%m-%d %H:%M')}</td>
                </tr>
"""

html_content += """
            </table>
        </div>
        
        <div class="section support">
            <h2>🟢 Top Support Levels (Below Current Price)</h2>
            <table>
                <tr>
                    <th>Price</th>
                    <th>Distance</th>
                    <th>Retracement %</th>
                    <th>Hits</th>
                    <th>Reversals</th>
                    <th>Strength Score</th>
                    <th>Strength</th>
                    <th>Date Identified</th>
                </tr>
"""

for idx, level in strong_support.iterrows():
    distance = ((current_price - level['price']) / current_price) * 100
    strength_class = level['strength'].lower().replace(' ', '-')
    html_content += f"""
                <tr>
                    <td>₹{level['price']:,.2f}</td>
                    <td>-{distance:.2f}%</td>
                    <td>{level['retracement_pct']:.2f}%</td>
                    <td>{level['num_hits']}</td>
                    <td>{level['num_reversals']}</td>
                    <td>{level['strength_score']:.2f}</td>
                    <td class="{strength_class}">{level['strength']}</td>
                    <td>{level['datetime'].strftime('%Y-%m-%d %H:%M')}</td>
                </tr>
"""

html_content += """
            </table>
        </div>
        
        <div class="section">
            <h2>ℹ️ How to Read This Analysis</h2>
            <ul>
                <li><strong>Resistance</strong>: Price levels where selling pressure is expected (above current price)</li>
                <li><strong>Support</strong>: Price levels where buying pressure is expected (below current price)</li>
                <li><strong>Hits</strong>: Number of times price touched this level</li>
                <li><strong>Reversals</strong>: Number of times price reversed direction at this level</li>
                <li><strong>Strength Score</strong>: Combined score based on retracement %, hits, and reversals (0-100)</li>
                <li><strong>Very Strong</strong>: Score ≥ 70 (High probability of holding)</li>
                <li><strong>Strong</strong>: Score ≥ 50 (Good probability of holding)</li>
                <li><strong>Moderate</strong>: Score ≥ 30 (May hold)</li>
                <li><strong>Weak</strong>: Score < 30 (Low probability of holding)</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

# Save HTML report
report_file = "support_resistance_report.html"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✓ Report saved to: {report_file}")

print("\n" + "=" * 70)
print("✓ Opening in browser...")
print("=" * 70)

# Open in browser
webbrowser.open('file://' + os.path.abspath(report_file))

print(f"\n✓ Browser opened with report!")
print(f"\nFiles created:")
print(f"  1. {report_file} - Detailed HTML report")
print(f"  2. {output_file} - Interactive candlestick chart")
print("\n" + "=" * 70)
