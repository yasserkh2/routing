# API Directory

This directory handles all API-related functionality for the SLA routing system.

## Components

- `main.py`: FastAPI application with endpoints for SLA metrics and profile configurations
- `api_interfaces.py`: Core interfaces for API responses and clients
- `api_caller.py`: Direct implementation of API calls and response aggregation

## Key Features

- Simple and direct API calls without strategy patterns
- Two main API endpoints:
  * Get SLA data for links
  * Get profile configurations
- Automatic execution of all APIs for each event
- Optional filtering by MNC or profile ID
- Mock data integration for development and testing
- Standardized API response format