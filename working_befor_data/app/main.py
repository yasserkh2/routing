from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
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
            "available_profiles": "/api/profiles/available - Get available profiles with network coverage",
            "profile_sla": "/api/profiles/sla - Get product SLA expectations",
            "links_sla": "/api/links/sla - Get SLA measurements for links",
            "sla": "/api/routes/{mcc}/{mnc}/sla - Get SLA data for specific route",
            "summary": "/api/routes/summary - Get SLA coverage statistics",
            "price_changes": "/api/routes/price-changes - Get routes with price changes"
        }
    }

@app.get("/api/routes")
async def get_routes(
    product_name: Optional[str] = Query(None, description="Filter by product name"),
    mcc: Optional[str] = Query(None, description="Filter by Mobile Country Code"),
    mnc: Optional[str] = Query(None, description="Filter by Mobile Network Code")
):
    """Get routes with their SLA information from all sources"""
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
    """Get product profiles with their route counts and SLA coverage statistics"""
    try:
        profiles = mock_api.get_profiles()
        return {
            "count": len(profiles),
            "profiles": profiles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/available")
async def get_available_profiles(
    mcc: Optional[str] = Query(None, description="Filter by Mobile Country Code"),
    mnc: Optional[str] = Query(None, description="Filter by Mobile Network Code")
):
    """Get available profiles with their network coverage"""
    try:
        network = {}
        if mcc:
            network['mcc'] = mcc
        if mnc:
            network['mnc'] = mnc
        return mock_api.get_available_profiles(network if network else None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/sla")
async def get_profile_sla(
    product_name: Optional[str] = Query(None, description="Filter by product name")
):
    """Get SLA expectations and thresholds for products"""
    try:
        return mock_api.get_profile_sla(product_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/links/sla")
async def get_links_sla(
    product_name: Optional[str] = Query(None, description="Filter by product name"),
    status: Optional[str] = Query(None, description="Filter by status (Healthy/Warning/Critical)"),
    mcc: Optional[str] = Query(None, description="Filter by Mobile Country Code"),
    mnc: Optional[str] = Query(None, description="Filter by Mobile Network Code"),
    provider: Optional[str] = Query(None, description="Filter by provider name")
):
    """Get SLA measurements for links grouped by profile"""
    try:
        network = {}
        if mcc:
            network['mcc'] = mcc
        if mnc:
            network['mnc'] = mnc
        return mock_api.get_links_sla(product_name, status, network if network else None, provider)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/routes/{mcc}/{mnc}/sla")
async def get_route_sla(
    mcc: str,
    mnc: str,
    product_name: Optional[str] = Query(None, description="Filter by product name")
):
    """Get SLA information for routes with specific MCC/MNC combination"""
    try:
        result = mock_api.get_route_sla(mcc, mnc, product_name)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No routes found for MCC: {mcc}, MNC: {mnc}"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/routes/summary")
async def get_routes_summary():
    """Get summary statistics about routes and their SLA coverage"""
    try:
        return mock_api.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/routes/price-changes")
async def get_price_changes(
    status: Optional[str] = Query(None, description="Filter by price change status (Increased/Decreased)"),
    min_margin: Optional[float] = Query(None, description="Filter by minimum margin percentage"),
    max_margin: Optional[float] = Query(None, description="Filter by maximum margin percentage")
):
    """Get routes with price changes, filtered by status and margin range"""
    try:
        return mock_api.get_price_changes(status, min_margin, max_margin)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mock/refresh")
async def refresh_mock_data():
    """Refresh the mock data (for testing purposes)"""
    try:
        mock_api.refresh_mock_data()
        return {"message": "Mock data refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)