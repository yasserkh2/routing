from typing import Dict, Any, List
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
        self.link_dict = {link.link: link for link in profile.links}  # Store links in a dictionary for O(1) lookups
        logger.info(f"Initialized RoutingOptimizer for profile {profile.profile_id}")
    
    def solve(self) -> bool:
        """
        Solve the optimization problem to minimize cost while meeting SLA requirements
        
        Returns:
            bool: True if optimization was successful, False otherwise
        """
        # Get links data using the Link class's to_optimizer_format method
        links_data = {}
        for link in self.profile.links:
            price = link.get_current_price()
            if price is not None:
                links_data[link.link] = link.to_optimizer_format()
        logger.info(f"Found {len(links_data)} links with valid prices")
        
        if not links_data:
            logger.error("No valid links found for optimization")
            return False

        # Sort links by SLA in descending order
        sorted_links = sorted(links_data.items(), key=lambda x: x[1]['SLA'], reverse=True)

        # Create a minimization LP problem
        self.model = LpProblem("Minimize_Cost_While_Achieving_SLA", LpMinimize)
        logger.info("Created LP minimization problem")

        # Decision variables: fraction of traffic on each link (only for links with valid prices)
        self.variables = {}
        for link_id, link_data in links_data.items():
            if 'Price' in link_data:  # Only create variables for links with valid prices
                self.variables[link_id] = LpVariable(f"x_{link_id.replace('-', '_')}", lowBound=0, upBound=1, cat='Continuous')

        # Objective: minimize sum(x_i * price_i)
        objective = []
        for link_id, link_data in links_data.items():
            if 'Price' in link_data:  # Only include links with valid prices
                objective.append(self.variables[link_id] * link_data['Price'])
        self.model += lpSum(objective), "Total_Cost"

        # Constraint 1: Fractions sum to 1 (all traffic allocated)
        self.model += lpSum(self.variables.values()) == 1, "TotalTraffic"

        # Constraint 2: Try to achieve target SLA
        target_sla = self.profile.expected_sla / 100.0  # Convert to decimal
        
        # Add SLA constraint - the model will automatically try to get as close as possible
        sla_constraint = []
        for link_id, link_data in links_data.items():
            sla_constraint.append(self.variables[link_id] * link_data['SLA'])
        
        # Set target SLA as the goal - optimizer will get as close as possible
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
            
        # If optimization fails and we have links available, use the highest SLA link
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
        for link in self.profile.links:
            percentage = self.results.get(link.link, 0) * 100  # Convert fraction to percentage
            if percentage > 0:  # Only include routes with traffic
                optimizer_data = link.to_optimizer_format()
                routes.append({
                    'link': link.link,
                    'percentage': percentage,
                    'sla': link.average_sla,
                    'price': optimizer_data['Price']
                })

        return {
            'profile_id': self.profile.profile_id,
            'name': self.profile.name,
            'expected_sla': self.profile.expected_sla,
            'routes': sorted(routes, key=lambda x: (-x['percentage'], -x['sla']))
        }

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        if not self.results:
            raise ValueError("No results available. Solve the model first.")

        routing_plan = self.get_routing_plan()
        total_cost = 0
        achieved_sla = 0
        active_links = 0
        logger.info("Calculating optimization statistics")

        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                link = self.link_dict.get(route['link'])
                if link:
                    optimizer_data = link.to_optimizer_format()
                    total_cost += (route['percentage'] / 100.0) * optimizer_data['Price']
                    achieved_sla += (route['percentage'] / 100.0) * optimizer_data['SLA']
                    active_links += 1

        stats = {
            'total_cost': total_cost,
            'links_used': active_links,
            'achieved_sla': achieved_sla * 100,  # Convert back to percentage
            'expected_sla': self.profile.expected_sla,
            'sla_achievable': getattr(self, 'sla_achievable', True),  # Default to True for backward compatibility
            'max_achievable_sla': getattr(self, 'max_achievable_sla', achieved_sla * 100)
        }
        logger.info(f"Optimization stats: Cost={total_cost:.2f}, Links={active_links}, SLA={achieved_sla*100:.2f}%")
        
        # Add warning if target SLA cannot be achieved
        if not stats['sla_achievable']:
            warning_msg = (
                f"Target SLA of {self.profile.expected_sla}% cannot be achieved. "
                f"Maximum achievable SLA with available links is {stats['max_achievable_sla']:.2f}%"
            )
            stats['warning'] = warning_msg
            logger.warning(warning_msg)
            
        return stats

    def calculate_cost(self, routing_plan: Dict[str, Any], use_previous_price: bool = False) -> float:
        """Calculate total cost based on a routing plan"""
        total_cost = 0.0
        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                link = self.link_dict.get(route['link'])
                if link:
                    price = link.get_previous_price() if use_previous_price else link.get_current_price()
                    total_cost += link.calculate_cost_for_traffic(route['percentage'], price)
        return total_cost

    def calculate_cost_impact(self, before_plan: Dict[str, Any], after_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost impact between two routing plans"""
        logger.info("Calculating cost impact between routing plans")
        before_cost = self.calculate_cost(before_plan)
        after_cost = self.calculate_cost(after_plan)
        cost_change = after_cost - before_cost
        cost_change_pct = (cost_change / before_cost) * 100 if before_cost > 0 else 0
        logger.info(f"Cost impact: Before={before_cost:.2f}, After={after_cost:.2f}, Change={cost_change_pct:.2f}%")
        
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
                link = self.link_dict.get(route['link'])
                if link:
                    optimizer_data = link.to_optimizer_format()
                    achieved_sla += (route['percentage'] / 100.0) * (optimizer_data['SLA'] * 100)  # Convert optimizer SLA back to percentage
        return achieved_sla  # Already in percentage

    def format_routing_display(self, routing_plan: Dict[str, Any], use_previous_price: bool = False) -> List[Dict[str, Any]]:
        """Format routing plan for display"""
        display_routes = []
        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                link = self.link_dict.get(route['link'])
                if link:
                    price = link.get_previous_price() if use_previous_price else link.get_current_price()
                    display_routes.append(link.format_display_info(route['percentage'], price))
        return display_routes

    def calculate_total_traffic(self, routing_plan: Dict[str, Any]) -> float:
        """Calculate total traffic allocation"""
        return sum(route['percentage'] for route in routing_plan['routes'])