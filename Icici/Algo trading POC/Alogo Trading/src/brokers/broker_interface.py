"""
Base broker interface for all trading brokers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class BrokerInterface(ABC):
    """
    Abstract base class for all broker implementations.
    """
    
    def __init__(self, name: str, paper_trading: bool = True):
        self.name = name
        self.paper_trading = paper_trading
        self.event_manager = None
        
    @abstractmethod
    async def connect(self, config: Optional[Dict] = None):
        """Connect to the broker."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the broker."""
        pass
    
    @abstractmethod
    async def submit_order(self, order: Dict[str, Any]) -> Optional[str]:
        """Submit an order to the broker."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, **kwargs) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> bool:
        """Modify an existing order."""
        pass
    
    @abstractmethod
    async def get_orders(self, **kwargs) -> List[Dict[str, Any]]:
        """Get list of orders."""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Get market data for symbols."""
        pass
    
    @abstractmethod
    async def start_market_data_stream(self, symbols: List[str], callback):
        """Start real-time market data stream."""
        pass
    
    @abstractmethod
    async def stop_market_data_stream(self):
        """Stop real-time market data stream."""
        pass
    
    def set_event_manager(self, event_manager):
        """Set the event manager for this broker."""
        self.event_manager = event_manager