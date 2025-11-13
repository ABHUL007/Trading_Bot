"""
Core trading engine that orchestrates the entire trading system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.core.config import Config
from src.core.strategy_base import StrategyBase
from src.data.market_data import MarketDataProvider
from src.portfolio.portfolio_manager import PortfolioManager
from src.risk_management.risk_manager import RiskManager
from src.brokers.broker_interface import BrokerInterface
from src.utils.events import EventManager, Event


logger = logging.getLogger(__name__)


class TradingEngine:
    """
    Main trading engine that coordinates all components of the trading system.
    """
    
    def __init__(self):
        self.config = Config()
        self.event_manager = EventManager()
        self.market_data = MarketDataProvider()
        self.portfolio_manager = PortfolioManager()
        self.risk_manager = RiskManager()
        
        self.strategies: Dict[str, StrategyBase] = {}
        self.broker: Optional[BrokerInterface] = None
        self.is_running = False
        
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers for the trading engine."""
        self.event_manager.subscribe('market_data', self._on_market_data)
        self.event_manager.subscribe('signal', self._on_signal)
        self.event_manager.subscribe('order_filled', self._on_order_filled)
        self.event_manager.subscribe('risk_violation', self._on_risk_violation)
    
    async def start(self, strategy_name: str, paper_trading: bool = True):
        """
        Start the trading engine with a specific strategy.
        
        Args:
            strategy_name: Name of the strategy to run
            paper_trading: Whether to run in paper trading mode
        """
        logger.info(f"Starting trading engine with strategy: {strategy_name}")
        logger.info(f"Paper trading mode: {paper_trading}")
        
        try:
            # Initialize broker
            await self._initialize_broker(paper_trading)
            
            # Load and initialize strategy
            await self._load_strategy(strategy_name)
            
            # Start market data feed
            await self.market_data.start()
            
            # Start the main trading loop
            self.is_running = True
            await self._run_trading_loop()
            
        except Exception as e:
            logger.error(f"Error in trading engine: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the trading engine and cleanup resources."""
        logger.info("Stopping trading engine...")
        
        self.is_running = False
        
        # Stop market data feed
        if self.market_data:
            await self.market_data.stop()
        
        # Close broker connections
        if self.broker:
            await self.broker.disconnect()
        
        logger.info("Trading engine stopped")
    
    async def _initialize_broker(self, paper_trading: bool):
        """Initialize the broker connection."""
        broker_name = self.config.get('broker.name', 'icici_breeze')
        
        if broker_name == 'icici_breeze':
            from src.brokers.icici_breeze_broker import ICICIBreezeBroker
            self.broker = ICICIBreezeBroker(paper_trading=paper_trading)
            
            # Get broker configuration
            broker_config = {
                'api_key': self.config.get('broker.api_key'),
                'api_secret': self.config.get('broker.api_secret'),
                'session_token': self.config.get('broker.session_token')
            }
            
        elif broker_name == 'alpaca':
            from src.brokers.alpaca_broker import AlpacaBroker
            self.broker = AlpacaBroker(paper_trading=paper_trading)
            broker_config = {}
        elif broker_name == 'interactive_brokers':
            from src.brokers.ib_broker import IBBroker
            self.broker = IBBroker(paper_trading=paper_trading)
            broker_config = {}
        else:
            raise ValueError(f"Unsupported broker: {broker_name}")
        
        # Set event manager for the broker
        self.broker.set_event_manager(self.event_manager)
        
        # Connect to broker
        await self.broker.connect(broker_config)
        logger.info(f"Connected to {broker_name} broker")
    
    async def _load_strategy(self, strategy_name: str):
        """Load and initialize a trading strategy."""
        # Dynamic strategy loading would go here
        # For now, we'll use a simple mapping
        
        if strategy_name == 'moving_average':
            from strategies.moving_average import MovingAverageStrategy
            strategy = MovingAverageStrategy()
        elif strategy_name == 'mean_reversion':
            from strategies.mean_reversion import MeanReversionStrategy
            strategy = MeanReversionStrategy()
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        strategy.initialize(self.event_manager)
        self.strategies[strategy_name] = strategy
        
        logger.info(f"Loaded strategy: {strategy_name}")
    
    async def _run_trading_loop(self):
        """Main trading loop."""
        logger.info("Starting trading loop...")
        
        while self.is_running:
            try:
                # Process events from the event queue
                await self.event_manager.process_events()
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(1)  # Wait before retrying
    
    async def _on_market_data(self, event: Event):
        """Handle market data events."""
        data = event.data
        
        # Update portfolio with latest prices
        await self.portfolio_manager.update_prices(data)
        
        # Forward to strategies
        for strategy in self.strategies.values():
            await strategy.on_market_data(data)
    
    async def _on_signal(self, event: Event):
        """Handle trading signals from strategies."""
        signal = event.data
        
        logger.info(f"Received signal: {signal}")
        
        # Risk check
        if not await self.risk_manager.check_signal(signal):
            logger.warning(f"Signal rejected by risk manager: {signal}")
            return
        
        # Convert signal to order
        order = await self._signal_to_order(signal)
        
        # Submit order to broker
        if order:
            await self.broker.submit_order(order)
    
    async def _on_order_filled(self, event: Event):
        """Handle order fill events."""
        fill = event.data
        
        logger.info(f"Order filled: {fill}")
        
        # Update portfolio
        await self.portfolio_manager.update_position(fill)
        
        # Notify strategies
        for strategy in self.strategies.values():
            await strategy.on_order_filled(fill)
    
    async def _on_risk_violation(self, event: Event):
        """Handle risk violation events."""
        violation = event.data
        
        logger.error(f"Risk violation: {violation}")
        
        # Take appropriate action (e.g., close positions, stop trading)
        if violation['severity'] == 'critical':
            logger.error("Critical risk violation - stopping trading")
            await self.stop()
    
    async def _signal_to_order(self, signal: Dict) -> Optional[Dict]:
        """Convert a trading signal to an order."""
        # This would contain logic to convert signals to orders
        # including position sizing, order type selection, etc.
        
        symbol = signal['symbol']
        action = signal['action']  # 'buy' or 'sell'
        
        # Calculate position size
        position_size = await self.portfolio_manager.calculate_position_size(
            symbol, signal.get('confidence', 1.0)
        )
        
        if position_size == 0:
            return None
        
        order = {
            'symbol': symbol,
            'side': action,
            'qty': abs(position_size),
            'type': 'market',
            'time_in_force': 'day',
            'timestamp': datetime.now()
        }
        
        return order