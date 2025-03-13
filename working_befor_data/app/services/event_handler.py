from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from ..utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class EventType(Enum):
    PRICE_UPDATE = "PriceUpdate"
    SLA_UPDATE = "sla_update"

@dataclass
class Event:
    """Event data structure"""
    type: str
    payload: Dict[str, Any]
    link: str
    mcc: str
    mnc: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the event"""
        self.metadata[key] = value
        logger.info(f"Added metadata {key}={value} to event {self.type}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create an Event instance from a dictionary"""
        return cls(
            type=data["Type"],
            payload=data["Payload"],
            link=data["link"],
            mcc=data["mcc"],
            mnc=data["mnc"],
            timestamp=datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        )

class EventHandler:
    """Handles events in the system"""
    
    def __init__(self):
        self.events = []
        self.handlers = {}  # Dictionary to store event handlers
        logger.info("EventHandler initialized")

    async def handle_event(self, event: Event) -> None:
        """Process an event using registered handlers"""
        logger.info(f"Attempting to handle event of type: {event.type}")
        
        if event.type not in self.handlers:
            error_msg = f"No handler registered for event type: {event.type}"
            logger.warning(error_msg)
            raise ValueError(error_msg)
            
        handler, is_async = self.handlers[event.type]
        logger.info(f"Found {'async' if is_async else 'sync'} handler for event type: {event.type}")
        
        try:
            if is_async:
                await handler(event)
            else:
                handler(event)
            logger.info(f"Successfully processed event {event.type}")
        except Exception as e:
            error_msg = f"Error processing event {event.type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    def register_handler(self, event_type: str, handler, is_async: bool = False) -> None:
        """Register a handler for a specific event type"""
        self.handlers[event_type] = (handler, is_async)
        logger.info(f"Registered {'async ' if is_async else ''}handler for event type: {event_type}")
    
    def create_event(self, event_data: Dict[str, Any]) -> Event:
        """Create and store a new event from raw event data"""
        try:
            event = Event.from_dict(event_data)
            self.events.append(event)
            logger.info(f"Created new event of type {event.type} for link {event.link} (MCC: {event.mcc}, MNC: {event.mnc})")
            return event
        except Exception as e:
            logger.error(f"Failed to create event from data: {event_data}. Error: {str(e)}", exc_info=True)
            raise
    
    def get_events_by_type(self, event_type: str) -> list[Event]:
        """Get all events of a specific type"""
        events = [e for e in self.events if e.type == event_type]
        logger.info(f"Retrieved {len(events)} events of type {event_type}")
        return events
    
    def get_latest_event(self, event_type: str) -> Optional[Event]:
        """Get the most recent event of a specific type"""
        events = self.get_events_by_type(event_type)
        if events:
            latest = max(events, key=lambda e: e.timestamp)
            logger.info(f"Retrieved latest event of type {event_type} from {latest.timestamp}")
            return latest
        logger.info(f"No events found of type {event_type}")
        return None
    
    def clear_history(self):
        """Clear event history"""
        event_count = len(self.events)
        self.events = []
        logger.info(f"Cleared event history ({event_count} events removed)")