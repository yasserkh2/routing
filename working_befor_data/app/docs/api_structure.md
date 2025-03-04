# API Directory Structure

The API directory provides a simple structure to call all available APIs:

## 1. main.py - FastAPI Application
- Two straightforward endpoints that always return all data:
  - `/api/links/sla`: Gets all SLA metrics (with optional MNC filter)
  - `/api/profiles`: Gets all profile configurations (with optional profile ID filter)
- Uses MockAPIService to fetch data

## 2. api_interfaces.py - Core Data Structures
- Defines APIResponse for standardized responses
- Provides APIClient interface for making API calls

## 3. api_strategy.py - Data Fetching Implementation
- GetLinksSLADataStrategy: Fetches all SLA data from mock_links_data.json
- GetProfileConfigStrategy: Fetches all profile data from mock_profiles.json
- Currently uses mock data but designed to easily switch to real API calls

The system simply fetches all available data from each API endpoint, with optional filtering parameters. There's no complex routing or selection logic - all APIs are called to get their complete datasets, which can then be filtered as needed by the consuming service.