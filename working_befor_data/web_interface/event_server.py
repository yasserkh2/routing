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
    return FileResponse(os.path.join(static_dir, "event_index.html"))

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

class EventHandler:
    def __init__(self, mock_api: MockAPIService, data_service: DataPreparationService):
        self.mock_api = mock_api
        self.data_service = data_service
        self.link_cache = {}  # Dictionary for fast link lookups
        self.profile_cache = None  # Cache for all profiles
        self._last_cache_update = None  # Timestamp of last cache update
        self.cache_ttl = 300  # Cache TTL in seconds (5 minutes)

    def get_link_by_id(self, profile: Profile, link_name: str) -> Optional[Link]:
        """Fast O(1) lookup for links using cache."""
        if link_name in self.link_cache:
            return self.link_cache[link_name]
        link = next((l for l in profile.links if l.link == link_name), None)
        if link:
            self.link_cache[link_name] = link
        return link

    async def handle_price_change(self, profile: Profile, link_name: str, new_rate: float, old_rate: float) -> Profile:
        """Handle price change event for a profile"""
        # Use DataPreparationService to update link price
        DataPreparationService.update_link_price([profile], link_name, new_rate, old_rate)
        self.mock_api.handle_price_change(link_name, new_rate, old_rate)
        return profile

    async def handle_sla_change(self, profile: Profile, link_name: str, changed_sla: Dict[str, Dict[str, float]]) -> Profile:
        """Handle SLA change event for a profile"""
        target_link = self.get_link_by_id(profile, link_name)
        if target_link:
            updated_link = target_link.update_sla(changed_sla)
            profile.links = [updated_link if l.link == link_name else l for l in profile.links]
        return profile

    async def get_profile_metrics(self, profile: Profile, optimizer: RoutingOptimizer) -> Dict:
        """Calculate profile metrics from optimization results"""
        plan = optimizer.get_routing_plan()
        stats = optimizer.get_optimization_stats()
        
        total_cost = 0.0
        active_links = 0
        routes_info = []
        
        for route in plan['routes']:
            if route['percentage'] > 0:
                active_links += 1
                current_link = self.get_link_by_id(profile, route['link'])
                if current_link:
                    route_info = current_link.format_display_info(route['percentage'])
                    route_info['price'] = current_link.price
                    total_cost += current_link.calculate_cost_for_traffic(route['percentage'])
                    routes_info.append(route_info)
        
        # Get profile's sell price
        profiles_path = os.path.join(os.path.dirname(__file__), '../mock_data/profiles.json')
        with open(profiles_path, 'r') as f:
            profiles_data = json.load(f)
            profile_data = next(p for p in profiles_data if p["profile_id"] == profile.profile_id)
            sell_price = profile_data["sell_price"]
        
        profit = sell_price - total_cost
        
        return {
            "routes": routes_info,
            "total_cost": total_cost,
            "sell_price": sell_price,
            "profit": profit,
            "active_links": active_links,
            "achieved_sla": stats['achieved_sla'],
            "sla_achievable": stats['sla_achievable'],
            "max_achievable_sla": stats.get('max_achievable_sla')
        }

    async def calculate_traffic_shifts(self, before_routes: list, after_routes: list) -> list:
        """Calculate traffic shifts between before and after states"""
        traffic_shifts = []
        for before_route in before_routes:
            before_traffic = before_route["traffic"]
            after_route = next((r for r in after_routes if r["link"] == before_route["link"]), None)
            after_traffic = after_route["traffic"] if after_route else 0
            if abs(after_traffic - before_traffic) > 0.1:  # Only show significant changes (>0.1%)
                traffic_shifts.append({
                    "link": before_route["link"],
                    "before": before_traffic,
                    "after": after_traffic,
                    "change": after_traffic - before_traffic
                })
        return traffic_shifts

    async def get_cached_profiles(self) -> list:
        """Get profiles from cache or load if cache is expired/empty"""
        current_time = datetime.now()
        
        # Check if cache needs refresh
        if (self.profile_cache is None or 
            self._last_cache_update is None or 
            (current_time - self._last_cache_update).total_seconds() > self.cache_ttl):
            
            # Reload cache
            self.profile_cache = await self.data_service.get_all_profiles()
            self._last_cache_update = current_time
            self.link_cache = {}  # Reset link cache when profiles are reloaded
            
        return self.profile_cache

    def invalidate_cache(self):
        """Force cache invalidation"""
        self.profile_cache = None
        self.link_cache = {}
        self._last_cache_update = None

@app.post("/analyze-event")
async def analyze_event(request: EventRequest):
    try:
        # Initialize services
        mock_api = MockAPIService()
        data_service = DataPreparationService()
        event_handler = EventHandler(mock_api, data_service)
        
        # Get event type and validate
        event_type = request.Type.lower()
        if event_type not in ["price", "sla"]:
            raise HTTPException(status_code=400, detail=f"Unsupported event type: {event_type}")
        
        # Get affected profiles using cache
        all_profiles = await event_handler.get_cached_profiles()
        # Use set lookup for O(n) complexity instead of nested loops
        affected_profiles = [profile for profile in all_profiles if request.link in {link.link for link in profile.links}]
        
        # Initialize results
        results = {
            "event_type": event_type,
            "link": request.link,
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
                "changes": {
                    sla_type: {
                        "old": values["old"],
                        "new": values["new"],
                        "difference": values["new"] - values["old"]
                    }
                    for sla_type, values in request.Payload.changed_sla.items()
                },
                "status": request.Payload.status
            }
        
        # Process each affected profile
        for profile in affected_profiles:
            try:
                profile_result = {
                    "name": profile.name,
                    "expected_sla": profile.expected_sla,
                    "available_links": len(profile.links),
                    "before": {},
                    "after": {}
                }
                
                # Invalidate cache if we're making changes that affect profiles
                if event_type in ["price", "sla"]:
                    event_handler.invalidate_cache()
                
                # Initial optimization with original values
                initial_profile = profile.clone()
                optimizer = RoutingOptimizer(initial_profile)
                if not optimizer.solve():
                    print(f"Initial optimization failed for profile {profile.name}")
                    continue
                
                # Get initial metrics
                profile_result["before"] = await event_handler.get_profile_metrics(initial_profile, optimizer)
                initial_profit = profile_result["before"]["profit"]
                
                # Apply changes based on event type
                updated_profile = profile.clone()
                if event_type == "price":
                    updated_profile = await event_handler.handle_price_change(
                        updated_profile, 
                        request.link, 
                        request.Payload.new_rate, 
                        request.Payload.old_rate
                    )
                else:  # SLA change
                    updated_profile = await event_handler.handle_sla_change(
                        updated_profile,
                        request.link,
                        request.Payload.changed_sla
                    )
                
                # Optimize with updated values
                optimizer = RoutingOptimizer(updated_profile)
                if not optimizer.solve():
                    print(f"Optimization after changes failed for profile {profile.name}")
                    continue
                
                # Get metrics after changes
                profile_result["after"] = await event_handler.get_profile_metrics(updated_profile, optimizer)
                
                # Calculate additional metrics
                profile_result["after"]["profit_change"] = profile_result["after"]["profit"] - initial_profit
                
                # Add SLA impact for SLA changes
                if event_type == "sla":
                    profile_result["after"]["sla_impact"] = {
                        "absolute": profile_result["after"]["achieved_sla"] - profile_result["before"]["achieved_sla"],
                        "percentage": ((profile_result["after"]["achieved_sla"] - profile_result["before"]["achieved_sla"]) 
                                    / profile_result["before"]["achieved_sla"]) * 100 if profile_result["before"]["achieved_sla"] > 0 else 0.0
                    }
                
                # Calculate traffic shifts
                traffic_shifts = await event_handler.calculate_traffic_shifts(
                    profile_result["before"]["routes"],
                    profile_result["after"]["routes"]
                )
                if traffic_shifts:
                    profile_result["after"]["traffic_shifts"] = traffic_shifts
                
                results["profiles"].append(profile_result)
                
            except Exception as e:
                print(f"Error processing profile {profile.name}: {str(e)}")
                continue
        
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