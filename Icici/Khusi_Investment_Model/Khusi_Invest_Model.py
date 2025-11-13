"""


"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import os

    
        
        
        
        
        
class KhusiInvestModel:
    """Advanced EMA prediction model with pattern recognition"""
    
    def __init__(self, timeframe='daily'):
        """
        Initialize model for daily timeframe only
        
        Args:
            timeframe: 'daily' only (15min uses Pranni, 1hour removed)
        """
        if timeframe != 'daily':
            raise ValueError("Only 'daily' timeframe supported in Khusi Model. Use Pranni model for intraday (15min) trading.")
        
        self.timeframe = timeframe
        self.ema_periods = [5, 9, 21, 50, 100, 200]
        self.model = None
        self.feature_importance = None
        
        # Database mapping - daily only
        self.db_map = {
            'daily': 'NIFTY_1day_data.db'
        }
        
        self.table_map = {
            'daily': 'data_1day'
        }
        
        print(f"\nKHUSI INVEST MODEL initialized for DAILY timeframe (long-term moves)")

    def load_data_from_database(self):
        """Load data from SQLite database"""
        print(f"\nLoading data from database...")
        
        db_file = self.db_map[self.timeframe]
        table_name = self.table_map[self.timeframe]
        
        if not os.path.exists(db_file):
            print(f"ERROR: Database not found: {db_file}")
            return None
        
        try:
            conn = sqlite3.connect(db_file)
            
            # Load only required columns
            query = f"SELECT datetime, open, high, low, close, volume FROM {table_name} ORDER BY datetime"
            df = pd.read_sql_query(query, conn)
            conn.close()

            # Convert datetime (handle both date-only and datetime formats)
            try:
                df['datetime'] = pd.to_datetime(df['datetime'])
            except:
                # Try with just date format
                df['datetime'] = pd.to_datetime(df['datetime'], format='mixed')

            # Ensure numeric types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Drop rows with any NaN in OHLCV
            df = df.dropna()

            print(f"SUCCESS: Loaded {len(df)} records from {db_file}")
            print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
            print(f"Price range: Rs.{df['close'].min():,.2f} to Rs.{df['close'].max():,.2f}")

            return df

        except Exception as e:
            print(f"ERROR: Error loading data: {e}")
            return None

    def calculate_emas(self, df):
        """Calculate all EMA periods"""
        print(f"\nCalculating EMAs...")

        for period in self.ema_periods:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()

        print(f"SUCCESS: Calculated {len(self.ema_periods)} EMAs")
        return df

    def detect_time_correction_phase(self, row):
        """Detect time correction phase based on EMA positions"""
        close = row['close']
        ema_5 = row['ema_5']
        ema_9 = row['ema_9']
        ema_21 = row['ema_21']
        ema_50 = row['ema_50']
        ema_100 = row['ema_100']
        ema_200 = row['ema_200']

        if close > ema_5 and close > ema_9 and close > ema_21:
            return 0, "BULL_TRENDING"
        elif close < ema_5 and close > ema_9:
            return 1, "PHASE_1"
        elif close < ema_9 and close > ema_21:
            return 2, "PHASE_2"
        elif close < ema_21 and close > ema_50:
            return 3, "PHASE_3"
        elif close < ema_50 and close > ema_100:
            return 4, "PHASE_4"
        elif close < ema_100:
            return 5, "PHASE_5"
        else:
            return -1, "BEAR_TRENDING"
        
    def create_basic_features(self, df):
        """Create basic EMA features (existing logic)"""
        print(f"\nCreating basic features...")

        # Price position relative to each EMA
        for period in self.ema_periods:
            df[f'price_above_ema_{period}'] = (df['close'] > df[f'ema_{period}']).astype(int)

        # Distance to each EMA (percentage)
        for period in self.ema_periods:
            df[f'distance_to_ema_{period}'] = (df['close'] - df[f'ema_{period}']) / df[f'ema_{period}'] * 100

        # EMA slopes (momentum)
        for period in self.ema_periods:
            df[f'ema_{period}_slope'] = df[f'ema_{period}'].pct_change(5) * 100

        # EMA convergences
        df['total_convergences'] = 0
        df['strong_convergences'] = 0

        for i in range(len(self.ema_periods) - 1):
            p1, p2 = self.ema_periods[i], self.ema_periods[i+1]
            df[f'conv_{p1}_{p2}'] = abs(df[f'ema_{p1}'] - df[f'ema_{p2}']) / df[f'ema_{p1}'] * 100

            # Count convergences
            df['total_convergences'] += (df[f'conv_{p1}_{p2}'] < 1.0).astype(int)
            df['strong_convergences'] += (df[f'conv_{p1}_{p2}'] < 0.5).astype(int)

        # EMA alignment (faster > slower)
        for i in range(len(self.ema_periods) - 1):
            p1, p2 = self.ema_periods[i], self.ema_periods[i+1]
            df[f'ema_aligned_{p1}_{p2}'] = (df[f'ema_{p1}'] > df[f'ema_{p2}']).astype(int)

        # Sequential below EMAs
        df['sequential_below_5'] = (df['close'] < df['ema_5']).astype(int)
        df['sequential_below_9'] = (df['close'] < df['ema_9']).astype(int)
        df['sequential_below_21'] = (df['close'] < df['ema_21']).astype(int)
        df['sequential_below_50'] = (df['close'] < df['ema_50']).astype(int)

        # Time Correction Phase
        df[['correction_phase', 'correction_phase_name']] = df.apply(
            lambda row: pd.Series(self.detect_time_correction_phase(row)), axis=1
        )

        # Days in phase
        df['days_in_phase'] = 0
        df = df.reset_index(drop=True)  # Reset index to ensure continuous 0-N indexing

        for idx in range(1, len(df)):
            if df.loc[idx, 'correction_phase'] == df.loc[idx-1, 'correction_phase']:
                df.loc[idx, 'days_in_phase'] = df.loc[idx-1, 'days_in_phase'] + 1
            else:
                df.loc[idx, 'days_in_phase'] = 1

        # Convergence velocity
        for i in range(len(self.ema_periods) - 1):
            p1, p2 = self.ema_periods[i], self.ema_periods[i+1]
            df[f'conv_velocity_{p1}_{p2}'] = df[f'conv_{p1}_{p2}'].diff()

        # Price action features
        df['daily_return'] = df['close'].pct_change() * 100
        df['volatility'] = df['daily_return'].rolling(20).std()
        df['high_low_range'] = (df['high'] - df['low']) / df['close'] * 100
        df['body_size'] = abs(df['close'] - df['open']) / df['close'] * 100
        df['upper_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close'] * 100
        df['lower_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close'] * 100

        # Bullish/Bearish patterns
        df['is_bullish_candle'] = (df['close'] > df['open']).astype(int)
        df['bullish_candles_5d'] = df['is_bullish_candle'].rolling(5).sum()

        # Trend strength
        df['emas_above_count'] = 0
        for p in self.ema_periods:
            df['emas_above_count'] += df[f'price_above_ema_{p}']

        df['ema_alignment_score'] = 0
        for i in range(len(self.ema_periods)-1):
            df['ema_alignment_score'] += df[f'ema_aligned_{self.ema_periods[i]}_{self.ema_periods[i+1]}']

        # Returns
        df['return_5d'] = df['close'].pct_change(5) * 100
        df['return_10d'] = df['close'].pct_change(10) * 100
        df['return_20d'] = df['close'].pct_change(20) * 100

        # Momentum
        df['momentum'] = df['close'].pct_change(14) * 100

        # Volume features
        if 'volume' in df.columns:
            # Ensure volume is numeric
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            df['volume_ma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']

        # High probability setup
        df['phase3_convergence'] = ((df['correction_phase'] == 3) & (df['total_convergences'] >= 2)).astype(int)

        print(f"SUCCESS: Created {30 + len(self.ema_periods)*4} basic features")

        return df
        
    def train_model(self, df):
        """Train the Khusi Invest model"""
        print(f"\n🚀 Training Khusi Invest Model ({self.timeframe})...")
        print("=" * 80)

        # Select features
        exclude_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume', 
                       'target', 'next_return', 'correction_phase_name']

        feature_cols = [col for col in df.columns if col not in exclude_cols]

        X = df[feature_cols]
        y = df['target']

        print(f"📊 Total Features: {len(feature_cols)}")
        print(f"📈 Training Samples: {len(X)}")
        print(f"🔺 UP samples: {y.sum()} ({y.sum()/len(y)*100:.1f}%)")
        print(f"🔻 DOWN samples: {len(y)-y.sum()} ({(len(y)-y.sum())/len(y)*100:.1f}%)")

        # Time-based split (80% train, 20% test)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        print(f"\n🎯 Training set: {len(X_train)} samples")
        print(f"📉 Test set: {len(X_test)} samples")

        # Train Gradient Boosting
        self.model = GradientBoostingClassifier(
            n_estimators=250,
            learning_rate=0.08,
            max_depth=6,
            min_samples_split=20,
            min_samples_leaf=10,
            subsample=0.8,
            random_state=42,
            verbose=0
        )

        print(f"\n⏳ Training model...")
        self.model.fit(X_train, y_train)

        # Evaluate
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)

        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)

        print(f"\n✅ Training Accuracy: {train_acc*100:.2f}%")
        print(f"✅ Test Accuracy: {test_acc*100:.2f}%")

        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        print(f"\n🔝 Top 10 Most Important Features:")
        print("=" * 50)
        for idx, row in self.feature_importance.head(10).iterrows():
            print(f"  {row['feature']:35s} {row['importance']:.4f}")

        # Classification report (handle imbalanced data)
        print(f"\n📊 Test Set Performance:")
        print("=" * 50)
        try:
            unique_labels = sorted(y_test.unique())
            if len(unique_labels) == 2:
                print(classification_report(y_test, test_pred, target_names=['DOWN ⬇️', 'UP ⬆️']))
            else:
                print(classification_report(y_test, test_pred))
        except Exception as e:
            print(f"Classification report: {e}")
            print(f"Test predictions distribution: {pd.Series(test_pred).value_counts().to_dict()}")

        return test_acc
        
    def run_full_training(self):
        """Run complete training pipeline"""
        print("🚀 KHUSI INVEST MODEL - Daily Training")
        print("=" * 60)
        
        # Load data
        df = self.load_data_from_database()
        if df is None:
            print("❌ ERROR: Cannot load data")
            return False
            
        # Calculate EMAs
        df = self.calculate_emas(df)
        
        # Create basic features
        df = self.create_basic_features(df)
        
        # Create target variable (next day return > 0.5% for better balance)
        print("\n📊 Creating target variable...")
        df['next_return'] = df['close'].pct_change(periods=-1) * 100  # Next day return
        df['target'] = (df['next_return'] > 0.5).astype(int)  # 0.5% threshold for UP
        
        # Remove rows with NaN (due to shifts and rolling operations)
        df = df.dropna()
        
        print(f"✅ Final dataset: {len(df)} samples with {df.columns.size - 7} features")
        print(f"📈 Target distribution: {df['target'].value_counts().to_dict()}")
        
        if len(df) < 100:
            print("❌ ERROR: Insufficient data for training")
            return False
            
        # Train model
        accuracy = self.train_model(df)
        
        # Save model
        if accuracy > 0.50:  # Only save if better than random
            self.save_model()
            print(f"\n🎉 Model trained successfully! Accuracy: {accuracy*100:.2f}%")
            return True
        else:
            print(f"\n⚠️ Model accuracy ({accuracy*100:.2f}%) too low - not saved")
            return False
    
    def save_model(self):
        """Save trained model to pickle file"""
        filename = f'khusi_model_{self.timeframe}.pkl'
        
        with open(filename, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_importance': self.feature_importance,
                'ema_periods': self.ema_periods,
                'timeframe': self.timeframe
            }, f)
        
        print(f"💾 Model saved to: {filename}")
        
    def load_model(self):
        """Load trained model from pickle file"""
        filename = f'khusi_model_{self.timeframe}.pkl'
        
        if not os.path.exists(filename):
            print(f"❌ Model file not found: {filename}")
            return False
            
        try:
            with open(filename, 'rb') as f:
                model_data = pickle.load(f)
                
            self.model = model_data['model']
            self.feature_importance = model_data['feature_importance']
            
            print(f"✅ Model loaded from: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False



def train_daily_model():
    """Utility function to train daily model"""
    print("🏛️ Training Daily Khusi Invest Model...")
    model = KhusiInvestModel(timeframe='daily')
    return model.run_full_training()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Check argument
        timeframe = sys.argv[1]
        if timeframe == 'daily':
            model = KhusiInvestModel(timeframe='daily')
            model.run_full_training()
        else:
            print("ERROR: Only 'daily' timeframe supported")
            print("📝 Use: python Khusi_Invest_Model.py daily")
            print("📝 Note: Pranni model handles intraday (15min) trading")
    else:
        # Train daily model by default
        train_daily_model()
