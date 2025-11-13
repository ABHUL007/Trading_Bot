#!/usr/bin/env python3
"""
Khusi Model - Today, Weekly, Monthly Predictions
"""

import sys
import os
import pickle
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Change to Khusi model directory
os.chdir(os.path.join(os.path.dirname(__file__), 'Khusi_Investment_Model'))

print("\n" + "="*80)
print("🔮 KHUSI MODEL - MARKET PREDICTIONS")
print("="*80)
print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

# Load the trained model
try:
    with open('enhanced_khusi_10year.pkl', 'rb') as f:
        model_data = pickle.load(f)
        model = model_data['model']
        feature_cols = model_data['feature_cols']
        print("✅ Loaded Enhanced Khusi 10-Year Model")
except:
    print("⚠️  Enhanced model not found, trying daily model...")
    try:
        with open('khusi_model_daily.pkl', 'rb') as f:
            model_data = pickle.load(f)
            model = model_data['model']
            feature_cols = model_data['feature_cols']
            print("✅ Loaded Khusi Daily Model")
    except:
        print("❌ No trained model found. Please train model first.")
        exit(1)

# Load latest data from database
db_path = '../NIFTY_1day_data.db'
conn = sqlite3.connect(db_path)

print(f"\n📊 Loading latest market data from database...")
query = """
SELECT datetime, open, high, low, close, volume
FROM data_1day
ORDER BY datetime DESC
LIMIT 250
"""
df = pd.read_sql_query(query, conn)
conn.close()

df = df.sort_values('datetime')
df['datetime'] = pd.to_datetime(df['datetime'])
print(f"✅ Loaded {len(df)} days of data")

# Calculate EMAs
ema_periods = [5, 9, 21, 50, 100, 200]
print(f"\n📈 Calculating EMAs: {ema_periods}")

for period in ema_periods:
    df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()

# Calculate EMA distances
df['ema_dist_100_200'] = ((df['ema_100'] - df['ema_200']) / df['ema_200']) * 100
df['ema_dist_50_100'] = ((df['ema_50'] - df['ema_100']) / df['ema_100']) * 100
df['ema_dist_21_50'] = ((df['ema_21'] - df['ema_50']) / df['ema_50']) * 100

# Calculate RSI
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi_14'] = calculate_rsi(df['close'], 14)

# Calculate momentum indicators
df['momentum_5'] = df['close'].pct_change(5) * 100
df['momentum_10'] = df['close'].pct_change(10) * 100
df['momentum_20'] = df['close'].pct_change(20) * 100

# Volume analysis
df['volume_ma_20'] = df['volume'].rolling(20).mean()
df['volume_ratio'] = df['volume'] / df['volume_ma_20']

# Current values
latest = df.iloc[-1]
current_price = latest['close']

print(f"\n📊 CURRENT MARKET STATUS")
print("-" * 80)
print(f"   Price: ₹{current_price:,.2f}")
print(f"   EMA 50: ₹{latest['ema_50']:,.2f} ({((current_price/latest['ema_50']-1)*100):+.2f}%)")
print(f"   EMA 200: ₹{latest['ema_200']:,.2f} ({((current_price/latest['ema_200']-1)*100):+.2f}%)")
print(f"   RSI-14: {latest['rsi_14']:.1f}")
print(f"   EMA 100-200 Distance: {latest['ema_dist_100_200']:.3f}%")

# Critical threshold check
critical_threshold = 2.08
if latest['ema_dist_100_200'] >= critical_threshold:
    print(f"   ⚠️  CRITICAL: Distance {latest['ema_dist_100_200']:.3f}% >= {critical_threshold}% threshold!")
else:
    distance_to_critical = critical_threshold - latest['ema_dist_100_200']
    print(f"   ✅ Distance to critical: {distance_to_critical:.3f}%")

# Prepare features for prediction
feature_data = latest[feature_cols].values.reshape(1, -1)

# Make predictions
pred_class = model.predict(feature_data)[0]
pred_proba = model.predict_proba(feature_data)[0]

direction = "📈 BULLISH" if pred_class == 1 else "📉 BEARISH"
confidence = max(pred_proba) * 100

print(f"\n🎯 TODAY'S PREDICTION")
print("-" * 80)
print(f"   Direction: {direction}")
print(f"   Confidence: {confidence:.1f}%")
if pred_class == 1:
    print(f"   Probability UP: {pred_proba[1]*100:.1f}%")
else:
    print(f"   Probability DOWN: {pred_proba[0]*100:.1f}%")

# Weekly prediction (5-day momentum + trend)
weekly_momentum = latest['momentum_5']
weekly_ema_trend = ((latest['ema_21'] - latest['ema_50']) / latest['ema_50']) * 100

print(f"\n📅 WEEKLY OUTLOOK (Next 5-7 Days)")
print("-" * 80)
print(f"   5-Day Momentum: {weekly_momentum:+.2f}%")
print(f"   Short-term EMA Trend: {weekly_ema_trend:+.2f}%")

if weekly_ema_trend > 0 and weekly_momentum > 0:
    print(f"   Direction: 📈 BULLISH")
    print(f"   Expected: Continuation of uptrend")
elif weekly_ema_trend < 0 and weekly_momentum < 0:
    print(f"   Direction: 📉 BEARISH")
    print(f"   Expected: Continuation of downtrend")
else:
    print(f"   Direction: ↔️ MIXED/SIDEWAYS")
    print(f"   Expected: Consolidation or reversal")

# Calculate weekly targets
weekly_high_target = current_price * 1.02
weekly_low_target = current_price * 0.98
print(f"   Potential Range: ₹{weekly_low_target:,.0f} - ₹{weekly_high_target:,.0f}")

# Monthly prediction (20-day momentum + medium-term trend)
monthly_momentum = latest['momentum_20']
monthly_ema_trend = ((latest['ema_50'] - latest['ema_100']) / latest['ema_100']) * 100

print(f"\n📆 MONTHLY OUTLOOK (Next 20-30 Days)")
print("-" * 80)
print(f"   20-Day Momentum: {monthly_momentum:+.2f}%")
print(f"   Medium-term EMA Trend: {monthly_ema_trend:+.2f}%")

if monthly_ema_trend > 0.5:
    print(f"   Direction: 📈 BULLISH")
    monthly_target = latest['ema_50'] * 1.05
    print(f"   Target: ₹{monthly_target:,.0f} (+5% from EMA 50)")
elif monthly_ema_trend < -0.5:
    print(f"   Direction: 📉 BEARISH")
    monthly_target = latest['ema_100'] * 0.98
    print(f"   Support: ₹{monthly_target:,.0f} (Near EMA 100)")
else:
    print(f"   Direction: ↔️ CONSOLIDATION")
    print(f"   Range: ₹{latest['ema_50']:,.0f} - ₹{latest['ema_100']:,.0f}")

# Key levels for month
monthly_high_target = current_price * 1.05
monthly_low_target = current_price * 0.95
print(f"   Potential Range: ₹{monthly_low_target:,.0f} - ₹{monthly_high_target:,.0f}")

# Critical analysis
print(f"\n⚠️  RISK ANALYSIS")
print("-" * 80)

risk_factors = []
if latest['rsi_14'] > 70:
    risk_factors.append("🔴 RSI Overbought (>70) - Correction risk")
elif latest['rsi_14'] < 30:
    risk_factors.append("🟢 RSI Oversold (<30) - Bounce opportunity")

if latest['ema_dist_100_200'] > critical_threshold * 0.9:
    risk_factors.append(f"🔴 Near critical threshold - Major correction risk")

if latest['ema_dist_50_100'] > 3.0:
    risk_factors.append("🟡 Short-term overextension - Pullback likely")

if abs(latest['momentum_5']) > 5:
    risk_factors.append(f"🟡 High 5-day momentum ({latest['momentum_5']:+.1f}%) - Reversal watch")

if risk_factors:
    for factor in risk_factors:
        print(f"   {factor}")
else:
    print(f"   ✅ No major risk factors detected")

# Trading recommendations
print(f"\n💡 TRADING RECOMMENDATIONS")
print("-" * 80)

if pred_class == 1 and latest['rsi_14'] < 60:
    print(f"   ✅ LONG BIAS: Price above EMA 50, RSI healthy")
    print(f"   Entry: ₹{current_price:,.0f}")
    print(f"   Target: ₹{current_price * 1.02:,.0f} (2%)")
    print(f"   Stop: ₹{latest['ema_21']:,.0f} (EMA 21)")
elif pred_class == 0 and latest['rsi_14'] > 40:
    print(f"   ✅ SHORT BIAS: Bearish indicators present")
    print(f"   Entry: ₹{current_price:,.0f}")
    print(f"   Target: ₹{current_price * 0.98:,.0f} (-2%)")
    print(f"   Stop: ₹{latest['ema_21']:,.0f} (EMA 21)")
else:
    print(f"   ⚠️ WAIT: Mixed signals or overbought/oversold conditions")
    print(f"   Strategy: Wait for clearer setup")

print("\n" + "="*80)
print("✅ KHUSI MODEL PREDICTION COMPLETE")
print("="*80 + "\n")
