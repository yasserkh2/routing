from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

class EventType(Enum):
    PRICE_UPDATE = "PriceUpdate"
    ROUTE_UPDATE = "route_update"
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
    
    def create_event(self, event_data: Dict[str, Any]) -> Event:
        """Create and store a new event from raw event data"""
        event = Event.from_dict(event_data)
        self.events.append(event)
        return event
    
    def get_events_by_type(self, event_type: str) -> list[Event]:
        """Get all events of a specific type"""
        return [e for e in self.events if e.type == event_type]
    
    def get_latest_event(self, event_type: str) -> Optional[Event]:
        """Get the most recent event of a specific type"""
        events = self.get_events_by_type(event_type)
        return max(events, key=lambda e: e.timestamp) if events else None
    
    def clear_history(self):
        """Clear event history"""
        self.events = []