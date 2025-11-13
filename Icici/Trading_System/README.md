# 🤖 Real Trading System

Complete automated trading system for NIFTY options using Super Pranni signals.

## 📁 Files

### Core System
- **real_trader.py** - Main trading bot (executes real trades via Breeze API)
- **websocket_data_collector.py** - Live NIFTY data collection
- **super_pranni_monitor.py** - Super Pranni signal detection
- **emergency_exit.py** - Manual exit script for all positions

### Launchers
- **START_TRADING_SYSTEM.bat** - Double-click to start everything!
- **start_trading_system.py** - Python launcher (starts both collector + trader)

### Setup
- **setup_real_trades_db.py** - Database migration (already executed)

## 🚀 Quick Start

### 1. Start Trading System
Double-click: `START_TRADING_SYSTEM.bat`

Or run from PowerShell:
```powershell
.\START_TRADING_SYSTEM.bat
```

### 2. Emergency Exit (if needed)
```powershell
conda run -p "../.conda" python emergency_exit.py
```

## ⚙️ Configuration

Configuration file: `../.env`

**IMPORTANT:** Set `PAPER_TRADING=false` for live trading (currently `true` for testing)

## 📊 Trading Parameters

- **Instrument:** NIFTY Options (Nearest 100s strike)
- **Lot Size:** 75 quantity (1 lot)
- **Target:** ₹10 per lot (immediate exit)
- **Stop-Loss:** 2 consecutive 5-min candles closing against breakout level
- **Signal:** Super Pranni 15-min breakout detection

## 💾 Databases Used

- `../NIFTY_5min_data.db` - 5-minute candles (for SL)
- `../NIFTY_15min_data.db` - 15-minute candles (for signals)
- `../paper_trades.db` - Trade records (real_trades table)

## 📝 Logs

- `trading_system.log` - System launcher logs
- `websocket_data_collector.log` - Data collection logs
- `real_trader.log` - Trading bot logs

## 🔄 System Flow

```
websocket_data_collector.py
    ↓ (populates databases)
NIFTY_5min_data.db & NIFTY_15min_data.db
    ↓ (reads for signals)
super_pranni_monitor.py
    ↓ (generates signals)
real_trader.py
    ↓ (executes via Breeze API)
Real Orders → Monitor → Exit
```

## ⚠️ Safety Features

- PAPER_TRADING mode for testing
- API rate limiting (95 calls/minute)
- Order verification after placement
- Auto-restart on crash
- Emergency exit with confirmation
- Complete audit trail (order IDs tracked)

## 📞 Support

Check logs for any issues:
- Real-time: Console output
- Historical: `*.log` files in this folder
