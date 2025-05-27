# Tests Directory

## Test Files

### Data Model Tests
- `test_profile_comprehensive.py`: Comprehensive tests for Profile class including:
  * Data extraction and validation
  * Link operations (add, remove, status changes)
  * Label management
  * Cloning and advanced operations
  * Error handling and validation

- `test_link_comprehensive.py`: Comprehensive tests for Link class including:
  * Basic link creation and properties
  * Link creation from API data
  * Label and status handling
  * Advanced operations like price updates
  * Error handling and validation

### Integration Tests
- `test_optimizer_sla.py`: Tests SLA-based optimization
- `system_integration_test.py`: End-to-end system tests
- `event_handler_example.py`: Tests event handling system
- `sla_change_example.py`: Tests SLA update scenarios
- `run_optimizer.py`: Tests optimizer functionality
- `test_data_preparation.py`: Tests data preparation service

## Required Files
```
tests/
├── __init__.py                     # Makes tests a package
├── README.md                       # This documentation
├── test_profile_comprehensive.py   # Comprehensive Profile model tests
├── test_link_comprehensive.py      # Comprehensive Link model tests
├── test_optimizer_sla.py           # Optimizer tests
├── system_integration_test.py      # System tests
├── event_handler_example.py        # Event system tests
├── sla_change_example.py           # SLA update tests
├── run_optimizer.py                # Optimizer runner
└── test_data_preparation.py        # Data preparation tests
```

## Running Tests
```bash
# Run model tests
python -m app.tests.test_profile_comprehensive
python -m app.tests.test_link_comprehensive

# Run optimizer tests
python -m app.tests.test_optimizer_sla
python -m app.tests.run_optimizer

# Run integration tests
python -m app.tests.system_integration_test