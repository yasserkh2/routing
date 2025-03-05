from typing import Dict, Any
from api_interfaces import APICallStrategy, APIResponse, APIClient
from event_handler import Event, EventType
import json
import os

class GetLinksSLADataStrategy(APICallStrategy):
    """Strategy for getting link SLA data"""
    
    def __init__(self, api_client: APIClient = None):
        self.api_client = api_client
        self.mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
    
    def can_handle(self, event: Event) -> bool:
        return event.event_type == EventType.SLA_UPDATE
    
    async def call_api(self, event: Event) -> APIResponse:
        """Get SLA data for links"""
        try:
            # Read from mock_links_data.json
            file_path = os.path.join(self.mock_data_dir, 'mock_links_data.json')
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Filter by MNC if provided
            if 'mnc' in event.data:
                data = [link for link in data if link['mnc'] == event.data['mnc']]
                
            return APIResponse(
                data=data,
                success=True,
                error=None
            )
        except Exception as e:
            return APIResponse(
                data={},
                success=False,
                error=str(e)
            )

class GetProfileConfigStrategy(APICallStrategy):
    """Strategy for getting profile configurations"""
    
    def __init__(self, api_client: APIClient = None):
        self.api_client = api_client
        self.mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
    
    def can_handle(self, event: Event) -> bool:
        return event.event_type == EventType.PROFILE_UPDATE
    
    async def call_api(self, event: Event) -> APIResponse:
        """Get profile configurations"""
        try:
            # Read from mock_profiles.json
            file_path = os.path.join(self.mock_data_dir, 'mock_profiles.json')
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Filter by profile_id if provided
            if 'profile_id' in event.data:
                data = [p for p in data if p['profile_id'] == event.data['profile_id']]
                
            return APIResponse(
                data=data,
                success=True,
                error=None
            )
        except Exception as e:
            return APIResponse(
                data={},
                success=False,
                error=str(e)
            )

class DefaultAPIStrategyFactory:
    """Factory for creating API strategy instances"""
    
    def __init__(self, api_client=None):
        self.api_client = api_client
        
    def create_strategy(self, strategy_class) -> APICallStrategy:
        """Create a strategy instance"""
        return strategy_class(self.api_client)

# Update EventType enum in event_handler.py to include:
# SLA_UPDATE = "sla_update"
# PROFILE_UPDATE = "profile_update"

def setup_api_registry(registry):
    """Setup API registry with our strategies"""
    registry.register_strategy(EventType.SLA_UPDATE, GetLinksSLADataStrategy)
    registry.register_strategy(EventType.PROFILE_UPDATE, GetProfileConfigStrategy)