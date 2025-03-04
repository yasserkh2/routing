"""
Routing SLA API - A system for optimizing telecom routing while meeting SLA requirements.

Project Structure:
- api/: API endpoints and routing
    - main.py: FastAPI application and route handlers
    - api_interfaces.py: API interface definitions
    - api_selector.py: API selection logic
    - api_strategy.py: API strategy implementations

- core/: Core business logic
    - optimizer.py: Linear programming optimization for routing

- models/: Data models
    - link.py: Link model representing routing paths
    - profile.py: Profile model for routing configurations
    - sla_data.py: SLA data structures

- services/: Service implementations
    - event_handler.py: Async event processing system
    - mock_services.py: Mock data services for testing

- utils/: Utility functions and helpers

- tests/: Test files and examples
    - *_example.py: Example implementations

- mock_data/: Mock data files for testing
    - *.json: Various mock data files
"""

__version__ = "1.0.0"