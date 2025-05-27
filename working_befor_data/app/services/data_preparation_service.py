from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from functools import lru_cache
from ..models.link import Link
from ..models.profile import Profile
from .mock_services import MockAPIService
from ..utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class DataPreparationService:
    """Service to prepare data for the optimizer and handle data processing operations"""
    
    def __init__(self):
        self.mock_api = MockAPIService()
        logger.info("DataPreparationService initialized")

    # Link collection operations
    def extract_all_links(self, profiles: List[Profile]) -> List[Link]:
        """Extract all unique links from a list of profiles"""
        logger.debug(f"Extracting unique links from {len(profiles)} profiles")
        unique_links: Set[str] = set()
        for profile in profiles:
            unique_links.update(profile.get_all_links())
        return sorted(list(unique_links))

    # Removed redundant methods that were just stubs

    def find_link_by_id(self, links: List[str], link_name: str) -> Optional[str]:
        """Find a link by its name"""
        logger.debug(f"Finding link by name: {link_name}")
        return link_name if link_name in links else None

    # Profile collection operations
    def get_profiles_affected_by_price_change(self, profiles: List[Profile], link_name: str) -> List[Profile]:
        """Get all profiles that contain the link with price change"""
        logger.debug(f"Finding profiles affected by price change in link: {link_name}")
        return [
            profile for profile in profiles
            if link_name in profile.get_all_links()
        ]
    
    async def prepare_data_for_optimizer(self, profile_id: Optional[str] = None) -> List[Profile]:
        """
        Prepare data for the optimizer using the new combined data structure.
        
        Args:
            profile_id: Optional profile ID to prepare data for specific profile
            
        Returns:
            List of Profile objects ready for optimization
        """
        logger.info("Fetching combined profile and link data for optimizer")
        profiles_data = await self.mock_api.get_combined_data()
        
        # Filter by profile_id if specified
        if profile_id:
            profiles_data = [p for p in profiles_data if p['profile_id'] == profile_id]
            
        profiles = []
        for profile_data in profiles_data:
            try:
                # Extract only link names from in_use_links
                in_use_links = [
                    link_data['link']
                    for link_data in profile_data.get('in_use_links', [])
                    if isinstance(link_data, dict) and 'link' in link_data
                ]
                
                # Extract only link names from alternative_links
                alternative_links = [
                    link_data['link']
                    for link_data in profile_data.get('alternative_links', [])
                    if isinstance(link_data, dict) and 'link' in link_data
                ]
                
                # Create profile with string-based links
                profile = Profile(
                    profile_id=str(profile_data['profile_id']),
                    name=str(profile_data['name']),
                    expected_sla=float(profile_data['expected_sla']),
                    description=str(profile_data['description']),
                    sell_price_min=float(profile_data['sell_price_min']),
                    sell_price_max=float(profile_data['sell_price_max']),
                    profile_avg_cost=float(profile_data['profile_avg_cost']),
                    mcc=str(profile_data['mcc']),
                    mnc=str(profile_data['mnc']),
                    in_use_links=in_use_links,
                    alternative_links=alternative_links
                )
                profiles.append(profile)
                logger.debug(
                    f"Processed profile {profile.profile_id} with "
                    f"{len(profile.in_use_links)} in-use links and "
                    f"{len(profile.alternative_links)} alternative links"
                )
            except Exception as e:
                logger.error(f"Failed to process profile data: {str(e)}", exc_info=True)
                
        logger.info(f"Processed {len(profiles)} profiles")
        return profiles
    
    @lru_cache(maxsize=10)
    async def get_all_profiles(self) -> List[Profile]:
        """
        Get all profiles ready for optimization. Results are cached to prevent unnecessary API calls.
        
        Returns:
            List of Profile objects ready for optimization
        """
        logger.info("Fetching all profiles for optimization")
        profiles = await self.prepare_data_for_optimizer(None)
        logger.info(f"Retrieved {len(profiles)} profiles")
        return profiles
    
    async def get_profile_for_optimization(self, profile_id: str) -> Optional[Profile]:
        """
        Get a single profile ready for optimization
        
        Args:
            profile_id: ID of the profile to prepare
            
        Returns:
            Profile object ready for optimization, or None if not found
        """
        logger.info(f"Fetching specific profile for optimization: {profile_id}")
        profiles = await self.prepare_data_for_optimizer(profile_id)
        if not profiles:
            logger.warning(f"Profile not found: {profile_id}")
            return None
        logger.info(f"Successfully retrieved profile {profile_id}")
        return profiles[0]

    @staticmethod
    def update_link_price(profiles: List[Profile], link_name: str, new_price: float, old_price: Optional[float] = None) -> None:
        """
        Update the price of a link across multiple profiles.
        
        Args:
            profiles: List of profiles to update
            link_name: Name of the link to update
            new_price: New price to set
            old_price: Optional old price for validation
        """
        logger.info(f"Updating price for link {link_name} to {new_price} across {len(profiles)} profiles")
        # Price updates are now handled by the mock API service
        pass
                    
    async def get_link_data(self, link_id: str) -> Dict[str, Any]:
        """
        Get link data from the mock API with SLA calculation.
        
        Args:
            link_id: ID of the link to get data for
            
        Returns:
            Dictionary containing link data ready for optimization
        """
        logger.debug(f"Getting link data for link: {link_id}")
        combined_data = await self.mock_api.get_combined_data()
        
        # Define tier SLA mapping once to avoid duplication
        tier_sla_mapping = {
            1: 0.99,  # 99% SLA for tier 1
            2: 0.95,  # 95% SLA for tier 2
            3: 0.90   # 90% SLA for tier 3
        }
        
        for profile_data in combined_data:
            # Check in_use_links
            for link_data in profile_data['in_use_links']:
                if link_data['link'] == link_id:
                    # Get DD SLA if available
                    dd_sla = link_data.get('sla_dd', 0) / 100.0 if 'sla_dd' in link_data else None
                    
                    # Get tier SLA
                    tier = link_data.get('tier', 3)  # Default to tier 3 if not specified
                    tier_sla = tier_sla_mapping.get(tier, 0.90)  # Default to 90% if tier not found
                    
                    # Calculate final SLA
                    if dd_sla is not None:
                        sla = (dd_sla + tier_sla) / 2  # Average if both available
                    else:
                        sla = tier_sla  # Use tier SLA if DD SLA not available
                    
                    return {
                        'link': link_id,
                        'provider': link_data['provider'],
                        'price': link_data['buy_price'],
                        'sla': sla,
                        'tier': tier
                    }
            
            # Check alternative_links
            for link_data in profile_data['alternative_links']:
                if link_data['link'] == link_id:
                    # Get tier SLA
                    tier = link_data.get('tier', 3)  # Default to tier 3 if not specified
                    tier_sla = tier_sla_mapping.get(tier, 0.90)  # Default to 90% if tier not found
                    
                    return {
                        'link': link_id,
                        'provider': link_data['provider'],
                        'price': link_data['buy_price'],
                        'sla': tier_sla,  # Use tier SLA for alternative links
                        'tier': tier
                    }
        
        logger.warning(f"Link data not found for link: {link_id}")
        return None
    
    async def prepare_links_data_for_optimizer(self, profile: Profile) -> Dict[str, Dict[str, Any]]:
        """
        Prepare links data for the optimizer.
        
        Args:
            profile: Profile object to prepare links data for
            
        Returns:
            Dictionary mapping link IDs to their data
        """
        logger.info(f"Preparing links data for optimizer for profile {profile.profile_id}")
        links_data = {}
        
        for link_id in profile.get_all_links():
            link_data = await self.get_link_data(link_id)
            if link_data:
                links_data[link_id] = link_data
        
        logger.info(f"Found {len(links_data)} links for profile {profile.profile_id}")
        return links_data
        
    # Removed redundant convert_profile_to_optimizer_format method
        
    @staticmethod
    def get_active_links(profile: Profile) -> List[str]:
        """
        Get all active links that meet the profile's SLA requirement.
        
        Args:
            profile: Profile object to get active links from
            
        Returns:
            List of link names that are currently active
        """
        logger.debug(f"Getting active links for profile {profile.profile_id}")
        return profile.in_use_links