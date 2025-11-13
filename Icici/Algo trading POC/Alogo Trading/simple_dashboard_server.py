"""
Simple WebSocket Dashboard Server for Live Trading
Starts immediately without complex dependencies
"""

import json
import time
import random
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import pandas as pd
import numpy as np

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'trading-dashboard-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Simple live data simulation
live_data = {
    'current_price': 23500.0,
    'resistance_levels': [],
    'support_levels': [],
    'last_update': datetime.now().isoformat()
}

def load_levels():
    """Load resistance and support levels"""
    try:
        data_dir = Path("data")
        
        # Load resistance levels
        resistance_file = data_dir / "NIFTY_resistance_multi_timeframe.csv"
        if resistance_file.exists():
            resistance_df = pd.read_csv(resistance_file)
            live_data['resistance_levels'] = resistance_df.to_dict('records')
        
        # Load support levels  
        support_file = data_dir / "NIFTY_support_multi_timeframe.csv"
        if support_file.exists():
            support_df = pd.read_csv(support_file)
            live_data['support_levels'] = support_df.to_dict('records')
            
        print(f"✓ Loaded {len(live_data['resistance_levels'])} resistance levels")
        print(f"✓ Loaded {len(live_data['support_levels'])} support levels")
        
    except Exception as e:
        print(f"⚠️ Error loading levels: {e}")
        # Create sample data if files don't exist
        live_data['resistance_levels'] = [
            {'resistance_level': 23600, 'timeframe': '1d', 'resistance_strength': 'Strong'},
            {'resistance_level': 23550, 'timeframe': '1h', 'resistance_strength': 'Moderate'},
            {'resistance_level': 23520, 'timeframe': '15m', 'resistance_strength': 'Weak'}
        ]
        live_data['support_levels'] = [
            {'support_level': 23450, 'timeframe': '1d', 'support_strength': 'Strong'},
            {'support_level': 23480, 'timeframe': '1h', 'support_strength': 'Moderate'},
            {'support_level': 23490, 'timeframe': '15m', 'support_strength': 'Weak'}
        ]

def simulate_price_movement():
    """Simulate live price movement"""
    try:
        while True:
            # Generate realistic price movement
            change = random.uniform(-5, 5)
            live_data['current_price'] += change
            live_data['current_price'] = round(live_data['current_price'], 2)
            live_data['last_update'] = datetime.now().isoformat()
            
            # Emit to all connected clients
            socketio.emit('price_update', {
                'price': live_data['current_price'],
                'change': change,
                'timestamp': live_data['last_update']
            })
            
            # Check for level crosses
            check_level_crosses(change)
            
            time.sleep(2)  # Update every 2 seconds
            
    except Exception as e:
        print(f"Price simulation error: {e}")

def check_level_crosses(price_change):
    """Check if price crossed any levels"""
    try:
        current_price = live_data['current_price']
        
        # Check resistance breakouts (price moving up)
        if price_change > 0:
            for resistance in live_data['resistance_levels']:
                level = resistance['resistance_level']
                if current_price >= level and (current_price - price_change) < level:
                    alert = {
                        'type': 'RESISTANCE_BREAKOUT',
                        'level': level,
                        'current_price': current_price,
                        'timeframe': resistance['timeframe'],
                        'strength': resistance['resistance_strength'],
                        'direction': 'BULLISH',
                        'probability': round(random.uniform(60, 85), 1),
                        'expected_value': round(random.uniform(10, 30), 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    socketio.emit('trading_alert', alert)
                    print(f"🟢 BREAKOUT: {current_price} broke resistance at {level}")
        
        # Check support breakdowns (price moving down)
        elif price_change < 0:
            for support in live_data['support_levels']:
                level = support['support_level']
                if current_price <= level and (current_price - price_change) > level:
                    alert = {
                        'type': 'SUPPORT_BREAKDOWN',
                        'level': level,
                        'current_price': current_price,
                        'timeframe': support['timeframe'],
                        'strength': support['support_strength'],
                        'direction': 'BEARISH',
                        'probability': round(random.uniform(60, 85), 1),
                        'expected_value': round(random.uniform(-30, -10), 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    socketio.emit('trading_alert', alert)
                    print(f"🔴 BREAKDOWN: {current_price} broke support at {level}")
                    
    except Exception as e:
        print(f"Level check error: {e}")

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        'success': True,
        'session_active': True,
        'websocket_active': True,
        'current_price': live_data['current_price'],
        'last_update': live_data['last_update'],
        'resistance_count': len(live_data['resistance_levels']),
        'support_count': len(live_data['support_levels'])
    })

@app.route('/api/levels')
def get_levels():
    """Get current levels with distances"""
    try:
        current_price = live_data['current_price']
        
        # Calculate distances for resistance
        resistance_with_distance = []
        for r in live_data['resistance_levels']:
            level = r['resistance_level']
            distance = level - current_price
            resistance_with_distance.append({
                **r,
                'distance_pts': round(distance, 2),
                'distance_pct': round((distance / current_price) * 100, 2),
                'abs_distance': abs(distance)
            })
        
        # Calculate distances for support
        support_with_distance = []
        for s in live_data['support_levels']:
            level = s['support_level']
            distance = current_price - level
            support_with_distance.append({
                **s,
                'distance_pts': round(distance, 2),
                'distance_pct': round((distance / current_price) * 100, 2),
                'abs_distance': abs(distance)
            })
        
        # Sort by distance
        resistance_with_distance.sort(key=lambda x: x['abs_distance'])
        support_with_distance.sort(key=lambda x: x['abs_distance'])
        
        return jsonify({
            'success': True,
            'current_price': current_price,
            'resistance_levels': resistance_with_distance,
            'support_levels': support_with_distance,
            'timestamp': live_data['last_update']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/session', methods=['POST'])
def update_session():
    """Mock session update"""
    return jsonify({'success': True, 'message': 'Session connected (simulation mode)'})

@app.route('/api/order', methods=['POST'])
def place_order():
    """Mock order placement"""
    order_id = f"SIM_{int(time.time())}"
    return jsonify({'success': True, 'order_id': order_id, 'message': 'Paper trade order placed'})

@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    print('📱 Client connected to WebSocket')
    emit('status_update', {
        'connected': True,
        'current_price': live_data['current_price'],
        'message': 'WebSocket connected - Live simulation active'
    })

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    print('📱 Client disconnected from WebSocket')

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 NIFTY Live Trading Dashboard - WebSocket Server")
    print("=" * 80)
    print("📊 Features:")
    print("  • Real-time price simulation")
    print("  • WebSocket live updates")
    print("  • Resistance/Support level monitoring")
    print("  • Live breakout/breakdown alerts")
    print("  • Interactive dashboard interface")
    print("=" * 80)
    
    # Load initial data
    load_levels()
    
    print(f"🎯 Current NIFTY Price: ₹{live_data['current_price']:,.2f}")
    print(f"📈 Resistance Levels: {len(live_data['resistance_levels'])}")
    print(f"📉 Support Levels: {len(live_data['support_levels'])}")
    print("=" * 80)
    print("🌐 Starting server at http://localhost:5000")
    print("💡 Open the URL in your browser to view dashboard")
    print("=" * 80)
    
    # Start price simulation in background
    import threading
    threading.Thread(target=simulate_price_movement, daemon=True).start()
    
    # Start the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)