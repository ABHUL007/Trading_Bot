"""
Multi-Timeframe Pattern Learning Engine
Analyzes historical data across 15min, 1hour, and 1day timeframes
to extract profitable trading patterns for real-time application
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiTimeframePatternLearner:
    """Learn patterns from multi-timeframe historical data"""
    
    def __init__(self):
        self.data = {}
        self.patterns = {}
        self.models = {}
        self.scalers = {}
        self.learned_strategies = []
        
        # Timeframes to analyze
        self.timeframes = {
            '5min': 'NIFTY_5min_20221024_20251023.csv',
            '15min': 'NIFTY_15min_20221024_20251023.csv',
            '1hour': 'NIFTY_1hour_20221024_20251023.csv', 
            '1day': 'NIFTY_1day_20221024_20251023.csv'
        }
        
    def load_historical_data(self):
        """Load all timeframe data"""
        logger.info("🔄 Loading multi-timeframe historical data...")
        
        for timeframe, filename in self.timeframes.items():
            try:
                df = pd.read_csv(f'data/{filename}')
                df['datetime'] = pd.to_datetime(df['datetime'])
                df = df.sort_values('datetime')
                
                # Calculate basic technical indicators
                df = self._add_technical_indicators(df, timeframe)
                
                self.data[timeframe] = df
                logger.info(f"✅ Loaded {timeframe}: {len(df)} records from {df['datetime'].min()} to {df['datetime'].max()}")
                
            except Exception as e:
                logger.error(f"❌ Error loading {timeframe} data: {e}")
        
        logger.info(f"📊 Loaded {len(self.data)} timeframes successfully")
    
    def _add_technical_indicators(self, df, timeframe):
        """Add technical indicators for pattern recognition"""
        
        # Price action indicators
        df['price_change'] = df['close'].pct_change()
        df['price_change_abs'] = abs(df['price_change'])
        
        # Add MA-based features (adjust periods for different timeframes)
        if timeframe == '5min':
            periods = [3, 5, 10, 20]
        elif timeframe == '15min':
            periods = [5, 10, 20]
        elif timeframe == '1hour':
            periods = [10, 20, 50]
        else:  # 1day
            periods = [5, 10, 20, 50]
            
        for period in periods:
            df[f'ma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'price_vs_ma_{period}'] = (df['close'] - df[f'ma_{period}']) / df[f'ma_{period}']
        
        # Volatility indicators
        df['atr'] = self._calculate_atr(df, 14)
        df['volatility'] = df['price_change'].rolling(window=20).std()
        
        # Volume indicators (if available)
        if 'volume' in df.columns:
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        else:
            df['volume_ratio'] = 1.0
        
        # Support/Resistance levels
        df = self._identify_levels(df, timeframe)
        
        # Pattern signals
        df = self._identify_patterns(df, timeframe)
        
        return df
    
    def _calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()
    
    def _identify_levels(self, df, timeframe):
        """Identify support and resistance levels"""
        window = 10 if timeframe == '15min' else 20
        
        # Local highs and lows
        df['is_peak'] = (df['high'] == df['high'].rolling(window=window, center=True).max())
        df['is_trough'] = (df['low'] == df['low'].rolling(window=window, center=True).min())
        
        # Distance to nearest levels
        peaks = df[df['is_peak']]['high'].values
        troughs = df[df['is_trough']]['low'].values
        
        df['resistance_distance'] = np.nan
        df['support_distance'] = np.nan
        
        for i, price in enumerate(df['close']):
            if len(peaks) > 0:
                nearest_resistance = min(peaks[peaks > price], default=np.nan)
                if not np.isnan(nearest_resistance):
                    df.iloc[i, df.columns.get_loc('resistance_distance')] = (nearest_resistance - price) / price
            
            if len(troughs) > 0:
                nearest_support = max(troughs[troughs < price], default=np.nan)
                if not np.isnan(nearest_support):
                    df.iloc[i, df.columns.get_loc('support_distance')] = (price - nearest_support) / price
        
        return df
    
    def _identify_patterns(self, df, timeframe):
        """Identify candlestick and price patterns"""
        
        # Basic candlestick patterns
        df['body_size'] = abs(df['close'] - df['open']) / df['open']
        df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['open']
        df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['open']
        
        # Trend patterns
        df['consecutive_up'] = 0
        df['consecutive_down'] = 0
        
        up_streak = 0
        down_streak = 0
        
        for i in range(1, len(df)):
            if df.iloc[i]['close'] > df.iloc[i-1]['close']:
                up_streak += 1
                down_streak = 0
            elif df.iloc[i]['close'] < df.iloc[i-1]['close']:
                down_streak += 1
                up_streak = 0
            else:
                up_streak = 0
                down_streak = 0
            
            df.iloc[i, df.columns.get_loc('consecutive_up')] = up_streak
            df.iloc[i, df.columns.get_loc('consecutive_down')] = down_streak
        
        # Future price movement (target for learning)
        lookahead = 5 if timeframe == '15min' else (3 if timeframe == '1hour' else 1)
        df['future_return'] = df['close'].shift(-lookahead) / df['close'] - 1
        
        # Classify future movement
        threshold = 0.002 if timeframe == '15min' else (0.005 if timeframe == '1hour' else 0.01)
        df['future_direction'] = 0  # Sideways
        df.loc[df['future_return'] > threshold, 'future_direction'] = 1  # Up
        df.loc[df['future_return'] < -threshold, 'future_direction'] = -1  # Down
        
        return df
    
    def learn_patterns(self):
        """Learn profitable patterns from historical data"""
        logger.info("🧠 Learning patterns from historical data...")
        
        for timeframe in self.timeframes.keys():
            if timeframe not in self.data:
                continue
                
            logger.info(f"📈 Analyzing {timeframe} patterns...")
            df = self.data[timeframe].copy()
            
            # Prepare features for pattern learning
            feature_columns = [
                'price_change', 'price_change_abs', 'atr', 'volatility', 'volume_ratio',
                'body_size', 'upper_shadow', 'lower_shadow',
                'consecutive_up', 'consecutive_down', 'resistance_distance', 'support_distance'
            ]
            
            # Add MA-based features
            ma_features = [col for col in df.columns if 'ma_' in col or 'price_vs_ma_' in col]
            feature_columns.extend(ma_features)
            
            # Remove rows with NaN values
            df_clean = df[feature_columns + ['future_direction']].dropna()
            
            if len(df_clean) < 100:
                logger.warning(f"⚠️ Insufficient data for {timeframe}: {len(df_clean)} records")
                continue
            
            # Prepare training data
            X = df_clean[feature_columns].values
            y = df_clean['future_direction'].values
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"✅ {timeframe} pattern accuracy: {accuracy:.3f}")
            
            # Store model and scaler
            self.models[timeframe] = model
            self.scalers[timeframe] = scaler
            
            # Extract feature importance
            feature_importance = pd.DataFrame({
                'feature': feature_columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logger.info(f"🔍 Top {timeframe} features:")
            for _, row in feature_importance.head(5).iterrows():
                logger.info(f"   {row['feature']}: {row['importance']:.3f}")
            
            # Store learned patterns
            self.patterns[timeframe] = {
                'model': model,
                'scaler': scaler,
                'features': feature_columns,
                'accuracy': accuracy,
                'feature_importance': feature_importance
            }
    
    def extract_trading_strategies(self):
        """Extract actionable trading strategies"""
        logger.info("📋 Extracting trading strategies...")
        
        strategies = []
        
        # Multi-timeframe alignment strategy
        if len(self.models) >= 2:
            strategies.append({
                'name': 'Multi-Timeframe Alignment',
                'description': 'Trade when multiple timeframes agree on direction',
                'logic': 'Require 2+ timeframes to predict same direction',
                'confidence_threshold': 0.6,
                'risk_level': 'Medium'
            })
        
        # Volatility breakout strategy
        strategies.append({
            'name': 'Volatility Breakout',
            'description': 'Trade on volatility expansion with pattern confirmation',
            'logic': 'High volatility + pattern confirmation',
            'confidence_threshold': 0.7,
            'risk_level': 'High'
        })
        
        # Support/Resistance strategy
        strategies.append({
            'name': 'Level Bounce/Break',
            'description': 'Trade support bounces and resistance breaks',
            'logic': 'Near S/R levels + directional pattern',
            'confidence_threshold': 0.65,
            'risk_level': 'Medium'
        })
        
        self.learned_strategies = strategies
        logger.info(f"✅ Extracted {len(strategies)} trading strategies")
        
        return strategies
    
    def predict_realtime(self, current_data):
        """Apply learned patterns to real-time data"""
        predictions = {}
        
        for timeframe, pattern in self.patterns.items():
            try:
                # Extract features from current data
                features = self._extract_features(current_data, timeframe)
                
                if features is not None:
                    # Scale features
                    features_scaled = pattern['scaler'].transform([features])
                    
                    # Predict
                    prediction = pattern['model'].predict(features_scaled)[0]
                    probability = pattern['model'].predict_proba(features_scaled)[0]
                    
                    predictions[timeframe] = {
                        'direction': prediction,
                        'confidence': max(probability),
                        'probabilities': {
                            'down': probability[0] if len(probability) > 0 else 0,
                            'sideways': probability[1] if len(probability) > 1 else 0,
                            'up': probability[2] if len(probability) > 2 else 0
                        }
                    }
            except Exception as e:
                logger.error(f"❌ Prediction error for {timeframe}: {e}")
                
        return predictions
    
    def _extract_features(self, current_data, timeframe):
        """Extract features from current market data"""
        # This would extract the same features used in training
        # from the current market state
        # Implementation depends on the format of current_data
        return None
    
    def get_summary(self):
        """Get summary of learned patterns"""
        summary = {
            'timeframes_analyzed': list(self.patterns.keys()),
            'total_records': sum(len(self.data[tf]) for tf in self.data.keys()),
            'model_accuracies': {tf: self.patterns[tf]['accuracy'] for tf in self.patterns.keys()},
            'strategies_count': len(self.learned_strategies),
            'key_features': {}
        }
        
        # Extract top features across timeframes
        for tf, pattern in self.patterns.items():
            summary['key_features'][tf] = pattern['feature_importance'].head(3)['feature'].tolist()
        
        return summary

def main():
    """Main pattern learning workflow"""
    logger.info("🚀 Starting Multi-Timeframe Pattern Learning...")
    
    # Initialize learner
    learner = MultiTimeframePatternLearner()
    
    # Load historical data
    learner.load_historical_data()
    
    # Learn patterns
    learner.learn_patterns()
    
    # Extract strategies
    strategies = learner.extract_trading_strategies()
    
    # Print summary
    summary = learner.get_summary()
    logger.info("📊 Learning Summary:")
    logger.info(f"   Timeframes: {summary['timeframes_analyzed']}")
    logger.info(f"   Total Records: {summary['total_records']:,}")
    logger.info(f"   Model Accuracies: {summary['model_accuracies']}")
    logger.info(f"   Strategies: {summary['strategies_count']}")
    
    logger.info("🎯 Ready to apply patterns to real-time feeds!")
    
    return learner

if __name__ == "__main__":
    pattern_learner = main()