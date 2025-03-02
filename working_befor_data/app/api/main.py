from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from ..services.mock_services import MockAPIService

app = FastAPI(
    title="Routing SLA API",
    description="API for retrieving link SLA data and profile configurations",
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
            "links_sla": "/api/links/sla - Get SLA metrics for links",
            "profiles": "/api/profiles - Get routing profile configurations"
        }
    }

@app.get("/api/links/sla")
async def get_links_sla(mnc: Optional[str] = None):
    """
    Get SLA metrics for links
    
    This endpoint retrieves SLA data (dd, tested, assumed) for all links,
    optionally filtered by MNC.
    
    Args:
        mnc: Optional MNC code to filter links
        
    Returns:
        List of links with their SLA metrics
    """
    try:
        data = await mock_api.get_links_sla_data(mnc)
        return {
            "success": True,
            "count": len(data),
            "links": data,
            "metadata": {
                "filtered_by_mnc": mnc is not None,
                "mnc": mnc
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Failed to retrieve link SLA data"
            }
        )

@app.get("/api/profiles")
async def get_profiles(profile_id: Optional[str] = None):
    """
    Get routing profile configurations
    
    This endpoint retrieves routing profiles with their configurations,
    optionally filtered by profile ID.
    
    Args:
        profile_id: Optional profile ID to get specific profile
        
    Returns:
        List of routing profiles with their configurations
    """
    try:
        data = await mock_api.get_profile_config(profile_id)
        return {
            "success": True,
            "count": len(data),
            "profiles": data,
            "metadata": {
                "filtered_by_id": profile_id is not None,
                "profile_id": profile_id
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Failed to retrieve profile configurations"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)