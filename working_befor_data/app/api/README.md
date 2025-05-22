# API Directory

## API Components

### Core API
- `api.py`: Main API implementation
  * Handles routing requests
  * Processes updates
  * Manages data access
  * Implements business logic

### Interfaces
- `api_interfaces.py`: API interface definitions
  * Base API interface
  * Required method signatures
  * Data type definitions
  * Contract specifications

### API Caller
- `api_caller.py`: API client implementation
  * Makes API requests
  * Handles responses
  * Manages authentication
  * Error handling

### Main Entry
- `main.py`: API entry points
  * Route configuration
  * Server setup
  * Middleware configuration
  * Error handlers

## Required Files
```
api/
├── __init__.py          # Makes api a package
├── README.md           # This documentation
├── api.py             # Main API implementation
├── api_interfaces.py  # Interface definitions
├── api_caller.py     # API client
└── main.py          # Entry points
```

## API Endpoints

### Data Access
```python
# Get profile configuration
GET /api/profiles/{profile_id}

# Get link information
GET /api/links/{link_id}

# Get combined data
GET /api/data/combined
```

### Updates
```python
# Update link price
POST /api/links/{link_id}/price
{
    "new_price": 10.5,
    "timestamp": "2025-05-22T15:00:00"
}

# Update link SLA
POST /api/links/{link_id}/sla
{
    "new_sla": 95.0,
    "timestamp": "2025-05-22T15:00:00"
}
```

### Routing
```python
# Get routing plan
GET /api/routing/{profile_id}

# Update traffic distribution
POST /api/routing/{profile_id}/traffic
{
    "distributions": [
        {
            "link_id": "LINK_001",
            "traffic": 25.0
        }
    ]
}
```

## Interface Example
```python
class BaseAPI:
    @abstractmethod
    def get_combined_data(self) -> Dict[str, Any]:
        """Get combined profile and link data"""
        pass
    
    @abstractmethod
    def handle_price_change(self, link_id: str, new_price: float) -> None:
        """Handle price update event"""
        pass
    
    @abstractmethod
    def handle_sla_change(self, link_id: str, new_sla: float) -> None:
        """Handle SLA update event"""
        pass