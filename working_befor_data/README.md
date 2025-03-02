# Routing Optimization System

A system for optimizing traffic routing across multiple links while balancing SLA requirements and costs.

## Components

### SLA Data Management
- `SLAData`: Manages SLA information for links
- Stores average SLA values
- Handles SLA data conversion and calculations

### Link Management
- `Link`: Represents a routing link with its properties
  * Link ID, operator, MNC
  * SLA data
  * Price information and history
  * Routing priority
  * Active status

### Profile Management
- `Profile`: Represents a routing profile
  * Expected SLA requirements
  * Associated links
  * Priority levels
  * Profile creation and updates
  * SLA requirement tracking
  * Link associations

### Event Handling System
- `EventHandler`: Manages system events
  * Price change events
  * Route updates
  * SLA updates
- `Event`: Represents system events with:
  * Event type
  * Timestamp
  * Event-specific data

### Cost Optimization
- `RoutingOptimizer`: Implements linear programming optimization
  * Minimizes total routing cost
  * Ensures SLA requirements are met
  * Distributes traffic across available links
  * Handles price change impacts

## Price Change Management

### Event Flow
1. Price change detected and event created
2. Event processed through API service
3. Affected links updated with new prices
4. Affected profiles identified
5. Routes re-optimized for each affected profile

### Revenue Impact Analysis
- Per-profile revenue tracking
- Before/after optimization comparison
- Total system revenue impact
- Routing plan adjustments

Example revenue impact:
```python
# Revenue Impact Dashboard
Profile: Ultra_Premium_OTP (99.0% SLA)
Before: $0.2415
After:  $0.2800
Change: +15.94%

Profile: Premium_2FA (95.0% SLA)
Before: $0.1972
After:  $0.1972
Change: +0.00%

Total System Impact:
Before: $0.8640
After:  $0.9089
Change: +5.20%
```

## Optimization Model

### Variables
- Traffic allocation fractions for each link (0-100%)

### Objective
- Minimize total cost: sum(price_i * fraction_i) for each link i

### Constraints
1. Total allocation must equal 100%
2. Weighted average SLA must meet or exceed target SLA
3. Optional capacity constraints per link

## Usage Example

```python
# Create a profile with links and SLA requirement
profile = Profile(
    profile_id="PROF_1",
    name="Standard_Profile",
    expected_sla=70.0,  # Target SLA requirement
    priority="MEDIUM",
    links=[...]  # List of available links
)

# Create and run optimizer
optimizer = RoutingOptimizer(profile)
if optimizer.solve():
    # Get optimization results
    routing_plan = optimizer.get_routing_plan()
    stats = optimizer.get_optimization_stats()

    # Example output:
    # Link 450273: 100.0% (SLA: 85.00%, Price: $60.00)
    # Total Cost: $60.00
    # Achieved SLA: 85.00%
```

## Features

1. Cost-Effective Routing
   - Finds minimum cost solution
   - Maintains required service levels
   - Optimizes traffic distribution
   - Adapts to price changes

2. SLA Management
   - Supports multiple SLA sources
   - Calculates average SLA values
   - Ensures SLA requirements are met

3. Event Handling
   - Price change detection and processing
   - Automatic route re-optimization
   - Revenue impact analysis
   - Historical price tracking

4. Flexible Configuration
   - Configurable SLA requirements
   - Adjustable link priorities
   - Optional capacity constraints

5. Clear Reporting
   - Detailed routing plans
   - Cost and SLA statistics
   - Link utilization information
   - Revenue impact metrics

## Implementation Details

The system uses the PuLP library for linear programming optimization:

1. Problem Definition
   ```python
   model = LpProblem("Minimize_Cost_While_Achieving_SLA", LpMinimize)
   ```

2. Decision Variables
   ```python
   x = LpVariable("x_link_id", lowBound=0, upBound=1)  # Traffic fraction
   ```

3. Objective Function
   ```python
   model += lpSum([x[i] * price[i] for i in links])  # Minimize total cost
   ```

4. Constraints
   ```python
   model += lpSum(x) == 1  # Total allocation = 100%
   model += lpSum([x[i] * sla[i] for i in links]) >= target_sla
   ```

## Requirements

- Python 3.7+
- PuLP (Linear Programming Toolkit)
- Additional dependencies in requirements.txt