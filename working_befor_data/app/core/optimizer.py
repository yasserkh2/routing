from typing import Dict, Any, List
from functools import lru_cache
from pulp import *
from ..models.profile import Profile
from ..models.link import Link
from ..utils.logger import setup_logger

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
        # Store all links (both in-use and alternative) in a dictionary for O(1) lookups
        self.link_dict = {link.link: link for link in profile.get_all_links()}
        logger.info(f"Initialized RoutingOptimizer for profile {profile.profile_id}")
    
    def solve(self) -> bool:
        """
        Solve the optimization problem to minimize cost while meeting SLA requirements.
        The tier requirements are automatically handled through the Link's SLA mapping.
        
        Returns:
            bool: True if optimization was successful, False otherwise
        """
        # Get links data using the Link class's to_optimizer_format method
        links_data = {}
        for link in self.profile.get_all_links():
            links_data[link.link] = link.to_optimizer_format()
        logger.info(f"Found {len(links_data)} links")
        
        if not links_data:
            logger.error("No valid links found for optimization")
            return False

        # Sort links by SLA (descending)
        sorted_links = sorted(
            links_data.items(), 
            key=lambda x: x[1]['SLA'], 
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
            objective.append(self.variables[link_id] * link_data['Price'])
        self.model += lpSum(objective), "Total_Cost"

        # Constraint 1: Fractions sum to 1 (all traffic allocated)
        self.model += lpSum(self.variables.values()) == 1, "TotalTraffic"

        # Constraint 2: Try to achieve target SLA
        target_sla = self.profile.expected_sla / 100.0  # Convert to decimal
        sla_constraint = []
        for link_id, link_data in links_data.items():
            sla_constraint.append(self.variables[link_id] * link_data['SLA'])
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

    def get_routing_plan(self) -> Dict[str, Any]:
        """Get the optimized routing plan"""
        if not self.results:
            logger.error("Attempted to get routing plan without results")
            raise ValueError("No results available. Solve the model first.")

        # Get allocation for all links
        routes = []
        for link_id, percentage in self.results.items():
            percentage = percentage * 100  # Convert fraction to percentage
            if percentage > 0:  # Only include routes with traffic
                link = self.link_dict[link_id]
                routes.append({
                    'link': link_id,
                    'provider': link.provider,
                    'percentage': percentage,
                    'sla_dd': link.sla_dd,
                    'tier': link.tier,
                    'tier_sla': link.TIER_SLA_MAP.get(link.tier, 90.0),
                    'price': link.price
                })

        return {
            'profile_id': self.profile.profile_id,
            'name': self.profile.name,
            'expected_sla': self.profile.expected_sla,
            'routes': sorted(routes, key=lambda x: (-x['percentage'], -x['sla_dd']))
        }

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        if not self.results:
            raise ValueError("No results available. Solve the model first.")

        routing_plan = self.get_routing_plan()
        total_cost = 0
        achieved_sla = 0
        active_links = 0
        tier_stats = {}  # Track stats per tier
        logger.info("Calculating optimization statistics")

        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                link = self.link_dict[route['link']]
                total_cost += (route['percentage'] / 100.0) * link.price
                achieved_sla += (route['percentage'] / 100.0) * (link.sla_dd / 100.0)
                active_links += 1
                
                # Track tier statistics
                tier = link.tier
                if tier not in tier_stats:
                    tier_stats[tier] = {
                        'traffic': 0,
                        'required_sla': link.TIER_SLA_MAP.get(tier, 90.0)
                    }
                tier_stats[tier]['traffic'] += route['percentage']

        stats = {
            'total_cost': total_cost,
            'links_used': active_links,
            'achieved_sla': achieved_sla * 100,  # Convert back to percentage
            'expected_sla': self.profile.expected_sla,
            'tier_stats': tier_stats,
            'sla_achievable': achieved_sla * 100 >= self.profile.expected_sla,
            'max_achievable_sla': max(link.sla_dd for link in self.link_dict.values())
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

    def calculate_cost(self, routing_plan: Dict[str, Any]) -> float:
        """Calculate total cost based on a routing plan"""
        total_cost = 0.0
        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                link = self.link_dict[route['link']]
                total_cost += (route['percentage'] / 100.0) * link.price
        return total_cost

    def calculate_cost_impact(self, before_plan: Dict[str, Any], after_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost impact between two routing plans"""
        logger.info("Calculating cost impact between routing plans")
        before_cost = self.calculate_cost(before_plan)
        after_cost = self.calculate_cost(after_plan)
        cost_change = after_cost - before_cost
        cost_change_pct = (cost_change / before_cost) * 100 if before_cost > 0 else 0
        logger.info(f"Cost impact: Before=${before_cost:.2f}, After=${after_cost:.2f}, Change={cost_change_pct:.2f}%")
        
        return {
            'before_cost': before_cost,
            'after_cost': after_cost,
            'savings': abs(cost_change),
            'percentage': abs(cost_change_pct)
        }

    def calculate_achieved_sla(self, routing_plan: Dict[str, Any]) -> float:
        """Calculate achieved SLA based on routing plan"""
        achieved_sla = 0.0
        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                link = self.link_dict[route['link']]
                achieved_sla += (route['percentage'] / 100.0) * link.sla_dd
        return achieved_sla

    def format_routing_display(self, routing_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format routing plan for display"""
        display_routes = []
        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                link = self.link_dict[route['link']]
                display_routes.append({
                    'link': link.link,
                    'provider': link.provider,
                    'traffic': route['percentage'],
                    'sla_dd': link.sla_dd,
                    'tier': link.tier,
                    'tier_sla': link.TIER_SLA_MAP.get(link.tier, 90.0),
                    'price': link.price
                })
        return display_routes

    def calculate_total_traffic(self, routing_plan: Dict[str, Any]) -> float:
        """Calculate total traffic allocation"""
        return sum(route['percentage'] for route in routing_plan['routes'])