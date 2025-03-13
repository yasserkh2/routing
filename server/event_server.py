from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Union
import os
import sys
import json
from datetime import datetime

# Add working_befor_data directory to path so we can import from app
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "working_befor_data"))

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
    return FileResponse(os.path.join(static_dir, "index.html"))

class PriceChangePayload(BaseModel):
    old_rate: float
    new_rate: float
    status: str

class SLAChangePayload(BaseModel):
    changed_sla: Dict[str, Dict[str, float]]  # e.g. {"DD": {"old": 75.0, "new": 78.0}}
    status: str

class EventRequest(BaseModel):
    Type: str
    Payload: Union[PriceChangePayload, SLAChangePayload]
    link: str
    mcc: str
    mnc: str
    timestamp: Optional[str] = None

@app.post("/analyze-event")
async def analyze_event(request: EventRequest):
    try:
        # Initialize services
        mock_api = MockAPIService()
        data_service = DataPreparationService()
        
        # Get event type
        event_type = request.Type.lower()
        if event_type not in ["price", "sla"]:
            raise HTTPException(status_code=400, detail=f"Unsupported event type: {event_type}")
        
        # Process the event
        link_name = request.link
        
        # Get all profiles
        all_profiles = await data_service.get_all_profiles()
        
        # Find affected profiles
        affected_profiles = data_service.get_profiles_affected_by_price_change(all_profiles, link_name)
        
        results = {
            "event_type": event_type,
            "link": link_name,
            "affected_profiles_count": len(affected_profiles),
            "profiles": []
        }

        # Add event-specific details
        if event_type == "price":
            results["price_change"] = {
                "old_price": request.Payload.old_rate,
                "new_price": request.Payload.new_rate,
                "change": request.Payload.status
            }
        else:  # SLA change
            results["sla_change"] = {
                "changes": {},
                "status": request.Payload.status
            }
            for sla_type, values in request.Payload.changed_sla.items():
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
            
            # Create a copy of the profile for initial optimization
            initial_profile = profile.clone()
            
            # Run initial optimization with old values
            optimizer = RoutingOptimizer(initial_profile)
            success = optimizer.solve()
            
            if success:
                # Get initial results
                initial_plan = optimizer.get_routing_plan()
                initial_stats = optimizer.get_optimization_stats()
                
                # Calculate initial costs and metrics
                total_cost = 0.0
                active_links = 0
                routes_info = []
                
                for route in initial_plan['routes']:
                    if route['percentage'] > 0:
                        active_links += 1
                        current_link = data_service.find_link_by_id(initial_profile.links, route['link'])
                        if current_link:
                            route_info = current_link.format_display_info(route['percentage'])
                            route_info['price'] = current_link.price
                            total_cost += current_link.calculate_cost_for_traffic(route['percentage'])
                            routes_info.append(route_info)
                
                # Get profile's sell price
                profiles_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'working_befor_data/mock_data/profiles.json')
                with open(profiles_path, 'r') as f:
                    profiles_data = json.load(f)
                    profile_data = next(p for p in profiles_data if p["profile_id"] == profile.profile_id)
                    sell_price = profile_data["sell_price"]
                
                initial_profit = sell_price - total_cost
                
                profile_result["before"] = {
                    "routes": routes_info,
                    "total_cost": total_cost,
                    "sell_price": sell_price,
                    "profit": initial_profit,
                    "active_links": active_links,
                    "achieved_sla": initial_stats['achieved_sla'],
                    "sla_achievable": initial_stats['sla_achievable'],
                    "max_achievable_sla": initial_stats.get('max_achievable_sla')
                }
                
                # Apply changes to profile based on event type
                if event_type == "price":
                    target_link = data_service.find_link_by_id(profile.links, link_name)
                    if target_link:
                        updated_link = target_link.with_updated_price(request.Payload.new_rate, request.Payload.old_rate)
                        profile.update_link_price(link_name, updated_link.price, request.Payload.old_rate)
                    mock_api.handle_price_change(link_name, request.Payload.new_rate, request.Payload.old_rate)
                else:  # SLA change
                    target_link = data_service.find_link_by_id(profile.links, link_name)
                    if target_link:
                        updated_link = target_link.update_sla(request.Payload.changed_sla)
                        profile.links = [updated_link if l.link == link_name else l for l in profile.links]
                
                # Run optimization with new values
                optimizer = RoutingOptimizer(profile)
                success = optimizer.solve()
                
                if success:
                    after_plan = optimizer.get_routing_plan()
                    after_stats = optimizer.get_optimization_stats()
                    
                    # Calculate after metrics
                    total_cost = 0.0
                    active_links = 0
                    routes_info = []
                    
                    for route in after_plan['routes']:
                        if route['percentage'] > 0:
                            active_links += 1
                            current_link = data_service.find_link_by_id(profile.links, route['link'])
                            if current_link:
                                route_info = current_link.format_display_info(route['percentage'])
                                route_info['price'] = current_link.price
                                total_cost += current_link.calculate_cost_for_traffic(route['percentage'])
                                routes_info.append(route_info)
                    
                    new_profit = sell_price - total_cost
                    profit_change = new_profit - initial_profit
                    
                    profile_result["after"] = {
                        "routes": routes_info,
                        "total_cost": total_cost,
                        "sell_price": sell_price,
                        "profit": new_profit,
                        "profit_change": profit_change,
                        "active_links": active_links,
                        "achieved_sla": after_stats['achieved_sla'],
                        "sla_achievable": after_stats['sla_achievable'],
                        "max_achievable_sla": after_stats.get('max_achievable_sla')
                    }
                    
                    # Add SLA impact metrics for SLA changes
                    if event_type == "sla":
                        profile_result["after"]["sla_impact"] = {
                            "absolute": after_stats.get('achieved_sla', 0.0) - initial_stats.get('achieved_sla', 0.0),
                            "percentage": ((after_stats.get('achieved_sla', 0.0) - initial_stats.get('achieved_sla', 0.0)) / initial_stats.get('achieved_sla', 1.0)) * 100 if initial_stats.get('achieved_sla', 0.0) > 0 else 0.0
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
        import traceback
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        raise HTTPException(status_code=500, detail=error_details)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)