from typing import Dict, Any, List
from functools import lru_cache
from pulp import *
from ..models.profile import Profile
from ..models.link import Link
from ..utils.logger import setup_logger
from ..services.mock_services import MockAPIService

# Setup logger
logger = setup_logger(__name__)

class RoutingOptimizer:
    """Linear optimization model for minimizing cost while meeting SLA requirements"""
    
    SOLVER = PULP_CBC_CMD(msg=0)  # Default solver configuration
    
    def __init__(self, profile: Profile):
        self.profile = profile
        self.model = None
        self.variables = {}
        self.results = {}
        self.mock_api = MockAPIService()
        logger.info(f"Initialized RoutingOptimizer for profile {profile.profile_id}")
    
    async def get_link_data(self, link_id: str) -> Dict[str, Any]:
        """Get link data from the mock API"""
        combined_data = await self.mock_api.get_combined_data()
        for profile_data in combined_data:
            # Check in_use_links
            for link_data in profile_data['in_use_links']:
                if link_data['link'] == link_id:
                    # Get DD SLA if available
                    dd_sla = link_data.get('sla_dd', 0) / 100.0 if 'sla_dd' in link_data else None
                    
                    # Get tier SLA based on tier mapping
                    tier = link_data.get('tier', 3)  # Default to tier 3 if not specified
                    tier_sla_mapping = {
                        1: 0.99,  # 99% SLA for tier 1
                        2: 0.95,  # 95% SLA for tier 2
                        3: 0.90   # 90% SLA for tier 3
                    }
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
                    # Get tier SLA based on tier mapping
                    tier = link_data.get('tier', 3)  # Default to tier 3 if not specified
                    tier_sla_mapping = {
                        1: 0.99,  # 99% SLA for tier 1
                        2: 0.95,  # 95% SLA for tier 2
                        3: 0.90   # 90% SLA for tier 3
                    }
                    tier_sla = tier_sla_mapping.get(tier, 0.90)  # Default to 90% if tier not found
                    
                    return {
                        'link': link_id,
                        'provider': link_data['provider'],
                        'price': link_data['buy_price'],
                        'sla': tier_sla,  # Use tier SLA for alternative links
                        'tier': tier
                    }
        return None

    async def solve(self) -> bool:
        """
        Solve the optimization problem to minimize cost while meeting SLA requirements.
        
        Returns:
            bool: True if optimization was successful, False otherwise
        """
        # Get links data from mock API
        links_data = {}
        for link_id in self.profile.get_all_links():
            link_data = await self.get_link_data(link_id)
            if link_data:
                links_data[link_id] = link_data
        
        logger.info(f"Found {len(links_data)} links")
        
        if not links_data:
            logger.error("No valid links found for optimization")
            return False

        # Sort links by SLA (descending)
        sorted_links = sorted(
            links_data.items(), 
            key=lambda x: x[1]['sla'], 
            reverse=True
        )

        # Create a minimization LP problem
        self.model = LpProblem("Minimize_Cost_While_Achieving_SLA", LpMinimize)
        logger.info("Created LP minimization problem")

        # Decision variables: fraction of traffic on each link
        self.variables = {}
        for link_id, link_data in links_data.items():
            self.variables[link_id] = LpVariable(f"x_{link_id.replace('-', '_')}", lowBound=0, upBound=1, cat='Continuous')

        # Objective: minimize sum(x_i * price_i)
        objective = []
        for link_id, link_data in links_data.items():
            objective.append(self.variables[link_id] * link_data['price'])
        self.model += lpSum(objective), "Total_Cost"

        # Constraint 1: Fractions sum to 1 (all traffic allocated)
        self.model += lpSum(self.variables.values()) == 1, "TotalTraffic"

        # Constraint 2: Try to achieve target SLA
        target_sla = self.profile.expected_sla / 100.0  # Convert to decimal
        sla_constraint = []
        for link_id, link_data in links_data.items():
            sla_constraint.append(self.variables[link_id] * link_data['sla'])
        self.model += lpSum(sla_constraint) >= target_sla, "SLA_Requirement"

        # Solve the problem
        logger.info("Starting optimization solver")
        status = self.model.solve(self.SOLVER)
        
        # Store results if optimization was successful
        if status == 1:  # LpStatusOptimal
            self.results = {
                link_id: var.varValue
                for link_id, var in self.variables.items()
            }
            logger.info("Optimization completed successfully")
            return True
            
        # If optimization fails, use the highest SLA link
        if sorted_links:
            best_link_id, _ = sorted_links[0]
            self.results = {best_link_id: 1.0}  # Assign 100% traffic to best link
            logger.warning("Optimization failed, falling back to highest SLA link")
            return True
            
        logger.error("Optimization failed and no fallback links available")
        return False

    async def get_routing_plan(self) -> Dict[str, Any]:
        """Get the optimized routing plan"""
        if not self.results:
            logger.error("Attempted to get routing plan without results")
            raise ValueError("No results available. Solve the model first.")

        # Get allocation for all links
        routes = []
        for link_id, percentage in self.results.items():
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
            'profile_id': self.profile.profile_id,
            'name': self.profile.name,
            'expected_sla': self.profile.expected_sla,
            'routes': sorted(routes, key=lambda x: (-x['percentage'], -x['sla']))
        }

    async def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        if not self.results:
            raise ValueError("No results available. Solve the model first.")

        routing_plan = await self.get_routing_plan()
        total_cost = 0
        achieved_sla = 0
        active_links = 0
        tier_stats = {}  # Track stats per tier
        logger.info("Calculating optimization statistics")

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
        max_sla = 0
        for link_id in self.profile.get_all_links():
            link_data = await self.get_link_data(link_id)
            if link_data:
                max_sla = max(max_sla, link_data['sla'] * 100)

        stats = {
            'total_cost': total_cost,
            'links_used': active_links,
            'achieved_sla': achieved_sla * 100,  # Convert back to percentage
            'expected_sla': self.profile.expected_sla,
            'tier_stats': tier_stats,
            'sla_achievable': achieved_sla * 100 >= self.profile.expected_sla,
            'max_achievable_sla': max_sla
        }
        logger.info(
            f"Optimization stats: Cost=${total_cost:.2f}, Links={active_links}, "
            f"SLA={achieved_sla*100:.2f}%, Tier Stats={tier_stats}"
        )
        
        # Add warning if target SLA cannot be achieved
        if not stats['sla_achievable']:
            warning_msg = (
                f"Target SLA of {self.profile.expected_sla}% cannot be achieved. "
                f"Maximum achievable SLA with available links is {stats['max_achievable_sla']:.2f}%"
            )
            stats['warning'] = warning_msg
            logger.warning(warning_msg)
            
        return stats