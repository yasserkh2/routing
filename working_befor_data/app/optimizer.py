from typing import Dict, Any
from pulp import *
from profile import Profile

class RoutingOptimizer:
    """Linear optimization model for minimizing cost while meeting SLA requirements"""
    
    SOLVER = PULP_CBC_CMD(msg=0)  # Default solver configuration
    
    def __init__(self, profile: Profile):
        self.profile = profile
        self.model = None
        self.variables = {}
        self.results = {}

    def _prepare_links_data(self) -> Dict[str, Dict[str, float]]:
        """Convert Profile's links to the format needed for optimization"""
        links_data = {}
        for link in self.profile.links:
            if link.average_sla > 0:
                links_data[link.link_id] = {
                    "SLA": link.average_sla / 100.0,  # Convert to decimal
                    "Price": float(link.price)
                }
        return links_data

    def solve(self) -> bool:
        """
        Solve the optimization problem to minimize cost while meeting SLA requirements
        
        Returns:
            bool: True if optimization was successful, False otherwise
        """
        # Prepare links data
        links = self._prepare_links_data()
        if not links:
            return False

        # Create a minimization LP problem
        self.model = LpProblem("Minimize_Cost_While_Achieving_SLA", LpMinimize)

        # Decision variables: fraction of traffic on each link
        self.variables = {}
        for link_id in links:
            self.variables[link_id] = LpVariable(f"x_{link_id}", lowBound=0, upBound=1, cat='Continuous')

        # Objective: minimize sum(x_i * price_i)
        objective = []
        for link_id, link_data in links.items():
            objective.append(self.variables[link_id] * link_data['Price'])
        self.model += lpSum(objective), "Total_Cost"

        # Constraint 1: Fractions sum to 1 (all traffic allocated)
        self.model += lpSum(self.variables.values()) == 1, "TotalTraffic"

        # Constraint 2: Weighted SLA >= target_sla
        target_sla = self.profile.expected_sla / 100.0  # Convert to decimal
        sla_constraint = []
        for link_id, link_data in links.items():
            sla_constraint.append(self.variables[link_id] * link_data['SLA'])
        self.model += lpSum(sla_constraint) >= target_sla, "SLA_Requirement"

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
            if link.average_sla > 0:
                percentage = self.results.get(link.link_id, 0) * 100  # Convert fraction to percentage
                routes.append({
                    'link_id': link.link_id,
                    'percentage': percentage,
                    'sla': link.average_sla,
                    'price': link.price
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
        links = self._prepare_links_data()
        total_cost = sum(
            self.results[link_id] * link_data['Price']
            for link_id, link_data in links.items()
        )
        achieved_sla = sum(
            self.results[link_id] * link_data['SLA']
            for link_id, link_data in links.items()
        ) * 100  # Convert back to percentage

        stats = {
            'total_cost': total_cost,
            'links_used': len([v for v in self.results.values() if v > 0.001]),  # Ignore very small allocations
            'achieved_sla': achieved_sla,
            'expected_sla': self.profile.expected_sla
        }

        return stats