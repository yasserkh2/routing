# Routing Optimizer

A FastAPI-based web application for analyzing and optimizing routing decisions based on price changes and SLA requirements.

## Project Structure

```
routing_repo/
├── project_design/       # Project documentation and design decisions
├── src/                 # Source code
│   ├── app/            # Core application code
│   │   ├── api/       # API interfaces and strategies
│   │   ├── core/      # Core optimization logic
│   │   ├── models/    # Data models
│   │   ├── services/  # Business logic services
│   │   ├── tests/     # Test cases
│   │   └── utils/     # Utility functions
│   ├── mock_data/     # Mock data for testing
│   ├── web/           # Web interface
│   │   ├── server.py  # FastAPI server
│   │   └── index.html # Web UI
│   └── requirements.txt # Python dependencies
└── SYSTEM_OVERVIEW.md   # System architecture overview
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd src
pip install -r requirements.txt
```

## Running the Application

1. Start the FastAPI server:
```bash
cd src/web
python server.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:8000
```

## Features

- Real-time price change impact analysis
- SLA-aware routing optimization
- Interactive web interface for:
  - Submitting price changes
  - Viewing affected profiles
  - Analyzing cost and profit impacts
  - Monitoring SLA compliance

## Development

- Core optimization logic is in `src/app/core/`
- API interfaces and strategies in `src/app/api/`
- Data models in `src/app/models/`
- Mock services in `src/app/services/`
- Test cases in `src/app/tests/`

For detailed system architecture and design decisions, see the documentation in the `project_design/` directory.