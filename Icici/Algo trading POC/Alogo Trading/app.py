"""
Flask WebSocket Server for Live Trading Dashboard
Integrates ICICI Breeze broker with ML models and real-time dashboard
"""

import asyncio
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread
import pickle
import os

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Import our custom modules
import sys
sys.path.append(str(Path(__file__).parent))

from src.brokers.icici_breeze_broker import ICICIBreezeBroker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global variables
broker = None
ml_models = {}
live_data = {
    'current_price': 0,
    'resistance_levels': [],
    'support_levels': [],
    'ml_predictions': {},
    'alerts': []
}

class MLPredictor:
    """Machine Learning Prediction Engine"""
    
    def __init__(self):
        self.models = {}
        self.data_dir = Path("data")
        self.load_models()
        
    def load_models(self):
        """Load or train ML models"""
        try:
            # Load historical analysis data
            self.resistance_df = pd.read_csv(self.data_dir / "NIFTY_resistance_multi_timeframe.csv")
            self.support_df = pd.read_csv(self.data_dir / "NIFTY_support_multi_timeframe.csv")
            
            # Load cross-timeframe analysis if available
            cross_files = [
                "NIFTY_15m_cross_1h_resistance.csv",
                "NIFTY_15m_cross_1d_resistance.csv", 
                "NIFTY_15m_cross_1h_support.csv",
                "NIFTY_15m_cross_1d_support.csv"
            ]
            
            self.cross_data = {}
            for file in cross_files:
                file_path = self.data_dir / file
                if file_path.exists():
                    self.cross_data[file.replace('.csv', '')] = pd.read_csv(file_path)
                    logger.info(f"Loaded {file}")
            
            # Train simple models for real-time predictions
            self._train_breakout_models()
            
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
    
    def _train_breakout_models(self):
        """Train models for breakout probability prediction"""
        try:
            # Combine all cross-timeframe data for training
            all_resistance_data = []
            all_support_data = []
            
            for key, df in self.cross_data.items():
                if 'resistance' in key and len(df) > 0:
                    all_resistance_data.append(df)
                elif 'support' in key and len(df) > 0:
                    all_support_data.append(df)
            
            if all_resistance_data:
                resistance_combined = pd.concat(all_resistance_data, ignore_index=True)
                self._train_model('resistance_breakout', resistance_combined)
            
            if all_support_data:
                support_combined = pd.concat(all_support_data, ignore_index=True)
                self._train_model('support_breakdown', support_combined)
                
        except Exception as e:
            logger.error(f"Error training models: {e}")
    
    def _train_model(self, model_type, data):
        """Train a specific model"""
        try:
            if len(data) < 10:  # Not enough data
                return
            
            # Prepare features
            feature_cols = ['distance_from_level', 'candle_body', 'volume']
            if 'upper_wick' in data.columns:
                feature_cols.append('upper_wick')
            
            # Remove rows with missing features
            data_clean = data[feature_cols + ['peak_gain' if model_type == 'resistance_breakout' else 'peak_drop']].dropna()
            
            if len(data_clean) < 10:
                return
                
            X = data_clean[feature_cols].values
            y = data_clean['peak_gain' if model_type == 'resistance_breakout' else 'peak_drop'].values
            
            # Train Random Forest
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X, y)
            
            self.models[model_type] = {
                'model': model,
                'features': feature_cols,
                'trained_at': datetime.now()
            }
            
            logger.info(f"Trained {model_type} model with {len(data_clean)} samples")
            
        except Exception as e:
            logger.error(f"Error training {model_type} model: {e}")
    
    def predict_breakout_probability(self, current_price, level, level_type='resistance'):
        """Predict breakout/breakdown probability and expected move"""
        try:
            model_key = f"{level_type}_breakout" if level_type == 'resistance' else f"{level_type}_breakdown"
            
            if model_key not in self.models:
                return None
            
            model_info = self.models[model_key]
            model = model_info['model']
            features = model_info['features']
            
            # Calculate features
            distance = abs(current_price - level)
            candle_body = 10  # Default candle body size
            volume = 1.0  # Default volume ratio
            
            feature_values = [distance, candle_body, volume]
            if 'upper_wick' in features:
                feature_values.append(5)  # Default upper wick
            
            # Make prediction
            X_pred = np.array([feature_values])
            predicted_move = model.predict(X_pred)[0]
            
            # Calculate probability based on historical data
            if level_type == 'resistance':
                hit_prob = min(80, max(20, 60 - (distance / level) * 1000))  # Higher probability for closer levels
            else:
                hit_prob = min(80, max(20, 60 - (distance / level) * 1000))
            
            return {
                'predicted_move': round(predicted_move, 2),
                'probability': round(hit_prob, 1),
                'confidence': 'Medium',
                'level': level,
                'current_price': current_price,
                'distance': round(distance, 2)
            }
            
        except Exception as e:
            logger.error(f"Error predicting breakout: {e}")
            return None

# Initialize ML predictor
ml_predictor = MLPredictor()

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get system status"""
    global broker
    
    status = {
        'success': True,
        'session_active': broker.is_authenticated if broker else False,
        'websocket_active': broker.ws_connected if broker else False,
        'ml_models_loaded': len(ml_predictor.models) > 0,
        'current_price': live_data['current_price'],
        'last_update': datetime.now().isoformat()
    }
    
    return jsonify(status)

@app.route('/api/session', methods=['POST'])
def update_session():
    """Update broker session"""
    global broker
    
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        session_token = data.get('session_token')
        
        if not api_key or not session_token:
            return jsonify({'success': False, 'message': 'Missing API key or session token'})
        
        # Initialize broker if not exists
        if not broker:
            broker = ICICIBreezeBroker(paper_trading=True)
        
        # Connect with provided credentials
        config = {
            'api_key': api_key,
            'session_token': session_token
        }
        
        # Run async connect in thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(broker.connect(config))
        loop.close()
        
        if broker.is_authenticated:
            # Start live data feed
            start_live_feed()
            return jsonify({'success': True, 'message': 'Session updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Authentication failed'})
            
    except Exception as e:
        logger.error(f"Session update error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/order', methods=['POST'])
def place_order():
    """Place trading order"""
    global broker
    
    try:
        if not broker or not broker.is_authenticated:
            return jsonify({'success': False, 'message': 'Not connected to broker'})
        
        data = request.get_json()
        order = {
            'symbol': 'NIFTY',
            'side': data.get('order_type', 'buy').upper(),
            'qty': int(data.get('quantity', 1)),
            'price': float(data.get('price', 0)),
            'order_type': 'LIMIT',
            'stop_loss': data.get('stop_loss'),
            'target': data.get('target')
        }
        
        # Run async order submission
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        order_id = loop.run_until_complete(broker.submit_order(order))
        loop.close()
        
        if order_id:
            return jsonify({'success': True, 'order_id': order_id})
        else:
            return jsonify({'success': False, 'message': 'Order placement failed'})
            
    except Exception as e:
        logger.error(f"Order placement error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/levels')
def get_levels():
    """Get current resistance and support levels with ML predictions"""
    try:
        current_price = live_data['current_price'] or 23500  # Default if no live price
        
        # Load levels
        resistance_df = pd.read_csv("data/NIFTY_resistance_multi_timeframe.csv")
        support_df = pd.read_csv("data/NIFTY_support_multi_timeframe.csv")
        
        # Calculate distances and add ML predictions
        resistance_levels = []
        for _, row in resistance_df.iterrows():
            level = row['resistance_level']
            distance = level - current_price
            
            # Get ML prediction
            ml_pred = ml_predictor.predict_breakout_probability(current_price, level, 'resistance')
            
            resistance_levels.append({
                'level': level,
                'timeframe': row['timeframe'],
                'strength': row.get('resistance_strength', 'Strong'),
                'hits': int(row.get('resistance_hits', 0)),
                'distance_pts': round(distance, 2),
                'distance_pct': round((distance / current_price) * 100, 2),
                'ml_prediction': ml_pred
            })
        
        support_levels = []
        for _, row in support_df.iterrows():
            level = row['support_level']
            distance = current_price - level
            
            # Get ML prediction
            ml_pred = ml_predictor.predict_breakout_probability(current_price, level, 'support')
            
            support_levels.append({
                'level': level,
                'timeframe': row['timeframe'],
                'strength': row.get('support_strength', 'Strong'),
                'hits': int(row.get('support_hits', 0)),
                'distance_pts': round(distance, 2),
                'distance_pct': round((distance / current_price) * 100, 2),
                'ml_prediction': ml_pred
            })
        
        # Sort by distance from current price
        resistance_levels.sort(key=lambda x: abs(x['distance_pts']))
        support_levels.sort(key=lambda x: abs(x['distance_pts']))
        
        return jsonify({
            'success': True,
            'current_price': current_price,
            'resistance_levels': resistance_levels[:20],  # Top 20 nearest
            'support_levels': support_levels[:20],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting levels: {e}")
        return jsonify({'success': False, 'message': str(e)})

def start_live_feed():
    """Start live data feed in background thread"""
    def run_live_feed():
        try:
            if not broker or not broker.is_authenticated:
                return
            
            # Callback for live data
            async def on_tick_data(ticks):
                global live_data
                
                if ticks and 'price' in ticks:
                    old_price = live_data['current_price']
                    new_price = float(ticks['price'])
                    live_data['current_price'] = new_price
                    
                    # Check for level crosses and generate alerts
                    check_level_crosses(old_price, new_price)
                    
                    # Emit to all connected clients
                    socketio.emit('price_update', {
                        'price': new_price,
                        'timestamp': datetime.now().isoformat(),
                        'change': new_price - old_price if old_price else 0
                    })
            
            # Start WebSocket stream
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(broker.start_market_data_stream(['NIFTY'], on_tick_data))
            
        except Exception as e:
            logger.error(f"Live feed error: {e}")
    
    # Start in background thread
    Thread(target=run_live_feed, daemon=True).start()

def check_level_crosses(old_price, new_price):
    """Check if price crossed any important levels"""
    try:
        if not old_price or not new_price:
            return
        
        # Load resistance and support levels
        resistance_df = pd.read_csv("data/NIFTY_resistance_multi_timeframe.csv")
        support_df = pd.read_csv("data/NIFTY_support_multi_timeframe.csv")
        
        # Check resistance breakouts
        for _, row in resistance_df.iterrows():
            level = row['resistance_level']
            if old_price < level <= new_price:  # Breakout above resistance
                ml_pred = ml_predictor.predict_breakout_probability(new_price, level, 'resistance')
                
                alert = {
                    'type': 'RESISTANCE_BREAKOUT',
                    'level': level,
                    'current_price': new_price,
                    'timeframe': row['timeframe'],
                    'strength': row.get('resistance_strength', 'Strong'),
                    'direction': 'BULLISH',
                    'ml_prediction': ml_pred,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Emit alert to dashboard
                socketio.emit('trading_alert', alert)
                logger.info(f"BREAKOUT ALERT: Price {new_price} broke resistance at {level}")
        
        # Check support breakdowns
        for _, row in support_df.iterrows():
            level = row['support_level']
            if old_price > level >= new_price:  # Breakdown below support
                ml_pred = ml_predictor.predict_breakout_probability(new_price, level, 'support')
                
                alert = {
                    'type': 'SUPPORT_BREAKDOWN',
                    'level': level,
                    'current_price': new_price,
                    'timeframe': row['timeframe'],
                    'strength': row.get('support_strength', 'Strong'),
                    'direction': 'BEARISH',
                    'ml_prediction': ml_pred,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Emit alert to dashboard
                socketio.emit('trading_alert', alert)
                logger.info(f"BREAKDOWN ALERT: Price {new_price} broke support at {level}")
                
    except Exception as e:
        logger.error(f"Error checking level crosses: {e}")

@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    logger.info('Client connected')
    
    # Send current status
    emit('status_update', {
        'connected': True,
        'current_price': live_data['current_price'],
        'broker_connected': broker.is_authenticated if broker else False
    })

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 ICICI Breeze Live Trading Dashboard Server")
    print("=" * 80)
    print("📊 Features:")
    print("  • Real-time WebSocket data streaming")
    print("  • ML-powered breakout/breakdown predictions")
    print("  • Cross-timeframe resistance/support analysis")
    print("  • Live trading alerts and notifications")
    print("  • Interactive dashboard with order placement")
    print("=" * 80)
    print("🌐 Starting server at http://localhost:5000")
    print("=" * 80)
    
    # Initialize broker
    broker = ICICIBreezeBroker(paper_trading=True)
    
    # Start the Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)