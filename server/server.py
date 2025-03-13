from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import sys
import os
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

class PriceChangeRequest(BaseModel):
    Type: str
    Payload: dict
    link: str
    mcc: str
    mnc: str
    timestamp: Optional[str] = None

@app.post("/analyze-price-change")
async def analyze_price_change(request: PriceChangeRequest):
    try:
        # Initialize services
        mock_api = MockAPIService()
        data_service = DataPreparationService()
        
        # Process the price change
        link_name = request.link
        old_rate = request.Payload["old_rate"]
        new_rate = request.Payload["new_rate"]
        status = request.Payload["status"]
        
        # Get all profiles
        all_profiles = await data_service.get_all_profiles()
        
        # Find affected profiles
        affected_profiles = data_service.get_profiles_affected_by_price_change(all_profiles, link_name)
        
        results = {
            "price_change": {
                "link": link_name,
                "old_price": old_rate,
                "new_price": new_rate,
                "change": status,
                "affected_profiles_count": len(affected_profiles)
            },
            "profiles": []
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
            
            # Run initial optimization with old price
            optimizer = RoutingOptimizer(initial_profile)
            success = optimizer.solve()
            
            if success:
                # Get initial results with old price
                initial_plan = optimizer.get_routing_plan()
                initial_stats = optimizer.get_optimization_stats()
                
                # Calculate initial costs
                total_cost = 0.0
                active_links = 0
                routes_info = []
                
                for route in initial_plan['routes']:
                    if route['percentage'] > 0:
                        active_links += 1
                        current_link = data_service.find_link_by_id(initial_profile.links, route['link'])
                        if current_link:
                            route_info = current_link.format_display_info(route['percentage'])
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
                
                # Apply price change to original profile
                target_link = data_service.find_link_by_id(profile.links, link_name)
                if target_link:
                    updated_link = target_link.with_updated_price(new_rate, old_rate)
                    profile.update_link_price(link_name, updated_link.price, old_rate)
                
                mock_api.handle_price_change(link_name, new_rate, old_rate)
                
                # Run optimization with new price
                optimizer = RoutingOptimizer(profile)
                success = optimizer.solve()
                
                if success:
                    after_plan = optimizer.get_routing_plan()
                    after_stats = optimizer.get_optimization_stats()
                    
                    # Calculate after costs
                    total_cost = 0.0
                    active_links = 0
                    routes_info = []
                    
                    for route in after_plan['routes']:
                        if route['percentage'] > 0:
                            active_links += 1
                            current_link = data_service.find_link_by_id(profile.links, route['link'])
                            if current_link:
                                override_price = new_rate if route['link'] == link_name else None
                                route_info = current_link.format_display_info(route['percentage'], override_price)
                                total_cost += current_link.calculate_cost_for_traffic(route['percentage'], override_price)
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