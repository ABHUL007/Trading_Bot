#!/usr/bin/env python3
"""
Trading Folder Cleanup Script
- Keeps only ESSENTIAL trading system files
- Moves old/obsolete trading bots to archive
- Preserves databases, logs, and utilities
"""

import os
import shutil
from datetime import datetime

# Essential files to KEEP (current trading system)
ESSENTIAL_FILES = {
    # Core trading system
    'real_trader.py',                    # NEW real trading bot
    'websocket_data_collector.py',      # Data collection
    'super_pranni_monitor.py',          # Signal detection
    'emergency_exit.py',                # Manual exit script
    'start_trading_system.py',          # Unified launcher
    
    # Database setup
    'setup_real_trades_db.py',          # Database migration script
    
    # Launchers
    'START_TRADING_SYSTEM.bat',         # Main launcher
    
    # Configuration
    '.env',
    '.env.example',
    '.gitignore',
    
    # Documentation
    'README.md',
    'LICENSE',
    'requirements.txt',
}

# Old trading bots to ARCHIVE (obsolete)
OLD_TRADING_BOTS = {
    'enhanced_safe_trader.py',          # Old paper trading bot (has OptionsCollector)
    'pranni_paper_trading.py',          # Old paper trading
    'candle_close_optimized_trader.py', # Old version
    'safe_100_api_trader.py',           # Old version
    'enhanced_pranni_detector.py',      # Replaced by super_pranni_monitor.py
    'optimized_15min_strategy.py',      # Old strategy
    'phase1_max_accuracy.py',           # Old version
    'live_options_integration.py',      # Replaced by real_trader.py
    'intelligent_trade_manager.py',     # Old version
}

# Analysis/utility scripts to ARCHIVE (not needed for live trading)
UTILITY_SCRIPTS = {
    'accurate_input_guide.py',
    'add_historical_data.py',
    'add_nov6_daily.py',
    'api_usage_analysis.py',
    'corrected_api_analysis.py',
    'check_bot_activity.py',
    'check_bot_status.py',
    'check_first_candle.py',
    'check_latest_candle.py',
    'check_safe_trades.py',
    'cleanup_workspace.py',
    'daily_startup_check.py',
    'debug_timing.py',
    'ema_distance_theory_analysis.py',
    'ema_distance_theory_simple.py',
    'ema_gap_analysis.py',
    'explain_first_candle.py',
    'explain_trades.py',
    'fix_database.py',
    'force_aggregate_check.py',
    'get_trade_details.py',
    'historical_candle_ema_analysis.py',
    'keep_bots_alive.py',
    'khusi_completion_summary.py',
    'khusi_predictions_summary.py',
    'mathematical_november_prediction.py',
    'max_accuracy_api_strategy.py',
    'micro_movement_analysis.py',
    'next_move_predictions.py',
    'nifty_optimized_summary.py',
    'organize_workspace.py',
    'setup_github.py',
    'show_all_trades.py',
    'show_pranni_levels.py',
    'simple_ema_explanation.py',
    'start_bot.py',
    'status_check.py',
    'system_health_check.py',
    'system_health_monitor.py',
    'system_readiness_test.py',
    'ten_year_ema_analysis.py',
    'tomorrow_checklist.py',
    'update_daily_database.py',
    'validate_trading_inputs.py',
    'verify_first_candle_fix.py',
    'verify_github_ready.py',
    'OPTIONS_COLLECTOR_CHANGES.py',
}

# Old batch files to ARCHIVE
OLD_BATCH_FILES = {
    'AUTO_RESTART_TRADING.bat',         # Old launcher
    'START_TRADING.bat',                # Old launcher
    'STOP_TRADING.bat',                 # Old launcher
    'START_BOTS.ps1',                   # Old launcher
    'Open_Dashboard.bat',               # Dashboard (optional)
    'start_dashboard_server.bat',       # Dashboard (optional)
}

# Documentation files to ARCHIVE (old session notes)
OLD_DOCS = {
    'COMPLETE_GITHUB_GUIDE.md',
    'GITHUB_SETUP.md',
    'INTEGRATION_SUMMARY.md',
    'POST_MARKET_FIX_PLAN.txt',
    'SAVE_CONFIRMATION.txt',
    'SESSION_NOTES_NOV11_2025.md',
    'SESSION_SAVE_20251107_174738.json',
    'SESSION_SAVE_NOV7.py',
    'START_HERE.md',
    'SUNDAY_QUICK_START.md',
    'SYSTEM_DOCUMENTATION.py',
}

# Khusi model files (investment model, not trading)
KHUSI_FILES = {
    'enhanced_khusi_10year.pkl',
    'enhanced_khusi_10year.py',
    'Khusi_Invest_Model.py',
    'khusi_model_daily.pkl',
}


def cleanup_trading_folder():
    """Main cleanup function"""
    print("=" * 80)
    print("🧹 TRADING FOLDER CLEANUP")
    print("=" * 80)
    print()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    archive_dir = os.path.join(base_dir, 'archive', f'cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    
    # Create archive directory
    os.makedirs(archive_dir, exist_ok=True)
    print(f"📁 Archive directory: {archive_dir}")
    print()
    
    moved_count = 0
    
    # Move old trading bots
    print("🤖 Moving old trading bots...")
    for filename in OLD_TRADING_BOTS:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            shutil.move(filepath, os.path.join(archive_dir, filename))
            print(f"   ✅ {filename}")
            moved_count += 1
    print()
    
    # Move utility scripts
    print("🔧 Moving utility/analysis scripts...")
    for filename in UTILITY_SCRIPTS:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            shutil.move(filepath, os.path.join(archive_dir, filename))
            print(f"   ✅ {filename}")
            moved_count += 1
    print()
    
    # Move old batch files
    print("📜 Moving old batch/script files...")
    for filename in OLD_BATCH_FILES:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            shutil.move(filepath, os.path.join(archive_dir, filename))
            print(f"   ✅ {filename}")
            moved_count += 1
    print()
    
    # Move old documentation
    print("📄 Moving old documentation...")
    for filename in OLD_DOCS:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            shutil.move(filepath, os.path.join(archive_dir, filename))
            print(f"   ✅ {filename}")
            moved_count += 1
    print()
    
    # Move Khusi investment files
    print("💼 Moving Khusi investment model files...")
    for filename in KHUSI_FILES:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            shutil.move(filepath, os.path.join(archive_dir, filename))
            print(f"   ✅ {filename}")
            moved_count += 1
    print()
    
    # Summary
    print("=" * 80)
    print(f"✅ CLEANUP COMPLETE!")
    print("=" * 80)
    print(f"📦 Total files archived: {moved_count}")
    print(f"📁 Archive location: {archive_dir}")
    print()
    print("🎯 ESSENTIAL FILES REMAINING:")
    print("   - real_trader.py (Real trading bot)")
    print("   - websocket_data_collector.py (Data collection)")
    print("   - super_pranni_monitor.py (Signal detection)")
    print("   - emergency_exit.py (Manual exit)")
    print("   - start_trading_system.py (Unified launcher)")
    print("   - START_TRADING_SYSTEM.bat (Windows launcher)")
    print()
    print("💾 PRESERVED:")
    print("   - All databases (*.db)")
    print("   - All logs (*.log)")
    print("   - Configuration (.env)")
    print("   - Folders (archive/, dashboards/, logs/, utilities/, .conda/)")
    print("=" * 80)


if __name__ == "__main__":
    try:
        cleanup_trading_folder()
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        print("Files are safe - nothing was deleted, only moved to archive/")
