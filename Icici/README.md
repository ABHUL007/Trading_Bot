# ICICI Algo Trading - Complete System

Organized workspace for NIFTY algorithmic trading and investment analysis.

## 📁 Project Structure

```
d:\Algo Trading\Icici\
│
├── 🤖 Trading_System/              ← Real Trading Bot
│   ├── real_trader.py              (Main trading bot)
│   ├── websocket_data_collector.py (Live data collection)
│   ├── super_pranni_monitor.py     (Signal detection)
│   ├── emergency_exit.py           (Manual exit)
│   ├── START_TRADING_SYSTEM.bat    (👈 Start trading here!)
│   └── README.md                   (Trading system docs)
│
├── 💼 Khusi_Investment_Model/      ← Investment Model
│   ├── Khusi_Invest_Model.py       (Main model)
│   ├── enhanced_khusi_10year.py    (10-year analysis)
│   └── README.md                   (Investment docs)
│
├── 💾 Databases/
│   ├── NIFTY_5min_data.db          (5-min candles)
│   ├── NIFTY_15min_data.db         (15-min candles)
│   ├── NIFTY_1hour_data.db         (1-hour candles)
│   ├── NIFTY_1day_data.db          (Daily candles)
│   └── paper_trades.db             (Trade records)
│
├── 📦 archive/                     (Old files safely stored)
├── 📊 dashboards/                  (Optional dashboards)
├── 📝 logs/                        (System logs)
└── ⚙️  .env                        (Configuration)
```

## 🚀 Quick Start

### Option 1: Main Launcher
Double-click: `START_MAIN.bat`

Choose:
1. Trading System (Real trading bot)
2. Khusi Investment Model

### Option 2: Direct Trading
Navigate to `Trading_System/` and double-click `START_TRADING_SYSTEM.bat`

## 📋 Prerequisites

- Python 3.10+
- Anaconda/Miniconda
- ICICI Breeze Trading Account
- API credentials (API Key, Secret, Session Token)

## 🚀 Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/nifty-algo-trading.git
cd nifty-algo-trading
```

2. **Create conda environment**
```bash
conda create -p ./.conda python=3.10 -y
conda activate ./.conda
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file in the root directory:
```env
ICICI_API_KEY=your_api_key_here
ICICI_API_SECRET=your_api_secret_here
ICICI_SESSION_TOKEN=your_session_token_here
```

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  NIFTY ALGO TRADING SYSTEM                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  websocket_data_collector.py    enhanced_safe_trader.py   │
│  (Data Collection)               (Trading Bot)              │
│          ↓                              ↓                   │
│    NIFTY Data via                 ┌──────────────┐         │
│    WebSocket/API                  │ Super Pranni │         │
│          ↓                        │   Monitor    │         │
│   SQLite Databases                └──────────────┘         │
│   - 5min, 15min                          ↓                 │
│   - 1hour, 1day                   ┌──────────────┐         │
│                                   │   Options    │         │
│                                   │  Collector   │         │
│                                   │ (Dynamic)    │         │
│                                   └──────────────┘         │
│                                          ↓                 │
│                                   Paper Trading            │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Usage

### Start Both Components

**Terminal 1: WebSocket Data Collector**
```bash
conda activate ./.conda
python websocket_data_collector.py
```

**Terminal 2: Trading Bot**
```bash
conda activate ./.conda
python enhanced_safe_trader.py
```

### Best Practice
Start both processes at or before **9:15 AM** (market open) to catch all signals.

## 📁 Project Structure

```
nifty-algo-trading/
├── .env                              # API credentials (DO NOT COMMIT)
├── .gitignore                        # Git ignore file
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── enhanced_safe_trader.py          # Main trading bot
├── websocket_data_collector.py      # Data collection script
├── super_pranni_monitor.py          # Breakout detection logic
├── start_bot.py                     # Bot startup script
├── logs/                            # Log files
├── *.db                             # SQLite databases (auto-created)
└── archive/                         # Archived/old files
```

## ⚙️ Configuration

### Dynamic Options Timing
- **PRE-TRADE**: Updates every 15 minutes + 3 seconds (latest data before trade)
- **POST-TRADE**: Updates every 1 minute (exit monitoring when position open)

### API Limits
- **Hard limit**: 95 API calls per minute
- **Safety buffer**: 5 calls
- **Real-time monitoring**: Automatic throttling

### Trading Parameters
- **Timeframes**: 15-minute breakouts (primary)
- **Confluence**: Multi-timeframe validation
- **Strike Selection**: Liquid 100s strikes only (25500, 25600, etc.)
- **Lot Size**: 75 (configurable)

## 🗃️ Database Schema

### NIFTY Data Tables
- `NIFTY_5min_data.db` → `data_5min`
- `NIFTY_15min_data.db` → `data_15min`
- `NIFTY_1hour_data.db` → `data_1hour`
- `NIFTY_1day_data.db` → `data_1day`

### Options Data
- `options_data.db` → `options_data`
  - Strike price, option type (CE/PE)
  - LTP, bid, ask, volume, OI
  - Timestamp

### Paper Trades
- `paper_trades.db` → `paper_trades`
  - Entry/exit prices
  - P&L tracking
  - Status (OPEN/CLOSED)

## 🎯 Trading Logic

### Fresh Breakout Detection
1. **Opening Range**: First 15-min candle high/low
2. **Previous Day**: Yesterday's high/low
3. **Multi-Week**: 1-week, 2-week levels
4. **Fresh Rule**: Previous candle ≤ level AND current candle > level

### Entry Conditions
- Fresh breakout within 5 minutes of candle completion
- Multi-timeframe confluence
- Liquid strikes selection
- API budget available

### Exit Strategy
- Target 1: +12 points
- Target 2: +24 points
- Stop Loss: -6 points

## 📈 Performance Monitoring

Check logs in real-time:
- `logs/paper_trading.log` - Trade execution logs
- `logs/websocketLogs_*.log` - Data collection logs
- `logs/apiLogs_*.log` - API call logs

## 🔒 Security

⚠️ **IMPORTANT**: Never commit your `.env` file with API credentials!

The `.gitignore` file is configured to exclude:
- `.env` files
- Database files (*.db)
- Log files
- Conda environment
- Sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Changelog

### v1.0.0 (Current)
- ✅ WebSocket data collection with 5-min intervals
- ✅ Multi-timeframe aggregation (15-min, 1-hour, daily)
- ✅ Fresh breakout detection (Super Pranni Monitor)
- ✅ Dynamic options collection timing
- ✅ API safety with 95 calls/minute limit
- ✅ Paper trading with P&L tracking
- ✅ Liquid 100s strike selection

## ⚠️ Disclaimer

This software is for educational purposes only. Trading involves substantial risk of loss. Past performance does not guarantee future results. Use at your own risk.

## 📄 License

MIT License - See LICENSE file for details

## 📧 Contact

For questions or suggestions, please open an issue on GitHub.

---

**Happy Trading! 🚀📈**
