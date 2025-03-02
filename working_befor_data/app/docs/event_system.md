# Event System Documentation

## Overview

The event system is designed to be highly scalable, currently handling price change events with the capability to easily extend to additional event types in the future. The system uses a modular architecture that separates concerns between event handling, API integration, and business logic, making it straightforward to add new event types and their corresponding handlers.

## Current Implementation

Currently implemented event:
- PRICE_CHANGE: Handles updates to link pricing, including:
  * Price update detection
  * Affected profile identification
  * Route re-optimization
  * Revenue impact analysis

## Scalability Design

The system is architected for easy extension to handle multiple event types:

1. **Event Type Registration**
   ```python
   # Adding new event types is as simple as extending the EventType enum
   class EventType(Enum):
       PRICE_CHANGE = "price_change"
       # Future events can be added here:
       # CAPACITY_CHANGE = "capacity_change"
       # QUALITY_UPDATE = "quality_update"
       # NETWORK_STATUS = "network_status"
   ```

2. **Strategy Pattern for Event Handling**
   - Each event type can have its own set of API strategies
   - New strategies can be registered without modifying existing code
   - Strategy selection based on event type

3. **Extensible API Integration**
   - APISelector design allows adding new strategies
   - Strategy factory pattern supports dynamic strategy creation
   - Clean separation between event types and their handlers

## Key Components

### 1. Event Handler (`services/event_handler.py`)
- Core event management system
- Defines event types:
  * PRICE_CHANGE: Updates to link pricing
  * ROUTE_UPDATE: Changes in routing configuration
  * SLA_UPDATE: Updates to service level metrics
- Provides event creation and handling capabilities
- Manages event metadata and history

### 2. API Integration

#### API Selector (`api/api_selector.py`)
- Coordinates API strategy selection and execution
- Components:
  * DefaultAPIRegistry: Manages available API strategies
  * DefaultAPIExecutor: Executes API calls
  * APISelector: Orchestrates the process

#### API Strategies (`api/api_strategy.py`)
- Implements specific API strategies:
  * GetLinksSLADataStrategy: Handles SLA data retrieval
  * GetProfileConfigStrategy: Manages profile configurations
- Factory pattern for strategy creation

### 3. Event Flow Example

```python
# Create event handler
handler = EventHandler()

# Create price change event
event = handler.create_event(
    EventType.PRICE_CHANGE,
    data={
        'link_id': 'LINK_001',
        'old_price': 0.1011,
        'new_price': 0.2415,
        'provider': 'Provider A',
        'network': 'Network X',
        'mnc': 'MNC123'
    }
)

# Process event through API service
api_selector = APISelector()
results = await api_selector.execute_strategies(event)
```

### 4. API Queries

The system implements three main queries:

1. **GetProfilesRelatedToLink**
   - Input: link ID, MNC
   - Output: Profiles using the specified link
   - Purpose: Identify affected profiles when link changes occur

2. **GetLinksSLAByMNC**
   - Input: MNC
   - Output: SLA data for all links in the MNC
   - Purpose: Retrieve comprehensive SLA information

3. **GetProfilesWithLinks**
   - Input: None
   - Output: All profiles with their associated links
   - Purpose: Get complete system configuration

### 5. Test Files

1. **event_handler_example.py**
   - Demonstrates basic event handling
   - Shows event creation and processing
   - Includes API integration examples

2. **price_change_example.py**
   - Specific to price change events
   - Shows complete flow from event creation to processing
   - Includes mock API service integration

3. **price_change_profile_example.py**
   - Demonstrates profile updates due to price changes
   - Shows interaction between events and profile management

### 6. Mock Services

The `mock_services.py` file provides mock implementations for testing:
- MockAPIService for simulating API calls
- Mock data files in `mock_data/` directory:
  * price_changes.json
  * mock_links_data.json
  * mock_profiles.json

## Event Processing Flow

1. **Event Creation**
   - Event created with specific type and data
   - Timestamp and metadata added
   - Event stored in handler's history

2. **API Strategy Selection**
   - APISelector determines applicable strategies
   - Strategies filtered based on event type
   - Strategy instances created via factory

3. **Strategy Execution**
   - Each strategy executed sequentially
   - Results collected and aggregated
   - Metadata updated with execution status

4. **Response Processing**
   - Results returned to calling service
   - Event metadata updated with final status
   - Any necessary follow-up actions triggered

## Best Practices

1. **Event Creation**
   - Always use EventHandler to create events
   - Include all relevant data in event payload
   - Set appropriate event type

2. **API Integration**
   - Use APISelector for strategy coordination
   - Implement new strategies for new event types
   - Handle API errors gracefully

3. **Testing**
   - Use mock services for testing
   - Test complete event flow
   - Verify event metadata and results

This event system provides a robust foundation for handling various system events while maintaining clean separation of concerns and extensibility.

## Implementing Future Events

To add new event types to the system, follow these steps:

1. **Define New Event Type**
   ```python
   class EventType(Enum):
       PRICE_CHANGE = "price_change"
       NEW_EVENT = "new_event"  # Add new event type
   ```

2. **Create Event-Specific Strategy**
   ```python
   class NewEventStrategy(APICallStrategy):
       def can_handle(self, event: Event) -> bool:
           return event.event_type == EventType.NEW_EVENT
           
       async def call_api(self, event: Event) -> APIResponse:
           # Implement event-specific logic
   ```

3. **Register Strategy in APIRegistry**
   ```python
   def _setup_default_strategies(self) -> None:
       self._strategies = {
           EventType.PRICE_CHANGE: [
               RouteDetailsAPIStrategy,
               GetProfilesRelatedToLinkStrategy,
               # ...
           ],
           EventType.NEW_EVENT: [
               NewEventStrategy,
               # Add other relevant strategies
           ]
       }
   ```

4. **Create Event Handler Example**
   ```python
   async def handle_new_event(event: Event) -> None:
       # Implement event handling logic
       pass
   
   # Register handler
   handler.register_handler(
       EventType.NEW_EVENT,
       handle_new_event,
       is_async=True
   )
   ```

5. **Add Mock Data (for testing)**
   - Create new JSON file in mock_data/ directory
   - Update mock services to handle new event type
   - Create test examples demonstrating new event flow

6. **Document New Event**
   - Update this documentation with new event details
   - Include example usage and best practices
   - Document any specific considerations

Example Future Events:
1. **Capacity Change Events**
   - Handle updates to link capacity
   - Adjust routing based on new constraints
   - Update affected profiles

2. **Quality Update Events**
   - Process changes in link quality metrics
   - Update SLA calculations
   - Trigger route re-optimization

3. **Network Status Events**
   - Handle link availability changes
   - Process network maintenance windows
   - Manage failover scenarios

4. **Compliance Update Events**
   - Handle regulatory requirement changes
   - Update routing rules
   - Ensure compliance validation

The modular design ensures that adding these new events requires minimal changes to the existing codebase while maintaining the system's robustness and reliability.