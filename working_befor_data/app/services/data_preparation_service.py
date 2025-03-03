from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models.link import Link
from ..models.profile import Profile
from ..models.sla_data import SLAData
from .mock_services import MockAPIService

class DataPreparationService:
    """Service to prepare data for the optimizer"""
    
    def __init__(self):
        self.mock_api = MockAPIService()
    
    async def prepare_data_for_optimizer(self, profile_id: Optional[str] = None) -> List[Profile]:
        """
        Prepare data for the optimizer by:
        1. Getting link data and creating Link objects
        2. Getting profile data and creating Profile objects with their links
        3. Converting data into format needed by optimizer
        
        Args:
            profile_id: Optional profile ID to prepare data for specific profile
            
        Returns:
            List of Profile objects ready for optimization
        """
        # Get all links first
        links_data = await self.mock_api.get_links_sla_data()
        links = []
        for link_data in links_data:
            link = Link.from_api_data(link_data)
            links.append(link)
        
        # Get profiles
        profiles_data = await self.mock_api.get_profile_config(profile_id)
        profiles = []
        for profile_data in profiles_data:
            profile = Profile.from_api_data(profile_data, links)
            profiles.append(profile)
        
        return profiles
    
    async def get_all_profiles(self) -> List[Profile]:
        """
        Get all profiles ready for optimization
        
        Returns:
            List of Profile objects ready for optimization
        """
        return await self.prepare_data_for_optimizer(None)
    
    async def get_profile_for_optimization(self, profile_id: str) -> Optional[Profile]:
        """
        Get a single profile ready for optimization
        
        Args:
            profile_id: ID of the profile to prepare
            
        Returns:
            Profile object ready for optimization, or None if not found
        """
        profiles = await self.prepare_data_for_optimizer(profile_id)
        return profiles[0] if profiles else None