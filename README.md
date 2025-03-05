# AI/ML Optimization Project

This project aims to provide an AI/ML-powered optimization solution for product pricing and decision-making. It includes the following components:

## Server
- **server/**: Contains the FastAPI server and web interface
  - **server.py**: FastAPI server implementation for handling price change analysis
  - **index.html**: Web interface for interacting with the optimization system

### Running the Server
1. Install dependencies:
```bash
pip install fastapi uvicorn
```

2. Run the server:
```bash
python server/server.py
```
The server will start at http://127.0.0.1:8000

3. Access the web interface at: http://127.0.0.1:8000

## API
- **routes/**: Individual route handlers for different functionality (products, providers, pricing, optimization, decisions, SLAs)
- **main.py**: Main API entry point
- **dependencies.py**: Common dependencies like database and logging

## Models
- **base.py**: Base class for all database models
- **provider.py**: Model for provider data
- **product.py**: Model for product data
- **pricing.py**: Model for price tracking
- **sla_link.py**: Model for SLA network details
- **optimization_result.py**: Model for optimization results
- **decision.py**: Model for decision storage

## Services
- **pricing_service.py**: Handles price data processing
- **ai_service.py**: AI/ML model serving and predictions
- **optimization_service.py**: Runs linear optimization
- **decision_service.py**: Manages business logic for decisions

## Database
- **database.py**: Database connection and session management
- **redis_cache.py**: Redis caching setup

## Config
- **config.py**: Global application settings
- **logging_config.py**: Logging configuration

## Utils
- **data_loader.py**: Loads initial data
- **event_handler.py**: Handles event-driven actions

## Tests
- **test_api.py**: Tests API endpoints
- **test_ml.py**: Tests AI model predictions
- **test_optimization.py**: Tests optimization logic

## Other Files
- **.env**: Environment variables
- **requirements.txt**: Dependencies
- **Dockerfile**: Docker container configuration
- **docker-compose.yml**: Multi-container setup