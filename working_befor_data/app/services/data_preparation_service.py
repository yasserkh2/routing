from typing import List, Dict, Any, Optional, Set
from datetime import datetime
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
        unique_links: Set[Link] = set()
        for profile in profiles:
            unique_links.update(profile.links)
        return sorted(unique_links, key=lambda x: x.mnc)

    def filter_by_mnc(self, links: List[Link], mnc: str) -> List[Link]:
        """Filter links by MNC"""
        logger.debug(f"Filtering links by MNC: {mnc}")
        return [link for link in links if link.mnc == mnc]

    def filter_by_operator(self, links: List[Link], operator: str) -> List[Link]:
        """Filter links by operator"""
        logger.debug(f"Filtering links by operator: {operator}")
        return [link for link in links if link.operator == operator]

    def get_links_with_price_changes(self, links: List[Link]) -> List[Link]:
        """Get all links that have price changes in their history"""
        logger.debug("Getting links with price changes")
        return [link for link in links if len(link.price_history) > 1]

    def calculate_average_sla(self, links: List[Link]) -> float:
        """Calculate average SLA across all links"""
        logger.debug(f"Calculating average SLA for {len(links)} links")
        if not links:
            return 0.0
        total_sla = sum(link.average_sla for link in links)
        return total_sla / len(links)

    def find_link_by_id(self, links: List[Link], link_name: str) -> Optional[Link]:
        """Find a link by its name"""
        logger.debug(f"Finding link by name: {link_name}")
        return next((link for link in links if link.link == link_name), None)

    # Profile collection operations
    def get_profiles_affected_by_price_change(self, profiles: List[Profile], link_name: str) -> List[Profile]:
        """Get all profiles that contain the link with price change"""
        logger.debug(f"Finding profiles affected by price change in link: {link_name}")
        return [
            profile for profile in profiles
            if any(link.link == link_name for link in profile.links)
        ]
    
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
        logger.info("Fetching links data for optimizer")
        links_data = await self.mock_api.get_links_data()
        links = []
        for link_data in links_data:
            try:
                link = Link.from_api_data(link_data)
                links.append(link)
            except Exception as e:
                logger.error(f"Failed to process link data: {str(e)}", exc_info=True)
        logger.info(f"Processed {len(links)} links")
        
        # Get profiles
        logger.info(f"Fetching profiles data for optimizer. Profile ID filter: {profile_id}")
        profiles_data = await self.mock_api.get_profile_config(profile_id)
        profiles = []
        for profile_data in profiles_data:
            try:
                profile = self.from_api_data(profile_data, links)
                profiles.append(profile)
                logger.debug(f"Processed profile {profile.profile_id} with {len(profile.links)} links")
            except Exception as e:
                logger.error(f"Failed to process profile data: {str(e)}", exc_info=True)
        logger.info(f"Processed {len(profiles)} profiles")
        
        return profiles
    
    async def get_all_profiles(self) -> List[Profile]:
        """
        Get all profiles ready for optimization
        
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
    def from_api_data(data: Dict[str, Any], available_links: List[Link]) -> Profile:
        """
        Create a Profile instance from API data.
        
        Args:
            data: API data dictionary containing profile information
            available_links: List of available Link objects
            
        Returns:
            Profile object created from API data
        """
        logger.debug(f"Creating Profile from API data: {data['profile_id']}")
        profile_links = [
            link for link in available_links 
            if link.link in data['links']
        ]
        
        return Profile(
            profile_id=data['profile_id'],
            name=data['name'],
            expected_sla=float(data['expected_sla']),
            links=profile_links
        )

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
        for profile in profiles:
            for i, link in enumerate(profile.links):
                if link.link == link_name:
                    profile.links[i] = link.with_updated_price(new_price, old_price)
                    logger.debug(f"Updated link price in profile {profile.profile_id}")