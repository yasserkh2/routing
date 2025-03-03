# Routing Optimization System

A system for optimizing traffic routing across multiple links while balancing SLA requirements and costs, with a focus on handling price change events.

## Quick Start

To run the optimizer:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure required mock data files are present in `mock_data/` directory:
   - links_data.json
   - profiles.json
   - price_changes.json

3. Run the optimizer:
   ```bash
   python -m app.tests.run_optimizer
   ```

The optimizer will output the optimized routing configuration, including traffic distribution, SLA compliance, and cost analysis.

## Components

### SLA Data Management
- `SLAData`: Manages SLA information for links
- Stores average SLA values (DD, Tested, Assumed)
- Handles SLA data conversion and calculations

### Link Management
- `Link`: Represents a routing link with its properties
  * Link ID, operator, MNC
  * SLA data (average of DD, Tested, and Assumed values)
  * Price information and history
  * Status tracking

### Profile Management
- `Profile`: Represents a routing profile
  * Expected SLA requirements
  * Associated links
  * Priority levels
  * Link associations
  * Methods for finding profiles affected by price changes

### Price Change Handling
- Detects and processes price changes
- Identifies affected profiles
- Re-optimizes routes for affected profiles
- Analyzes cost impact
- Maintains price history

### Cost Optimization
- `RoutingOptimizer`: Implements linear programming optimization
  * Minimizes total routing cost
  * Ensures SLA requirements are met
  * Distributes traffic across available links
  * Handles price change impacts

## Price Change Analysis

### Process Flow
1. Price change detected for specific link
2. Affected profiles identified using Profile class method
3. Each affected profile analyzed:
   - Current routing plan captured
   - New prices applied
   - Routes re-optimized
   - Cost impact calculated

### Example Output
```
PRICE CHANGE DETAILS FOR LINK_021
--------------------------------------------------
Provider:     MessageBird
Network:      Stc Bahrain
Old Price:    $0.205
New Price:    $0.189
Change:       Decreased
SLA:         80.0%

Affected Profile: Standard_Bulk_Plus
--------------------------------------------------
Expected SLA:    80.0%
Available Links: 5

BEFORE PRICE CHANGE:
Link LINK_021:
  Traffic:    86.7%
  SLA:        79.2%
  Price:      $0.205
Link LINK_017:
  Traffic:    13.3%
  SLA:        85.4%
  Price:      $0.210

Total Cost:    $0.192
Active Links:  2
Achieved SLA:  80.00%

AFTER PRICE CHANGE:
Link LINK_021:
  Traffic:    86.7%
  SLA:        79.2%
  Price:      $0.189
Link LINK_017:
  Traffic:    13.3%
  SLA:        85.4%
  Price:      $0.210

Total Cost:    $0.189
Active Links:  2
Achieved SLA:  80.00%

COST IMPACT:
Savings:      $0.003
Percentage:   1.5%
```

## Optimization Model

### Variables
- Traffic allocation fractions for each link (0-100%)

### Objective
- Minimize total cost: sum(price_i * fraction_i) for each link i

### Constraints
1. Total allocation must equal 100%
2. Weighted average SLA must meet or exceed target SLA

## Usage Example

```python
# Get profiles affected by price change
affected_profiles = Profile.get_profiles_affected_by_price_change(all_profiles, link_id)

# For each affected profile
for profile in affected_profiles:
    # Run initial optimization
    optimizer = RoutingOptimizer(profile)
    if optimizer.solve():
        initial_plan = optimizer.get_routing_plan()
        initial_stats = optimizer.get_optimization_stats()

        # Apply price change and re-optimize
        profile.update_link_price(link_id, new_price)
        optimizer = RoutingOptimizer(profile)
        if optimizer.solve():
            new_plan = optimizer.get_routing_plan()
            new_stats = optimizer.get_optimization_stats()
```

## Features

1. Cost-Effective Routing
   - Finds minimum cost solution
   - Maintains required service levels
   - Optimizes traffic distribution
   - Adapts to price changes

2. SLA Management
   - Supports multiple SLA metrics (DD, Tested, Assumed)
   - Calculates average SLA values
   - Ensures SLA requirements are met

3. Price Change Analysis
   - Automatic affected profile detection
   - Before/after comparison
   - Cost impact calculation
   - Historical price tracking

4. Clear Reporting
   - Detailed routing plans
   - Cost and SLA statistics
   - Link utilization information
   - Cost impact metrics

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