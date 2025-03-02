# Routing Optimization System Overview

## System Architecture

This document provides a comprehensive overview of the routing optimization system implementation.

### Core Components

1. **Data Models**
   - **Link Management**
     - Represents routing links with properties:
       * Link ID, operator, MNC
       * Price and price history
       * SLA metrics
     - Handles price updates and history tracking
     - Provides SLA validation and calculations
   
   - **Profile Management**
     - Manages routing profiles with:
       * Expected SLA requirements
       * Priority levels
       * Associated links
     - Handles link associations and updates
     - Provides filtering and grouping capabilities

2. **Optimization Engine**
   - Uses PuLP for linear programming optimization
   - Objective: Minimize total routing cost
   - Key Constraints:
     * Total traffic allocation must sum to 100%
     * Weighted average SLA must meet target requirements
   - Provides detailed routing plans and statistics

### Implementation Details

1. **Technology Stack**
   - Primary Language: Python
   - Optimization Library: PuLP
   - Data Structures: Dataclasses with immutability where appropriate
   - Type System: Strong typing with mypy support

2. **Key Features**
   - Cost-effective routing with SLA guarantees
   - Dynamic price change handling
   - Revenue impact analysis
   - Flexible configuration
   - Detailed reporting

3. **Project Structure**
```
working_befor_data/
├── app/
│   ├── api/         # API interfaces and strategies
│   ├── core/        # Core optimization logic
│   ├── models/      # Data models (Link, Profile)
│   ├── services/    # Business services
│   ├── tests/       # Test cases
│   └── utils/       # Utility functions
└── mock_data/       # Sample data for testing
```

### Event Handling System

1. **Event Types**
   - Price Changes: Updates to link pricing
   - Route Updates: Changes in routing configuration
   - SLA Updates: Updates to service level metrics

2. **Event Processing**
   - Asynchronous event handling
   - Priority-based processing
   - Event metadata tracking
   - Complete audit trail

3. **API Integration**
   - Strategy-based API selection
   - Multiple query support:
     * GetProfilesRelatedToLink: Finds profiles affected by link changes
     * GetLinksSLAByMNC: Retrieves SLA data for links by MNC
     * GetProfilesWithLinks: Gets complete profile-link associations
   - Mock API support for testing

4. **Event Flow Example (Price Change)**
   ```python
   # Event Creation
   event = handler.create_event(
       EventType.PRICE_CHANGE,
       data={
           "product_id": "450271",
           "old_price": 0.1011,
           "new_price": 0.2415,
           "status": "Increased"
       }
   )

   # Event Processing
   - Query affected profiles
   - Retrieve SLA data
   - Update link prices
   - Re-optimize routes
   - Track revenue impact
   ```

### Core Functionality

1. **Price Change Management**
   - Detection and processing of price updates
   - Historical price tracking
   - Impact analysis on routing decisions
   - Automatic re-optimization of affected profiles

2. **SLA Management**
   - Multiple SLA data sources support
   - Average SLA calculation
   - SLA requirement validation
   - Profile-based SLA targeting

3. **Optimization Process**
   - Linear programming model setup
   - Cost minimization with SLA constraints
   - Traffic allocation calculation
   - Results validation and reporting

4. **Reporting Capabilities**
   - Detailed routing plans
   - Cost and SLA statistics
   - Link utilization information
   - Revenue impact metrics

### System Benefits

1. **Cost Optimization**
   - Minimizes total routing costs
   - Maintains required service levels
   - Adapts to price changes
   - Provides revenue impact analysis

2. **Flexibility**
   - Supports multiple routing profiles
   - Handles dynamic price updates
   - Configurable SLA requirements
   - Adjustable link priorities

3. **Scalability**
   - Efficient data structures
   - Clean separation of concerns
   - Modular architecture
   - Comprehensive test coverage

4. **Maintainability**
   - Well-documented code
   - Strong type system
   - Clear error handling
   - Consistent coding style

### Future Enhancements

The system's modular design allows for several potential enhancements:

1. **Machine Learning Integration**
   - SLA prediction models
   - Price trend analysis
   - Traffic pattern optimization
   - Anomaly detection

2. **Advanced Optimization**
   - Multi-objective optimization
   - Real-time optimization
   - Capacity-aware routing
   - Geographic optimization

3. **Additional Features**
   - Advanced analytics dashboard
   - Real-time monitoring
   - Automated testing
   - Performance optimization

This system provides a robust foundation for managing and optimizing routing decisions while maintaining service quality and minimizing costs.