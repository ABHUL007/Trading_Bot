# Algorithmic Trading Platform

A comprehensive Python-based algorithmic trading platform supporting multiple brokers, strategies, and risk management systems.

## Features

- **Multiple Trading Strategies**: Moving Average, Mean Reversion, and custom strategies
- **Broker Integration**: Alpaca, Interactive Brokers, and other major brokers
- **Risk Management**: Portfolio-level and position-level risk controls
- **Backtesting Engine**: Historical strategy testing with performance metrics
- **Real-time Data**: Live market data feeds and processing
- **Portfolio Management**: Position tracking and performance monitoring

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp config/example.env .env
   # Edit .env with your broker credentials
   ```

3. **Run a Backtest**:
   ```bash
   python main.py backtest -s moving_average --start-date 2023-01-01 --end-date 2023-12-31
   ```

4. **Start Paper Trading**:
   ```bash
   python main.py live-trade -s moving_average --paper
   ```

## Project Structure

```
├── src/                    # Core source code
├── strategies/            # Trading strategy implementations
├── data/                  # Data handling and storage
├── backtesting/          # Backtesting framework
├── risk_management/      # Risk management components
├── portfolio/            # Portfolio management
├── config/               # Configuration files
├── tests/                # Unit tests
├── docs/                 # Documentation
└── notebooks/            # Jupyter notebooks for research
```

## Configuration

Copy `config/example.yaml` to `config/default.yaml` and customize:

- Broker credentials
- Strategy parameters
- Risk management settings
- Data sources

## Available Commands

- `python main.py live-trade -s <strategy> [--paper]` - Start live trading
- `python main.py backtest -s <strategy>` - Run backtests
- `python main.py data-collect` - Start data collection
- `python main.py portfolio-status` - View portfolio status

## Development

1. Install development dependencies: `pip install -r requirements-dev.txt`
2. Run tests: `pytest`
3. Format code: `black .`
4. Lint code: `flake8`

## License

MIT License