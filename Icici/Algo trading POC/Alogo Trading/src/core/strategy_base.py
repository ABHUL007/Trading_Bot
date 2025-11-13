"""
Base class for all trading strategies.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from src.utils.events import EventManager, Event


logger = logging.getLogger(__name__)


class StrategyBase(ABC):
    """
    Abstract base class for all trading strategies.
    
    All strategies must inherit from this class and implement the required methods.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.event_manager: Optional[EventManager] = None
        self.is_initialized = False
        self.positions: Dict[str, float] = {}
        self.parameters: Dict[str, Any] = {}
        
    def initialize(self, event_manager: EventManager):
        """
        Initialize the strategy with the event manager.
        
        Args:
            event_manager: Event manager for publishing signals
        """
        self.event_manager = event_manager
        self.is_initialized = True
        logger.info(f"Strategy {self.name} initialized")
    
    @abstractmethod
    async def on_market_data(self, data: Dict[str, Any]):
        """
        Handle incoming market data.
        
        Args:
            data: Market data dictionary containing price information
        """
        pass
    
    @abstractmethod
    async def on_order_filled(self, fill: Dict[str, Any]):
        """
        Handle order fill notifications.
        
        Args:
            fill: Order fill information
        """
        pass
    
    async def emit_signal(self, symbol: str, action: str, confidence: float = 1.0, **kwargs):
        """
        Emit a trading signal.
        
        Args:
            symbol: Trading symbol
            action: 'buy' or 'sell'
            confidence: Confidence level (0.0 to 1.0)
            **kwargs: Additional signal parameters
        """
        if not self.event_manager:
            logger.error("Strategy not initialized - cannot emit signal")
            return
        
        signal = {
            'strategy': self.name,
            'symbol': symbol,
            'action': action,
            'confidence': confidence,
            'timestamp': datetime.now(),
            **kwargs
        }
        
        event = Event('signal', signal)
        await self.event_manager.publish(event)
        
        logger.info(f"Signal emitted: {signal}")
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """
        Set strategy parameters.
        
        Args:
            parameters: Dictionary of parameter name-value pairs
        """
        self.parameters.update(parameters)
        logger.info(f"Parameters updated for {self.name}: {parameters}")
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """
        Get a strategy parameter value.
        
        Args:
            name: Parameter name
            default: Default value if parameter not found
            
        Returns:
            Parameter value or default
        """
        return self.parameters.get(name, default)
    
    def update_position(self, symbol: str, quantity: float):
        """
        Update position tracking.
        
        Args:
            symbol: Trading symbol
            quantity: Position quantity (positive for long, negative for short)
        """
        self.positions[symbol] = quantity
        logger.debug(f"Position updated: {symbol} = {quantity}")
    
    def get_position(self, symbol: str) -> float:
        """
        Get current position for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Current position quantity
        """
        return self.positions.get(symbol, 0.0)
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get strategy information and current state.
        
        Returns:
            Dictionary containing strategy information
        """
        pass