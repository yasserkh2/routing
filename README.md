# Routing SLA Optimization Project

This project implements an intelligent routing system with SLA (Service Level Agreement) optimization capabilities. The system analyzes network links, optimizes routing paths based on SLAs, and provides both API and web interfaces for interaction.

## Project Structure

### Working Data and Implementation
- **working_befor_data/**: Contains the core implementation
  - **app/**: Core application modules
    - **api/**: API implementation including interfaces and strategies
    - **core/**: Core optimization logic
    - **models/**: Data models for links, profiles, and SLA data
    - **services/**: Service implementations including data preparation and event handling
    - **tests/**: Test cases and examples
    - **utils/**: Utility functions and helpers
  - **mock_data/**: Sample data for testing
    - `links_data.json`: Network link configurations
    - `profiles.json`: Routing profiles
    - `price_changes.json`: Price change scenarios
    - `sla_update.json`: SLA update examples
  - **web_interface/**: Web-based user interface
    - `sla.html`: SLA management interface
    - `sla_server.py`: Web server implementation

### Project Design Documentation
- **project_design/**: Comprehensive design documentation
  - **architecture/**: System architecture details
    - Components, scalability, and technology stack documentation
  - **data/**: Data model and sources documentation
  - **decision_making/**: Decision logic and approval workflows
  - **deployment/**: CI/CD and monitoring strategies
  - **ml/**: Machine learning model documentation
  - **optimization/**: Optimization algorithms and objective functions
  - **security/**: Security considerations and data privacy
  - **testing/**: Testing strategies and test cases

### Source Code
- **src/**: New implementation directory
  - **app/**: Application modules
    - api/, core/, models/, services/, tests/
  - **web/**: Web interface components

### Server
- **server/**: Server implementation
  - `server.py`: Main server implementation
  - `index.html`: Server interface

## Getting Started

1. Install dependencies:
```bash
pip install -r working_befor_data/requirements.txt
```

2. Run the SLA web interface:
```bash
python working_befor_data/web_interface/sla_server.py
```

3. For testing the optimization:
```bash
python working_befor_data/app/tests/run_optimizer.py
```

## API Documentation

The project includes a Postman collection (`Routing_SLA_API.postman_collection.json`) for testing the API endpoints.

## Testing

Various test cases are available in the `working_befor_data/app/tests/` directory:
- `test_optimizer_sla.py`: Tests for SLA optimization
- `system_integration_test.py`: Integration tests
- `sla_change_example.py`: Examples of SLA changes
- `event_handler_example.py`: Event handling examples

## Documentation

Detailed documentation is available in the project_design/ directory, covering:
- System architecture and components
- Data models and sources
- Decision-making logic
- Deployment strategies
- Security considerations
- Testing approaches