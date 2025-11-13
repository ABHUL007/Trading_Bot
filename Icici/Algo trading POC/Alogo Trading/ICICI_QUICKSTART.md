# ICICI Direct Breeze Integration - Quick Start Guide

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. ICICI API Setup
1. **Register for ICICI Direct API**:
   - Visit: https://api.icicidirect.com/
   - Register and create an app
   - Note down your `API Key` and `Secret Key`

2. **Run Setup Script**:
   ```bash
   python setup_icici.py
   ```
   
   This script will:
   - Check dependencies
   - Help you configure API credentials
   - Generate session token URL
   - Test the connection

3. **Manual Configuration** (Alternative):
   - Copy `config/example.env` to `.env`
   - Fill in your ICICI credentials:
     ```
     ICICI_API_KEY=your_api_key_here
     ICICI_API_SECRET=your_secret_key_here
     ICICI_SESSION_TOKEN=your_session_token_here
     PAPER_TRADING=true
     ```

### 3. Get Session Token
1. Open the login URL provided by setup script
2. Login with your ICICI Direct credentials
3. Copy the session token from the redirected URL
4. Update your `.env` file or run setup script again

## 🧪 Testing the Integration

### Basic Connection Test
```bash
python test_icici.py
```

This will test:
- ✅ Broker connection
- ✅ Account information retrieval
- ✅ Market data access
- ✅ Order placement (paper trading)
- ✅ Real-time data streaming

### Manual Testing
```python
from src.brokers.icici_breeze_broker import ICICIBreezeBroker
import asyncio

async def test():
    broker = ICICIBreezeBroker(paper_trading=True)
    config = {
        'api_key': 'your_key',
        'api_secret': 'your_secret', 
        'session_token': 'your_token'
    }
    await broker.connect(config)
    account_info = await broker.get_account_info()
    print(account_info)

asyncio.run(test())
```

## 📊 Running Strategies

### 1. Paper Trading (Recommended First)
```bash
# Run with ICICI NIFTY strategy
python main.py live-trade -s icici_nifty_strategy --paper

# Run with moving average strategy  
python main.py live-trade -s moving_average --paper
```

### 2. Backtesting
```bash
python main.py backtest -s icici_nifty_strategy --start-date 2023-01-01 --end-date 2023-12-31
```

### 3. Live Trading (After Testing)
```bash
# Update .env file: PAPER_TRADING=false
python main.py live-trade -s icici_nifty_strategy
```

## 🔧 Configuration

### Key Configuration Files

1. **`.env`** - Credentials and environment variables
2. **`config/icici_breeze.yaml`** - Main configuration
3. **`config/example.env`** - Template for environment variables

### Important Settings

#### Risk Management
```yaml
risk:
  max_position_size: 100000      # Max position in INR
  max_daily_loss: 10000          # Daily loss limit
  max_open_positions: 10         # Max concurrent positions
  position_size_percent: 0.02    # 2% of portfolio per trade
```

#### Broker Settings
```yaml
broker:
  name: icici_breeze
  paper_trading: true            # Always test first!
  requests_per_minute: 100       # API rate limit
  requests_per_day: 5000         # Daily API limit
```

## 📈 Available Strategies

### 1. ICICI NIFTY Strategy (`icici_nifty_strategy`)
- **Focus**: NIFTY and BANKNIFTY futures/options
- **Indicators**: EMA crossover + RSI
- **Timeframe**: Intraday
- **Products**: Futures, Options

### 2. Moving Average Strategy (`moving_average`)
- **Focus**: Multiple symbols
- **Indicators**: SMA crossover
- **Timeframe**: Any
- **Products**: Cash, Futures

## 🔍 Monitoring & Logs

### Log Files
- **Main Log**: `logs/icici_trading.log`
- **Error Log**: Console output
- **Debug**: Set `LOG_LEVEL=DEBUG` in `.env`

### Real-time Monitoring
```bash
# View live logs
tail -f logs/icici_trading.log

# Monitor positions
python main.py portfolio-status
```

## ⚠️ Important Notes

### Before Live Trading
1. **✅ Test with paper trading extensively**
2. **✅ Verify all credentials and permissions**
3. **✅ Check risk management settings**
4. **✅ Understand ICICI API rate limits**
5. **✅ Test during market hours**

### Rate Limits
- **100 API calls per minute**
- **5000 API calls per day**
- Monitor usage to avoid limits

### Session Token
- **Expires**: Session tokens expire (usually 24 hours)
- **Renewal**: Generate new token when needed
- **Automation**: Consider automating token refresh

### Market Data
- **Live Data**: Available during market hours (9:15 AM - 3:30 PM IST)
- **Historical Data**: Available 24/7
- **Symbols**: Use ICICI format (e.g., "NSE.NIFTY")

## 🆘 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check API key and secret
   - Verify session token is not expired
   - Ensure correct URL encoding for special characters

2. **No Market Data**
   - Check if markets are open
   - Verify symbol format
   - Check WebSocket connection

3. **Order Rejected**
   - Verify account permissions
   - Check margin requirements
   - Validate order parameters

4. **Rate Limit Exceeded**
   - Reduce API call frequency
   - Implement proper delays
   - Monitor daily usage

### Getting Help

1. **ICICI Support**: https://api.icicidirect.com/breezeapi/documents/
2. **Logs**: Check `logs/icici_trading.log`
3. **Debug Mode**: Set `DEBUG_MODE=true` in config

## 📚 Next Steps

1. **Familiarize** with ICICI Breeze API documentation
2. **Develop** custom strategies using the framework
3. **Test thoroughly** with paper trading
4. **Monitor** performance and risk metrics
5. **Optimize** strategies based on results

## 🎯 Quick Commands Summary

```bash
# Setup
python setup_icici.py

# Test connection
python test_icici.py

# Paper trading
python main.py live-trade -s icici_nifty_strategy --paper

# Live trading (after testing)
python main.py live-trade -s icici_nifty_strategy

# Portfolio status
python main.py portfolio-status

# Data collection
python main.py data-collect
```

Happy Trading! 🚀📈