#!/usr/bin/env python3
"""
KHUSI PREDICTION DASHBOARD - HTML GENERATOR
===========================================

Generate a beautiful static HTML dashboard with predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime
from khusi_prediction_dashboard import KhusiPredictionDashboard

def generate_html_dashboard():
    """Generate a beautiful HTML dashboard"""
    
    print("🎨 Generating HTML Dashboard...")
    
    # Run the prediction dashboard
    dashboard = KhusiPredictionDashboard()
    df = dashboard.load_latest_data()
    if df is None:
        return False
        
    dashboard.analyze_current_market_state()
    if not dashboard.generate_predictions():
        return False
    
    # Extract data for HTML
    latest_close = dashboard.latest_close
    latest_date = dashboard.latest_date
    current_data = dashboard.current_data
    predictions = dashboard.predictions
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Khusi Invest Model - NIFTY Predictions</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .header .subtitle {{
                font-size: 1.2em;
                opacity: 0.9;
            }}
            
            .main-content {{
                padding: 30px;
            }}
            
            .current-price {{
                text-align: center;
                margin-bottom: 40px;
                padding: 20px;
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                border-radius: 15px;
                color: white;
            }}
            
            .current-price .price {{
                font-size: 3em;
                font-weight: bold;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .current-price .date {{
                font-size: 1.2em;
                margin-top: 10px;
                opacity: 0.9;
            }}
            
            .predictions-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 30px;
                margin-bottom: 40px;
            }}
            
            .prediction-card {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                border-left: 5px solid;
            }}
            
            .next-day {{ border-left-color: #ff6b6b; }}
            .next-week {{ border-left-color: #4ecdc4; }}
            .next-month {{ border-left-color: #45b7d1; }}
            
            .prediction-card h3 {{
                color: #2c3e50;
                margin-bottom: 20px;
                font-size: 1.4em;
            }}
            
            .prediction-value {{
                font-size: 2em;
                font-weight: bold;
                margin: 15px 0;
            }}
            
            .up {{ color: #27ae60; }}
            .down {{ color: #e74c3c; }}
            .neutral {{ color: #f39c12; }}
            
            .confidence {{
                background: #ecf0f1;
                padding: 10px;
                border-radius: 8px;
                margin: 15px 0;
            }}
            
            .confidence-bar {{
                background: #bdc3c7;
                border-radius: 10px;
                height: 20px;
                overflow: hidden;
            }}
            
            .confidence-fill {{
                background: linear-gradient(90deg, #27ae60, #2ecc71);
                height: 100%;
                border-radius: 10px;
                transition: width 0.5s ease;
            }}
            
            .ema-analysis {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }}
            
            .ema-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }}
            
            .ema-item {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
            }}
            
            .ema-item .ema-label {{
                font-weight: bold;
                color: #2c3e50;
            }}
            
            .ema-item .ema-value {{
                font-size: 1.2em;
                margin: 5px 0;
            }}
            
            .ema-item .ema-diff {{
                font-size: 0.9em;
                padding: 5px 10px;
                border-radius: 15px;
            }}
            
            .positive {{ background: #d4edda; color: #155724; }}
            .negative {{ background: #f8d7da; color: #721c24; }}
            
            .market-state {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }}
            
            .state-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
            }}
            
            .state-item {{
                text-align: center;
                padding: 20px;
                border-radius: 10px;
                background: #f8f9fa;
            }}
            
            .state-item .value {{
                font-size: 2em;
                font-weight: bold;
                color: #2c3e50;
            }}
            
            .state-item .label {{
                margin-top: 10px;
                color: #7f8c8d;
            }}
            
            .risk-assessment {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                text-align: center;
            }}
            
            .risk-level {{
                font-size: 2.5em;
                margin: 20px 0;
            }}
            
            .footer {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 20px;
                font-size: 0.9em;
            }}
            
            @media (max-width: 768px) {{
                .predictions-grid {{
                    grid-template-columns: 1fr;
                }}
                .current-price .price {{
                    font-size: 2em;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 KHUSI INVEST MODEL</h1>
                <div class="subtitle">Advanced EMA-Based NIFTY Predictions</div>
                <div class="subtitle">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
            
            <div class="main-content">
                <div class="current-price">
                    <div class="price">₹{latest_close:,.2f}</div>
                    <div class="date">Latest Data: {latest_date.strftime('%Y-%m-%d')}</div>
                </div>
                
                <div class="predictions-grid">
                    <div class="prediction-card next-day">
                        <h3>🌅 NEXT DAY PREDICTION</h3>
                        <div class="prediction-value {predictions['next_day']['direction'].lower().split()[0].lower()}">{predictions['next_day']['direction']}</div>
                        <div class="confidence">
                            <div style="margin-bottom: 10px;">Confidence: {predictions['next_day']['confidence']*100:.1f}%</div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: {predictions['next_day']['confidence']*100}%"></div>
                            </div>
                        </div>
                        <div><strong>Probability UP:</strong> {predictions['next_day']['probability_up']*100:.1f}%</div>
                        <div><strong>Probability DOWN:</strong> {predictions['next_day']['probability_down']*100:.1f}%</div>
                        <div style="margin-top: 15px; font-size: 0.9em; color: #7f8c8d;">
                            Expected Target: ₹{latest_close * (1 + (-0.005 if predictions['next_day']['prediction'] == 0 else 0.005)):,.2f}
                        </div>
                    </div>
                    
                    <div class="prediction-card next-week">
                        <h3>📅 NEXT WEEK OUTLOOK</h3>
                        <div class="prediction-value {predictions['next_week']['outlook'].lower().split()[0].lower()}">{predictions['next_week']['outlook']}</div>
                        <div class="confidence">
                            <div style="margin-bottom: 10px;">Confidence: {predictions['next_week']['confidence']:.0f}%</div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: {predictions['next_week']['confidence']}%"></div>
                            </div>
                        </div>
                        <div style="font-size: 0.9em;">
                            <strong>Key Factors:</strong><br>
                            {'<br>'.join(['• ' + factor for factor in predictions['next_week']['factors']])}
                        </div>
                    </div>
                    
                    <div class="prediction-card next-month">
                        <h3>📆 NEXT MONTH OUTLOOK</h3>
                        <div class="prediction-value {predictions['next_month']['outlook'].lower().split()[0].lower()}">{predictions['next_month']['outlook']}</div>
                        <div class="confidence">
                            <div style="margin-bottom: 10px;">Confidence: {predictions['next_month']['confidence']:.0f}%</div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: {predictions['next_month']['confidence']}%"></div>
                            </div>
                        </div>
                        <div style="font-size: 0.9em;">
                            <strong>Key Factors:</strong><br>
                            {'<br>'.join(['• ' + factor for factor in predictions['next_month']['factors']])}
                        </div>
                    </div>
                </div>
                
                <div class="ema-analysis">
                    <h3 style="margin-bottom: 25px; color: #2c3e50;">📈 EMA Analysis</h3>
                    <div class="ema-grid">"""
    
    # Add EMA data
    ema_periods = [5, 9, 21, 50, 100, 200]
    for period in ema_periods:
        ema_value = current_data[f'ema_{period}']
        diff_pct = ((latest_close - ema_value) / ema_value) * 100
        diff_class = 'positive' if diff_pct >= 0 else 'negative'
        
        html_content += f"""
                        <div class="ema-item">
                            <div class="ema-label">EMA {period}</div>
                            <div class="ema-value">₹{ema_value:,.2f}</div>
                            <div class="ema-diff {diff_class}">{diff_pct:+.2f}%</div>
                        </div>"""
    
    html_content += f"""
                    </div>
                </div>
                
                <div class="market-state">
                    <h3 style="margin-bottom: 25px; color: #2c3e50;">🎯 Current Market State</h3>
                    <div class="state-grid">
                        <div class="state-item">
                            <div class="value">{current_data['correction_phase_name']}</div>
                            <div class="label">Market Phase (Day {int(current_data['days_in_phase'])})</div>
                        </div>
                        <div class="state-item">
                            <div class="value">{int(current_data['emas_above_count'])}/6</div>
                            <div class="label">EMAs Above Price</div>
                        </div>
                        <div class="state-item">
                            <div class="value">{int(current_data['ema_alignment_score'])}/5</div>
                            <div class="label">EMA Alignment Score</div>
                        </div>
                        <div class="state-item">
                            <div class="value">{current_data['daily_return']:+.2f}%</div>
                            <div class="label">Daily Return</div>
                        </div>
                        <div class="state-item">
                            <div class="value">{current_data['return_5d']:+.2f}%</div>
                            <div class="label">5-Day Return</div>
                        </div>
                        <div class="state-item">
                            <div class="value">{current_data['volatility']:.1f}%</div>
                            <div class="label">Volatility</div>
                        </div>
                    </div>
                </div>
                
                <div class="risk-assessment">
                    <h3 style="margin-bottom: 20px; color: #2c3e50;">⚠️ Risk Assessment</h3>
                    <div class="risk-level">{"🟢 LOW RISK" if current_data['volatility'] < 15 else "🟡 MEDIUM RISK" if current_data['volatility'] < 25 else "🔴 HIGH RISK"}</div>
                    <div style="font-size: 1.2em; margin: 10px 0;">
                        Current Volatility: {current_data['volatility']:.1f}%
                    </div>
                    <div style="color: #7f8c8d;">
                        Market Regime: {current_data['correction_phase_name']}
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>📊 Khusi Invest Model - Advanced EMA-based ML Predictions</p>
                <p>⚠️ For educational purposes. Always combine with fundamental analysis and proper risk management.</p>
                <p>💡 Model trained on 3+ years of historical data with 66.7% accuracy</p>
            </div>
        </div>
    </body>
    </html>"""
    
    # Save HTML file
    with open('khusi_prediction_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ HTML Dashboard saved as: khusi_prediction_dashboard.html")
    return True

if __name__ == "__main__":
    generate_html_dashboard()