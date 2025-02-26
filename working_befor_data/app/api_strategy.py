from typing import Dict, Any, Optional, List
from event_handler import Event, EventType
import asyncio
from api_interfaces import APICallStrategy, APIResponse, APIClient

class MockAPIClient(APIClient):
    """Mock API client for simulating API calls"""
    async def call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        # Simulate API call delay
        await asyncio.sleep(0.5)
        
        try:
            # Mock different endpoints
            if endpoint == "GetProfilesRelatedToLink":
                # Query1: GetProfilesRelatedToLink(link, mnc)
                return APIResponse(
                    data={
                        "link": params.get("link"),
                        "mnc": params.get("mnc"),
                        "profiles": [
                            {
                                "profile_id": "PROF_1",
                                "name": "Premium_Gold_Profile",
                                "expected_sla": 99.9,
                                "priority": "CRITICAL",
                                "link_info": {
                                    "is_active": True,
                                    "last_used": "2025-02-06T12:00:00Z",
                                    "routing_priority": 1
                                }
                            },
                            {
                                "profile_id": "PROF_2",
                                "name": "Premium_Silver_Profile",
                                "expected_sla": 99.5,
                                "priority": "HIGH",
                                "link_info": {
                                    "is_active": True,
                                    "last_used": "2025-02-06T11:00:00Z",
                                    "routing_priority": 2
                                }
                            },
                            {
                                "profile_id": "PROF_3",
                                "name": "Standard_Plus_Profile",
                                "expected_sla": 98.5,
                                "priority": "MEDIUM_HIGH",
                                "link_info": {
                                    "is_active": True,
                                    "last_used": "2025-02-06T10:00:00Z",
                                    "routing_priority": 3
                                }
                            },
                            {
                                "profile_id": "PROF_4",
                                "name": "Standard_Profile",
                                "expected_sla": 97.0,
                                "priority": "MEDIUM",
                                "link_info": {
                                    "is_active": True,
                                    "last_used": "2025-02-06T09:00:00Z",
                                    "routing_priority": 4
                                }
                            },
                            {
                                "profile_id": "PROF_5",
                                "name": "Basic_Profile",
                                "expected_sla": 95.0,
                                "priority": "LOW",
                                "link_info": {
                                    "is_active": True,
                                    "last_used": "2025-02-06T08:00:00Z",
                                    "routing_priority": 5
                                }
                            }
                        ]
                    },
                    success=True
                )
            elif endpoint == "GetLinksSLAByMNC":
                # Query2: Get links with MNC and their SLA data
                return APIResponse(
                    data={
                        "mnc": params.get("mnc"),
                        "links": [
                            {
                                "link_id": "450271",
                                "operator": "Togo Cell",
                                "mnc": "01",
                                "sla_data": {
                                    "sla_dd": 99.1,
                                    "sla_tested": 98.5,
                                    "sla_assumed": 97.0,
                                    "last_updated": "2025-02-06T12:00:00Z"
                                }
                            },
                            {
                                "link_id": "450272",
                                "operator": "Togo Cell",
                                "mnc": "01",
                                "sla_data": {
                                    "sla_dd": None,
                                    "sla_tested": 97.8,
                                    "sla_assumed": 96.5,
                                    "last_updated": "2025-02-06T11:00:00Z"
                                }
                            },
                            {
                                "link_id": "450273",
                                "operator": "Togo Cell",
                                "mnc": "01",
                                "sla_data": {
                                    "sla_dd": None,
                                    "sla_tested": None,
                                    "sla_assumed": 95.0,
                                    "last_updated": "2025-02-06T10:00:00Z"
                                }
                            }
                        ]
                    },
                    success=True
                )
            elif endpoint == "GetProfilesWithLinks":
                # Query3: Get profiles with their associated links
                return APIResponse(
                    data={
                        "profiles": [
                            {
                                "profile_id": "PROF_1",
                                "name": "Premium_Gold_Profile",
                                "expected_sla": 99.9,
                                "priority": "CRITICAL",
                                "links": [
                                    {
                                        "link_id": "450271",
                                        "operator": "Togo Cell",
                                        "mnc": "01",
                                        "routing_priority": 1,
                                        "is_active": True,
                                        "last_used": "2025-02-06T12:00:00Z"
                                    },
                                    {
                                        "link_id": "450272",
                                        "operator": "Togo Cell",
                                        "mnc": "01",
                                        "routing_priority": 2,
                                        "is_active": True,
                                        "last_used": "2025-02-06T11:00:00Z"
                                    }
                                ]
                            },
                            {
                                "profile_id": "PROF_2",
                                "name": "Premium_Silver_Profile",
                                "expected_sla": 99.5,
                                "priority": "HIGH",
                                "links": [
                                    {
                                        "link_id": "450271",
                                        "operator": "Togo Cell",
                                        "mnc": "01",
                                        "routing_priority": 1,
                                        "is_active": True,
                                        "last_used": "2025-02-06T12:00:00Z"
                                    }
                                ]
                            },
                            {
                                "profile_id": "PROF_3",
                                "name": "Standard_Plus_Profile",
                                "expected_sla": 98.5,
                                "priority": "MEDIUM_HIGH",
                                "links": [
                                    {
                                        "link_id": "450272",
                                        "operator": "Togo Cell",
                                        "mnc": "01",
                                        "routing_priority": 1,
                                        "is_active": True,
                                        "last_used": "2025-02-06T11:00:00Z"
                                    },
                                    {
                                        "link_id": "450273",
                                        "operator": "Togo Cell",
                                        "mnc": "01",
                                        "routing_priority": 2,
                                        "is_active": True,
                                        "last_used": "2025-02-06T10:00:00Z"
                                    }
                                ]
                            }
                        ]
                    },
                    success=True
                )
            elif endpoint == "route":
                return APIResponse(
                    data={
                        "route_id": params.get("route_id"),
                        "operator_id": "615",
                        "country": "Togo",
                        "network": "Togo Cell",
                        "quality_score": 0.95,
                        "active": True,
                        "mnc": "01"
                    },
                    success=True
                )
            else:
                return APIResponse(
                    data={},
                    success=False,
                    error=f"Unknown endpoint: {endpoint}"
                )
        except Exception as e:
            return APIResponse(
                data={},
                success=False,
                error=str(e)
            )

class GetProfilesRelatedToLinkStrategy(APICallStrategy):
    """Strategy for Query1: GetProfilesRelatedToLink(link, mnc)"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def call_api(self, event: Event) -> APIResponse:
        # Extract link and mnc from the event data
        link = event.data.get("product_id")
        
        # First get route details to get the mnc
        route_response = await self.api_client.call(
            endpoint="route",
            params={"route_id": link}
        )
        
        if not route_response.success:
            return route_response
            
        mnc = route_response.data.get("mnc")
        
        # Now get profiles related to this link and mnc
        return await self.api_client.call(
            endpoint="GetProfilesRelatedToLink",
            params={
                "link": link,
                "mnc": mnc
            }
        )

    def can_handle(self, event: Event) -> bool:
        return (
            event.event_type == EventType.PRICE_CHANGE and
            "product_id" in event.data
        )

class GetLinksSLAByMNCStrategy(APICallStrategy):
    """Strategy for Query2: Get links with MNC and their SLA data"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def call_api(self, event: Event) -> APIResponse:
        # First get route details to get the mnc
        route_response = await self.api_client.call(
            endpoint="route",
            params={"route_id": event.data.get("product_id")}
        )
        
        if not route_response.success:
            return route_response
            
        mnc = route_response.data.get("mnc")
        
        # Get all links' SLA data for this MNC
        return await self.api_client.call(
            endpoint="GetLinksSLAByMNC",
            params={"mnc": mnc}
        )

    def can_handle(self, event: Event) -> bool:
        return (
            event.event_type == EventType.PRICE_CHANGE and
            "product_id" in event.data
        )

class GetProfilesWithLinksStrategy(APICallStrategy):
    """Strategy for Query3: Get profiles with their associated links"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def call_api(self, event: Event) -> APIResponse:
        # Get all profiles with their associated links
        return await self.api_client.call(
            endpoint="GetProfilesWithLinks",
            params={}
        )

    def can_handle(self, event: Event) -> bool:
        return event.event_type == EventType.PRICE_CHANGE

class RouteDetailsAPIStrategy(APICallStrategy):
    """Strategy for fetching route details"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def call_api(self, event: Event) -> APIResponse:
        return await self.api_client.call(
            endpoint="route",
            params={
                "route_id": event.data.get("product_id")
            }
        )

    def can_handle(self, event: Event) -> bool:
        return (
            event.event_type == EventType.PRICE_CHANGE and
            "product_id" in event.data
        )

class DefaultAPIStrategyFactory:
    """Factory for creating API strategy instances"""
    
    def __init__(self, api_client: Optional[APIClient] = None):
        self.api_client = api_client or MockAPIClient()

    def create_strategy(self, strategy_class: type) -> APICallStrategy:
        return strategy_class(self.api_client)

# Note: This implementation includes three main queries:
# Query1: GetProfilesRelatedToLink(link, mnc) -> profilesWithLinks
# Query2: GetLinksSLAByMNC(mnc) -> links with their SLA data
# Query3: GetProfilesWithLinks() -> profiles with their associated links