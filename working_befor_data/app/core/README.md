# Core Directory

## Core Components

### Optimizer
- `optimizer.py`: Core optimization engine
  * SLA-based routing optimization
  * Cost optimization
  * Traffic distribution
  * Tier-based routing

## Required Files
```
core/
├── __init__.py          # Makes core a package
├── README.md           # This documentation
└── optimizer.py        # Optimization engine
```

## Optimization Features

### SLA Optimization
- Considers link SLA performance
- Maintains profile SLA requirements
- Handles tier-based SLA requirements
- Balances SLA vs cost

### Cost Optimization
- Minimizes routing costs
- Considers buy prices
- Maintains profit margins
- Respects price constraints

### Traffic Distribution
- Balances traffic across links
- Handles link capacity
- Manages active/backup links
- Optimizes distribution patterns

### Tier-Based Routing
- Respects link tiers
- Prioritizes higher tiers
- Handles tier requirements
- Balances tier distribution

## Usage Example
```python
from .optimizer import Optimizer

# Initialize optimizer
optimizer = Optimizer()

# Prepare data
profiles = data_service.get_all_profiles()
links = data_service.extract_all_links()

# Run optimization
result = optimizer.optimize(
    profiles=profiles,
    links=links,
    constraints={
        'min_sla': 95.0,
        'max_cost': 10.0,
        'required_tier': 1
    }
)

# Get routing plan
routing_plan = result.get_routing_plan()
stats = result.get_statistics()
```

## Optimization Process

1. Data Preparation
   - Load profile and link data
   - Validate constraints
   - Prepare optimization model

2. Constraint Application
   - Apply SLA requirements
   - Apply cost constraints
   - Apply tier requirements
   - Apply traffic constraints

3. Optimization
   - Run optimization algorithm
   - Find optimal solution
   - Validate results
   - Generate routing plan

4. Result Generation
   - Create routing plan
   - Calculate statistics
   - Format output
   - Validate final plan