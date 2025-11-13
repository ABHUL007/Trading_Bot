#!/usr/bin/env python3
"""
Real-time Trading Performance Dashboard
Shows live confluence scores, active trades, and system performance
"""

import sys
sys.path.append('.')

from super_pranni_monitor import get_fixed_monitor
from intelligent_trade_manager import get_trade_manager
import sqlite3
import pandas as pd
from datetime import datetime
import time

def show_live_dashboard():
    """Display live trading dashboard"""
    
    print("\n" + "="*80)
    print("🚀 ENHANCED PRANNI TRADING SYSTEM - LIVE DASHBOARD")
    print("="*80)
    
    # 1. System Status
    monitor = get_fixed_monitor()
    status = monitor.get_live_status()
    
    print(f"\n📊 MARKET STATUS - {datetime.now().strftime('%H:%M:%S')}")
    print(f"   💰 Current Price: ₹{status['current_price']:.2f}")
    print(f"   📏 ATR-14: {status['atr_14']:.2f}")
    print(f"   🔥 Broken Levels: {status['total_broken']}")
    print(f"   📈 Processed Candles: {status['processed_candles']}")
    
    # 2. Broken Levels Summary
    if status['broken_levels']:
        print(f"\n🚨 BROKEN LEVELS ({len(status['broken_levels'])}):")
        for i, level in enumerate(status['broken_levels'], 1):
            print(f"   {i}. {level}")
    else:
        print(f"\n✅ No levels currently broken")
    
    # 3. All Trading Levels with Scores
    print(f"\n📋 ALL TRADING LEVELS:")
    print(f"{'Level':<15} {'High':<8} {'Low':<8} {'H-Prob':<6} {'L-Prob':<6} {'Status':<15}")
    print("-" * 70)
    
    for name, level_data in status['levels'].items():
        high = level_data.get('high', 0)
        low = level_data.get('low', 0)
        high_prob = level_data.get('high_probability', 0)
        low_prob = level_data.get('low_probability', 0)
        high_broken = level_data.get('high_broken', False)
        low_broken = level_data.get('low_broken', False)
        
        if high_broken:
            status_text = "🔥 HIGH BROKEN"
        elif low_broken:
            status_text = "🔥 LOW BROKEN"
        else:
            status_text = "✅ Intact"
        
        print(f"{name:<15} {high:<8.0f} {low:<8.0f} {high_prob:<6.0f}% {low_prob:<6.0f}% {status_text:<15}")
    
    # 4. Latest Breakout Check
    print(f"\n🔍 LIVE BREAKOUT CHECK:")
    breakout = monitor.check_all_breakouts()
    
    if breakout:
        print(f"   🚨 {breakout['type']} DETECTED!")
        print(f"   📊 Level: {breakout['timeframe']} - ₹{breakout['level']:.2f}")
        print(f"   💰 Close Price: ₹{breakout['close_price']:.2f}")
        print(f"   🎯 Probability: {breakout['probability']}%")
        print(f"   📈 Direction: {breakout['direction']}")
        print(f"   ⏰ Candle: {breakout['candle_time']}")
        
        # Test confluence for this breakout
        print(f"\n🔬 CONFLUENCE ANALYSIS:")
        try:
            from enhanced_safe_trader import SafePranniTrader
            trader = SafePranniTrader()
            confluence = trader.validate_confluence_database_only(breakout)
            
            print(f"   🎯 Overall Score: {confluence['confluence_score']:.3f}")
            print(f"   📊 Volume: {confluence['volume_score']:.2f}")
            print(f"   ⚡ Momentum: {confluence['momentum_score']:.2f}")
            print(f"   🎯 Level Strength: {confluence['level_strength_score']:.2f}")
            print(f"   📈 Volatility: {confluence['volatility_score']:.2f}")
            print(f"   🕐 Time Score: {confluence['time_score']:.2f}")
            
            # Determine if trade would be taken
            level_type = breakout.get('level_type', 'unknown')
            base_threshold = 0.55
            
            if level_type == 'previous_day':
                threshold = base_threshold - 0.05
            elif level_type in ['5min_opening', '5min_first']:
                threshold = base_threshold - 0.03
            else:
                threshold = base_threshold
                
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 10:
                threshold -= 0.03
            elif 14 <= current_hour <= 15:
                threshold -= 0.02
                
            threshold = max(0.45, min(0.65, threshold))
            
            if confluence['confluence_score'] >= threshold:
                print(f"   ✅ TRADE APPROVED (Score {confluence['confluence_score']:.3f} > Threshold {threshold:.3f})")
            else:
                print(f"   ❌ TRADE REJECTED (Score {confluence['confluence_score']:.3f} < Threshold {threshold:.3f})")
                
        except Exception as e:
            print(f"   ❌ Error calculating confluence: {e}")
    else:
        print(f"   📈 No active breakouts detected")
    
    # 5. Portfolio Status
    try:
        trade_manager = get_trade_manager()
        portfolio = trade_manager.get_portfolio_status()
        
        print(f"\n💼 PORTFOLIO STATUS:")
        print(f"   🎯 Active Positions: {portfolio['active_positions']}")
        print(f"   💰 Total Risk: ₹{portfolio['total_risk']:.0f}")
        print(f"   📊 Today's P&L: ₹{portfolio['todays_pnl']:.0f}")
        print(f"   📈 Trades Today: {portfolio['trades_today']}")
        
    except Exception as e:
        print(f"\n💼 PORTFOLIO: Unable to fetch ({e})")
    
    # 6. Recent Activity Log
    try:
        conn = sqlite3.connect('NIFTY_15min_data.db')
        recent_data = pd.read_sql_query("""
            SELECT datetime, close, volume 
            FROM data_15min 
            ORDER BY datetime DESC 
            LIMIT 5
        """, conn)
        conn.close()
        
        print(f"\n📈 RECENT 15-MIN CANDLES:")
        for _, row in recent_data.iterrows():
            dt = datetime.strptime(row['datetime'], '%Y-%m-%d %H:%M:%S')
            print(f"   {dt.strftime('%H:%M')} - Close: ₹{row['close']:.2f} | Vol: {row['volume']:,.0f}")
            
    except Exception as e:
        print(f"\n📈 RECENT DATA: Unable to fetch ({e})")

if __name__ == "__main__":
    while True:
        try:
            # Clear screen (Windows)
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            
            show_live_dashboard()
            
            print(f"\n⏰ Last updated: {datetime.now().strftime('%H:%M:%S')} | Refreshing in 30 seconds...")
            print("   Press Ctrl+C to exit")
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print(f"\n👋 Dashboard stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Dashboard error: {e}")
            print("Retrying in 10 seconds...")
            time.sleep(10)