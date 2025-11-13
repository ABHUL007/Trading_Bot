"""
Enhanced ICICI Breeze WebSocket Server with Advanced ML Integration
Combines existing functionality with sophisticated ML algorithms and risk management
"""

import asyncio
import websockets
import json
import pandas as pd
import numpy as np
from datetime import datetime
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
    print("❌ breeze_connect not available - install with: pip install breeze-connect")

# Import our advanced ML engines
try:
    from advanced_ml_engine import AdvancedMLEngine, get_ml_engine
    from risk_management_engine import RiskManagementEngine, get_risk_engine
    ML_ENGINES_AVAILABLE = True
except ImportError:
    ML_ENGINES_AVAILABLE = False
    print("⚠️ Advanced ML engines not available - using basic predictions")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global data storage with enhanced ML capabilities
live_data = {
    'current_price': 0.0,
    'resistance_levels': [],
    'support_levels': [],
    'ml_predictions': {},
    'advanced_ml_predictions': {},
    'risk_metrics': {},
    'trading_signals': {},
    'market_sentiment': {},
    'portfolio_metrics': {},
    'last_update': datetime.now().isoformat(),
    'connected_clients': set(),
    'breeze_connected': False,
    'price_history': [],
    'tick_count': 0,
    'ml_engine_status': 'initializing',
    'risk_engine_status': 'initializing'
}

# Initialize ML engines
ml_engine = None
risk_engine = None

if ML_ENGINES_AVAILABLE:
    try:
        ml_engine = get_ml_engine()
        risk_engine = get_risk_engine()
        live_data['ml_engine_status'] = 'active'
        live_data['risk_engine_status'] = 'active'
        logger.info("✅ Advanced ML engines initialized")
    except Exception as e:
        logger.error(f"❌ ML engine initialization error: {e}")
        live_data['ml_engine_status'] = 'error'
        live_data['risk_engine_status'] = 'error'

# ICICI Breeze connection
breeze = None
ws_thread = None

def initialize_breeze():
    """Initialize ICICI Breeze connection with proper session handling"""
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
            return False
        
        logger.info(f"🔐 Initializing ICICI Breeze...")
        logger.info(f"📋 API Key: {api_key[:10]}...")
        logger.info(f"🎟️ Session Token: {session_token}")
        
        # Initialize Breeze
        breeze = BreezeConnect(api_key=api_key)
        
        # Generate session
        logger.info("📡 Generating session...")
        session_response = breeze.generate_session(
            api_secret=api_secret,
            session_token=session_token
        )
        
        logger.info(f"📡 Session Response: {session_response}")
        
        if session_response and session_response.get('Status') == 200:
            logger.info("✅ Session generated successfully")
            
            # Test connection
            customer_details = breeze.get_customer_details()
            if customer_details and customer_details.get('Status') == 200:
                live_data['breeze_connected'] = True
                success_data = customer_details.get('Success', {})
                user_name = success_data.get('idirect_user_name', 'Unknown')
                client_code = success_data.get('client_code', 'Unknown')
                logger.info(f"✅ Connected to ICICI Breeze")
                logger.info(f"👤 User: {user_name}")
                logger.info(f"🆔 Client Code: {client_code}")
                
                # Get initial NIFTY price
                get_initial_nifty_price()
                return True
            else:
                logger.error(f"❌ Customer details failed: {customer_details}")
                return False
        else:
            logger.error(f"❌ Session generation failed: {session_response}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Breeze initialization error: {e}")
        return False

def get_initial_nifty_price():
    """Get initial NIFTY price from ICICI Breeze"""
    global breeze
    
    if not breeze or not live_data['breeze_connected']:
        return False
    
    try:
        # Get NIFTY quote
        quote = breeze.get_quotes(
            stock_code="NIFTY",
            exchange_code="NSE",
            product_type="cash"
        )
        
        if quote and quote.get('Status') == 200:
            quote_data = quote.get('Success', [])
            if quote_data:
                ltp = float(quote_data[0].get('ltp', 0))
                if ltp > 0:
                    live_data['current_price'] = ltp
                    logger.info(f"💰 Initial NIFTY price: ₹{ltp:,.2f}")
                    
                    # Add to ML engines
                    if ml_engine:
                        ml_engine.add_price_data(
                            price=ltp,
                            volume=quote_data[0].get('volume', 0),
                            high=quote_data[0].get('high', ltp),
                            low=quote_data[0].get('low', ltp),
                            open_price=quote_data[0].get('open', ltp)
                        )
                    
                    if risk_engine:
                        risk_engine.add_price_data(
                            price=ltp,
                            volume=quote_data[0].get('volume', 0)
                        )
                    
                    return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error getting initial NIFTY price: {e}")
        return False

def start_live_websocket_feed():
    """Start live WebSocket feed from ICICI Breeze"""
    global breeze, ws_thread
    
    if not breeze or not live_data['breeze_connected']:
        logger.warning("⚠️ Breeze not connected - cannot start live feed")
        return False
    
    try:
        def on_ticks(ticks):
            """Handle real-time tick data from ICICI Breeze WebSocket"""
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
                                live_data['tick_count'] += 1
                                
                                # Enhanced price data storage
                                price_data = {
                                    'price': new_price,
                                    'timestamp': datetime.now(),
                                    'volume': tick.get('volume', 0),
                                    'open': tick.get('open', new_price),
                                    'high': tick.get('high', new_price),
                                    'low': tick.get('low', new_price),
                                    'change': tick.get('change', 0),
                                    'change_percent': tick.get('change_percent', 0)
                                }
                                live_data['price_history'].append(price_data)
                                
                                # Keep only last 200 prices for efficiency
                                if len(live_data['price_history']) > 200:
                                    live_data['price_history'] = live_data['price_history'][-200:]
                                
                                # Update ML engines with enhanced data
                                if ml_engine:
                                    ml_engine.add_price_data(
                                        price=new_price,
                                        timestamp=datetime.now(),
                                        volume=tick.get('volume', 0),
                                        high=tick.get('high', new_price),
                                        low=tick.get('low', new_price),
                                        open_price=tick.get('open', new_price)
                                    )
                                    
                                    # Generate advanced ML predictions
                                    live_data['advanced_ml_predictions'] = ml_engine.predict_price_direction(
                                        new_price, live_data['resistance_levels'], live_data['support_levels']
                                    )
                                    
                                    # Generate trading signals
                                    live_data['trading_signals'] = ml_engine.generate_trading_signals(
                                        new_price, live_data['resistance_levels'], live_data['support_levels']
                                    )
                                    
                                    # Market sentiment analysis
                                    live_data['market_sentiment'] = ml_engine.get_market_sentiment()
                                
                                if risk_engine:
                                    risk_engine.add_price_data(
                                        price=new_price,
                                        volume=tick.get('volume', 0)
                                    )
                                    
                                    # Calculate risk metrics
                                    live_data['risk_metrics'] = {
                                        'var': risk_engine.calculate_var(),
                                        'sharpe_ratio': risk_engine.calculate_sharpe_ratio(),
                                        'max_drawdown': risk_engine.calculate_maximum_drawdown()
                                    }
                                
                                # Update basic ML predictions (existing functionality)
                                live_data['ml_predictions'] = calculate_basic_ml_predictions(new_price)
                                
                                # Check for level crosses
                                check_level_crosses(old_price, new_price)
                                
                                change = new_price - old_price
                                logger.info(f"📊 NIFTY LIVE: ₹{new_price:,.2f} | Change: {change:+.2f} | Ticks: {live_data['tick_count']}")
                                
                                # Broadcast enhanced data to WebSocket clients
                                asyncio.create_task(broadcast_enhanced_data())
                                break
                            
            except Exception as e:
                logger.error(f"❌ Tick processing error: {e}")
        
        # Subscribe to NIFTY WebSocket feed
        breeze.ws_connect()
        breeze.on_ticks = on_ticks
        
        # Subscribe to NIFTY
        breeze.subscribe_feeds(
            exchange_code="NSE",
            stock_code="NIFTY",
            product_type="cash",
            expiry_date="",
            strike_price="",
            right=""
        )
        
        logger.info("🔌 Subscribed to NIFTY WebSocket feed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebSocket feed error: {e}")
        return False

def start_enhanced_simulation_mode():
    """Enhanced simulation mode with advanced ML features"""
    logger.info("🎮 Starting enhanced simulation mode for NIFTY...")
    
    # Load ML levels
    load_ml_levels()
    
    # Set initial price
    live_data['current_price'] = 25763.0
    
    # Initialize ML engines with historical data
    if ml_engine:
        # Simulate historical data for better predictions
        base_price = live_data['current_price']
        for i in range(50):
            price = base_price + np.random.normal(0, 15)
            volume = 100000 + np.random.normal(0, 20000)
            ml_engine.add_price_data(
                price=price,
                volume=max(volume, 0),
                high=price + np.random.uniform(0, 10),
                low=price - np.random.uniform(0, 10),
                open_price=price + np.random.normal(0, 5)
            )
    
    if risk_engine:
        # Initialize risk engine with data
        base_price = live_data['current_price']
        for i in range(100):
            price = base_price + np.random.normal(0, 20)
            volume = 100000 + np.random.normal(0, 30000)
            risk_engine.add_price_data(price=price, volume=max(volume, 0))
        
        # Add sample position for portfolio tracking
        risk_engine.add_position('NIFTY', 100, base_price, stop_loss=base_price*0.98, take_profit=base_price*1.03)
    
    def simulate_enhanced_price():
        """Enhanced price simulation with ML features"""
        while True:
            try:
                old_price = live_data['current_price']
                
                # Enhanced price movement simulation
                current_hour = datetime.now().hour
                
                # Market hours have different volatility
                if 9 <= current_hour <= 15:
                    volatility = 0.3  # Lower volatility during market hours
                    base_change = np.random.normal(0, 8)
                    update_interval = 1  # Faster updates during market hours
                else:
                    volatility = 0.1  # Very low volatility after hours
                    base_change = np.random.normal(0, 3)
                    update_interval = 3  # Slower updates after hours
                
                # Add trend and momentum
                if len(live_data['price_history']) >= 5:
                    recent_prices = [p['price'] for p in live_data['price_history'][-5:]]
                    momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                    trend_influence = momentum * 20  # Amplify momentum
                    base_change += trend_influence
                
                # Level-based price action
                nearest_resistance = None
                nearest_support = None
                
                for resistance in live_data['resistance_levels']:
                    if resistance['level'] > live_data['current_price']:
                        if not nearest_resistance or resistance['level'] < nearest_resistance['level']:
                            nearest_resistance = resistance
                
                for support in live_data['support_levels']:
                    if support['level'] < live_data['current_price']:
                        if not nearest_support or support['level'] > nearest_support['level']:
                            nearest_support = support
                
                # Resistance/support influence
                if nearest_resistance:
                    distance_to_resistance = nearest_resistance['level'] - live_data['current_price']
                    if distance_to_resistance < 20:  # Close to resistance
                        resistance_effect = -5 * (20 - distance_to_resistance) / 20
                        base_change += resistance_effect
                
                if nearest_support:
                    distance_to_support = live_data['current_price'] - nearest_support['level']
                    if distance_to_support < 20:  # Close to support
                        support_effect = 5 * (20 - distance_to_support) / 20
                        base_change += support_effect
                
                # Apply change
                new_price = live_data['current_price'] + base_change
                new_price = max(new_price, 20000)  # Floor price
                new_price = min(new_price, 30000)  # Ceiling price
                
                live_data['current_price'] = new_price
                live_data['last_update'] = datetime.now().isoformat()
                live_data['tick_count'] += 1
                
                # Enhanced price history
                volume = max(100000 + np.random.normal(0, 50000), 10000)
                high_price = new_price + np.random.uniform(0, abs(base_change) * 0.5)
                low_price = new_price - np.random.uniform(0, abs(base_change) * 0.5)
                open_price = old_price + np.random.normal(0, abs(base_change) * 0.3)
                
                price_data = {
                    'price': new_price,
                    'timestamp': datetime.now(),
                    'volume': volume,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'change': new_price - old_price,
                    'change_percent': (new_price - old_price) / old_price * 100
                }
                live_data['price_history'].append(price_data)
                
                # Keep only last 200 prices
                if len(live_data['price_history']) > 200:
                    live_data['price_history'] = live_data['price_history'][-200:]
                
                # Update ML engines
                if ml_engine:
                    ml_engine.add_price_data(
                        price=new_price,
                        volume=volume,
                        high=high_price,
                        low=low_price,
                        open_price=open_price
                    )
                    
                    # Generate advanced predictions
                    live_data['advanced_ml_predictions'] = ml_engine.predict_price_direction(
                        new_price, live_data['resistance_levels'], live_data['support_levels']
                    )
                    
                    # Generate trading signals
                    live_data['trading_signals'] = ml_engine.generate_trading_signals(
                        new_price, live_data['resistance_levels'], live_data['support_levels']
                    )
                    
                    # Market sentiment
                    live_data['market_sentiment'] = ml_engine.get_market_sentiment()
                
                if risk_engine:
                    risk_engine.add_price_data(price=new_price, volume=volume)
                    
                    # Risk metrics
                    live_data['risk_metrics'] = {
                        'var': risk_engine.calculate_var(),
                        'sharpe_ratio': risk_engine.calculate_sharpe_ratio(),
                        'max_drawdown': risk_engine.calculate_maximum_drawdown()
                    }
                    
                    # Portfolio metrics
                    live_data['portfolio_metrics'] = risk_engine.calculate_portfolio_metrics(new_price)
                
                # Basic ML predictions (compatibility)
                live_data['ml_predictions'] = calculate_basic_ml_predictions(new_price)
                
                # Check for level crosses
                check_level_crosses(old_price, new_price)
                
                change = new_price - old_price
                market_status = "MARKET HOURS" if 9 <= current_hour <= 15 else "AFTER HOURS"
                logger.info(f"🎮 NIFTY (SIM) {market_status}: ₹{new_price:,.2f} | Change: {change:+.2f} | ML: {live_data['trading_signals'].get('signal_class', 'N/A')}")
                
                time.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"❌ Enhanced simulation error: {e}")
                time.sleep(2)
    
    # Start simulation in a separate thread
    sim_thread = threading.Thread(target=simulate_enhanced_price, daemon=True)
    sim_thread.start()
    
    logger.info("✅ Enhanced simulation mode started")

def calculate_basic_ml_predictions(current_price):
    """Calculate basic ML predictions (existing functionality)"""
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
        if len(live_data['price_history']) >= 10:
            recent_prices = [p['price'] for p in live_data['price_history'][-10:]]
            momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
            predictions['momentum'] = momentum
            
            # Trend analysis
            if momentum > 0.2:
                predictions['trend'] = 'Strong Bullish'
            elif momentum > 0.05:
                predictions['trend'] = 'Bullish'
            elif momentum < -0.2:
                predictions['trend'] = 'Strong Bearish'
            elif momentum < -0.05:
                predictions['trend'] = 'Bearish'
            else:
                predictions['trend'] = 'Sideways'
                
            # Volume analysis if available
            if live_data['price_history']:
                recent_volumes = [p.get('volume', 0) for p in live_data['price_history'][-5:]]
                avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
                predictions['avg_volume'] = avg_volume
        
        return predictions
        
    except Exception as e:
        logger.error(f"❌ Basic ML prediction error: {e}")
        return {}

def check_level_crosses(old_price, new_price):
    """Check if price has crossed any resistance or support levels"""
    try:
        # Check resistance breaks
        for resistance in live_data['resistance_levels']:
            level = resistance['level']
            if old_price < level <= new_price:
                logger.info(f"🚀 RESISTANCE BREAK: ₹{level:,.2f} ({resistance['timeframe']}) - {resistance['strength']}")
            elif old_price > level >= new_price:
                logger.info(f"📉 RESISTANCE REJECTION: ₹{level:,.2f} ({resistance['timeframe']}) - {resistance['strength']}")
        
        # Check support breaks
        for support in live_data['support_levels']:
            level = support['level']
            if old_price > level >= new_price:
                logger.info(f"📉 SUPPORT BREAK: ₹{level:,.2f} ({support['timeframe']}) - {support['strength']}")
            elif old_price < level <= new_price:
                logger.info(f"🚀 SUPPORT BOUNCE: ₹{level:,.2f} ({support['timeframe']}) - {support['strength']}")
    
    except Exception as e:
        logger.error(f"❌ Level cross check error: {e}")

def load_ml_levels():
    """Load ML-identified resistance and support levels"""
    logger.info("📊 Loading ML resistance and support levels...")
    
    # Current NIFTY levels based on 25,763
    live_data['resistance_levels'] = [
        {'level': 25850, 'timeframe': '1d', 'strength': 'Very Strong', 'ml_confidence': 0.92, 'hit_probability': 0.78, 'hits': 8},
        {'level': 25800, 'timeframe': '1h', 'strength': 'Strong', 'ml_confidence': 0.85, 'hit_probability': 0.72, 'hits': 5},
        {'level': 25780, 'timeframe': '15m', 'strength': 'Moderate', 'ml_confidence': 0.76, 'hit_probability': 0.65, 'hits': 3}
    ]
    
    live_data['support_levels'] = [
        {'level': 25650, 'timeframe': '1d', 'strength': 'Very Strong', 'ml_confidence': 0.89, 'hit_probability': 0.82, 'hits': 9},
        {'level': 25700, 'timeframe': '1h', 'strength': 'Strong', 'ml_confidence': 0.83, 'hit_probability': 0.74, 'hits': 6},
        {'level': 25740, 'timeframe': '15m', 'strength': 'Moderate', 'ml_confidence': 0.71, 'hit_probability': 0.68, 'hits': 4}
    ]
    
    logger.info(f"✅ Loaded {len(live_data['resistance_levels'])} resistance levels")
    logger.info(f"✅ Loaded {len(live_data['support_levels'])} support levels")

async def handle_websocket(websocket, path):
    """Handle WebSocket connections from dashboard with enhanced data"""
    logger.info(f"🔗 New WebSocket connection from {websocket.remote_address}")
    live_data['connected_clients'].add(websocket)
    
    try:
        # Send initial enhanced data
        initial_data = {
            'type': 'initial_data',
            'current_price': live_data['current_price'],
            'resistance_levels': live_data['resistance_levels'],
            'support_levels': live_data['support_levels'],
            'ml_predictions': live_data['ml_predictions'],
            'advanced_ml_predictions': live_data['advanced_ml_predictions'],
            'trading_signals': live_data['trading_signals'],
            'market_sentiment': live_data['market_sentiment'],
            'risk_metrics': live_data['risk_metrics'],
            'portfolio_metrics': live_data['portfolio_metrics'],
            'last_update': live_data['last_update'],
            'breeze_connected': live_data['breeze_connected'],
            'tick_count': live_data['tick_count'],
            'ml_engine_status': live_data['ml_engine_status'],
            'risk_engine_status': live_data['risk_engine_status']
        }
        
        await websocket.send(json.dumps(initial_data))
        
        # Keep connection alive
        async for message in websocket:
            # Handle incoming messages (commands, requests)
            try:
                data = json.loads(message)
                command = data.get('command')
                
                if command == 'get_risk_alerts':
                    if risk_engine:
                        account_balance = data.get('account_balance', 1000000)
                        alerts = risk_engine.generate_risk_alerts(live_data['current_price'], account_balance)
                        await websocket.send(json.dumps({
                            'type': 'risk_alerts',
                            'data': alerts
                        }))
                
                elif command == 'optimize_position':
                    if risk_engine:
                        account_balance = data.get('account_balance', 1000000)
                        risk_tolerance = data.get('risk_tolerance', 2)
                        optimization = risk_engine.optimize_position_size(
                            account_balance, risk_tolerance
                        )
                        await websocket.send(json.dumps({
                            'type': 'position_optimization',
                            'data': optimization
                        }))
                
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Invalid JSON from {websocket.remote_address}")
            except Exception as e:
                logger.error(f"❌ Message handling error: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"🔌 WebSocket connection closed: {websocket.remote_address}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        live_data['connected_clients'].discard(websocket)

async def broadcast_enhanced_data():
    """Broadcast enhanced price update to all connected WebSocket clients"""
    if not live_data['connected_clients']:
        return
    
    # Prepare enhanced data payload
    data = {
        'type': 'price_update',
        'current_price': live_data['current_price'],
        'ml_predictions': live_data['ml_predictions'],
        'advanced_ml_predictions': live_data['advanced_ml_predictions'],
        'trading_signals': live_data['trading_signals'],
        'market_sentiment': live_data['market_sentiment'],
        'risk_metrics': live_data['risk_metrics'],
        'portfolio_metrics': live_data['portfolio_metrics'],
        'resistance_levels': live_data['resistance_levels'],
        'support_levels': live_data['support_levels'],
        'timestamp': live_data['last_update'],
        'tick_count': live_data['tick_count']
    }
    
    message = json.dumps(data)
    
    # Send to all connected clients
    disconnected_clients = set()
    for websocket in live_data['connected_clients']:
        try:
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            disconnected_clients.add(websocket)
        except Exception as e:
            logger.error(f"❌ Broadcast error: {e}")
            disconnected_clients.add(websocket)
    
    # Remove disconnected clients
    live_data['connected_clients'] -= disconnected_clients

def start_websocket_server():
    """Start the enhanced WebSocket server"""
    async def main():
        logger.info("🚀 Starting enhanced WebSocket server on ws://localhost:8766")
        
        async with websockets.serve(handle_websocket, "localhost", 8766):
            logger.info("📊 Enhanced dashboard available at live_dashboard.html")
            await asyncio.Future()  # Run forever
    
    asyncio.run(main())

if __name__ == "__main__":
    try:
        logger.info("🌐 Starting Enhanced ICICI Breeze WebSocket Dashboard Server...")
        
        # Load ML levels first
        load_ml_levels()
        
        # Try to initialize ICICI Breeze
        if initialize_breeze():
            logger.info("✅ ICICI Breeze initialized - attempting live feed")
            if start_live_websocket_feed():
                logger.info("📡 Live WebSocket feed started")
            else:
                logger.warning("⚠️ Live feed failed - falling back to enhanced simulation")
                start_enhanced_simulation_mode()
        else:
            logger.warning("⚠️ ICICI Breeze connection failed - using enhanced simulation mode")
            start_enhanced_simulation_mode()
        
        # Start WebSocket server
        start_websocket_server()
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        raise