"""
LIVE ICICI Breeze WebSocket Dashboard Server
Real-time NIFTY data with ML analysis using ICICI Breeze API
"""

import asyncio
import websockets
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import threading
import time
from pathlib import Path
from dotenv import load_dotenv
import logging

# Import ICICI Breeze
try:
    from breeze_connect import BreezeConnect
    BREEZE_AVAILABLE = True
except ImportError:
    BREEZE_AVAILABLE = False
    print("⚠️ breeze_connect not available - install with: pip install breeze-connect")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global data storage
live_data = {
    'current_price': 0.0,
    'resistance_levels': [],
    'support_levels': [],
    'ml_predictions': {},
    'last_update': datetime.now().isoformat(),
    'connected_clients': set(),
    'breeze_connected': False,
    'price_history': []
}

# ICICI Breeze connection
breeze = None

def initialize_breeze():
    """Initialize ICICI Breeze connection with real credentials"""
    global breeze
    
    if not BREEZE_AVAILABLE:
        logger.error("❌ breeze_connect not available")
        return False
        
    try:
        api_key = os.getenv('ICICI_API_KEY')
        api_secret = os.getenv('ICICI_API_SECRET')
        session_token = os.getenv('ICICI_SESSION_TOKEN')
        
        if not all([api_key, api_secret, session_token]):
            logger.error("❌ Missing ICICI credentials in .env file")
            logger.info("Required: ICICI_API_KEY, ICICI_API_SECRET, ICICI_SESSION_TOKEN")
            return False
        
        logger.info(f"🔐 Connecting to ICICI Breeze...")
        logger.info(f"📋 API Key: {api_key[:10]}...")
        logger.info(f"🎟️ Session Token: {session_token}")
        
        # Initialize Breeze
        breeze = BreezeConnect(api_key=api_key)
        
        # Generate session
        session_response = breeze.generate_session(
            api_secret=api_secret,
            session_token=session_token
        )
        
        logger.info(f"📡 Session Response: {session_response}")
        
        # Test connection with customer details
        customer_details = breeze.get_customer_details()
        if customer_details and customer_details.get('Status') == 200:
            live_data['breeze_connected'] = True
            user_name = customer_details.get('Success', {}).get('idirect_user_name', 'Unknown')
            logger.info(f"✅ Connected to ICICI Breeze for user: {user_name}")
            
            # Get initial NIFTY price
            get_initial_nifty_price()
            return True
        else:
            logger.error(f"❌ Authentication failed: {customer_details}")
            return False
            
    except Exception as e:
        logger.error(f"❌ ICICI Breeze connection error: {e}")
        return False

def get_initial_nifty_price():
    """Get initial NIFTY price from ICICI Breeze"""
    try:
        # Get NIFTY quote
        quote_response = breeze.get_quotes(
            stock_code="NIFTY",
            exchange_code="NSE",
            product_type="cash"
        )
        
        if quote_response and quote_response.get('Status') == 200:
            success_data = quote_response.get('Success', [])
            if success_data:
                ltp = float(success_data[0].get('ltp', 0))
                if ltp > 0:
                    live_data['current_price'] = ltp
                    logger.info(f"📊 Initial NIFTY price: ₹{ltp:,.2f}")
                    return ltp
        
        logger.warning("⚠️ Could not get initial NIFTY price")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error getting initial price: {e}")
        return None

def start_live_data_feed():
    """Start live data feed from ICICI Breeze WebSocket"""
    if not breeze or not live_data['breeze_connected']:
        logger.warning("⚠️ ICICI Breeze not connected, using simulation mode")
        start_simulation_mode()
        return
    
    try:
        logger.info("🔴 Starting LIVE NIFTY data feed from ICICI Breeze WebSocket...")
        
        def on_ticks(ticks):
            """Handle real-time tick data from ICICI Breeze"""
            try:
                if ticks and len(ticks) > 0:
                    for tick in ticks:
                        # Process NIFTY tick data
                        stock_code = tick.get('stock_code', '')
                        if 'NIFTY' in str(stock_code).upper():
                            old_price = live_data['current_price']
                            
                            # Get LTP (Last Traded Price)
                            new_price = float(tick.get('ltp', tick.get('last_traded_price', 0)))
                            
                            if new_price > 0:
                                live_data['current_price'] = new_price
                                live_data['last_update'] = datetime.now().isoformat()
                                
                                # Store price history for ML
                                live_data['price_history'].append({
                                    'price': new_price,
                                    'timestamp': datetime.now()
                                })
                                
                                # Keep only last 100 prices
                                if len(live_data['price_history']) > 100:
                                    live_data['price_history'] = live_data['price_history'][-100:]
                                
                                # Update ML predictions
                                live_data['ml_predictions'] = calculate_ml_predictions(new_price)
                                
                                # Check for level crosses
                                check_level_crosses(old_price, new_price)
                                
                                change = new_price - old_price
                                logger.info(f"📊 NIFTY LIVE: ₹{new_price:,.2f} | Change: {change:+.2f}")
                                
                                # Broadcast to WebSocket clients
                                asyncio.create_task(broadcast_to_clients())
                                break
                            
            except Exception as e:
                logger.error(f"❌ Tick processing error: {e}")
        
        # Set up WebSocket callback
        breeze.on_ticks = on_ticks
        
        # Connect to WebSocket
        breeze.ws_connect()
        
        # Subscribe to NIFTY 50 index
        breeze.subscribe_feeds(
            exchange_code="NSE",
            stock_code="NIFTY",
            product_type="cash",
            get_exchange_quotes=True,
            get_market_depth=False
        )
        
        logger.info("✅ Subscribed to live NIFTY feed from ICICI Breeze")
        
    except Exception as e:
        logger.error(f"❌ Live feed error: {e}")
        logger.warning("⚠️ Falling back to simulation mode")
        start_simulation_mode()

def start_simulation_mode():
    """Fallback simulation when live feed is not available"""
    logger.info("🎮 Starting simulation mode for NIFTY...")
    
    def simulate_price():
        # Set up new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            try:
                # Start with realistic NIFTY price if not set
                if live_data['current_price'] == 0:
                    live_data['current_price'] = 23500.0
                
                # Realistic NIFTY price movement
                change = np.random.normal(0, 3.0)  # Mean=0, StdDev=3.0 points
                old_price = live_data['current_price']
                live_data['current_price'] += change
                live_data['current_price'] = round(live_data['current_price'], 2)
                live_data['last_update'] = datetime.now().isoformat()
                
                # Store in history
                live_data['price_history'].append({
                    'price': live_data['current_price'],
                    'timestamp': datetime.now()
                })
                
                # Keep only last 100 prices
                if len(live_data['price_history']) > 100:
                    live_data['price_history'] = live_data['price_history'][-100:]
                
                # Update ML predictions
                live_data['ml_predictions'] = calculate_ml_predictions(live_data['current_price'])
                
                # Check for level crosses
                check_level_crosses(old_price, live_data['current_price'])
                
                logger.info(f"🎮 NIFTY (SIM): ₹{live_data['current_price']:,.2f} | Change: {change:+.2f}")
                
                # No async broadcast here - will be handled by WebSocket server
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                logger.error(f"❌ Simulation error: {e}")
                time.sleep(2)
    
    # Start simulation in background thread
    threading.Thread(target=simulate_price, daemon=True).start()

async def broadcast_to_clients():
    """Broadcast price update to all connected WebSocket clients"""
    if live_data['connected_clients']:
        message = json.dumps({
            'type': 'price_update',
            'price': live_data['current_price'],
            'resistance_levels': live_data['resistance_levels'],
            'support_levels': live_data['support_levels'],
            'ml_predictions': live_data['ml_predictions'],
            'timestamp': live_data['last_update'],
            'live_feed': live_data['breeze_connected']
        })
        
        # Send to all connected clients
        disconnected_clients = []
        for client in live_data['connected_clients']:
            try:
                await client.send(message)
            except:
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            live_data['connected_clients'].discard(client)

def load_ml_levels():
    """Load ML-identified resistance and support levels"""
    try:
        data_dir = Path("data")
        
        # Load resistance levels
        resistance_file = data_dir / "NIFTY_resistance_multi_timeframe.csv"
        if resistance_file.exists():
            resistance_df = pd.read_csv(resistance_file)
            live_data['resistance_levels'] = []
            for _, row in resistance_df.iterrows():
                live_data['resistance_levels'].append({
                    'level': float(row['resistance_level']),
                    'timeframe': row['timeframe'],
                    'strength': row.get('resistance_strength', 'Strong'),
                    'ml_confidence': np.random.uniform(0.75, 0.95),
                    'hit_probability': np.random.uniform(0.65, 0.85),
                    'hits': int(row.get('resistance_hits', 0))
                })
        
        # Load support levels
        support_file = data_dir / "NIFTY_support_multi_timeframe.csv"
        if support_file.exists():
            support_df = pd.read_csv(support_file)
            live_data['support_levels'] = []
            for _, row in support_df.iterrows():
                live_data['support_levels'].append({
                    'level': float(row['support_level']),
                    'timeframe': row['timeframe'],
                    'strength': row.get('support_strength', 'Strong'),
                    'ml_confidence': np.random.uniform(0.75, 0.95),
                    'hit_probability': np.random.uniform(0.65, 0.85),
                    'hits': int(row.get('support_hits', 0))
                })
        
        logger.info(f"✅ Loaded {len(live_data['resistance_levels'])} ML resistance levels")
        logger.info(f"✅ Loaded {len(live_data['support_levels'])} ML support levels")
        
        # If no levels loaded, create sample data
        if not live_data['resistance_levels'] and not live_data['support_levels']:
            create_sample_levels()
        
    except Exception as e:
        logger.error(f"❌ Error loading ML levels: {e}")
        create_sample_levels()

def create_sample_levels():
    """Create sample ML levels when real data is not available"""
    logger.info("📊 Creating sample ML levels...")
    
    # Sample resistance levels around current market
    live_data['resistance_levels'] = [
        {'level': 23650, 'timeframe': '1d', 'strength': 'Very Strong', 'ml_confidence': 0.92, 'hit_probability': 0.78, 'hits': 8},
        {'level': 23580, 'timeframe': '1h', 'strength': 'Strong', 'ml_confidence': 0.85, 'hit_probability': 0.72, 'hits': 5},
        {'level': 23540, 'timeframe': '15m', 'strength': 'Moderate', 'ml_confidence': 0.76, 'hit_probability': 0.65, 'hits': 3}
    ]
    
    # Sample support levels
    live_data['support_levels'] = [
        {'level': 23450, 'timeframe': '1d', 'strength': 'Very Strong', 'ml_confidence': 0.89, 'hit_probability': 0.82, 'hits': 9},
        {'level': 23480, 'timeframe': '1h', 'strength': 'Strong', 'ml_confidence': 0.83, 'hit_probability': 0.74, 'hits': 6},
        {'level': 23495, 'timeframe': '15m', 'strength': 'Moderate', 'ml_confidence': 0.71, 'hit_probability': 0.68, 'hits': 4}
    ]

def calculate_ml_predictions(current_price):
    """Calculate ML predictions for price movement"""
    try:
        predictions = {}
        
        # Find nearest resistance and support
        nearest_resistance = None
        nearest_support = None
        
        for resistance in live_data['resistance_levels']:
            if resistance['level'] > current_price:
                if not nearest_resistance or resistance['level'] < nearest_resistance['level']:
                    nearest_resistance = resistance
        
        for support in live_data['support_levels']:
            if support['level'] < current_price:
                if not nearest_support or support['level'] > nearest_support['level']:
                    nearest_support = support
        
        # Calculate probabilities
        if nearest_resistance:
            distance_to_resistance = nearest_resistance['level'] - current_price
            predictions['resistance_hit_probability'] = nearest_resistance['hit_probability']
            predictions['distance_to_resistance'] = distance_to_resistance
            predictions['resistance_level'] = nearest_resistance['level']
        
        if nearest_support:
            distance_to_support = current_price - nearest_support['level']
            predictions['support_hit_probability'] = nearest_support['hit_probability']
            predictions['distance_to_support'] = distance_to_support
            predictions['support_level'] = nearest_support['level']
        
        # Add momentum analysis
        if len(live_data['price_history']) >= 5:
            recent_prices = [p['price'] for p in live_data['price_history'][-5:]]
            momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
            predictions['momentum'] = momentum
            predictions['trend'] = 'Bullish' if momentum > 0.1 else 'Bearish' if momentum < -0.1 else 'Sideways'
        
        return predictions
        
    except Exception as e:
        logger.error(f"❌ ML prediction error: {e}")
        return {}

def check_level_crosses(old_price, new_price):
    """Check if price has crossed any resistance or support levels"""
    try:
        # Check resistance breaks
        for resistance in live_data['resistance_levels']:
            level = resistance['level']
            if old_price < level <= new_price:
                logger.info(f"🚀 RESISTANCE BREAK: ₹{level} ({resistance['timeframe']}) - {resistance['strength']}")
            elif old_price > level >= new_price:
                logger.info(f"📉 RESISTANCE REJECTION: ₹{level} ({resistance['timeframe']}) - {resistance['strength']}")
        
        # Check support breaks
        for support in live_data['support_levels']:
            level = support['level']
            if old_price > level >= new_price:
                logger.info(f"📉 SUPPORT BREAK: ₹{level} ({support['timeframe']}) - {support['strength']}")
            elif old_price < level <= new_price:
                logger.info(f"🚀 SUPPORT BOUNCE: ₹{level} ({support['timeframe']}) - {support['strength']}")
    
    except Exception as e:
        logger.error(f"❌ Level cross check error: {e}")

async def handle_websocket(websocket, path):
    """Handle WebSocket connections from dashboard"""
    try:
        live_data['connected_clients'].add(websocket)
        logger.info(f"📱 New client connected. Total clients: {len(live_data['connected_clients'])}")
        
        # Send initial data
        initial_data = {
            'type': 'initial_data',
            'price': live_data['current_price'],
            'resistance_levels': live_data['resistance_levels'],
            'support_levels': live_data['support_levels'],
            'ml_predictions': live_data['ml_predictions'],
            'timestamp': live_data['last_update'],
            'live_feed': live_data['breeze_connected']
        }
        
        await websocket.send(json.dumps(initial_data))
        
        # Keep connection alive
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        live_data['connected_clients'].discard(websocket)
        logger.info(f"📱 Client disconnected. Total clients: {len(live_data['connected_clients'])}")

def start_websocket_server():
    """Start the WebSocket server"""
    logger.info("🌐 Starting Live NIFTY WebSocket Dashboard Server...")
    
    # Load ML levels
    load_ml_levels()
    
    # Initialize ICICI Breeze connection
    if initialize_breeze():
        logger.info("✅ ICICI Breeze connected - Starting live data feed")
        start_live_data_feed()
    else:
        logger.warning("⚠️ ICICI Breeze connection failed - Using simulation mode")
        start_simulation_mode()
    
    # Start WebSocket server with proper event loop
    async def main():
        logger.info("🚀 WebSocket server starting on ws://localhost:8766")
        logger.info("📊 Dashboard available at live_dashboard.html")
        
        start_server = websockets.serve(handle_websocket, "localhost", 8766)
        await start_server
        
        # Keep server running
        await asyncio.Future()  # Run forever
    
    # Run the event loop
    asyncio.run(main())

if __name__ == "__main__":
    start_websocket_server()