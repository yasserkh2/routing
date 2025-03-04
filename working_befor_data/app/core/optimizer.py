from typing import Dict, Any
from pulp import *
from ..models.profile import Profile
from ..models.link import Link

class RoutingOptimizer:
    """Linear optimization model for minimizing cost while meeting SLA requirements"""
    
    SOLVER = PULP_CBC_CMD(msg=0)  # Default solver configuration
    
    def __init__(self, profile: Profile):
        self.profile = profile
        self.model = None
        self.variables = {}
        self.results = {}
    
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
                links_data[link.link_id] = link.to_optimizer_format()
        
        if not links_data:
            return False

        # Create a minimization LP problem
        self.model = LpProblem("Minimize_Cost_While_Achieving_SLA", LpMinimize)

        # Decision variables: fraction of traffic on each link (only for links with valid prices)
        self.variables = {}
        for link_id, link_data in links_data.items():
            if 'Price' in link_data:  # Only create variables for links with valid prices
                self.variables[link_id] = LpVariable(f"x_{link_id}", lowBound=0, upBound=1, cat='Continuous')

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
        
        # Calculate average SLA using Link class method
        avg_sla = Link.calculate_average_sla(self.profile.links) / 100.0  # Convert to decimal
        
        # If target SLA is higher than average available, use average
        effective_target = min(target_sla, avg_sla)
        
        sla_constraint = []
        for link_id, link_data in links_data.items():
            sla_constraint.append(self.variables[link_id] * link_data['SLA'])
        self.model += lpSum(sla_constraint) >= effective_target, "SLA_Requirement"

        # Solve the problem
        status = self.model.solve(self.SOLVER)
        
        # Store results if optimization was successful
        if status == 1:  # LpStatusOptimal
            self.results = {
                link_id: var.varValue
                for link_id, var in self.variables.items()
            }
            return True
        return False

    def get_routing_plan(self) -> Dict[str, Any]:
        """Get the optimized routing plan"""
        if not self.results:
            raise ValueError("No results available. Solve the model first.")

        # Get allocation for all links
        routes = []
        for link in self.profile.links:
            percentage = self.results.get(link.link_id, 0) * 100  # Convert fraction to percentage
            if percentage > 0:  # Only include routes with traffic
                optimizer_data = link.to_optimizer_format()
                routes.append({
                    'link_id': link.link_id,
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

        # Calculate total cost and achieved SLA
        total_cost = 0
        achieved_sla = 0
        
        for link in self.profile.links:
            allocation = self.results.get(link.link_id, 0)
            if allocation > 0:
                optimizer_data = link.to_optimizer_format()
                total_cost += allocation * optimizer_data['Price']
                achieved_sla += allocation * optimizer_data['SLA']

        return {
            'total_cost': total_cost,
            'links_used': len([v for v in self.results.values() if v > 0.001]),  # Ignore very small allocations
            'achieved_sla': achieved_sla * 100,  # Convert back to percentage
            'expected_sla': self.profile.expected_sla
        }