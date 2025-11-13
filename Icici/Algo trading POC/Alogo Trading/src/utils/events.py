"""
Event management system for the trading platform.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Callable, List
import logging

logger = logging.getLogger(__name__)


class Event:
    """Represents an event in the trading system."""
    
    def __init__(self, event_type: str, data: Any, timestamp: datetime = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now()
        self.event_id = f"{event_type}_{self.timestamp.strftime('%Y%m%d_%H%M%S_%f')}"


class EventManager:
    """
    Manages events and subscriptions for the trading system.
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_queue = asyncio.Queue()
        self.is_processing = False
        
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        logger.info(f"Subscribed to event type: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                logger.info(f"Unsubscribed from event type: {event_type}")
            except ValueError:
                logger.warning(f"Callback not found for event type: {event_type}")
    
    async def emit(self, event: Event):
        """Emit an event to all subscribers."""
        await self.event_queue.put(event)
        logger.debug(f"Event emitted: {event.event_type}")
    
    async def process_events(self):
        """Process events from the queue."""
        if self.is_processing:
            return
        
        self.is_processing = True
        
        try:
            while not self.event_queue.empty():
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=0.1)
                    await self._handle_event(event)
                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
        finally:
            self.is_processing = False
    
    async def _handle_event(self, event: Event):
        """Handle a single event by calling all subscribers."""
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback for {event.event_type}: {e}")
        
        logger.debug(f"Event processed: {event.event_type}")
    
    def get_event_types(self) -> List[str]:
        """Get all registered event types."""
        return list(self.subscribers.keys())
    
    def get_subscriber_count(self, event_type: str) -> int:
        """Get the number of subscribers for an event type."""
        return len(self.subscribers.get(event_type, []))