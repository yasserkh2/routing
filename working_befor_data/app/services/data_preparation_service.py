from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from functools import lru_cache
from ..models.link import Link
from ..models.profile import Profile
from .mock_services import MockAPIService
from ..utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Inclusion list for profiles that should be included in calculations
PROFILE_INCLUSION_LIST = [
    "Standard_MTN_Adv_Nigeria",
    "International_Airtel_Nigeria",
    "International_Etisalat_Nigeria",
    "International_GLO_Nigeria",
    "Standard_Mobilis_Algeria",
    "Standard_Djezzy_Algeria",
    "Standard_Ooredoo_Algeria",
    "Direct_Alfa_International_Lebanon",
    "Direct_Touch_International_Lebanon",
    "Standard_Vodacom_Tanzania",
    "Standard_Tigo_Tanzania",
    "Standard_Airtel_Tanzania",
    "Standard_Halotel / Viettel Ltd_Tanzania",
    "Standard_International_Meditel_Morocco",
    "Standard_IAM_ETISALAT_Morocco",
    "Standard_Inwi_Morocco",
    "Direct_Yemen Mobile_Yemen",
    "Direct_Spacetel(MTN)_Yemen",
    "Direct_Sabafon_Yemen",
    "Direct_Y(Hits-UNITEL)_Yemen",
    "Standard_Orange_Jordan",
    "Standard_Umniah_Jordan",
    "Standard_Zain_Jordan",
    "Standard_INTL_Vodafone_Qatar",
    "Standard_INTL_Ooredoo_Qatar",
    "Standard_Asiacell_Iraq",
    "Standard_Zain_Iraq",
    "Standard_Korek Telecom_Iraq",
    "Premium_International_MTN_Nigeria",
    "Premium_Airtel_Nigeria",
    "Premium_International_Etisalat_Nigeria",
    "Premium_International_GLO_Nigeria",
    "Premium_Asiacell_Iraq",
    "Premium_Zain_Iraq",
    "Premium_Korek Telecom_Iraq",
    "Premium_Yemen Mobile_Yemen",
    "Premium_Spacetel_Yemen",
    "Premium_Sabafon_Yemen",
    "Premium_YHits_Yemen",
    "Premium_Orange_Jordan",
    "Premium_Umniah_Jordan",
    "Premium_Zain_Jordan",
    "Premium_Djezzy_Algeria",
    "Premium_Mobilis_Algeria",
    "Premium_Ooredoo_Algeria",
    "Premium_ MIC 1 (Alfa)",
    "Premium_MIC 2 (MTC-Touch)",
    "Premium_Halotel / Viettel Ltd_Tanzania",
    "Premium_Airtel_Tanzania",
    "Premium_Tigo_Tanzania",
    "Premium_Vodacom_Tanzania",
    "Premium_International_Meditel_Morocco",
    "Premium_IAM_ETISALAT_Morocco",
    "Premium_Inwi_Morocco",
    "Premium_INTL_Vodafone_Qatar",
    "Premium_INTL_Ooredoo_Qatar",
    "Premium_Etisalat_Togo",
    "Premium_Togo Cell_Togo",
    "Standard_Vodafone_Egypt",
    "Standard_Orange_Egypt_Route",
]

class DataPreparationService:
    """Service to prepare data for the optimizer and handle data processing operations"""
    
    def __init__(self):
        self.mock_api = MockAPIService()
        self.ignored_links: List[Dict[str, Any]] = [] # To store links ignored due to price checks
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
                # Skip profiles not in the inclusion list
                if profile_data['name'] not in PROFILE_INCLUSION_LIST:
                    logger.info(f"Skipping profile {profile_data['name']} as it's not in the inclusion list")
                    continue
                
                # Extract only link names from in_use_links
                in_use_links = [
                    link_data['link']
                    for link_data in profile_data.get('in_use_links', [])
                    if isinstance(link_data, dict) and 'link' in link_data
                ]
                
                # Extract only link names from alternative_links (now includes all global alternatives)
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
                    f"{len(profile.alternative_links)} alternative links (shared globally)"
                )
            except Exception as e:
                logger.error(f"Failed to process profile data: {str(e)}", exc_info=True)
                
        logger.info(f"Processed {len(profiles)} profiles from inclusion list")
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
                    sla_dd_value = link_data.get('sla_dd')
                    # The sla_dd value is already in decimal format (e.g., 0.854406 for 85.44%)
                    dd_sla = sla_dd_value if sla_dd_value is not None else None
                    
                    # Get tier SLA - DO NOT default to tier 4, keep original tier value
                    tier_value = link_data.get('tier')
                    
                    # Handle string tier values like "Tier 1 - Prime"
                    if isinstance(tier_value, str) and tier_value.startswith("Tier "):
                        try:
                            # Extract the numeric part
                            tier = int(tier_value.split(" ")[1])
                        except (ValueError, IndexError):
                            tier = None  # Invalid tier format
                    elif isinstance(tier_value, int):
                        tier = tier_value
                    else:
                        tier = None  # No valid tier
                    
                    # Calculate final SLA - Focus: when sla_dd exists and tier is null, use sla_dd
                    if dd_sla is not None and dd_sla > 0:
                        if tier is not None:
                            tier_sla = tier_sla_mapping.get(tier, 0.70)  # Default to 70% if tier not found
                            sla = (dd_sla + tier_sla) / 2  # Average if both available
                        else:
                            # Case: sla_dd exists but tier is null - use sla_dd
                            sla = dd_sla
                            logger.debug(f"Using sla_dd ({dd_sla*100:.1f}%) for link {link_id} as tier is null")
                    elif dd_sla is not None and dd_sla == 0:
                        # Case: sla_dd is explicitly 0 - use it for SLA mixing calculations
                        sla = 0.0
                        logger.debug(f"Using zero SLA for link {link_id} (sla_dd=0) for SLA mixing")
                    elif tier is not None:
                        tier_sla = tier_sla_mapping.get(tier, 0.70)  # Default to 70% if tier not found
                        sla = tier_sla  # Use tier SLA if DD SLA not available
                    else:
                        sla = 0.0  # No valid SLA data
                    
                    return {
                        'link': link_id,
                        'provider': link_data['provider'],
                        'price': link_data['buy_price'],
                        'sla': sla,
                        'tier': tier,
                        'sla_dd': link_data.get('sla_dd', 0)  # Include original sla_dd value
                    }
            
            # Check alternative_links
            for link_data in profile_data['alternative_links']:
                if link_data['link'] == link_id:
                    # Get tier SLA - for alternative links, tier is required and must be 1-4
                    tier_value = link_data.get('tier')
                    
                    # Handle string tier values like "Tier 1 - Prime"
                    if isinstance(tier_value, str) and tier_value.startswith("Tier "):
                        try:
                            # Extract the numeric part
                            tier = int(tier_value.split(" ")[1])
                        except (ValueError, IndexError):
                            tier = None  # Invalid tier format
                    elif isinstance(tier_value, int):
                        tier = tier_value
                    else:
                        tier = None  # No valid tier
                    
                    # For alternative links: if no tier or tier > 4, exclude from calculations
                    if tier is None:
                        logger.debug(f"Excluding alternative link {link_id} from calculations - no tier available")
                        return None
                    elif tier > 4:
                        logger.debug(f"Excluding alternative link {link_id} from calculations - tier {tier} is above maximum supported tier 4")
                        return None
                    
                    # Get DD SLA if available
                    sla_dd_value = link_data.get('sla_dd')
                    # The sla_dd value is already in decimal format (e.g., 0.854406 for 85.44%)
                    dd_sla = sla_dd_value if sla_dd_value is not None else None
                    
                    # Calculate final SLA - tier is guaranteed to exist here and be 1-4
                    tier_sla = tier_sla_mapping.get(tier, 0.70)  # Default to 70% if tier not found
                    if dd_sla is not None and dd_sla > 0:
                        sla = (dd_sla + tier_sla) / 2  # Average if both available
                    else:
                        sla = tier_sla  # Use tier SLA if DD SLA not available
                    
                    return {
                        'link': link_id,
                        'provider': link_data['provider'],
                        'price': link_data['buy_price'],
                        'sla': sla,
                        'tier': tier,
                        'sla_dd': link_data.get('sla_dd', 0)  # Include original sla_dd value
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
                # Check if the link has a valid tier or has a dd_sla value
                tier = link_data.get('tier')
                # Consider any non-empty tier as valid (not empty string, not None, and not just whitespace)
                has_valid_tier = tier is not None and str(tier).strip() != ""
                has_dd_sla = 'sla_dd' in link_data and link_data['sla_dd'] is not None
                
                # For in-use links, include them if they have valid data OR if they can be used for SLA mixing
                if link_id in profile.in_use_links:
                    # Include if has valid tier OR dd_sla, OR if it has 0% SLA for mixing, OR if it's a special link
                    include_link = (
                        has_valid_tier or has_dd_sla or  # Include if either tier or dd_sla is valid
                        (link_data.get('sla') == 0.0) or    # Special case: 0% SLA for mixing
                        (link_data.get('provider') == 'ignore')  # Special provider case
                    )
                    
                    if include_link:
                        links_data[link_id] = link_data
                        logger.info(
                            f"Including in-use link {link_id} with tier {link_data.get('tier', 'N/A')} "
                            f"and SLA {link_data['sla']*100:.1f}% (provider: {link_data.get('provider', 'Unknown')})"
                        )
                    else:
                        logger.warning(
                            f"Excluding in-use link {link_id} from optimizer: "
                            f"missing tier ({has_valid_tier}) or dd_sla ({has_dd_sla})"
                        )
                # For alternative links, apply price cleaning rules
                elif link_id in profile.alternative_links:
                    link_cost = link_data.get('price')
                    link_tier = link_data.get('tier')
                    profile_avg_cost = profile.profile_avg_cost

                    ignore_reason = None

                    if link_tier == 1 and link_cost is not None and link_cost < (profile_avg_cost * 0.6):
                        ignore_reason = f"Tier 1 link cost ({link_cost}) is less than 60% of profile average cost ({profile_avg_cost * 0.6:.2f})"
                    elif link_tier == 2 and link_cost is not None and link_cost < (profile_avg_cost * 0.4):
                        ignore_reason = f"Tier 2 link cost ({link_cost}) is less than 40% of profile average cost ({profile_avg_cost * 0.4:.2f})"
                    
                    if ignore_reason:
                        self.ignored_links.append({
                            'profile_id': profile.profile_id,
                            'profile_name': profile.name,
                            'link_id': link_id,
                            'link_cost': link_cost,
                            'link_tier': link_tier,
                            'profile_avg_cost': profile_avg_cost,
                            'reason': ignore_reason
                        })
                        logger.warning(f"Ignoring alternative link {link_id} for profile {profile.profile_id}: {ignore_reason}")
                        continue # Skip adding this link to links_data
                    
                    # If not ignored by price rules, then include if they have valid tier or SLA
                    if has_valid_tier or has_dd_sla:
                        links_data[link_id] = link_data
                    else:
                        logger.warning(
                            f"Excluding alternative link {link_id} from optimizer: no valid tier (1-4) and no dd_sla"
                        )
                else: # This handles links that are neither in-use nor alternative (shouldn't happen if logic is correct)
                    logger.warning(
                        f"Excluding link {link_id} from optimizer: no valid tier (1-4) and no dd_sla"
                    )
        
        logger.info(f"Found {len(links_data)} valid links for profile {profile.profile_id}")
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
        
        # Get original link data from the mock API
        combined_data = await self.mock_api.get_combined_data()
        original_links_data = {}
        
        # Find the profile in the combined data
        for profile_data in combined_data:
            if profile_data['profile_id'] == profile.profile_id:
                # Extract original link data
                for link_data in profile_data['in_use_links']:
                    original_links_data[link_data['link']] = {
                        'provider': link_data['provider'],
                        'price': link_data['buy_price'],
                        'traffic': link_data.get('traffic', 0),
                        'sla': link_data.get('sla_dd', 0)
                    }
                break
        
        # Calculate statistics using the base method
        stats = await self.calculate_optimization_stats(profile, routing_plan, links_data)
        
        # Add detailed price and SLA comparison for each link in the routing plan
        link_details = []
        for route in routing_plan['routes']:
            link_id = route['link']
            new_price = route['price']
            new_traffic = route['percentage']
            new_sla = route['sla']
            
            # Get original data if available
            original_data = original_links_data.get(link_id, {})
            old_price = original_data.get('price', new_price)
            old_traffic = original_data.get('traffic', 0)
            old_sla = original_data.get('sla', 0)
            
            # Calculate changes
            price_change = new_price - old_price
            price_change_pct = (price_change / old_price) * 100 if old_price > 0 else 0
            traffic_change = new_traffic - old_traffic
            # Handle None values for SLA calculation
            sla_change = new_sla - old_sla if old_sla is not None else new_sla
            
            link_details.append({
                'link': link_id,
                'provider': route['provider'],
                'old_price': old_price,
                'new_price': new_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'old_traffic': old_traffic,
                'new_traffic': new_traffic,
                'traffic_change': traffic_change,
                'old_sla': old_sla,
                'new_sla': new_sla,
                'sla_change': sla_change
            })
        
        # Add detailed information to the stats
        stats['link_details'] = link_details
        stats['summary'] = {
            'achieved_sla': stats['achieved_sla'],
            'expected_sla': stats['expected_sla'],
            'sla_difference': stats['achieved_sla'] - stats['expected_sla'],
            'total_cost': stats['total_cost'],
            'links_used': stats['links_used']
        }
        
        # Add ignored links to the stats
        profile_ignored_links = [link for link in self.ignored_links if link['profile_id'] == profile.profile_id]
        if profile_ignored_links:
            stats['ignored_links'] = profile_ignored_links
            logger.info(f"Added {len(profile_ignored_links)} ignored links to optimization stats for profile {profile.profile_id}")
        
        return stats
        
    def get_ignored_links(self, profile_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get links that were ignored due to price check rules.
        
        Args:
            profile_id: Optional profile ID to filter ignored links
            
        Returns:
            List of dictionaries containing information about ignored links
        """
        if profile_id:
            return [link for link in self.ignored_links if link['profile_id'] == profile_id]
        return self.ignored_links
        
    def clear_ignored_links(self) -> None:
        """
        Clear the list of ignored links.
        This is useful when processing multiple profiles or when rerunning the optimization.
        """
        logger.debug(f"Clearing {len(self.ignored_links)} ignored links")
        self.ignored_links = []