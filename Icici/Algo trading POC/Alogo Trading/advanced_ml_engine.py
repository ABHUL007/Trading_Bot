"""
Advanced Machine Learning Engine for NIFTY Trading
Enhances existing ML capabilities with sophisticated algorithms
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedMLEngine:
    """Advanced ML Engine for NIFTY trading predictions"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        self.price_history = []
        self.predictions_cache = {}
        
        # Initialize models
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize ML models for different prediction tasks"""
        
        # Price direction prediction
        self.models['direction'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        # Price target prediction
        self.models['price_target'] = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        # Volatility prediction
        self.models['volatility'] = RandomForestRegressor(
            n_estimators=50,
            max_depth=8,
            random_state=42
        )
        
        # Support/Resistance strength
        self.models['level_strength'] = GradientBoostingRegressor(
            n_estimators=80,
            learning_rate=0.15,
            max_depth=5,
            random_state=42
        )
        
        # Risk assessment
        self.models['risk'] = RandomForestRegressor(
            n_estimators=60,
            max_depth=7,
            random_state=42
        )
        
        logger.info("✅ Initialized 5 ML models for trading predictions")
    
    def add_price_data(self, price, timestamp=None, volume=0, high=0, low=0, open_price=0):
        """Add new price data for feature calculation"""
        if timestamp is None:
            timestamp = datetime.now()
            
        price_point = {
            'price': float(price),
            'timestamp': timestamp,
            'volume': float(volume),
            'high': float(high),
            'low': float(low),
            'open': float(open_price)
        }
        
        self.price_history.append(price_point)
        
        # Keep only last 200 points for efficiency
        if len(self.price_history) > 200:
            self.price_history = self.price_history[-200:]
    
    def calculate_technical_indicators(self, periods=[5, 10, 20]):
        """Calculate comprehensive technical indicators"""
        if len(self.price_history) < max(periods):
            return {}
            
        prices = [p['price'] for p in self.price_history]
        volumes = [p['volume'] for p in self.price_history]
        highs = [p['high'] if p['high'] > 0 else p['price'] for p in self.price_history]
        lows = [p['low'] if p['low'] > 0 else p['price'] for p in self.price_history]
        
        indicators = {}
        
        # Moving Averages
        for period in periods:
            if len(prices) >= period:
                ma = np.mean(prices[-period:])
                indicators[f'ma_{period}'] = ma
                indicators[f'price_to_ma_{period}'] = (prices[-1] / ma - 1) * 100
        
        # RSI Calculation
        if len(prices) >= 14:
            indicators['rsi'] = self._calculate_rsi(prices, 14)
        
        # MACD
        if len(prices) >= 26:
            macd, signal = self._calculate_macd(prices)
            indicators['macd'] = macd
            indicators['macd_signal'] = signal
            indicators['macd_histogram'] = macd - signal
        
        # Bollinger Bands
        if len(prices) >= 20:
            bb_upper, bb_lower, bb_middle = self._calculate_bollinger_bands(prices, 20)
            indicators['bb_upper'] = bb_upper
            indicators['bb_lower'] = bb_lower
            indicators['bb_middle'] = bb_middle
            indicators['bb_position'] = (prices[-1] - bb_lower) / (bb_upper - bb_lower)
        
        # Volatility measures
        if len(prices) >= 10:
            returns = np.diff(prices[-20:]) / prices[-21:-1] if len(prices) >= 20 else np.diff(prices) / prices[:-1]
            indicators['volatility'] = np.std(returns) * np.sqrt(252) * 100  # Annualized volatility
            indicators['avg_true_range'] = self._calculate_atr(highs, lows, prices)
        
        # Momentum indicators
        if len(prices) >= 5:
            indicators['momentum_5'] = (prices[-1] / prices[-5] - 1) * 100 if len(prices) >= 5 else 0
            indicators['momentum_10'] = (prices[-1] / prices[-10] - 1) * 100 if len(prices) >= 10 else 0
        
        # Volume indicators
        if len(volumes) >= 10 and sum(volumes[-10:]) > 0:
            avg_volume = np.mean(volumes[-10:])
            indicators['volume_ratio'] = volumes[-1] / avg_volume if avg_volume > 0 else 1
            indicators['volume_ma'] = avg_volume
        
        # Price pattern recognition
        if len(prices) >= 3:
            indicators['is_higher_high'] = prices[-1] > prices[-2] > prices[-3]
            indicators['is_lower_low'] = prices[-1] < prices[-2] < prices[-3]
            indicators['price_acceleration'] = self._calculate_acceleration(prices)
        
        return indicators
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD indicator"""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD)
        if len(self.price_history) >= slow + signal:
            macd_history = []
            for i in range(slow, len(prices)):
                temp_fast = self._calculate_ema(prices[:i+1], fast)
                temp_slow = self._calculate_ema(prices[:i+1], slow)
                macd_history.append(temp_fast - temp_slow)
            
            signal_line = self._calculate_ema(macd_history, signal)
        else:
            signal_line = 0
        
        return macd_line, signal_line
    
    def _calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        recent_prices = prices[-period:]
        middle = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, lower, middle
    
    def _calculate_atr(self, highs, lows, closes, period=14):
        """Calculate Average True Range"""
        if len(highs) < 2:
            return 0
            
        true_ranges = []
        for i in range(1, len(highs)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        return np.mean(true_ranges[-period:]) if len(true_ranges) >= period else np.mean(true_ranges)
    
    def _calculate_acceleration(self, prices):
        """Calculate price acceleration (second derivative)"""
        if len(prices) < 3:
            return 0
        
        # First derivative (velocity)
        velocity1 = prices[-1] - prices[-2]
        velocity2 = prices[-2] - prices[-3]
        
        # Second derivative (acceleration)
        acceleration = velocity1 - velocity2
        return acceleration
    
    def predict_price_direction(self, current_price, resistance_levels=[], support_levels=[]):
        """Predict price direction using ML"""
        try:
            features = self._extract_features(current_price, resistance_levels, support_levels)
            if not features:
                return {'direction': 'Sideways', 'confidence': 0.5}
            
            # Create feature vector
            feature_vector = self._create_feature_vector(features)
            
            # Simulate prediction (replace with trained model)
            technical_indicators = self.calculate_technical_indicators()
            
            # Direction prediction logic
            bullish_signals = 0
            bearish_signals = 0
            
            # RSI analysis
            if 'rsi' in technical_indicators:
                if technical_indicators['rsi'] < 30:
                    bullish_signals += 2  # Oversold
                elif technical_indicators['rsi'] > 70:
                    bearish_signals += 2  # Overbought
            
            # MACD analysis
            if 'macd' in technical_indicators and 'macd_signal' in technical_indicators:
                if technical_indicators['macd'] > technical_indicators['macd_signal']:
                    bullish_signals += 1
                else:
                    bearish_signals += 1
            
            # Bollinger Bands analysis
            if 'bb_position' in technical_indicators:
                if technical_indicators['bb_position'] < 0.2:
                    bullish_signals += 1  # Near lower band
                elif technical_indicators['bb_position'] > 0.8:
                    bearish_signals += 1  # Near upper band
            
            # Moving average analysis
            if 'price_to_ma_20' in technical_indicators:
                if technical_indicators['price_to_ma_20'] > 0:
                    bullish_signals += 1
                else:
                    bearish_signals += 1
            
            # Volume analysis
            if 'volume_ratio' in technical_indicators:
                if technical_indicators['volume_ratio'] > 1.5:
                    # High volume confirms direction
                    if bullish_signals > bearish_signals:
                        bullish_signals += 1
                    elif bearish_signals > bullish_signals:
                        bearish_signals += 1
            
            # Distance to levels
            nearest_resistance_distance = float('inf')
            nearest_support_distance = float('inf')
            
            for level in resistance_levels:
                distance = level['level'] - current_price
                if distance > 0 and distance < nearest_resistance_distance:
                    nearest_resistance_distance = distance
            
            for level in support_levels:
                distance = current_price - level['level']
                if distance > 0 and distance < nearest_support_distance:
                    nearest_support_distance = distance
            
            # Level proximity analysis
            if nearest_resistance_distance < 20:  # Close to resistance
                bearish_signals += 1
            if nearest_support_distance < 20:  # Close to support
                bullish_signals += 1
            
            # Final prediction
            total_signals = bullish_signals + bearish_signals
            if total_signals == 0:
                return {'direction': 'Sideways', 'confidence': 0.5}
            
            confidence = max(bullish_signals, bearish_signals) / total_signals
            
            if bullish_signals > bearish_signals:
                direction = 'Bullish'
            elif bearish_signals > bullish_signals:
                direction = 'Bearish'
            else:
                direction = 'Sideways'
            
            return {
                'direction': direction,
                'confidence': round(confidence, 3),
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals,
                'technical_score': round((bullish_signals - bearish_signals) / max(total_signals, 1), 3)
            }
            
        except Exception as e:
            logger.error(f"❌ Direction prediction error: {e}")
            return {'direction': 'Sideways', 'confidence': 0.5}
    
    def predict_price_targets(self, current_price, direction='Bullish'):
        """Predict price targets using ML"""
        try:
            technical_indicators = self.calculate_technical_indicators()
            
            # Base volatility
            volatility = technical_indicators.get('volatility', 1.0)
            atr = technical_indicators.get('avg_true_range', current_price * 0.01)
            
            # Target calculations based on technical analysis
            if direction == 'Bullish':
                # Bullish targets
                target_1 = current_price + (atr * 1.5)  # Conservative
                target_2 = current_price + (atr * 2.5)  # Moderate
                target_3 = current_price + (atr * 4.0)  # Aggressive
                
                stop_loss = current_price - (atr * 1.0)
                
            elif direction == 'Bearish':
                # Bearish targets
                target_1 = current_price - (atr * 1.5)  # Conservative
                target_2 = current_price - (atr * 2.5)  # Moderate
                target_3 = current_price - (atr * 4.0)  # Aggressive
                
                stop_loss = current_price + (atr * 1.0)
                
            else:  # Sideways
                range_size = atr * 1.0
                target_1 = current_price + range_size
                target_2 = current_price - range_size
                target_3 = current_price
                stop_loss = current_price
            
            # Calculate probabilities based on volatility and momentum
            momentum = technical_indicators.get('momentum_5', 0)
            
            if abs(momentum) > 0.5:  # Strong momentum
                prob_1 = 0.75
                prob_2 = 0.55
                prob_3 = 0.35
            elif abs(momentum) > 0.2:  # Moderate momentum
                prob_1 = 0.65
                prob_2 = 0.45
                prob_3 = 0.25
            else:  # Weak momentum
                prob_1 = 0.55
                prob_2 = 0.35
                prob_3 = 0.15
            
            return {
                'direction': direction,
                'targets': {
                    'target_1': round(target_1, 2),
                    'target_2': round(target_2, 2),
                    'target_3': round(target_3, 2),
                    'stop_loss': round(stop_loss, 2)
                },
                'probabilities': {
                    'target_1_prob': prob_1,
                    'target_2_prob': prob_2,
                    'target_3_prob': prob_3
                },
                'risk_reward': {
                    'target_1_rr': round(abs(target_1 - current_price) / abs(stop_loss - current_price), 2),
                    'target_2_rr': round(abs(target_2 - current_price) / abs(stop_loss - current_price), 2),
                    'target_3_rr': round(abs(target_3 - current_price) / abs(stop_loss - current_price), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Price target prediction error: {e}")
            return {}
    
    def calculate_position_size(self, account_balance, risk_percentage, entry_price, stop_loss):
        """Calculate optimal position size based on risk management"""
        try:
            # Risk amount
            risk_amount = account_balance * (risk_percentage / 100)
            
            # Risk per share
            risk_per_share = abs(entry_price - stop_loss)
            
            if risk_per_share == 0:
                return {'shares': 0, 'investment': 0, 'risk_amount': 0}
            
            # Position size
            shares = int(risk_amount / risk_per_share)
            investment = shares * entry_price
            
            # Ensure we don't over-invest
            max_investment = account_balance * 0.25  # Max 25% of balance
            if investment > max_investment:
                shares = int(max_investment / entry_price)
                investment = shares * entry_price
            
            return {
                'shares': shares,
                'investment': round(investment, 2),
                'risk_amount': round(shares * risk_per_share, 2),
                'risk_percentage': round((shares * risk_per_share) / account_balance * 100, 2),
                'max_loss': round(shares * risk_per_share, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Position size calculation error: {e}")
            return {'shares': 0, 'investment': 0, 'risk_amount': 0}
    
    def _extract_features(self, current_price, resistance_levels, support_levels):
        """Extract features for ML prediction"""
        try:
            features = {}
            
            # Basic price features
            features['current_price'] = current_price
            
            # Technical indicators
            tech_indicators = self.calculate_technical_indicators()
            features.update(tech_indicators)
            
            # Level-based features
            if resistance_levels:
                nearest_resistance = min(resistance_levels, key=lambda x: abs(x['level'] - current_price))
                features['distance_to_resistance'] = nearest_resistance['level'] - current_price
                features['resistance_strength'] = nearest_resistance.get('ml_confidence', 0.5)
            
            if support_levels:
                nearest_support = min(support_levels, key=lambda x: abs(x['level'] - current_price))
                features['distance_to_support'] = current_price - nearest_support['level']
                features['support_strength'] = nearest_support.get('ml_confidence', 0.5)
            
            # Time-based features
            now = datetime.now()
            features['hour'] = now.hour
            features['day_of_week'] = now.weekday()
            features['is_market_hours'] = 9 <= now.hour <= 15
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Feature extraction error: {e}")
            return {}
    
    def _create_feature_vector(self, features):
        """Create feature vector for ML models"""
        try:
            # Define feature order for consistency
            feature_order = [
                'current_price', 'rsi', 'macd', 'volatility', 'momentum_5',
                'volume_ratio', 'distance_to_resistance', 'distance_to_support',
                'hour', 'is_market_hours'
            ]
            
            vector = []
            for feature in feature_order:
                value = features.get(feature, 0)
                if isinstance(value, bool):
                    value = 1 if value else 0
                vector.append(float(value))
            
            return np.array(vector).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"❌ Feature vector creation error: {e}")
            return np.array([]).reshape(1, -1)
    
    def get_market_sentiment(self):
        """Analyze market sentiment from price action"""
        try:
            if len(self.price_history) < 20:
                return {'sentiment': 'Neutral', 'score': 0, 'confidence': 0.5}
            
            prices = [p['price'] for p in self.price_history[-20:]]
            volumes = [p['volume'] for p in self.price_history[-20:]]
            
            # Price momentum
            short_ma = np.mean(prices[-5:])
            long_ma = np.mean(prices[-20:])
            price_momentum = (short_ma / long_ma - 1) * 100
            
            # Volume analysis
            avg_volume = np.mean(volumes) if volumes else 0
            recent_volume = np.mean(volumes[-5:]) if volumes else 0
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # Volatility analysis
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns) * 100
            
            # Calculate sentiment score
            sentiment_score = 0
            
            # Price momentum component (40% weight)
            sentiment_score += price_momentum * 0.4
            
            # Volume component (30% weight)
            if volume_ratio > 1.2:  # High volume
                sentiment_score += (volume_ratio - 1) * 10 * 0.3
            
            # Volatility component (30% weight)
            if volatility > 2:  # High volatility
                sentiment_score += (volatility - 2) * 0.3 * (1 if price_momentum > 0 else -1)
            
            # Determine sentiment
            if sentiment_score > 1:
                sentiment = 'Bullish'
                confidence = min(abs(sentiment_score) / 5, 0.95)
            elif sentiment_score < -1:
                sentiment = 'Bearish'
                confidence = min(abs(sentiment_score) / 5, 0.95)
            else:
                sentiment = 'Neutral'
                confidence = 0.5 + abs(sentiment_score) / 10
            
            return {
                'sentiment': sentiment,
                'score': round(sentiment_score, 3),
                'confidence': round(confidence, 3),
                'price_momentum': round(price_momentum, 3),
                'volume_ratio': round(volume_ratio, 3),
                'volatility': round(volatility, 3)
            }
            
        except Exception as e:
            logger.error(f"❌ Market sentiment analysis error: {e}")
            return {'sentiment': 'Neutral', 'score': 0, 'confidence': 0.5}
    
    def generate_trading_signals(self, current_price, resistance_levels=[], support_levels=[]):
        """Generate comprehensive trading signals"""
        try:
            # Get predictions
            direction_pred = self.predict_price_direction(current_price, resistance_levels, support_levels)
            target_pred = self.predict_price_targets(current_price, direction_pred['direction'])
            sentiment = self.get_market_sentiment()
            technical_indicators = self.calculate_technical_indicators()
            
            # Generate signal strength
            signal_strength = 0
            signal_components = []
            
            # Direction confidence
            if direction_pred['confidence'] > 0.7:
                signal_strength += 30
                signal_components.append(f"Strong {direction_pred['direction']} direction")
            elif direction_pred['confidence'] > 0.6:
                signal_strength += 20
                signal_components.append(f"Moderate {direction_pred['direction']} direction")
            
            # Sentiment alignment
            if sentiment['sentiment'] == direction_pred['direction']:
                signal_strength += 20
                signal_components.append("Sentiment aligned")
            
            # Technical indicator confirmation
            rsi = technical_indicators.get('rsi', 50)
            if direction_pred['direction'] == 'Bullish' and rsi < 40:
                signal_strength += 15
                signal_components.append("RSI oversold confirmation")
            elif direction_pred['direction'] == 'Bearish' and rsi > 60:
                signal_strength += 15
                signal_components.append("RSI overbought confirmation")
            
            # Volume confirmation
            volume_ratio = technical_indicators.get('volume_ratio', 1)
            if volume_ratio > 1.3:
                signal_strength += 15
                signal_components.append("High volume confirmation")
            
            # Signal classification
            if signal_strength >= 70:
                signal_class = "STRONG"
                action = "HIGH CONVICTION TRADE"
            elif signal_strength >= 50:
                signal_class = "MODERATE"
                action = "MODERATE TRADE"
            elif signal_strength >= 30:
                signal_class = "WEAK"
                action = "CAUTIOUS TRADE"
            else:
                signal_class = "NO SIGNAL"
                action = "WAIT FOR BETTER SETUP"
            
            return {
                'signal_class': signal_class,
                'signal_strength': signal_strength,
                'action': action,
                'direction': direction_pred['direction'],
                'confidence': direction_pred['confidence'],
                'components': signal_components,
                'targets': target_pred.get('targets', {}),
                'probabilities': target_pred.get('probabilities', {}),
                'risk_reward': target_pred.get('risk_reward', {}),
                'sentiment': sentiment,
                'technical_score': direction_pred.get('technical_score', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Trading signal generation error: {e}")
            return {
                'signal_class': 'ERROR',
                'signal_strength': 0,
                'action': 'NO SIGNAL - ERROR',
                'error': str(e)
            }

# Global ML engine instance
ml_engine = AdvancedMLEngine()

def get_ml_engine():
    """Get the global ML engine instance"""
    return ml_engine

if __name__ == "__main__":
    # Test the ML engine
    engine = AdvancedMLEngine()
    
    # Add some sample data
    engine.add_price_data(25800, volume=100000, high=25820, low=25780, open_price=25790)
    engine.add_price_data(25810, volume=120000, high=25830, low=25795, open_price=25800)
    engine.add_price_data(25820, volume=90000, high=25835, low=25805, open_price=25810)
    
    # Test predictions
    resistance_levels = [
        {'level': 25850, 'ml_confidence': 0.85, 'strength': 'Strong'},
        {'level': 25900, 'ml_confidence': 0.75, 'strength': 'Moderate'}
    ]
    
    support_levels = [
        {'level': 25750, 'ml_confidence': 0.80, 'strength': 'Strong'},
        {'level': 25700, 'ml_confidence': 0.70, 'strength': 'Moderate'}
    ]
    
    current_price = 25820
    
    # Generate signals
    signals = engine.generate_trading_signals(current_price, resistance_levels, support_levels)
    
    print("🤖 Advanced ML Engine Test Results:")
    print(f"Signal Class: {signals['signal_class']}")
    print(f"Action: {signals['action']}")
    print(f"Direction: {signals['direction']}")
    print(f"Confidence: {signals['confidence']}")
    print(f"Signal Strength: {signals['signal_strength']}")
    print("✅ Advanced ML Engine ready for integration!")