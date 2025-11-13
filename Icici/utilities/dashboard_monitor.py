#!/usr/bin/env python3
"""
Dashboard Monitoring System
Track predictions vs actual results and update dashboard
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

def load_latest_data():
    """Load latest market data"""
    conn = sqlite3.connect('NIFTY_1day_data.db')
    df = pd.read_sql_query(
        "SELECT datetime, open, high, low, close FROM data_1day ORDER BY datetime DESC LIMIT 10", 
        conn
    )
    conn.close()
    return df

def check_predictions():
    """Check prediction accuracy as new data comes in"""
    df = load_latest_data()
    
    print("PREDICTION MONITORING SYSTEM")
    print("=" * 50)
    
    # Current position
    current = df.iloc[0]
    print(f"Latest: {current['datetime']} - Close: {current['close']:,.2f}")
    
    # Nov 4 reference (our prediction base)
    nov4_close = 25597.65
    
    print(f"\nTARGET TRACKING (from Nov 4 base: {nov4_close:,.2f}):")
    print("-" * 50)
    
    # 1-Day targets (Nov 5)
    target_1d_1 = 25750  # +0.6%
    target_1d_2 = 25900  # +1.2%
    stop_1d = 25450      # -0.6%
    
    print(f"1-Day Targets (Nov 5):")
    print(f"  Target 1: {target_1d_1:,} (+0.6%) - {'✅ HIT' if current['close'] >= target_1d_1 else '⏳ PENDING'}")
    print(f"  Target 2: {target_1d_2:,} (+1.2%) - {'✅ HIT' if current['close'] >= target_1d_2 else '⏳ PENDING'}")
    print(f"  Stop Loss: {stop_1d:,} (-0.6%) - {'🚨 HIT' if current['close'] <= stop_1d else '✅ SAFE'}")
    
    # 1-Week targets
    target_1w_1 = 26000  # +1.6%
    target_1w_2 = 26200  # +2.4%
    target_1w_3 = 26400  # +3.1%
    stop_1w = 25300      # -1.2%
    
    print(f"\n1-Week Targets (by Nov 11):")
    print(f"  Target 1: {target_1w_1:,} (+1.6%) - {'✅ HIT' if current['close'] >= target_1w_1 else '⏳ PENDING'}")
    print(f"  Target 2: {target_1w_2:,} (+2.4%) - {'✅ HIT' if current['close'] >= target_1w_2 else '⏳ PENDING'}")
    print(f"  Target 3: {target_1w_3:,} (+3.1%) - {'✅ HIT' if current['close'] >= target_1w_3 else '⏳ PENDING'}")
    print(f"  Stop Loss: {stop_1w:,} (-1.2%) - {'🚨 HIT' if current['close'] <= stop_1w else '✅ SAFE'}")
    
    # 1-Month targets
    target_1m_1 = 24800  # -3.1%
    target_1m_2 = 24500  # -4.3%
    target_1m_3 = 24000  # -6.2%
    
    print(f"\n1-Month Targets (by Dec 4) - BEARISH:")
    print(f"  Target 1: {target_1m_1:,} (-3.1%) - {'⬇️ HIT' if current['close'] <= target_1m_1 else '⏳ PENDING'}")
    print(f"  Target 2: {target_1m_2:,} (-4.3%) - {'⬇️ HIT' if current['close'] <= target_1m_2 else '⏳ PENDING'}")
    print(f"  Target 3: {target_1m_3:,} (-6.2%) - {'⬇️ HIT' if current['close'] <= target_1m_3 else '⏳ PENDING'}")
    
    # Current phase determination
    current_price = current['close']
    
    print(f"\nCURRENT PHASE ANALYSIS:")
    print("-" * 30)
    
    if current_price >= target_1w_1:
        phase = "🔄 Phase 2: PROFIT TAKING"
        action = "Start reducing positions, lock profits"
    elif current_price >= nov4_close * 0.995:  # Within 0.5% of Nov 4
        phase = "📈 Phase 1: ACCUMULATE LONG"
        action = "Continue bullish positioning"
    else:
        phase = "⚠️ Phase 1: REASSESS"
        action = "Monitor for stop loss breach"
    
    print(f"Active Phase: {phase}")
    print(f"Recommended Action: {action}")
    
    # Performance calculation
    current_return = (current_price / nov4_close - 1) * 100
    print(f"\nCurrent P&L from Nov 4: {current_return:+.2f}%")
    
    return {
        'current_price': current_price,
        'current_return': current_return,
        'phase': phase,
        'action': action
    }

def save_monitoring_log():
    """Save monitoring results"""
    results = check_predictions()
    
    # Save to log file
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp},{results['current_price']},{results['current_return']:.2f},{results['phase']},{results['action']}\n"
    
    with open('prediction_monitoring.log', 'a') as f:
        f.write(log_entry)
    
    print(f"\nMonitoring log updated: {timestamp}")

if __name__ == "__main__":
    save_monitoring_log()