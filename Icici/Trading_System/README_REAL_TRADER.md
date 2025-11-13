# Real Trader System - High-Level Design (HLD)

## 📋 Overview

The Real Trader System is an automated options trading bot that integrates with ICICI Breeze Connect API to execute live trades on NIFTY options based on breakout signals from the Super Pranni Monitor.

### Key Features
- **Live Trading**: Real-time order placement and execution via ICICI Breeze API
- **Paper Trading Mode**: Simulated trading for testing without risking capital
- **API Rate Limiting**: Safe API manager ensures <95 calls/minute (ICICI limit)
- **Risk Management**: Fixed lot size, target-based exits, and level-based stop-loss
- **On-Demand Pricing**: Fetches option premiums only when needed (no background collection)
- **Automated Monitoring**: Continuous monitoring of open positions with automatic exits

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Real Trader System                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├─────────────────────────┐
                              │                         │
                    ┌─────────▼─────────┐    ┌─────────▼──────────┐
                    │  SafeAPIManager   │    │  FixedPranniMonitor│
                    │  (Rate Limiting)  │    │  (Signal Detection)│
                    └─────────┬─────────┘    └─────────┬──────────┘
                              │                         │
                              └──────────┬──────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   Breeze Connect    │
                              │   (ICICI API)       │
                              └──────────┬──────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
          ┌─────────▼─────────┐  ┌──────▼──────┐  ┌─────────▼─────────┐
          │  Order Placement  │  │ Get Quotes  │  │   Square Off      │
          │  (Entry Trades)   │  │ (Live LTP)  │  │  (Exit Trades)    │
          └─────────┬─────────┘  └──────┬──────┘  └─────────┬─────────┘
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   SQLite Database   │
                              │  (paper_trades.db)  │
                              └─────────────────────┘
```

---

## 🔧 Core Components

### 1. **RealTrader (Main Controller)**
**Purpose**: Orchestrates the entire trading lifecycle

**Responsibilities**:
- Initialize trading session
- Connect to Breeze API
- Monitor market hours
- Execute trading loop
- Coordinate between signal detection and order execution

**Key Methods**:
- `run_trading_session()`: Main event loop (checks every 15 seconds)
- `connect_to_breeze()`: Establish API connection (live or paper mode)
- `is_market_hours()`: Validate trading time (9:15 AM - 3:30 PM)

---

### 2. **SafeAPIManager (Rate Limiter)**
**Purpose**: Prevent API rate limit violations (ICICI limit: 95 calls/minute)

**Features**:
- Tracks all API calls in rolling 60-second window
- Automatic throttling when approaching limit
- Call history using `deque` for efficient time-based filtering
- Real-time usage statistics

**Key Methods**:
- `can_make_api_call()`: Check if call is safe
- `record_api_call()`: Log each API invocation
- `safe_api_call()`: Wrapper with automatic throttling
- `get_usage_stats()`: Real-time API usage metrics

**Data Structure**:
```python
call_history: deque()  # Rolling window of timestamps
max_calls_per_minute: 95
total_session_calls: int
```

---

### 3. **FixedPranniMonitor (Signal Generator)**
**Purpose**: Detect breakout signals from 15-minute NIFTY data

**Integration**:
- External module: `super_pranni_monitor.py`
- Analyzes price levels and breakout patterns
- Provides confluence scores and probability metrics

**Signal Structure**:
```python
{
    'timeframe': '15min',
    'level': 24500.00,
    'direction': 'CALL' or 'PUT',
    'type': 'breakout',
    'probability': 85,
    'close_price': 24512.50,
    'confluence_score': 3
}
```

---

## 📊 Trading Logic

### Entry Conditions
1. **Signal Detection**: FixedPranniMonitor identifies breakout
2. **Market Hours**: Current time between 9:15 AM - 3:30 PM
3. **Strike Selection**: Round NIFTY price to nearest 100
4. **Premium Check**: Fetch current option LTP via `get_quotes()`
5. **Order Placement**: Market order via `place_order()`

### Position Monitoring
**Continuous Loop** (every 15 seconds):
1. Fetch current premium for each open trade
2. Calculate real-time P&L
3. Check exit conditions (target or stop-loss)

### Exit Conditions

#### **Target Exit** (₹10 Profit/Lot)
```python
if current_premium - entry_premium >= 10:
    exit_trade(reason="TARGET")
```

#### **Level-Based Stop-Loss**
- **For CALL**: Exit if 2 consecutive 5-min candles close BELOW breakout level
- **For PUT**: Exit if 2 consecutive 5-min candles close ABOVE breakout level

```python
# Example: CALL trade with breakout at 24500
Candle 1: Close = 24480  # Below 24500
Candle 2: Close = 24470  # Below 24500
→ Trigger STOP_LOSS_LEVEL exit
```

---

## 🗄️ Database Schema

### Table: `real_trades`
```sql
CREATE TABLE real_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    strike INTEGER NOT NULL,
    direction TEXT NOT NULL,  -- 'CALL' or 'PUT'
    entry_premium REAL NOT NULL,
    exit_premium REAL,
    quantity INTEGER NOT NULL,  -- 75 (lot size)
    breakout_level REAL NOT NULL,
    confluence_score INTEGER,
    order_id TEXT,  -- Entry order ID
    entry_order_status TEXT,
    exit_order_id TEXT,
    exit_order_status TEXT,
    status TEXT NOT NULL,  -- 'OPEN' or 'CLOSED'
    exit_timestamp TEXT,
    pnl REAL,
    exit_reason TEXT,  -- 'TARGET', 'STOP_LOSS_LEVEL'
    sl_candle_count INTEGER DEFAULT 0,
    last_sl_check_time TEXT
);
```

---

## 🔌 API Integration

### Breeze Connect Methods Used

#### 1. **place_order()**
```python
breeze.place_order(
    stock_code="NIFTY",
    exchange_code="NFO",
    product="options",
    action="buy",
    order_type="market",
    quantity="75",
    expiry_date="2025-11-14T06:00:00.000Z",
    right="call" or "put",
    strike_price="24500",
    validity="day"
)
```

#### 2. **get_quotes()** (On-Demand Pricing)
```python
breeze.get_quotes(
    stock_code="NIFTY",
    exchange_code="NFO",
    expiry_date="2025-11-14T06:00:00.000Z",
    product_type="options",
    right="call" or "put",
    strike_price="24500"
)
# Returns: {'Success': [{'ltp': 125.50}]}
```

#### 3. **square_off()** (Exit Position)
```python
breeze.square_off(
    exchange_code="NFO",
    product="options",
    stock_code="NIFTY",
    expiry_date="2025-11-14T06:00:00.000Z",
    right="call" or "put",
    strike_price="24500",
    action="sell",
    order_type="market",
    quantity="75"
)
```

#### 4. **get_order_detail()** (Verify Execution)
```python
breeze.get_order_detail(
    exchange_code="NFO",
    order_id="20251113001"
)
# Returns: {'Success': [{'status': 'Executed'}]}
```

---

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# API Credentials
ICICI_API_KEY=your_api_key_here
ICICI_API_SECRET=your_api_secret_here
ICICI_SESSION_TOKEN=your_session_token_here

# Trading Mode
PAPER_TRADING=true  # Set to 'false' for live trading
```

### Trading Parameters
```python
lot_size = 75  # NIFTY lot size
target_per_lot = 10  # ₹10 profit target
sl_consecutive_candles = 1  # Stop-loss trigger threshold
```

---

## 🔄 Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  START: run_trading_session()                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ Connect to Breeze API │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Check Market Hours   │
         └───────────┬───────────┘
                     │
                     ├─── Market Closed ──► Wait 60s ──┐
                     │                                  │
                     ▼                                  │
         ┌───────────────────────┐                     │
         │ Monitor Open Trades   │                     │
         └───────────┬───────────┘                     │
                     │                                  │
                     ├─── Target Hit ──► Exit Trade    │
                     ├─── Stop-Loss ───► Exit Trade    │
                     │                                  │
                     ▼                                  │
         ┌───────────────────────┐                     │
         │ Check for New Signals │                     │
         └───────────┬───────────┘                     │
                     │                                  │
                     ├─── No Signal ──► Wait 15s ──────┤
                     │                                  │
                     ▼                                  │
         ┌───────────────────────┐                     │
         │  Signal Detected!     │                     │
         └───────────┬───────────┘                     │
                     │                                  │
                     ▼                                  │
         ┌───────────────────────┐                     │
         │  Calculate Strike     │                     │
         └───────────┬───────────┘                     │
                     │                                  │
                     ▼                                  │
         ┌───────────────────────┐                     │
         │  Get Option Premium   │                     │
         └───────────┬───────────┘                     │
                     │                                  │
                     ▼                                  │
         ┌───────────────────────┐                     │
         │   Place Order (BUY)   │                     │
         └───────────┬───────────┘                     │
                     │                                  │
                     ▼                                  │
         ┌───────────────────────┐                     │
         │   Save to Database    │                     │
         └───────────┬───────────┘                     │
                     │                                  │
                     ▼                                  │
         ┌───────────────────────┐                     │
         │    Wait 15 Seconds    │                     │
         └───────────┬───────────┘                     │
                     │                                  │
                     └──────────────────────────────────┘
```

---

## 📈 Performance Metrics

### API Usage Tracking
```python
stats = {
    'current_minute_usage': 12,      # Calls in last 60 seconds
    'remaining_calls': 83,           # Available in this minute
    'usage_percentage': 12.6,        # % of limit used
    'total_session_calls': 1247,    # Total since bot start
    'is_safe': True                  # Below 90% threshold
}
```

### Trade Metrics (Logged)
- Entry/Exit timestamps
- Entry/Exit premiums
- P&L per trade
- Strike and direction
- Order IDs and statuses
- Exit reasons (TARGET/STOP_LOSS_LEVEL)

---

## 🛡️ Risk Management

### Position Sizing
- **Fixed Lot Size**: 75 (1 NIFTY lot)
- **Max Positions**: Limited by signal frequency (typically 1-2 per session)

### Loss Prevention
1. **Level-Based Stop-Loss**: Exits on sustained price reversal
2. **No Martingale**: Single lot per signal (no averaging down)
3. **API Safety**: Rate limiter prevents API blocks

### Capital Protection
- **Quick Target**: ₹10/lot = ₹750 profit per trade
- **Defined Risk**: Stop-loss based on technical levels, not arbitrary points

---

## 🚀 Usage

### Start Trading Bot
```bash
# Paper trading (default)
python real_trader.py

# Live trading (requires .env configuration)
# Set PAPER_TRADING=false in .env
python real_trader.py
```

### Monitor Logs
```bash
# Real-time log file
tail -f real_trader.log

# Console output shows:
# - API usage statistics
# - Signal detections
# - Order placements
# - Position monitoring
# - Exit triggers
```

---

## 📝 Logging

### Log Levels
- **INFO**: Normal operations (signals, orders, exits)
- **WARNING**: API throttling, missing data
- **ERROR**: API failures, order errors
- **DEBUG**: Detailed price checks, candle analysis

### Log Rotation
- **Max File Size**: 10 MB
- **Backup Count**: 5 files
- **Encoding**: UTF-8 (supports ₹ symbol)

---

## 🔍 Troubleshooting

### Common Issues

#### 1. API Connection Failed
```
❌ Breeze connection failed: Invalid session token
```
**Solution**: Regenerate session token from ICICI Breeze portal

#### 2. Module Not Found
```
ModuleNotFoundError: No module named 'pandas'
```
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

#### 3. Database Locked
```
sqlite3.OperationalError: database is locked
```
**Solution**: Close other programs accessing the database

#### 4. API Rate Limit Hit
```
⚠️ API limit reached: 95/95
```
**Solution**: Bot automatically throttles; wait for next minute window

---

## 🔐 Security Best Practices

1. **Never Commit .env**: Add to `.gitignore`
2. **Rotate Tokens**: Regenerate session tokens regularly
3. **Monitor Logs**: Review `real_trader.log` daily
4. **Start with Paper Trading**: Test strategies before live trading
5. **Backup Database**: Regular backups of `paper_trades.db`

---

## 📚 Dependencies

```
breeze-connect>=1.0.0      # ICICI Breeze API
pandas>=2.0.0              # Data manipulation
numpy>=1.24.0              # Numerical operations
python-dotenv>=1.0.0       # Environment management
asyncio>=3.4.3             # Async operations
```

---

## 🔮 Future Enhancements

1. **Multi-Symbol Support**: Trade BANKNIFTY, FINNIFTY
2. **Advanced Stop-Loss**: Trailing stop-loss based on ATR
3. **Web Dashboard**: Real-time position monitoring via web UI
4. **Telegram Alerts**: Instant notifications on signal/exit
5. **Backtesting Module**: Historical performance analysis
6. **Position Scaling**: Multiple lots based on signal strength

---

## 📞 Support

For issues or questions:
- Check logs: `real_trader.log`
- Review database: `paper_trades.db`
- Verify API credentials in `.env`
- Test in paper trading mode first

---

## ⚖️ Disclaimer

**This is an automated trading system. Trading involves risk of loss. Use at your own discretion.**

- Start with paper trading
- Understand the strategy before live deployment
- Monitor positions regularly
- Keep API credentials secure
- Follow exchange regulations

---

*Last Updated: November 13, 2025*
