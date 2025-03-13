# Routing Optimization System

## Overview
This system provides routing optimization capabilities with support for analyzing both price changes and SLA changes through a unified event-based interface.

## Components

### Event Server
Located in `web_interface/event_server.py`, this is a unified server that handles both price and SLA change events. It provides:
- Single endpoint `/analyze-event` for processing both types of events
- Comprehensive analysis of changes' impact on routing
- Profile-level impact assessment

### Event Interface
Located in `web_interface/event_index.html`, this provides a user-friendly interface for:
- Price Change Analysis
  - Input old and new rates
  - View impact on routing and costs
  - Analyze profit changes
- SLA Change Analysis
  - Input changes for DD, Tested, and Assumed SLA
  - View impact on routing quality
  - Analyze SLA achievement levels

## API Endpoints

### POST /analyze-event
Analyzes the impact of price or SLA changes on routing.

#### Request Format for Price Change
```json
{
  "Type": "price",
  "Payload": {
    "old_rate": 4.5,
    "new_rate": 5.0,
    "status": "updated"
  },
  "link": "LINK_001",
  "mcc": "426",
  "mnc": "01",
  "timestamp": "2025-03-13T16:30:00Z"
}
```

#### Request Format for SLA Change
```json
{
  "Type": "sla",
  "Payload": {
    "changed_sla": {
      "DD": {
        "old": 99.0,
        "new": 97.0
      },
      "Tested": {
        "old": 99.0,
        "new": 97.0
      },
      "Assumed": {
        "old": 99.0,
        "new": 97.0
      }
    },
    "status": "updated"
  },
  "link": "LINK_001",
  "mcc": "426",
  "mnc": "01",
  "timestamp": "2025-03-13T16:30:00Z"
}
```

## Features
- Unified event handling for both price and SLA changes
- Real-time impact analysis
- Profile-specific optimization
- Detailed routing analysis including:
  - Cost impact
  - Profit changes
  - SLA achievement levels
  - Traffic distribution
  - Route optimization

## Running the System

1. Start the event server:
```bash
python web_interface/event_server.py
```

2. Access the interface:
- Open a browser and navigate to `http://localhost:8000`
- Select the type of event to analyze (Price or SLA)
- Enter the required details
- View comprehensive analysis results

## Analysis Results
The system provides detailed analysis including:
- Affected profiles count
- Before/After comparisons
- Cost and profit impact
- SLA achievement levels
- Traffic distribution changes
- Optimization recommendations

## Error Handling
- Input validation for all fields
- Proper error messages for invalid requests
- Fallback options for optimization failures

## Dependencies
- FastAPI for the backend server
- Python 3.8+ for core functionality
- Modern web browser for the interface