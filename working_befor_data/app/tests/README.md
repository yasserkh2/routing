# Tests Directory

## Test Files

### Data Model Tests
- `test_profile_output.py`: Tests Profile data extraction and validation
- `test_link_output.py`: Tests Link data extraction and validation
- `test_data_validation.py`: Tests data validation and error handling
- `test_data_models.py`: Combined model tests

### Integration Tests
- `test_optimizer_sla.py`: Tests SLA-based optimization
- `system_integration_test.py`: End-to-end system tests
- `event_handler_example.py`: Tests event handling system
- `sla_change_example.py`: Tests SLA update scenarios
- `run_optimizer.py`: Tests optimizer functionality

## Required Files
```
tests/
├── __init__.py                 # Makes tests a package
├── README.md                  # This documentation
├── test_profile_output.py     # Profile model tests
├── test_link_output.py        # Link model tests
├── test_data_validation.py    # Data validation tests
├── test_data_models.py        # Combined model tests
├── test_optimizer_sla.py      # Optimizer tests
├── system_integration_test.py # System tests
├── event_handler_example.py   # Event system tests
├── sla_change_example.py      # SLA update tests
└── run_optimizer.py          # Optimizer runner
```

## Running Tests
```bash
# Run individual tests
python -m app.tests.test_profile_output
python -m app.tests.test_link_output
python -m app.tests.test_data_validation

# Run optimizer tests
python -m app.tests.test_optimizer_sla
python -m app.tests.run_optimizer

# Run integration tests
python -m app.tests.system_integration_test