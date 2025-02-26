from typing import List, Dict, Any, Optional
from pulp import *
from profile import Profile
from link import Link

class RoutingOptimizer:
    """Linear optimization model for maximizing profit while meeting SLA requirements"""
    
    def __init__(self, profiles: List[Profile], default_volume: float = 1000.0):
        self.profiles = profiles
        self.default_volume = default_volume
        self.model = None
        self.variables = {}
        self.results = {}

    def setup_model(self, profile_volumes: Optional[Dict[str, float]] = None):
        """Setup the linear programming model"""
        # Create optimization model
        self.model = LpProblem("Routing_Optimization", LpMaximize)
        
        # Create decision variables for each profile-link combination
        # x[i,j] = volume of traffic from profile i through link j
        self.variables = {}
        for profile in self.profiles:
            volume = profile_volumes.get(profile.profile_id, self.default_volume) if profile_volumes else self.default_volume
            for link in profile.links:
                if link.is_usable():
                    var_name = f"x_{profile.profile_id}_{link.link_id}"
                    self.variables[var_name] = LpVariable(var_name, 0, volume)

        # Objective function: Maximize profit
        # Profit = Sum(volume * (price_difference))
        objective = []
        for profile in self.profiles:
            for link in profile.links:
                if link.is_usable():
                    var_name = f"x_{profile.profile_id}_{link.link_id}"
                    # Assuming price_difference is stored in link data
                    price_diff = link.price_difference if hasattr(link, 'price_difference') else 1.0
                    objective.append(self.variables[var_name] * price_diff)
        
        self.model += lpSum(objective)

        # Constraints
        for profile in self.profiles:
            volume = profile_volumes.get(profile.profile_id, self.default_volume) if profile_volumes else self.default_volume
            
            # 1. Volume constraint: Total volume through all links must equal profile volume
            profile_vars = [
                self.variables[f"x_{profile.profile_id}_{link.link_id}"]
                for link in profile.links
                if link.is_usable()
            ]
            if profile_vars:
                self.model += lpSum(profile_vars) == volume

            # 2. SLA constraint: Average SLA must meet profile requirement
            sla_constraint = []
            for link in profile.links:
                if link.is_usable():
                    var_name = f"x_{profile.profile_id}_{link.link_id}"
                    effective_sla = link.get_effective_sla() or 0
                    sla_constraint.append(self.variables[var_name] * effective_sla)
            
            if sla_constraint:
                self.model += lpSum(sla_constraint) >= profile.expected_sla * volume

            # 3. Link capacity constraints (if available)
            for link in profile.links:
                if link.is_usable() and hasattr(link, 'capacity'):
                    var_name = f"x_{profile.profile_id}_{link.link_id}"
                    self.model += self.variables[var_name] <= link.capacity

    def solve(self) -> bool:
        """Solve the optimization model"""
        if not self.model:
            raise ValueError("Model not set up. Call setup_model first.")
            
        status = self.model.solve()
        
        # Store results if optimization was successful
        if status == 1:  # LpStatusOptimal
            self.results = {
                var.name: var.varValue
                for var in self.model.variables()
            }
            return True
        return False

    def get_routing_plan(self) -> Dict[str, Any]:
        """Get the optimized routing plan"""
        if not self.results:
            raise ValueError("No results available. Solve the model first.")

        routing_plan = {}
        for profile in self.profiles:
            profile_routes = []
            for link in profile.links:
                if link.is_usable():
                    var_name = f"x_{profile.profile_id}_{link.link_id}"
                    if var_name in self.results and self.results[var_name] > 0:
                        profile_routes.append({
                            'link_id': link.link_id,
                            'volume': self.results[var_name],
                            'effective_sla': link.get_effective_sla(),
                            'routing_priority': link.routing_priority
                        })
            
            if profile_routes:
                routing_plan[profile.profile_id] = {
                    'name': profile.name,
                    'expected_sla': profile.expected_sla,
                    'routes': sorted(profile_routes, key=lambda x: x['routing_priority'])
                }

        return routing_plan

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        if not self.results:
            raise ValueError("No results available. Solve the model first.")

        total_profit = value(self.model.objective)
        total_volume = sum(
            volume for var_name, volume in self.results.items()
            if volume > 0
        )

        stats = {
            'total_profit': total_profit,
            'total_volume': total_volume,
            'profiles_optimized': len(self.profiles),
            'links_used': len([v for v in self.results.values() if v > 0]),
            'objective_value': value(self.model.objective)
        }

        return stats