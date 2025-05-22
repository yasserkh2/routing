# Services Directory

## Service Components

### Data Services
- `data_preparation_service.py`: Prepares data for optimizer
  * Loads and processes raw data
  * Creates Profile and Link instances
  * Caches prepared data
  * Converts data for optimizer format

### Mock Services
- `mock_services.py`: Mock API implementation
  * Reads from mock data files
  * Handles price and SLA updates
  * Simulates API responses
  * Manages combined data format

### Event Handling
- `event_handler.py`: Handles real-time events
  * Price change events
  * SLA update events
  * Link status changes
  * Traffic distribution updates

### Base Classes
- `base_mock_service.py`: Base class for mock services
  * Common functionality
  * Interface definitions
  * Error handling

## Required Files
```
services/
├── __init__.py                    # Makes services a package
├── README.md                      # This documentation
├── data_preparation_service.py    # Data preparation logic
├── mock_services.py              # Mock API implementation
├── event_handler.py              # Event handling system
└── base_mock_service.py          # Base service class
```

## Service Interactions

### Data Flow
1. MockAPIService reads raw JSON data
2. DataPreparationService requests data via MockAPIService
3. DataPreparationService creates Profile/Link instances
4. EventHandler monitors for updates
5. Services notify subscribers of changes

### Event Flow
1. Event received (price/SLA change)
2. EventHandler processes event
3. MockAPIService updates internal state
4. DataPreparationService refreshes cached data
5. System recalculates routing if needed

## Usage Example
```python
# Initialize services
mock_service = MockAPIService()
data_service = DataPreparationService(mock_service)
event_handler = EventHandler()

# Get prepared data
profiles = data_service.get_all_profiles()
links = data_service.extract_all_links()

# Handle events
event_handler.register_listener(mock_service)
event_handler.process_event(price_change_event)