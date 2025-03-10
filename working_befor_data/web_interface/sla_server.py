from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict
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

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_root():
    return FileResponse(os.path.join(static_dir, "sla.html"))

class SLAChangePayload(BaseModel):
    changed_sla: Dict[str, Dict[str, float]]  # e.g. {"DD": {"old": 75.0, "new": 78.0}}
    status: str

class SLAChangeRequest(BaseModel):
    Type: str
    Payload: SLAChangePayload
    link: str
    mcc: str
    mnc: str
    timestamp: Optional[str] = None

@app.post("/analyze-sla-change")
async def analyze_sla_change(request: SLAChangeRequest):
    try:
        # Initialize services
        mock_api = MockAPIService()
        data_service = DataPreparationService()
        
        # Process the SLA change
        link_name = request.link
        changed_sla = request.Payload.changed_sla
        status = request.Payload.status
        
        try:
            # Handle SLA change in mock service first
            print(f"Handling SLA change for link {link_name}")
            print(f"Changed SLA data: {changed_sla}")
            mock_api.handle_sla_change(link_name, changed_sla)
            print("SLA change handled in mock service")
            
            # Get all profiles after SLA update
            print("Getting all profiles")
            all_profiles = await data_service.get_all_profiles()
            print(f"Got {len(all_profiles)} profiles")
        except Exception as e:
            print(f"Error in initial processing: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error in initial processing: {str(e)}")
        
        # Find affected profiles
        affected_profiles = Profile.get_profiles_affected_by_price_change(all_profiles, link_name)
        
        results = {
            "sla_change": {
                "link": link_name,
                "changes": {},
                "status": status,
                "affected_profiles_count": len(affected_profiles)
            },
            "profiles": []
        }
        
        # Add SLA changes to results
        for sla_type, values in changed_sla.items():
            results["sla_change"]["changes"][sla_type] = {
                "old": values["old"],
                "new": values["new"],
                "difference": values["new"] - values["old"]
            }
        
        # Process each affected profile
        for profile in affected_profiles:
            profile_result = {
                "name": profile.name,
                "expected_sla": profile.expected_sla,
                "available_links": len(profile.links),
                "before": {},
                "after": {}
            }
            
            try:
                print(f"\nOptimizing profile {profile.name} with expected SLA {profile.expected_sla}%")
                # Run initial optimization with old SLA values
                optimizer = RoutingOptimizer(profile)
                success = optimizer.solve()
                
                if success:
                    print("Initial optimization successful")
                    # Get initial results with old SLA values
                    initial_plan = optimizer.get_routing_plan()
                    initial_stats = optimizer.get_optimization_stats()
                    print(f"Initial achieved SLA: {initial_stats['achieved_sla']}%")
                else:
                    print("Initial optimization failed")
                    raise ValueError("Failed to find initial optimal solution")
            except Exception as e:
                print(f"Error in initial optimization: {str(e)}")
                raise
                
            try:
                # Calculate initial metrics
                active_links = 0
                routes_info = []
                
                for route in initial_plan['routes']:
                    if route['percentage'] > 0:
                        active_links += 1
                        current_link = Link.find_by_id(profile.links, route['link'])
                        if current_link:
                            route_info = current_link.format_display_info(route['percentage'])
                            routes_info.append(route_info)
                
                profile_result["before"] = {
                    "routes": routes_info,
                    "active_links": active_links,
                    "achieved_sla": initial_stats.get('achieved_sla', 0.0),
                    "sla_achievable": initial_stats.get('sla_achievable', False),
                    "max_achievable_sla": initial_stats.get('max_achievable_sla', 0.0)
                }
            except Exception as e:
                print(f"Error calculating initial metrics: {str(e)}")
                raise
            
            try:
                print("\nSimulating SLA change...")
                # Create a temporary copy of the profile for simulation
                updated_profile = profile.clone()
                
                # Update the SLA in the temporary profile without persisting
                target_link = Link.find_by_id(updated_profile.links, link_name)
                if target_link:
                    print(f"Found target link {link_name} in profile")
                    # Update the link with new SLA values
                    updated_link = target_link.update_sla(changed_sla)
                    print(f"Updated link SLA values: DD={updated_link.sla_dd}, Tested={updated_link.sla_tested}, Assumed={updated_link.sla_assumed}")
                    # Update the link in the temporary profile
                    updated_profile.links = [updated_link if l.link == link_name else l for l in updated_profile.links]
                else:
                    print(f"Target link {link_name} not found in profile")
                    raise ValueError(f"Link {link_name} not found in profile {profile.name}")
                
                optimizer = RoutingOptimizer(updated_profile)
                success = optimizer.solve()
                if not success:
                    print("Optimization after SLA change failed")
                    raise ValueError("Failed to find optimal solution after SLA change")
                print("Optimization after SLA change successful")
            except Exception as e:
                print(f"Error in SLA change simulation: {str(e)}")
                raise
            
            if success:
                after_plan = optimizer.get_routing_plan()
                after_stats = optimizer.get_optimization_stats()
                
                # Calculate after metrics
                active_links = 0
                routes_info = []
                
                for route in after_plan['routes']:
                    if route['percentage'] > 0:
                        active_links += 1
                        current_link = Link.find_by_id(updated_profile.links, route['link'])
                        if current_link:
                            route_info = current_link.format_display_info(route['percentage'])
                            routes_info.append(route_info)
                
                profile_result["after"] = {
                    "routes": routes_info,
                    "active_links": active_links,
                    "achieved_sla": after_stats.get('achieved_sla', 0.0),
                    "sla_achievable": after_stats.get('sla_achievable', False),
                    "max_achievable_sla": after_stats.get('max_achievable_sla', 0.0),
                    "sla_impact": {
                        "absolute": after_stats.get('achieved_sla', 0.0) - initial_stats.get('achieved_sla', 0.0),
                        "percentage": ((after_stats.get('achieved_sla', 0.0) - initial_stats.get('achieved_sla', 0.0)) / initial_stats.get('achieved_sla', 1.0)) * 100 if initial_stats.get('achieved_sla', 0.0) > 0 else 0.0
                    }
                }
                
                # Add routing changes analysis
                traffic_shifts = []
                for before_route in profile_result["before"]["routes"]:
                    before_traffic = before_route["traffic"]
                    after_route = next((r for r in profile_result["after"]["routes"] if r["link"] == before_route["link"]), None)
                    after_traffic = after_route["traffic"] if after_route else 0
                    if abs(after_traffic - before_traffic) > 0.1:  # Only show significant changes (>0.1%)
                        traffic_shifts.append({
                            "link": before_route["link"],
                            "before": before_traffic,
                            "after": after_traffic,
                            "change": after_traffic - before_traffic
                        })
                
                if traffic_shifts:
                    profile_result["after"]["traffic_shifts"] = traffic_shifts
            
            results["profiles"].append(profile_result)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)  # Using port 8001 to avoid conflict with price server