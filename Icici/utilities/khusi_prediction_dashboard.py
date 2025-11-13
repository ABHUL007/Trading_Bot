#!/usr/bin/env python3
"""
KHUSI INVEST MODEL - COMPREHENSIVE PREDICTION DASHBOARD
======================================================

Multi-timeframe NIFTY forecasting dashboard:
- Next Day Prediction
- Next Week Forecast (5 trading days)
- Next Month Outlook (20 trading days)

Features live market data, EMA analysis, and ML predictions
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import pickle
import os
from Khusi_Invest_Model import KhusiInvestModel

class KhusiPredictionDashboard:
    """Comprehensive prediction dashboard for NIFTY forecasting"""
    
    def __init__(self):
        self.model = KhusiInvestModel()
        self.current_data = None
        self.predictions = {}
        
    def load_latest_data(self):
        """Load the most recent market data"""
        print("📊 Loading latest market data...")
        
        # Load data from model
        df = self.model.load_data_from_database()
        if df is None:
            return None
            
        # Calculate EMAs and features
        df = self.model.calculate_emas(df)
        df = self.model.create_basic_features(df)
        
        # Get the latest row with all features
        self.current_data = df.iloc[-1]
        self.latest_close = self.current_data['close']
        self.latest_date = df.iloc[-1]['datetime']
        
        print(f"✅ Latest data: {self.latest_date.strftime('%Y-%m-%d')} | NIFTY: ₹{self.latest_close:,.2f}")
        return df
        
    def analyze_current_market_state(self):
        """Analyze current EMA positioning and market phase"""
        print("\n📈 CURRENT MARKET ANALYSIS")
        print("=" * 50)
        
        # EMA positioning
        close = self.current_data['close']
        ema_5 = self.current_data['ema_5']
        ema_9 = self.current_data['ema_9'] 
        ema_21 = self.current_data['ema_21']
        ema_50 = self.current_data['ema_50']
        ema_100 = self.current_data['ema_100']
        ema_200 = self.current_data['ema_200']
        
        print(f"📍 Current NIFTY: ₹{close:,.2f}")
        print(f"🔸 EMA 5:   ₹{ema_5:,.2f}   ({((close-ema_5)/ema_5*100):+.2f}%)")
        print(f"🔸 EMA 9:   ₹{ema_9:,.2f}   ({((close-ema_9)/ema_9*100):+.2f}%)")
        print(f"🔸 EMA 21:  ₹{ema_21:,.2f}  ({((close-ema_21)/ema_21*100):+.2f}%)")
        print(f"🔸 EMA 50:  ₹{ema_50:,.2f}  ({((close-ema_50)/ema_50*100):+.2f}%)")
        print(f"🔸 EMA 100: ₹{ema_100:,.2f} ({((close-ema_100)/ema_100*100):+.2f}%)")
        print(f"🔸 EMA 200: ₹{ema_200:,.2f} ({((close-ema_200)/ema_200*100):+.2f}%)")
        
        # Market phase analysis
        phase, phase_name = self.model.detect_time_correction_phase(self.current_data)
        days_in_phase = self.current_data['days_in_phase']
        
        print(f"\n🎯 Market Phase: {phase_name} (Day {int(days_in_phase)})")
        
        # EMA alignment
        emas_above = int(self.current_data['emas_above_count'])
        alignment_score = int(self.current_data['ema_alignment_score'])
        
        print(f"📊 EMAs Above Price: {emas_above}/6")
        print(f"📊 EMA Alignment Score: {alignment_score}/5")
        
        # Convergence analysis
        total_conv = int(self.current_data['total_convergences'])
        strong_conv = int(self.current_data['strong_convergences'])
        
        print(f"🔗 EMA Convergences: {total_conv} total, {strong_conv} strong")
        
        # Recent performance
        daily_return = self.current_data['daily_return']
        return_5d = self.current_data['return_5d']
        volatility = self.current_data['volatility']
        
        print(f"\n📈 Recent Performance:")
        print(f"   Daily Return: {daily_return:+.2f}%")
        print(f"   5-Day Return: {return_5d:+.2f}%")
        print(f"   Volatility: {volatility:.2f}%")
        
    def generate_predictions(self):
        """Generate predictions for multiple timeframes"""
        print("\n🔮 GENERATING PREDICTIONS")
        print("=" * 50)
        
        # Load trained model
        if not self.model.load_model():
            print("❌ Cannot load trained model. Please train first.")
            return False
            
        # Prepare features for prediction
        exclude_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume', 
                       'target', 'next_return', 'correction_phase_name']
        
        # Create a DataFrame with just the current row for prediction
        feature_data = pd.DataFrame([self.current_data])
        feature_cols = [col for col in feature_data.columns if col not in exclude_cols]
        X_current = feature_data[feature_cols]
        
        # Handle NaN values - fill with median or 0
        X_current = X_current.fillna(0)  # Fill NaN with 0 for prediction
        
        print(f"📊 Using {len(feature_cols)} features for prediction")
        print(f"📊 Features shape: {X_current.shape}")
        
        # Check for any remaining NaN values
        if X_current.isnull().sum().sum() > 0:
            print(f"⚠️ Warning: {X_current.isnull().sum().sum()} NaN values found and filled")
        
        # Get prediction and probability
        prediction = self.model.model.predict(X_current)[0]
        probability = self.model.model.predict_proba(X_current)[0]
        
        # Store predictions
        self.predictions = {
            'next_day': {
                'prediction': prediction,
                'probability_down': probability[0],
                'probability_up': probability[1],
                'confidence': max(probability),
                'direction': 'UP ⬆️' if prediction == 1 else 'DOWN ⬇️'
            }
        }
        
        # Generate week and month outlook based on current market state
        self._generate_extended_outlook()
        
        return True
        
    def _generate_extended_outlook(self):
        """Generate extended outlook for week and month"""
        
        # Week outlook (based on current trends and momentum)
        weekly_factors = []
        monthly_factors = []
        
        # Factor 1: EMA positioning strength
        emas_above = int(self.current_data['emas_above_count'])
        if emas_above >= 4:
            weekly_factors.append('BULLISH: Strong EMA support')
            monthly_factors.append('BULLISH: Sustained uptrend likely')
        elif emas_above <= 2:
            weekly_factors.append('BEARISH: Multiple EMA resistance')
            monthly_factors.append('BEARISH: Downward pressure')
        else:
            weekly_factors.append('NEUTRAL: Mixed EMA signals')
            monthly_factors.append('NEUTRAL: Sideways consolidation')
            
        # Factor 2: Market phase analysis
        phase_name = self.current_data['correction_phase_name']
        days_in_phase = int(self.current_data['days_in_phase'])
        
        if phase_name == 'BULL_TRENDING':
            weekly_factors.append('BULLISH: Bull trend continuation')
            monthly_factors.append('BULLISH: Strong momentum phase')
        elif 'PHASE_3' in phase_name and days_in_phase > 10:
            weekly_factors.append('BULLISH: Oversold bounce potential')
            monthly_factors.append('NEUTRAL: Recovery phase beginning')
        elif 'PHASE_5' in phase_name:
            weekly_factors.append('BEARISH: Deep correction ongoing')
            monthly_factors.append('BEARISH: Extended weakness')
            
        # Factor 3: Momentum and volatility
        momentum = self.current_data['momentum']
        volatility = self.current_data['volatility']
        
        if momentum > 2 and volatility < 20:
            weekly_factors.append('BULLISH: Strong positive momentum')
            monthly_factors.append('BULLISH: Sustained growth trend')
        elif momentum < -2 and volatility > 25:
            weekly_factors.append('BEARISH: Negative momentum + high vol')
            monthly_factors.append('BEARISH: Uncertain market conditions')
            
        # Compile outlook
        week_bullish = sum(1 for f in weekly_factors if 'BULLISH' in f)
        week_bearish = sum(1 for f in weekly_factors if 'BEARISH' in f)
        
        month_bullish = sum(1 for f in monthly_factors if 'BULLISH' in f)
        month_bearish = sum(1 for f in monthly_factors if 'BEARISH' in f)
        
        # Week outlook
        if week_bullish > week_bearish:
            week_outlook = 'BULLISH ⬆️'
            week_confidence = min(85, 60 + week_bullish * 8)
        elif week_bearish > week_bullish:
            week_outlook = 'BEARISH ⬇️'
            week_confidence = min(85, 60 + week_bearish * 8)
        else:
            week_outlook = 'NEUTRAL ➡️'
            week_confidence = 55
            
        # Month outlook
        if month_bullish > month_bearish:
            month_outlook = 'BULLISH ⬆️'
            month_confidence = min(80, 55 + month_bullish * 7)
        elif month_bearish > month_bullish:
            month_outlook = 'BEARISH ⬇️'
            month_confidence = min(80, 55 + month_bearish * 7)
        else:
            month_outlook = 'NEUTRAL ➡️'
            month_confidence = 50
            
        self.predictions['next_week'] = {
            'outlook': week_outlook,
            'confidence': week_confidence,
            'factors': weekly_factors
        }
        
        self.predictions['next_month'] = {
            'outlook': month_outlook,
            'confidence': month_confidence,
            'factors': monthly_factors
        }
        
    def display_prediction_dashboard(self):
        """Display comprehensive prediction dashboard"""
        print("\n" + "="*70)
        print("🎯 KHUSI INVEST MODEL - NIFTY PREDICTION DASHBOARD")
        print("="*70)
        print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Latest NIFTY: ₹{self.latest_close:,.2f} ({self.latest_date.strftime('%Y-%m-%d')})")
        
        # Next Day Prediction
        print(f"\n🌅 NEXT DAY PREDICTION")
        print("-" * 30)
        next_day = self.predictions['next_day']
        print(f"Direction: {next_day['direction']}")
        print(f"Confidence: {next_day['confidence']*100:.1f}%")
        print(f"Probability UP: {next_day['probability_up']*100:.1f}%")
        print(f"Probability DOWN: {next_day['probability_down']*100:.1f}%")
        
        if next_day['prediction'] == 1:
            expected_move = self.latest_close * 0.005  # 0.5% expected move
            target_level = self.latest_close + expected_move
            print(f"Expected Target: ₹{target_level:,.2f} (+0.5%)")
        else:
            expected_move = self.latest_close * 0.005
            target_level = self.latest_close - expected_move
            print(f"Expected Target: ₹{target_level:,.2f} (-0.5%)")
            
        # Next Week Outlook
        print(f"\n📅 NEXT WEEK OUTLOOK (5 trading days)")
        print("-" * 40)
        week = self.predictions['next_week']
        print(f"Outlook: {week['outlook']}")
        print(f"Confidence: {week['confidence']:.0f}%")
        print("Key Factors:")
        for factor in week['factors']:
            print(f"  • {factor}")
            
        # Price range estimate
        weekly_volatility = self.current_data['volatility'] * np.sqrt(5)  # Scale to week
        upper_range = self.latest_close * (1 + weekly_volatility/100)
        lower_range = self.latest_close * (1 - weekly_volatility/100)
        print(f"Expected Range: ₹{lower_range:,.0f} - ₹{upper_range:,.0f}")
        
        # Next Month Outlook
        print(f"\n📆 NEXT MONTH OUTLOOK (20 trading days)")
        print("-" * 42)
        month = self.predictions['next_month']
        print(f"Outlook: {month['outlook']}")
        print(f"Confidence: {month['confidence']:.0f}%")
        print("Key Factors:")
        for factor in month['factors']:
            print(f"  • {factor}")
            
        # Monthly range estimate
        monthly_volatility = self.current_data['volatility'] * np.sqrt(20)  # Scale to month
        upper_range_m = self.latest_close * (1 + monthly_volatility/100)
        lower_range_m = self.latest_close * (1 - monthly_volatility/100)
        print(f"Expected Range: ₹{lower_range_m:,.0f} - ₹{upper_range_m:,.0f}")
        
        # Risk levels
        print(f"\n⚠️  RISK ASSESSMENT")
        print("-" * 20)
        current_vol = self.current_data['volatility']
        if current_vol > 25:
            risk_level = "HIGH 🔴"
        elif current_vol > 15:
            risk_level = "MEDIUM 🟡"
        else:
            risk_level = "LOW 🟢"
        print(f"Current Risk Level: {risk_level}")
        print(f"Volatility: {current_vol:.1f}%")
        
        # Market regime
        phase_name = self.current_data['correction_phase_name']
        print(f"Market Regime: {phase_name}")
        
        print("\n" + "="*70)
        print("📝 Note: Predictions based on EMA analysis and ML model")
        print("⚠️  Always combine with fundamental analysis and risk management")
        print("="*70)

def main():
    """Run the prediction dashboard"""
    print("🚀 KHUSI PREDICTION DASHBOARD STARTING...")
    
    try:
        dashboard = KhusiPredictionDashboard()
        
        # Load latest data
        df = dashboard.load_latest_data()
        if df is None:
            print("❌ Error: Cannot load market data")
            return
            
        # Analyze current state
        dashboard.analyze_current_market_state()
        
        # Generate predictions
        if not dashboard.generate_predictions():
            print("❌ Error: Cannot generate predictions")
            return
            
        # Display dashboard
        dashboard.display_prediction_dashboard()
        
        print("\n✅ Dashboard generated successfully!")
        
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()