"""
Algorithmic Trading Platform
===========================

A comprehensive algorithmic trading platform built with Python.
Supports multiple brokers, strategies, and risk management systems.
"""

__version__ = "1.0.0"
__author__ = "Algo Trading Team"

from src.core.engine import TradingEngine
from src.core.strategy_base import StrategyBase
from src.data.market_data import MarketDataProvider
from src.portfolio.portfolio_manager import PortfolioManager

__all__ = [
    "TradingEngine",
    "StrategyBase", 
    "MarketDataProvider",
    "PortfolioManager"
]