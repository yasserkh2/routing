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
            1: 0.95,  # Tier 1 – Prime
            2: 0.90,  # Tier 2 – High
            3: 0.80,  # Tier 3 – Med
            4: 0.70   # Tier 4 – Low
        }
        
        for profile_data in combined_data:
            # Check in_use_links
            for link_data in profile_data['in_use_links']:
                if link_data['link'] == link_id:
                    # Get DD SLA if available
                    dd_sla = link_data.get('sla_dd', 0) / 100.0 if 'sla_dd' in link_data else None
                    
                    # Get tier SLA
                    tier = link_data.get('tier', 4)  # Default to tier 4 (Low) if not specified
                    tier_sla = tier_sla_mapping.get(tier, 0.70)  # Default to 70% if tier not found
                    
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
                    tier = link_data.get('tier', 4)  # Default to tier 4 (Low) if not specified
                    tier_sla = tier_sla_mapping.get(tier, 0.70)  # Default to 70% if tier not found
                    
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
        
    def sort_links_by_sla(self, links_data: Dict[str, Dict[str, Any]]) -> List[tuple]:
        """
        Sort links by SLA (descending).
        
        Args:
            links_data: Dictionary mapping link IDs to their data
            
        Returns:
            List of (link_id, link_data) tuples sorted by SLA (descending)
        """
        logger.debug(f"Sorting {len(links_data)} links by SLA (descending)")
        return sorted(
            links_data.items(), 
            key=lambda x: x[1]['sla'], 
            reverse=True
        )
        
    def get_highest_sla_link(self, links_data: Dict[str, Dict[str, Any]]) -> str:
        """
        Get the link with the highest SLA.
        
        Args:
            links_data: Dictionary mapping link IDs to their data
            
        Returns:
            ID of the link with the highest SLA
        """
        if not links_data:
            logger.warning("No links data available to find highest SLA link")
            return None
            
        sorted_links = self.sort_links_by_sla(links_data)
        if sorted_links:
            best_link_id, _ = sorted_links[0]
            logger.debug(f"Highest SLA link: {best_link_id}")
            return best_link_id
        return None
        
    async def get_highest_sla_link_for_profile(self, profile: 'Profile') -> str:
        """
        Get the link with the highest SLA for a specific profile.
        
        Args:
            profile: Profile object to get the highest SLA link for
            
        Returns:
            ID of the link with the highest SLA
        """
        logger.info(f"Finding highest SLA link for profile {profile.profile_id}")
        links_data = await self.prepare_links_data_for_optimizer(profile)
        return self.get_highest_sla_link(links_data)
        
    def calculate_max_achievable_sla(self, links_data: Dict[str, Dict[str, Any]]) -> float:
        """
        Calculate the maximum achievable SLA from the available links.
        
        Args:
            links_data: Dictionary mapping link IDs to their data
            
        Returns:
            Maximum achievable SLA as a percentage
        """
        if not links_data:
            logger.warning("No links data available to calculate max SLA")
            return 0.0
            
        max_sla = max(link_data['sla'] for link_data in links_data.values())
        logger.debug(f"Maximum achievable SLA: {max_sla * 100:.2f}%")
        return max_sla * 100  # Convert to percentage
        
    async def prepare_routing_plan(self, profile: Profile, results: Dict[str, float]) -> Dict[str, Any]:
        """
        Prepare the routing plan based on optimization results.
        
        Args:
            profile: Profile object
            results: Dictionary mapping link IDs to traffic percentages (as fractions)
            
        Returns:
            Dictionary containing the routing plan
        """
        logger.info(f"Preparing routing plan for profile {profile.profile_id}")
        
        # Get allocation for all links
        routes = []
        for link_id, percentage in results.items():
            percentage = percentage * 100  # Convert fraction to percentage
            if percentage > 0:  # Only include routes with traffic
                link_data = await self.get_link_data(link_id)
                if link_data:
                    routes.append({
                        'link': link_id,
                        'provider': link_data['provider'],
                        'percentage': percentage,
                        'sla': link_data['sla'] * 100,  # Convert back to percentage
                        'tier': link_data['tier'],
                        'price': link_data['price']
                    })

        return {
            'profile_id': profile.profile_id,
            'name': profile.name,
            'expected_sla': profile.expected_sla,
            'routes': sorted(routes, key=lambda x: (-x['percentage'], -x['sla']))
        }
        
    async def prepare_routing_plan_for_profile(self, profile: Profile, results: Dict[str, float]) -> Dict[str, Any]:
        """
        Prepare the routing plan for a specific profile based on optimization results.
        This method is a wrapper around prepare_routing_plan that provides additional
        profile-specific processing if needed.
        
        Args:
            profile: Profile object
            results: Dictionary mapping link IDs to traffic percentages (as fractions)
            
        Returns:
            Dictionary containing the routing plan
        """
        logger.info(f"Preparing profile-specific routing plan for profile {profile.profile_id}")
        
        # For now, this just calls the base method, but can be extended with profile-specific logic
        routing_plan = await self.prepare_routing_plan(profile, results)
        
        # Additional profile-specific processing could be added here
        
        return routing_plan
        
    async def calculate_optimization_stats(self, profile: Profile, routing_plan: Dict[str, Any], links_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate optimization statistics.
        
        Args:
            profile: Profile object
            routing_plan: Routing plan dictionary
            links_data: Dictionary mapping link IDs to their data
            
        Returns:
            Dictionary containing optimization statistics
        """
        logger.info(f"Calculating optimization statistics for profile {profile.profile_id}")
        
        total_cost = 0
        achieved_sla = 0
        active_links = 0
        tier_stats = {}  # Track stats per tier
        
        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                total_cost += (route['percentage'] / 100.0) * route['price']
                achieved_sla += (route['percentage'] / 100.0) * (route['sla'] / 100.0)
                active_links += 1
                
                # Track tier statistics
                tier = route['tier']
                if tier not in tier_stats:
                    tier_stats[tier] = {
                        'traffic': 0,
                        'required_sla': 90.0  # Default tier SLA requirement
                    }
                tier_stats[tier]['traffic'] += route['percentage']
        
        # Get max achievable SLA
        max_sla = self.calculate_max_achievable_sla(links_data)
        
        stats = {
            'total_cost': total_cost,
            'links_used': active_links,
            'achieved_sla': achieved_sla * 100,  # Convert back to percentage
            'expected_sla': profile.expected_sla,
            'tier_stats': tier_stats,
            'sla_achievable': achieved_sla * 100 >= profile.expected_sla,
            'max_achievable_sla': max_sla
        }
        
        logger.info(
            f"Optimization stats: Cost=${total_cost:.2f}, Links={active_links}, "
            f"SLA={achieved_sla*100:.2f}%, Tier Stats={tier_stats}"
        )
        
        # Add warning if target SLA cannot be achieved
        if not stats['sla_achievable']:
            warning_msg = (
                f"Target SLA of {profile.expected_sla}% cannot be achieved. "
                f"Maximum achievable SLA with available links is {stats['max_achievable_sla']:.2f}%"
            )
            stats['warning'] = warning_msg
            logger.warning(warning_msg)
            
        return stats
        
    async def calculate_optimization_stats_for_profile(self, profile: Profile, routing_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate optimization statistics for a specific profile.
        This method handles the data preparation needed for statistics calculation.
        
        Args:
            profile: Profile object
            routing_plan: Routing plan dictionary
            
        Returns:
            Dictionary containing optimization statistics
        """
        logger.info(f"Calculating profile-specific optimization statistics for profile {profile.profile_id}")
        
        # Get links data for this profile
        links_data = await self.prepare_links_data_for_optimizer(profile)
        
        # Calculate statistics using the base method
        return await self.calculate_optimization_stats(profile, routing_plan, links_data)