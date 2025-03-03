# Price Change Event System Documentation

## Overview

The system is designed to handle price change events efficiently, focusing on detecting price updates, identifying affected profiles, and optimizing routes accordingly.

## Implementation

### Price Change Event
The system processes price changes with the following information:
- Link ID
- Old and new prices
- Provider and network details
- SLA metrics (DD, Tested, Assumed)
- Timestamp

## Key Components

### 1. Price Change Handler
- Processes price change events
- Updates link pricing
- Identifies affected profiles
- Triggers route optimization

### 2. API Integration

#### API Selector
- Coordinates API strategy selection
- Components:
  * DefaultAPIRegistry: Manages API strategies
  * DefaultAPIExecutor: Executes API calls
  * APISelector: Orchestrates the process

#### API Strategies
- GetLinksSLADataStrategy: Retrieves SLA data
- GetProfileConfigStrategy: Manages profile configurations

### 3. Price Change Flow Example

```python
# Create event handler
handler = EventHandler()

# Process price change
event = handler.create_event(
    EventType.PRICE_CHANGE,
    data={
        'link_id': 'LINK_021',
        'old_price': 0.2050,
        'new_price': 0.1890,
        'provider': 'MessageBird',
        'network': 'Stc Bahrain',
        'mnc': '21'
    }
)

# Process through API service
api_selector = APISelector()
results = await api_selector.execute_strategies(event)
```

### 4. API Queries

The system implements two main queries:

1. **GetProfilesRelatedToLink**
   - Input: link ID, MNC
   - Output: Profiles using the specified link
   - Purpose: Identify affected profiles when price changes

2. **GetLinksSLAByMNC**
   - Input: MNC
   - Output: SLA data for all links in the MNC
   - Purpose: Retrieve SLA information for optimization

### 5. Test Files

1. **price_change_example.py**
   - Shows complete price change handling flow
   - Includes mock API service integration

2. **price_change_profile_example.py**
   - Demonstrates profile updates due to price changes
   - Shows optimization results

### 6. Mock Services

The `mock_services.py` provides mock implementations for testing:
- MockAPIService for simulating API calls
- Mock data files:
  * price_changes.json: Price change events
  * links_data.json: Link information
  * profiles.json: Profile configurations

## Price Change Processing Flow

1. **Event Creation**
   - Price change event created with new price data
   - Timestamp and metadata added

2. **Profile Identification**
   - System identifies profiles using the affected link
   - Retrieves current routing configurations

3. **Route Optimization**
   - For each affected profile:
     * Captures current routing plan
     * Updates link price
     * Re-runs optimization
     * Calculates cost impact

4. **Results Analysis**
   - Compares before/after routing plans
   - Calculates cost savings
   - Updates routing if beneficial

## Example Output

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

AFTER PRICE CHANGE:
Link LINK_021:
  Traffic:    86.7%
  SLA:        79.2%
  Price:      $0.189
Link LINK_017:
  Traffic:    13.3%
  SLA:        85.4%
  Price:      $0.210

COST IMPACT:
Savings:      $0.003
Percentage:   1.5%