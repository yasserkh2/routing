from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
from datetime import datetime

from .mock_services import MockAPIService

app = FastAPI(
    title="Routing SLA API",
    description="API for retrieving and analyzing route SLA data from multiple sources",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize mock service
mock_api = MockAPIService()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
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

@app.get("/api/routes")
async def get_routes(
    product_name: Optional[str] = Query(None, description="Filter by product name"),
    mcc: Optional[str] = Query(None, description="Filter by Mobile Country Code"),
    mnc: Optional[str] = Query(None, description="Filter by Mobile Network Code")
):
    """
    Get routes with their SLA information from all sources.
    Optionally filter by product_name, mcc, or mnc.
    """
    try:
        routes = mock_api.get_routes_with_sla(product_name, mcc, mnc)
        return {
            "count": len(routes),
            "routes": routes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles")
async def get_profiles():
    """
    Get product profiles with their route counts and SLA coverage statistics
    """
    try:
        profiles = mock_api.get_profiles()
        return {
            "count": len(profiles),
            "profiles": profiles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/routes/{mcc}/{mnc}/sla")
async def get_route_sla(
    mcc: str,
    mnc: str,
    product_name: Optional[str] = Query(None, description="Filter by product name")
):
    """
    Get SLA information for routes with specific MCC/MNC combination.
    Optionally filter by product_name.
    """
    try:
        routes = mock_api.get_routes_with_sla(product_name=product_name, mcc=mcc, mnc=mnc)
        if not routes:
            raise HTTPException(
                status_code=404,
                detail=f"No routes found for MCC: {mcc}, MNC: {mnc}"
            )
            
        # Group SLA data by product
        sla_by_product = {}
        for route in routes:
            product = route['product_name']
            if product not in sla_by_product:
                sla_by_product[product] = {
                    'routes': [],
                    'sla_dd_available': 0,
                    'sla_tested_available': 0,
                    'average_sla_dd': 0,
                    'average_sla_tested': 0,
                    'sla_assumed': route['sla_assumed']  # Same for all routes with same MCC/MNC
                }
            
            product_data = sla_by_product[product]
            product_data['routes'].append(route)
            
            if route['sla_dd'] is not None:
                product_data['sla_dd_available'] += 1
                product_data['average_sla_dd'] += route['sla_dd']
                
            if route['sla_tested'] is not None:
                product_data['sla_tested_available'] += 1
                product_data['average_sla_tested'] += route['sla_tested']
        
        # Calculate averages
        for product_data in sla_by_product.values():
            if product_data['sla_dd_available'] > 0:
                product_data['average_sla_dd'] /= product_data['sla_dd_available']
            if product_data['sla_tested_available'] > 0:
                product_data['average_sla_tested'] /= product_data['sla_tested_available']
                
            # Round averages
            product_data['average_sla_dd'] = round(product_data['average_sla_dd'], 2)
            product_data['average_sla_tested'] = round(product_data['average_sla_tested'], 2)
            
        return {
            "mcc": mcc,
            "mnc": mnc,
            "products": sla_by_product
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/routes/summary")
async def get_routes_summary():
    """
    Get summary statistics about routes and their SLA coverage
    """
    try:
        routes = mock_api.get_routes_with_sla()
        total_routes = len(routes)
        
        if total_routes == 0:
            return {
                "total_routes": 0,
                "sla_coverage": {
                    "datadog": 0,
                    "tested": 0,
                    "assumed": 100  # Always available
                },
                "unique_products": 0,
                "unique_networks": 0
            }

        # Calculate statistics
        routes_with_dd = sum(1 for r in routes if r['sla_dd'] is not None)
        routes_with_tested = sum(1 for r in routes if r['sla_tested'] is not None)
        unique_products = len(set(r['product_name'] for r in routes))
        unique_networks = len(set((r['mcc'], r['mnc']) for r in routes))
        
        return {
            "total_routes": total_routes,
            "sla_coverage": {
                "datadog": round(routes_with_dd / total_routes * 100, 2),
                "tested": round(routes_with_tested / total_routes * 100, 2),
                "assumed": 100  # Always available through tiering
            },
            "unique_products": unique_products,
            "unique_networks": unique_networks,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mock/refresh")
async def refresh_mock_data():
    """
    Refresh the mock data (for testing purposes)
    """
    try:
        mock_api.refresh_mock_data()
        return {"message": "Mock data refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)