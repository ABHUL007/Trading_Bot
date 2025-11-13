<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Algorithmic Trading Project Instructions

This is a comprehensive algorithmic trading project built with Python. When working on this project, please follow these guidelines:

## Project Structure
- `src/` - Main source code for trading algorithms
- `strategies/` - Trading strategy implementations
- `data/` - Data handling and market data ingestion
- `backtesting/` - Backtesting framework and results
- `risk_management/` - Risk management components
- `portfolio/` - Portfolio management and tracking
- `config/` - Configuration files and settings
- `tests/` - Unit tests and integration tests
- `docs/` - Documentation and research notes

## Development Guidelines
- Use type hints for all function parameters and return values
- Follow PEP 8 style guidelines
- Implement proper error handling and logging
- Use dataclasses for structured data
- Implement comprehensive unit tests
- Use configuration files for all parameters (no hardcoded values)
- Implement proper risk management checks
- Use vectorized operations for performance (numpy, pandas)

## Trading Specific Guidelines
- Always implement paper trading before live trading
- Include position sizing and risk management in all strategies
- Implement proper data validation for market data
- Use proper timestamp handling for backtesting
- Include slippage and transaction costs in backtesting
- Implement proper connection handling for broker APIs
- Log all trades and strategy decisions
- Include performance metrics and reporting

## Security Guidelines
- Never hardcode API keys or sensitive credentials
- Use environment variables for configuration
- Implement proper authentication handling
- Log security events appropriately
- Validate all external data inputs

## Performance Guidelines
- Use efficient data structures (pandas, numpy)
- Implement proper caching for expensive operations
- Use async programming for I/O operations where appropriate
- Profile code for performance bottlenecks
- Implement proper memory management for large datasets