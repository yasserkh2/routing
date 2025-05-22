from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import json
from datetime import datetime

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.mock_services import MockAPIService
from app.services.data_preparation_service import DataPreparationService
from app.core.optimizer import RoutingOptimizer
from app.models.profile import Profile
from app.models.link import Link
from app.utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LinkRequest(BaseModel):
    link: str
    mcc: str
    mnc: str

@app.get("/")
async def read_root():
    static_dir = os.path.dirname(os.path.abspath(__file__))
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.post("/api/profiles/links")
async def get_profile_links(request: LinkRequest):
    try:
        # Initialize services
        mock_api = MockAPIService()
        
        # Get data directly from mock API
        data = await mock_api.get_combined_data()
        
        # Filter profiles by MCC and MNC
        matching_profiles = [
            profile for profile in data 
            if profile['mcc'] == request.mcc and profile['mnc'] == request.mnc
        ]
        
        if not matching_profiles:
            return JSONResponse(content=[], status_code=200)
        
        # Create Profile object and optimize for each matching profile
        optimized_profiles = []
        for profile_data in matching_profiles:
            try:
                # Create Profile object using from_api_data
                profile = Profile.from_api_data(profile_data)
                logger.info(f"Created profile object for {profile_data['profile_id']}")
                
                # Initialize and run optimizer
                optimizer = RoutingOptimizer(profile)
                if await optimizer.solve():
                    # Get optimization results
                    routing_plan = await optimizer.get_routing_plan()
                    stats = await optimizer.get_optimization_stats()
                    
                # Get tier-based SLA mapping
                tier_sla_mapping = {
                    1: 99.0,  # 99% SLA for tier 1
                    2: 95.0,  # 95% SLA for tier 2
                    3: 90.0   # 90% SLA for tier 3
                }

                # Update traffic percentages and SLAs in profile data
                for link in profile_data['in_use_links']:
                    # Calculate SLA based on tier
                    tier = link.get('tier', 3)
                    tier_sla = tier_sla_mapping.get(tier, 90.0)
                    
                    # Calculate final SLA (average of DD and tier if DD exists)
                    dd_sla = link.get('sla_dd', 0)
                    link['sla'] = (dd_sla + tier_sla) / 2 if dd_sla > 0 else tier_sla
                    
                    # Update traffic from optimization results
                    link['traffic'] = 0  # Default to 0
                    for route in routing_plan['routes']:
                        if route['link'] == link['link']:
                            link['traffic'] = route['percentage']
                            break

                # Update SLAs for alternative links
                for link in profile_data['alternative_links']:
                    # Calculate SLA based on tier
                    tier = link.get('tier', 3)
                    tier_sla = tier_sla_mapping.get(tier, 90.0)
                    link['sla'] = tier_sla
                    link['traffic'] = 0  # Alternative links have 0 traffic
                
                optimized_profiles.append(profile_data)
                
            except Exception as e:
                logger.error(f"Error processing profile {profile_data.get('profile_id', 'unknown')}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error processing profile: {str(e)}")
            
        return JSONResponse(content=optimized_profiles, status_code=200)
        
    except Exception as e:
        logger.error(f"Error in get_profile_links: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files after routes
static_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8004)