"""
Test Advanced ML Engine with Real Historical Data
"""

import pandas as pd
import numpy as np
from advanced_ml_engine import AdvancedMLEngine
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_nifty_data():
    """Load NIFTY historical data from CSV files"""
    try:
        # Load 5-minute data (most recent and detailed)
        df = pd.read_csv('data/NIFTY_5min_20221024_20251023.csv')
        logger.info(f"📊 Loaded {len(df)} rows of 5-minute NIFTY data")
        
        # Display basic info
        logger.info(f"📅 Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        logger.info(f"💰 Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
        
        return df
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")
        return None

def test_ml_engine_with_real_data():
    """Test the ML engine with real historical data"""
    logger.info("🚀 Testing Advanced ML Engine with Real Data")
    
    # Load data
    df = load_nifty_data()
    if df is None:
        return
    
    # Initialize ML engine
    engine = AdvancedMLEngine()
    
    # Take last 100 data points for testing
    test_data = df.tail(100).copy()
    logger.info(f"🔬 Testing with last {len(test_data)} data points")
    
    # Add data to ML engine progressively
    logger.info("📈 Adding historical data to ML engine...")
    
    successful_predictions = 0
    total_attempts = 0
    
    for i, row in test_data.iterrows():
        try:
            # Add price data
            engine.add_price_data(
                price=row['close'],
                volume=row.get('volume', 100000),  # Default volume if not available
                high=row['high'],
                low=row['low'],
                open_price=row['open']
            )
            
            # Try predictions after we have enough data (at least 20 points)
            if len(engine.price_history) >= 20:
                total_attempts += 1
                
                try:
                    current_price = row['close']
                    
                    # Test price direction prediction
                    direction = engine.predict_price_direction(current_price)
                    logger.info(f"📊 Direction: {direction}")
                    
                    # Test price targets
                    targets = engine.predict_price_targets(current_price)
                    logger.info(f"🎯 Targets: {targets}")
                    
                    # Test market sentiment
                    sentiment = engine.get_market_sentiment(current_price)
                    logger.info(f"🎭 Sentiment: {sentiment}")
                    
                    # Test trading signals
                    signals = engine.generate_trading_signals(current_price)
                    logger.info(f"📈 Signals: {signals}")
                    
                    successful_predictions += 1
                    logger.info(f"✅ Successful prediction #{successful_predictions}")
                    
                except Exception as e:
                    logger.error(f"❌ Prediction error: {e}")
                
                # Test every 10th point to avoid spam
                if total_attempts % 10 == 0:
                    logger.info(f"🔄 Progress: {total_attempts} attempts, {successful_predictions} successful")
                
        except Exception as e:
            logger.error(f"❌ Error adding data point: {e}")
    
    # Final summary
    success_rate = (successful_predictions / total_attempts * 100) if total_attempts > 0 else 0
    logger.info(f"📊 Final Results:")
    logger.info(f"   Total attempts: {total_attempts}")
    logger.info(f"   Successful predictions: {successful_predictions}")
    logger.info(f"   Success rate: {success_rate:.1f}%")
    
    if successful_predictions > 0:
        logger.info("✅ ML Engine working with real data!")
        
        # Show final ML state
        logger.info(f"📈 Final price history length: {len(engine.price_history)}")
        logger.info(f"💾 Cached predictions: {len(engine.predictions_cache)}")
        
    else:
        logger.error("❌ ML Engine failed with real data")

if __name__ == "__main__":
    test_ml_engine_with_real_data()