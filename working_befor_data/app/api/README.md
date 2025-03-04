# API Directory

This directory handles all API-related functionality for the SLA routing system.

## Components

- `main.py`: FastAPI application with endpoints for SLA metrics and profile configurations
- `api_interfaces.py`: Core interfaces and data structures for API responses and clients
- `api_strategy.py`: Implementation of data fetching strategies for different API endpoints
- `api_selector.py`: Handles API calls and response processing

## Key Features

- Simple API endpoints that return complete datasets
- Optional filtering by MNC or profile ID
- Mock data integration for development and testing
- Standardized API response format