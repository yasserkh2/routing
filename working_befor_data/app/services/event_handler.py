from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

class EventType(Enum):
    PRICE_CHANGE = "price_change"
    ROUTE_UPDATE = "route_update"
    SLA_UPDATE = "sla_update"

@dataclass
class Event:
    """Event data structure"""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class EventHandler:
    """Handles events in the system"""
    
    def __init__(self):
        self.events = []
    
    def create_event(self, event_type: EventType, data: Dict[str, Any]) -> Event:
        """Create and store a new event"""
        event = Event(event_type=event_type, data=data)
        self.events.append(event)
        return event
    
    def get_events_by_type(self, event_type: EventType) -> list[Event]:
        """Get all events of a specific type"""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_latest_event(self, event_type: EventType) -> Optional[Event]:
        """Get the most recent event of a specific type"""
        events = self.get_events_by_type(event_type)
        return max(events, key=lambda e: e.timestamp) if events else None
    
    def clear_history(self):
        """Clear event history"""
        self.events = []