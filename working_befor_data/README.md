# Routing Project

## Recent Updates (May 2025)

### Data Model Enhancements
- Migrated to new combined data format using `api_round_2_reorganized_links_no_sla.json`
- Added comprehensive data validation
- Enhanced error handling
- Improved type safety

### Profile Model
The Profile class handles profile-specific data extraction and validation:

#### Data Fields:
- Basic Information:
  * profile_id
  * name
  * expected_sla (0-100%)
  * description
- Pricing Information:
  * sell_price_min (non-negative)
  * sell_price_max (must be ≥ min)
  * profile_avg_cost (non-negative)
- Network Information:
  * mcc (Mobile Country Code)
  * mnc (Mobile Network Code)
- Link References:
  * in_use_links (list of link names)
  * alternative_links (list of link names)

#### Validation:
- Required field checks
- Numeric range validation
- Price consistency checks
- Type validation

### Link Model
The Link class handles link-specific data extraction and validation:

#### Data Fields:
- Basic Information:
  * link (ID)
  * provider
  * buy_price (non-negative)
- Performance Metrics:
  * sla_dd (0-100%)
  * tier (positive integer)
  * traffic (0-100%)
  * last_updated (timestamp)

#### Validation:
- Required field checks
- SLA range validation (0-100%)
- Traffic distribution validation (0-100%)
- Tier validation (must be positive)
- Price validation (non-negative)
- Timestamp parsing

### Testing
Added comprehensive test suite:
- test_profile_output.py: Verifies profile data extraction
- test_link_output.py: Verifies link data extraction
- test_data_validation.py: Validates error handling and data constraints

## Project Overview
This project implements an intelligent routing system that optimizes message routing based on:
- SLA requirements
- Cost considerations
- Link availability
- Traffic distribution

## Key Components
- Data Models (Profile, Link)
- Optimization Engine
- API Interface
- Mock Services for testing
- Event System for real-time updates

## Setup and Running

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
python -m app.tests.test_profile_output  # Test profile data extraction
python -m app.tests.test_link_output     # Test link data extraction
python -m app.tests.test_data_validation # Test data validation
```

## Project Structure
```
working_befor_data/
├── app/
│   ├── models/          # Data models (Profile, Link)
│   ├── core/           # Core optimization logic
│   ├── services/       # Services including data preparation
│   ├── api/           # API interfaces and implementation
│   └── tests/         # Test suite
├── mock_data/         # Test data files
└── web_interface/     # Web UI for visualization
```

## Data Format
The system now uses a combined data format that includes:
- Profile configuration
- In-use links with traffic distribution
- Alternative links for backup
- SLA and pricing information

Example:
```json
{
  "profile_id": "PROF_001",
  "name": "Ultra_Premium_OTP",
  "expected_sla": 96.0,
  "description": "Ultra premium OTP service",
  "sell_price_min": 12.0,
  "sell_price_max": 18.0,
  "profile_avg_cost": 7.2,
  "mcc": "426",
  "mnc": "01",
  "in_use_links": [...],
  "alternative_links": [...]
}
