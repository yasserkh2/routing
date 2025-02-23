# Routing Optimization Project - Working Before Data

## API Structure

### 1. Root Endpoint
```
GET /

Response 200:
{
    "name": "Routing SLA API",
    "version": "1.0.0",
    "status": "operational",
    "endpoints": {
        "routes": "/api/routes - Get routes with SLA data",
        "profiles": "/api/profiles - Get product profiles with SLA coverage",
        "sla": "/api/routes/{mcc}/{mnc}/sla - Get SLA data for specific route",
        "summary": "/api/routes/summary - Get SLA coverage statistics"
    }
}
```

### 2. Get All Routes
```
GET /api/routes

Query Parameters:
- product_name (optional): Filter by product name
- mcc (optional): Filter by Mobile Country Code
- mnc (optional): Filter by Mobile Network Code

Response 200:
{
    "count": 20,
    "routes": [
        {
            "reference_id": "450000",
            "product_name": "Cequens_Premium_EUR",
            "provider_name": "Twilio",
            "name": "Cequens_STC Kuwait_Twilio",
            "network_name": "STC Kuwait",
            "mcc": "419",
            "mnc": "2",
            "old_rate": 0.0717,
            "new_rate": 0.0725,
            "margin_percentage": 1.12,
            "price_change_status": "Increased",
            "created_on": "2025-01-26T20:54:45.611681",
            "sla_dd": null,
            "sla_tested": null,
            "sla_assumed": 96.0
        }
    ]
}

Error Response 500:
{
    "detail": "Internal server error message"
}
```

### 3. Get Product Profiles
```
GET /api/profiles

Response 200:
{
    "count": integer,
    "profiles": [
        {
            "product_name": string,
            "route_count": integer,
            "average_margin": float,
            "dd_coverage": float,
            "test_coverage": float
        }
    ]
}

Error Response 500:
{
    "detail": "Internal server error message"
}
```

### 4. Get Route SLA Data
```
GET /api/routes/{mcc}/{mnc}/sla

Path Parameters:
- mcc: Mobile Country Code
- mnc: Mobile Network Code

Query Parameters:
- product_name (optional): Filter by product name

Response 200:
{
    "mcc": string,
    "mnc": string,
    "products": {
        "product_name": {
            "routes": [Route],
            "sla_dd_available": integer,
            "sla_tested_available": integer,
            "average_sla_dd": float,
            "average_sla_tested": float,
            "sla_assumed": float
        }
    }
}

Error Response 404:
{
    "detail": "No routes found for MCC: {mcc}, MNC: {mnc}"
}

Error Response 500:
{
    "detail": "Internal server error message"
}
```

### 5. Get Routes Summary
```
GET /api/routes/summary

Response 200:
{
    "total_routes": integer,
    "sla_coverage": {
        "datadog": float,
        "tested": float,
        "assumed": float
    },
    "unique_products": integer,
    "unique_networks": integer,
    "timestamp": string (ISO format)
}

Error Response 500:
{
    "detail": "Internal server error message"
}
```

### 6. Refresh Mock Data
```
POST /api/mock/refresh

Response 200:
{
    "message": "Mock data refreshed successfully"
}

Error Response 500:
{
    "detail": "Internal server error message"
}
```

## Mock Data Structure

### SLA Data Sources

1. **Datadog API (MockDatadogAPI)**
   - Coverage: 30% of routes
   - SLA Range: 95.0-99.9%
   - Returns: Optional[float]

2. **Auto Router V1 (MockAutoRouterAPI)**
   - Coverage: 40% of routes
   - SLA Range: 90.0-99.0%
   - Returns: Optional[float]

3. **Tiering Data (MockTieringAPI)**
   - Coverage: 100% (fallback)
   - Tier Mapping:
     * Europe (MCC 100-299): 98.5%
     * North America (MCC 300-499): 96.0%
     * Asia & Africa (MCC 500-799): 94.0%
   - Returns: float

### Route Data Structure

```python
{
    "reference_id": str,          # Format: "45XXXX"
    "product_name": str,          # e.g., "Cequens_Premium_EUR"
    "provider_name": str,         # e.g., "Twilio"
    "name": str,                  # Combined name
    "network_name": str,          # e.g., "Vodafone Egypt"
    "mcc": str,                   # Mobile Country Code
    "mnc": str,                   # Mobile Network Code
    "old_rate": float,           # Previous rate
    "new_rate": float,           # Current rate
    "margin_percentage": float,   # Rate change percentage
    "price_change_status": str,   # "Increased" or "Decreased"
    "created_on": str,           # ISO format datetime
    "sla_dd": Optional[float],   # Datadog SLA if available
    "sla_tested": Optional[float], # Test results if available
    "sla_assumed": float         # Tiering-based SLA
}
```

## Setup and Running

1. Create virtual environment:
```bash
cd working_befor_data
python -m venv venv
```

2. Activate virtual environment:
```bash
source venv/Scripts/activate  # Git Bash
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the FastAPI server:
```bash
python -m uvicorn app.main:app --reload
```

## Testing the API

Basic tests with curl:

```bash
# Get all routes
curl http://localhost:8000/api/routes

# Get profiles
curl http://localhost:8000/api/profiles

# Get SLA for specific route
curl http://localhost:8000/api/routes/602/2/sla

# Get summary statistics
curl http://localhost:8000/api/routes/summary

# Filter routes by product
curl http://localhost:8000/api/routes?product_name=Talabat_Jordan

# Refresh mock data
curl -X POST http://localhost:8000/api/mock/refresh
```

For prettier JSON output:
```bash
curl http://localhost:8000/api/routes | python -m json.tool