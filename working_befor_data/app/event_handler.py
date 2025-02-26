from typing import Dict, Any, Callable, List, Optional, Union, Awaitable
from datetime import datetime
from enum import Enum, auto
import asyncio
from functools import partial


class EventType(Enum):
    """Enum for different types of events that can occur"""
    ROUTE_UPDATE = auto()
    PROFILE_UPDATE = auto()
    SLA_UPDATE = auto()
    PRICE_CHANGE = auto()
    DATA_REFRESH = auto()
    VALIDATION = auto()
    CUSTOM = auto()


class EventPriority(Enum):
    """Priority levels for events"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class Event:
    """Class representing an event with its data and metadata"""
    def __init__(self, 
                 event_type: EventType, 
                 data: Dict[str, Any], 
                 priority: EventPriority = EventPriority.MEDIUM,
                 parent_event: Optional['Event'] = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now()
        self.processed = False
        self.metadata: Dict[str, Any] = {}
        self.priority = priority
        self.parent_event = parent_event
        self.child_events: List['Event'] = []

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the event"""
        self.metadata[key] = value

    def mark_processed(self) -> None:
        """Mark the event as processed"""
        self.processed = True

    def add_child_event(self, event: 'Event') -> None:
        """Add a child event to this event"""
        event.parent_event = self
        self.child_events.append(event)

    def get_event_chain(self) -> List['Event']:
        """Get the complete chain of events (parents and children)"""
        chain = []
        # Add parent chain
        current = self.parent_event
        while current is not None:
            chain.insert(0, current)
            current = current.parent_event
        # Add self and children chain
        chain.append(self)
        chain.extend(self.child_events)
        return chain


class EventFilter:
    """Class for filtering events based on various criteria"""
    def __init__(self,
                 event_types: Optional[List[EventType]] = None,
                 min_priority: Optional[EventPriority] = None,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 metadata_criteria: Optional[Dict[str, Any]] = None):
        self.event_types = event_types
        self.min_priority = min_priority
        self.start_time = start_time
        self.end_time = end_time
        self.metadata_criteria = metadata_criteria

    def matches(self, event: Event) -> bool:
        """Check if an event matches the filter criteria"""
        if self.event_types and event.event_type not in self.event_types:
            return False
        if self.min_priority and event.priority.value < self.min_priority.value:
            return False
        if self.start_time and event.timestamp < self.start_time:
            return False
        if self.end_time and event.timestamp > self.end_time:
            return False
        if self.metadata_criteria:
            for key, value in self.metadata_criteria.items():
                if key not in event.metadata or event.metadata[key] != value:
                    return False
        return True


class EventHandler:
    """Main event handling class for processing events before data operations"""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable[[Event], Awaitable[None]]]] = {
            event_type: [] for event_type in EventType
        }
        self._event_history: List[Event] = []
        self._max_history = 1000  # Maximum number of events to keep in history
        self._default_handler: Optional[Callable[[Event], Awaitable[None]]] = None

    def register_handler(self, 
                        event_type: EventType, 
                        handler: Union[Callable[[Event], None], Callable[[Event], Awaitable[None]]],
                        is_async: bool = False) -> None:
        """Register a new handler for a specific event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            
        if is_async:
            async_handler = handler
        else:
            async def async_handler(event: Event) -> None:
                return await asyncio.to_thread(handler, event)
                
        self._handlers[event_type].append(async_handler)

    def register_default_handler(self, 
                               handler: Union[Callable[[Event], None], Callable[[Event], Awaitable[None]]],
                               is_async: bool = False) -> None:
        """Register a default handler for events with no specific handlers"""
        if is_async:
            self._default_handler = handler
        else:
            async def async_handler(event: Event) -> None:
                return await asyncio.to_thread(handler, event)
            self._default_handler = async_handler

    def unregister_handler(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Unregister a handler for a specific event type"""
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h.__name__ != handler.__name__]

    async def handle_event(self, event: Event) -> None:
        """Process an event through all registered handlers for its type"""
        handlers_to_execute = []
        
        # Get specific handlers for the event type
        if event.event_type in self._handlers and self._handlers[event.event_type]:
            handlers_to_execute.extend(self._handlers[event.event_type])
        # If no specific handlers and default handler exists, use default handler
        elif self._default_handler is not None:
            handlers_to_execute.append(self._default_handler)
            event.add_metadata('handled_by', 'default_handler')
        else:
            # Log unhandled event
            print(f"Warning: No handler registered for event type: {event.event_type}")
            event.add_metadata('handled_by', 'none')
            event.add_metadata('warning', 'no_handler_registered')

        # Execute all handlers
        if handlers_to_execute:
            tasks = []
            for handler in handlers_to_execute:
                try:
                    task = asyncio.create_task(handler(event))
                    tasks.append(task)
                except Exception as e:
                    event.add_metadata('error', str(e))
                    raise

            # Wait for all handlers to complete
            await asyncio.gather(*tasks)

        event.mark_processed()
        self._add_to_history(event)

        # Process any child events
        for child_event in event.child_events:
            await self.handle_event(child_event)

    def create_event(self, 
                     event_type: EventType, 
                     data: Dict[str, Any],
                     priority: EventPriority = EventPriority.MEDIUM,
                     parent_event: Optional[Event] = None) -> Event:
        """Create and return a new event instance"""
        return Event(event_type, data, priority, parent_event)

    def _add_to_history(self, event: Event) -> None:
        """Add an event to the history, maintaining the maximum size"""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

    def get_history(self, 
                   event_filter: Optional[EventFilter] = None) -> List[Event]:
        """Get event history, optionally filtered by criteria"""
        if event_filter is None:
            return self._event_history
        return [e for e in self._event_history if event_filter.matches(e)]

    def clear_history(self) -> None:
        """Clear the event history"""
        self._event_history = []


# Example validation handlers
def validate_route_data(event: Event) -> None:
    """Validate route data before processing"""
    required_fields = ['product_name', 'mcc', 'mnc']
    for field in required_fields:
        if field not in event.data:
            raise ValueError(f"Missing required field: {field}")

def validate_sla_data(event: Event) -> None:
    """Validate SLA data before processing"""
    if 'sla_dd' in event.data and not isinstance(event.data['sla_dd'], (int, float, type(None))):
        raise ValueError("Invalid SLA DD value")
    if 'sla_tested' in event.data and not isinstance(event.data['sla_tested'], (int, float, type(None))):
        raise ValueError("Invalid SLA tested value")

async def log_event(event: Event) -> None:
    """Log event details"""
    print(f"Event processed: {event.event_type} at {event.timestamp}")
    print(f"Priority: {event.priority}")
    print(f"Data: {event.data}")
    print(f"Metadata: {event.metadata}")
    if event.parent_event:
        print(f"Parent event: {event.parent_event.event_type}")
    if event.child_events:
        print(f"Child events: {[e.event_type for e in event.child_events]}")

async def default_event_handler(event: Event) -> None:
    """Default handler for events with no specific handlers"""
    print(f"Default handler processing event: {event.event_type}")
    print(f"Event data: {event.data}")
    print(f"Event priority: {event.priority}")
    # Add default handling metadata
    event.add_metadata('default_handled', True)
    event.add_metadata('default_handled_at', datetime.now().isoformat())