"""
Real-Time NIFTY Trading Application
Features:
- Live NIFTY quotes via WebSocket
- Real-time candlestick charts
- Best trading signals based on analysis
- Buy/Sell order execution
- Session key management
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import pandas as pd
import json
from datetime import datetime, timedelta
import threading
import time
from breeze_connect import BreezeConnect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
breeze = None
session_active = False
current_price = 0
live_data = []
best_trades = []

# Load best trades from analysis
def load_best_trades():
    """Load best trading scenarios from CSV files"""
    global best_trades
    
    try:
        import os
        
        # Check if data directory exists
        if not os.path.exists('data'):
            print("⚠️  Warning: 'data' directory not found. No trading signals loaded.")
            print("   Run analysis scripts first to generate trading signals.")
            best_trades = []
            return []
        
        # Load tomorrow's scenarios if available
        try:
            with open('data/tomorrow_scenarios.json', 'r') as f:
                scenarios_data = json.load(f)
                return scenarios_data['scenarios']
        except:
            pass
        
        # Load resistance breakout data
        resistance_breakouts = pd.read_csv('data/NIFTY_breakouts_multi_timeframe.csv')
        resistance_rejections = pd.read_csv('data/NIFTY_resistance_rejections_analysis.csv')
        support_bounces = pd.read_csv('data/NIFTY_support_bounces_analysis.csv')
        support_breakdowns = pd.read_csv('data/NIFTY_support_breakdowns_analysis.csv')
        
        trades = []
        
        # Get top 3 resistance levels (nearest to current price)
        for _, row in resistance_breakouts.head(3).iterrows():
            trades.append({
                'type': 'BREAKOUT',
                'direction': 'BULLISH',
                'level': row['resistance_level'],
                'timeframe': row['timeframe'],
                'probability_10pts': row['hit_10'] * 100,
                'probability_20pts': row['hit_20'] * 100,
                'probability_50pts': row['hit_50'] * 100,
                'entry': row['resistance_level'],
                'stop_loss': row['resistance_level'] - 15,
                'target_conservative': row['resistance_level'] + 10,
                'target_aggressive': row['resistance_level'] + 50,
                'expected_value': 9.81 if row['timeframe'] == '1-hour' else 8.50
            })
        
        # Get top 3 support levels
        for _, row in support_bounces.head(3).iterrows():
            trades.append({
                'type': 'BOUNCE',
                'direction': 'BULLISH',
                'level': row['support_level'],
                'timeframe': row['timeframe'],
                'probability_10pts': row['rally_10'] * 100,
                'probability_20pts': row['rally_20'] * 100,
                'probability_50pts': row['rally_50'] * 100,
                'entry': row['support_level'],
                'stop_loss': row['support_level'] - 15,
                'target_conservative': row['support_level'] + 10,
                'target_aggressive': row['support_level'] + 50,
                'expected_value': 9.78 if row['timeframe'] == '1-hour' else 7.22
            })
        
        # Get top 3 resistance rejections (for shorting)
        for _, row in resistance_rejections.head(3).iterrows():
            trades.append({
                'type': 'REJECTION',
                'direction': 'BEARISH',
                'level': row['resistance_level'],
                'timeframe': row['timeframe'],
                'probability_10pts': row['drop_10'] * 100,
                'probability_20pts': row['drop_20'] * 100,
                'probability_50pts': row['drop_50'] * 100,
                'entry': row['resistance_level'],
                'stop_loss': row['resistance_level'] + 15,
                'target_conservative': row['resistance_level'] - 10,
                'target_aggressive': row['resistance_level'] - 50,
                'expected_value': 8.50
            })
        
        # Sort by expected value
        trades.sort(key=lambda x: x['expected_value'], reverse=True)
        best_trades = trades[:10]  # Top 10 trades
        
        print(f"✓ Loaded {len(best_trades)} best trading scenarios")
        return best_trades
        
    except FileNotFoundError as e:
        print(f"⚠️  Warning: CSV file not found - {e}")
        print("   Run these scripts first:")
        print("   - multi_timeframe_analysis.py")
        print("   - analyze_resistance_rejection.py")
        print("   - analyze_support_breakdown.py")
        print("   - analyze_support_bounce.py")
        best_trades = []
        return []
    except Exception as e:
        print(f"❌ Error loading trades: {e}")
        best_trades = []
        return []

# Initialize Breeze connection
def initialize_breeze(api_key, session_token):
    """Initialize ICICI Breeze connection"""
    global breeze, session_active
    
    try:
        breeze = BreezeConnect(api_key=api_key)
        breeze.generate_session(api_secret="your_api_secret", session_token=session_token)
        session_active = True
        print("✓ Breeze session initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Breeze initialization failed: {e}")
        session_active = False
        return False

# WebSocket for live data
def start_websocket():
    """Start WebSocket for real-time NIFTY quotes"""
    global breeze, current_price
    
    if not breeze or not session_active:
        print("✗ Breeze not initialized. Cannot start WebSocket.")
        return
    
    def on_ticks(tick):
        """Handle incoming tick data"""
        global current_price, live_data
        
        try:
            if tick and len(tick) > 0:
                tick_data = tick[0]
                current_price = tick_data.get('last', 0)
                
                # Create candlestick data
                candle = {
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'timestamp': datetime.now().timestamp() * 1000,
                    'open': tick_data.get('open', current_price),
                    'high': tick_data.get('high', current_price),
                    'low': tick_data.get('low', current_price),
                    'close': current_price,
                    'volume': tick_data.get('volume', 0)
                }
                
                # Emit to all connected clients
                socketio.emit('price_update', {
                    'price': current_price,
                    'time': candle['time'],
                    'candle': candle
                }, namespace='/live')
                
                # Check for trading signals
                check_trading_signals(current_price)
                
        except Exception as e:
            print(f"Error processing tick: {e}")
    
    # Subscribe to NIFTY
    try:
        breeze.subscribe_feeds(
            stock_token="1.1!4.1",  # NIFTY 50
            interval="1second"
        )
        breeze.on_ticks = on_ticks
        print("✓ WebSocket subscribed to NIFTY 50")
    except Exception as e:
        print(f"✗ WebSocket subscription failed: {e}")

def check_trading_signals(price):
    """Check if current price triggers any trading signals"""
    global best_trades
    
    for trade in best_trades:
        level = trade['level']
        distance = abs(price - level)
        distance_pct = (distance / price) * 100
        
        # Alert if within 0.1% of key level
        if distance_pct < 0.1:
            socketio.emit('trading_alert', {
                'type': trade['type'],
                'direction': trade['direction'],
                'level': level,
                'current_price': price,
                'probability': trade['probability_10pts'],
                'entry': trade['entry'],
                'target': trade['target_conservative'],
                'stop_loss': trade['stop_loss'],
                'expected_value': trade['expected_value']
            }, namespace='/live')

# Flask Routes
@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/session', methods=['POST'])
def update_session():
    """Update ICICI Breeze session key"""
    try:
        data = request.json
        api_key = data.get('api_key')
        session_token = data.get('session_token')
        
        if initialize_breeze(api_key, session_token):
            # Start WebSocket in background thread
            threading.Thread(target=start_websocket, daemon=True).start()
            
            return jsonify({
                'success': True,
                'message': 'Session updated successfully. WebSocket started.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to initialize session'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/trades')
def get_trades():
    """Get best trading scenarios"""
    global best_trades, current_price
    
    # Try to load tomorrow's scenarios first
    try:
        with open('data/tomorrow_scenarios.json', 'r') as f:
            scenarios_data = json.load(f)
            scenarios = scenarios_data['scenarios']
            summary = scenarios_data['summary']
            
            # Add distance from current price to each scenario
            for scenario in scenarios:
                if current_price > 0:
                    distance = scenario['level'] - current_price
                    distance_pct = (distance / current_price) * 100
                    scenario['distance_pts'] = round(distance, 2)
                    scenario['distance_pct'] = round(distance_pct, 2)
            
            return jsonify({
                'success': True,
                'trades': scenarios[:20],  # Top 20 scenarios
                'current_price': current_price,
                'summary': summary
            })
    except:
        pass
    
    # Fallback to best_trades
    trades_with_distance = []
    for trade in best_trades:
        trade_copy = trade.copy()
        if current_price > 0:
            distance = trade['level'] - current_price
            distance_pct = (distance / current_price) * 100
            trade_copy['distance_pts'] = round(distance, 2)
            trade_copy['distance_pct'] = round(distance_pct, 2)
        trades_with_distance.append(trade_copy)
    
    return jsonify({
        'success': True,
        'trades': trades_with_distance,
        'current_price': current_price
    })

@app.route('/api/order', methods=['POST'])
def place_order():
    """Place buy/sell order"""
    global breeze, session_active
    
    if not session_active:
        return jsonify({
            'success': False,
            'message': 'Session not active. Please update session key.'
        }), 400
    
    try:
        data = request.json
        order_type = data.get('order_type')  # 'buy' or 'sell'
        quantity = data.get('quantity', 50)
        price = data.get('price')
        stop_loss = data.get('stop_loss')
        target = data.get('target')
        
        # Place order via Breeze
        order_response = breeze.place_order(
            stock_code="NIFTY",
            exchange_code="NFO",
            product="futures",
            action="buy" if order_type == 'buy' else "sell",
            order_type="limit",
            quantity=str(quantity),
            price=str(price),
            validity="day"
        )
        
        return jsonify({
            'success': True,
            'message': f'{order_type.upper()} order placed successfully',
            'order_id': order_response.get('Success', {}).get('order_id', 'N/A'),
            'details': {
                'type': order_type,
                'quantity': quantity,
                'price': price,
                'stop_loss': stop_loss,
                'target': target
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Order failed: {str(e)}'
        }), 500

@app.route('/api/status')
def get_status():
    """Get current system status"""
    return jsonify({
        'success': True,
        'session_active': session_active,
        'current_price': current_price,
        'trades_loaded': len(best_trades),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/tomorrow')
def get_tomorrow_outlook():
    """Get tomorrow's market outlook and scenarios"""
    try:
        with open('data/tomorrow_scenarios.json', 'r') as f:
            data = json.load(f)
            return jsonify({
                'success': True,
                'data': data
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Tomorrow scenarios not available: {str(e)}'
        }), 404

# SocketIO Events
@socketio.on('connect', namespace='/live')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect', namespace='/live')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    print("=" * 80)
    print("NIFTY REAL-TIME TRADING APPLICATION")
    print("=" * 80)
    print("\n🔧 Initializing application...")
    
    # Load best trades
    load_best_trades()
    
    print("\n🌐 Starting web server...")
    print("📊 Dashboard URL: http://localhost:5000")
    print("\n⚠️  Remember to update your session key in the dashboard!")
    print("=" * 80)
    
    # Start Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
