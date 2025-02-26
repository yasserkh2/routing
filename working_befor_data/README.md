# Routing Optimization System

A system for optimizing routing decisions based on SLA requirements and profit maximization.

## Components

### 1. Data Models

#### SLA Data (`sla_data.py`)
- Handles SLA information from multiple sources:
  * DataDog (current performance)
  * Auto Router V1 (testing results)
  * Tiering-based assumptions
- Provides best available SLA selection

#### Link (`link.py`)
- Represents routing links with properties:
  * Link ID and operator information
  * SLA data and status
  * Routing priority
  * Active/inactive status
- Methods for SLA validation and usability checks

#### Profile (`profile.py`)
- Manages routing profiles with:
  * Expected SLA requirements
  * Associated links
  * Priority levels
- Methods for link management and SLA verification

### 2. Optimization System

#### Route Optimizer (`optimizer.py`)
- Linear programming model for profit maximization
- Constraints:
  * SLA requirements per profile
  * Link capacity limits
  * Volume distribution
- Provides optimal routing plans

### 3. API Integration

#### API Strategies (`api_strategy.py`)
- Query1: GetProfilesRelatedToLink(link, mnc)
  * Gets profiles associated with a link
  * Shows expected SLA per profile
  * Includes link-specific information

- Query2: GetLinksSLAByMNC(mnc)
  * Gets all links for an MNC
  * Shows SLA from different sources
  * Includes performance metrics

- Query3: GetProfilesWithLinks()
  * Gets all profiles with their links
  * Shows routing priorities
  * Includes active status

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from optimizer import RoutingOptimizer
from profile import Profile

# Create profiles with links
profiles = [...]

# Initialize optimizer
optimizer = RoutingOptimizer(profiles)

# Set volumes per profile
profile_volumes = {
    'PROF_1': 2000.0,
    'PROF_2': 5000.0
}

# Setup and solve
optimizer.setup_model(profile_volumes)
if optimizer.solve():
    routing_plan = optimizer.get_routing_plan()
    stats = optimizer.get_optimization_stats()
```

### Example Output

```
Profile: Premium_Gold_Profile (99.5% SLA)
- Link 450271: 1619 units at 99.9% SLA
- Link 450272: 381 units at 97.8% SLA

Profile: Standard_Profile (97.0% SLA)
- Link 450272: 5000 units at 97.8% SLA

Total Profit: $7,000.00
Total Volume: 7,000 units
```

## Features

1. Multi-Source SLA Data:
   - Real-time performance (DataDog)
   - Testing results
   - Assumed values

2. Profit Optimization:
   - Maximizes revenue while meeting SLA
   - Considers link costs and capacity
   - Balances traffic distribution

3. Profile Management:
   - Flexible link assignment
   - Priority-based routing
   - SLA requirement validation

4. API Integration:
   - Profile and link queries
   - SLA data retrieval
   - Real-time updates

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
black .
pylint app/
mypy app/
```

## Requirements

See `requirements.txt` for full list of dependencies:
- pulp: Linear programming solver
- python-dateutil: Date handling
- typing-extensions: Enhanced typing
- pytest: Testing framework
- black: Code formatter
- pylint: Code linter
- mypy: Static type checker

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is proprietary and confidential.