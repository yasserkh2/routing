ai_ml_optimization_project/
│── src/
│   ├── api/                 # API Endpoints & Routing
│   │   ├── routes/          # Individual route handlers
│   │   │   ├── product_routes.py
│   │   │   ├── provider_routes.py
│   │   │   ├── pricing_routes.py
│   │   │   ├── optimization_routes.py
│   │   │   ├── decision_routes.py
│   │   │   ├── sla_routes.py
│   │   ├── main.py          # Main API Entry Point
│   │   ├── dependencies.py  # Common dependencies (DB, logging)
│   ├── models/              # Database ORM Models
│   │   ├── base.py          # Base class for all models
│   │   ├── provider.py      # Model for providers
│   │   ├── product.py       # Model for products
│   │   ├── pricing.py       # Model for price tracking
│   │   ├── sla_link.py      # Model for SLA network details
│   │   ├── optimization_result.py # Model for optimization results
│   │   ├── decision.py      # Model for decision storage
│   ├── services/            # Business Logic and Processing
│   │   ├── pricing_service.py   # Handles price data processing
│   │   ├── ai_service.py        # AI/ML model serving & predictions
│   │   ├── optimization_service.py # Runs linear optimization
│   │   ├── decision_service.py  # Manages business logic for decisions
│   ├── database/            # Database Configuration & Setup
│   │   ├── database.py      # Database connection & session management
│   │   ├── redis_cache.py   # Redis caching setup
│   ├── config/              # Configuration Files
│   │   ├── config.py        # Global application settings
│   │   ├── logging_config.py# Logging configuration
│   ├── utils/               # Utility Functions & Helpers
│   │   ├── data_loader.py   # Loads initial data
│   │   ├── event_handler.py # Handles event-driven actions
│   ├── tests/               # Unit & Integration Tests
│   │   ├── test_api.py      # Tests API endpoints
│   │   ├── test_ml.py       # Tests AI model predictions
│   │   ├── test_optimization.py # Tests optimization logic
│── .env                     # Environment Variables
│── requirements.txt          # Dependencies
│── Dockerfile                # Docker Container Configuration
│── docker-compose.yml        # Multi-container Setup
│── README.md                 # Project Documentation
