from typing import Dict, Any
from pulp import *
from ..models.profile import Profile

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
        # Get links data
        links_data = {}
        for link in self.profile.links:
            optimizer_data = {
                "SLA": link.average_sla / 100.0,  # Convert to decimal
                "Price": float(link.price)
            }
            links_data[link.link_id] = optimizer_data
            print(f"Processing link {link.link_id}: SLA={link.average_sla}%, Price=${link.price}")
        
        print("\nPreparing optimization model:")
        print(f"- Number of usable links: {len(links_data)}")
        for link_id, data in links_data.items():
            print(f"- Link {link_id}: SLA={data['SLA']*100:.1f}%, Price=${data['Price']:.2f}")
        
        if not links_data:
            print("No usable links found!")
            return False

        # Create a minimization LP problem
        self.model = LpProblem("Minimize_Cost_While_Achieving_SLA", LpMinimize)
        print("\nSetting up optimization constraints:")

        # Decision variables: fraction of traffic on each link
        self.variables = {}
        for link_id in links_data:
            self.variables[link_id] = LpVariable(f"x_{link_id}", lowBound=0, upBound=1, cat='Continuous')

        # Objective: minimize sum(x_i * price_i)
        objective = []
        for link_id, link_data in links_data.items():
            objective.append(self.variables[link_id] * link_data['Price'])
        self.model += lpSum(objective), "Total_Cost"

        # Constraint 1: Fractions sum to 1 (all traffic allocated)
        self.model += lpSum(self.variables.values()) == 1, "TotalTraffic"

        # Constraint 2: Try to achieve target SLA
        target_sla = self.profile.expected_sla / 100.0  # Convert to decimal
        print(f"- Target SLA: {self.profile.expected_sla}%")
        
        # Analyze available SLAs
        sla_values = [(link_id, link_data['SLA']) for link_id, link_data in links_data.items()]
        print("\nAvailable SLAs:")
        for link_id, sla in sorted(sla_values, key=lambda x: -x[1]):
            print(f"- {link_id}: {sla * 100:.1f}%")
        
        # Find best available SLA
        best_sla = max(sla for _, sla in sla_values)
        print(f"\n- Best Available SLA: {best_sla * 100:.1f}%")
        print(f"- Target SLA: {target_sla * 100:.1f}%")
        
        # If target SLA is higher than best available, use best available
        effective_target = min(target_sla, best_sla)
        print(f"- Using Effective Target SLA: {effective_target * 100:.1f}%")
        
        sla_constraint = []
        for link_id, link_data in links_data.items():
            sla_constraint.append(self.variables[link_id] * link_data['SLA'])
        self.model += lpSum(sla_constraint) >= effective_target, "SLA_Requirement"

        # Solve the problem
        print("\nSolving optimization problem...")
        status = self.model.solve(self.SOLVER)
        
        # Store results if optimization was successful
        if status == 1:  # LpStatusOptimal
            self.results = {
                link_id: var.varValue
                for link_id, var in self.variables.items()
            }
            print("Found optimal solution!")
            return True
            
        print(f"Failed to find optimal solution. Status: {LpStatus[status]}")
        return False

    def get_routing_plan(self) -> Dict[str, Any]:
        """Get the optimized routing plan"""
        if not self.results:
            raise ValueError("No results available. Solve the model first.")

        # Get allocation for all links
        routes = []
        for link in self.profile.links:
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
        total_cost = 0
        achieved_sla = 0
        
        for link in self.profile.links:
            allocation = self.results.get(link.link_id, 0)
            if allocation > 0:
                total_cost += allocation * link.price
                achieved_sla += allocation * (link.average_sla / 100.0)

        return {
            'total_cost': total_cost,
            'links_used': len([v for v in self.results.values() if v > 0.001]),  # Ignore very small allocations
            'achieved_sla': achieved_sla * 100,  # Convert back to percentage
            'expected_sla': self.profile.expected_sla
        }