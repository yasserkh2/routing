import pulp
from typing import Dict, Any, List
from link import Link
from profile import Profile
from sla_data import SLAData

class SimpleRoutingOptimizer:
    """Simplified routing optimizer using Profile and Link classes"""
    
    def __init__(self):
        self.model = None
        self.variables = {}
    
    def optimize(self, profiles: List[Profile], default_volume: float = 1000.0) -> Dict[str, Any]:
        """
        Optimize traffic distribution across links for given profiles
        
        Args:
            profiles: List of Profile objects with their associated links
            default_volume: Default traffic volume per profile
        """
        # Create the model
        self.model = pulp.LpProblem("Route_Optimization", pulp.LpMaximize)
        
        # Decision variables: traffic per profile-link combination
        self.variables = {}
        for profile in profiles:
            for link in profile.get_active_links():
                var_name = f"x_{profile.profile_id}_{link.link_id}"
                self.variables[var_name] = pulp.LpVariable(
                    var_name,
                    lowBound=0,
                    upBound=default_volume,
                    cat=pulp.LpContinuous
                )
        
        # Objective: Balance between SLA and traffic distribution
        objective = []
        for profile in profiles:
            active_links = profile.get_active_links()
            if not active_links:
                continue
                
            # Calculate average SLA for normalization
            avg_sla = sum(link.get_effective_sla() or 0 for link in active_links) / len(active_links)
            
            for link in active_links:
                var_name = f"x_{profile.profile_id}_{link.link_id}"
                effective_sla = link.get_effective_sla() or 0
                sla_decimal = effective_sla / 100.0
                
                # SLA term: prefer higher SLA links
                sla_weight = 1.0 / (link.routing_priority + 1)
                sla_term = self.variables[var_name] * sla_decimal * sla_weight
                
                # Distribution term: encourage spreading traffic
                dist_weight = -0.1 * (self.variables[var_name] / default_volume)
                
                objective.extend([sla_term, dist_weight])
        
        self.model += pulp.lpSum(objective)
        
        # Constraints
        for profile in profiles:
            active_links = profile.get_active_links()
            if not active_links:
                continue
                
            # 1. Total volume per profile must equal default_volume
            profile_vars = [
                self.variables[f"x_{profile.profile_id}_{link.link_id}"]
                for link in active_links
            ]
            self.model += pulp.lpSum(profile_vars) == default_volume
            
            # 2. Weighted average SLA must meet or exceed requirement
            sla_terms = []
            for link in active_links:
                var_name = f"x_{profile.profile_id}_{link.link_id}"
                effective_sla = (link.get_effective_sla() or 0) / 100.0
                sla_terms.append(self.variables[var_name] * effective_sla)
            
            if sla_terms:
                self.model += (
                    pulp.lpSum(sla_terms) >= 
                    (profile.expected_sla / 100.0) * default_volume
                )
            
            # 3. Minimum volume per link if used (to avoid tiny allocations)
            min_volume = default_volume * 0.1  # 10% minimum
            for link in active_links:
                var_name = f"x_{profile.profile_id}_{link.link_id}"
                # Either use 0 or at least min_volume
                self.model += (
                    self.variables[var_name] == 0 or 
                    self.variables[var_name] >= min_volume
                )
        
        # Solve the model
        self.model.solve(pulp.PULP_CBC_CMD(msg=0))
        
        # Process results
        results = {
            'status': pulp.LpStatus[self.model.status],
            'objective_value': pulp.value(self.model.objective),
            'allocations': {}
        }
        
        for profile in profiles:
            profile_results = []
            for link in profile.get_active_links():
                var_name = f"x_{profile.profile_id}_{link.link_id}"
                amount = pulp.value(self.variables[var_name])
                if amount and amount > 0:
                    profile_results.append({
                        'link_id': link.link_id,
                        'volume': amount,
                        'sla': link.get_effective_sla(),
                        'routing_priority': link.routing_priority
                    })
            
            if profile_results:
                results['allocations'][profile.profile_id] = {
                    'name': profile.name,
                    'expected_sla': profile.expected_sla,
                    'routes': sorted(profile_results, key=lambda x: x['routing_priority'])
                }
        
        return results

    def get_optimization_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed statistics about the optimization results"""
        stats = {
            'total_volume': 0,
            'total_profiles': len(results['allocations']),
            'total_links_used': 0,
            'profiles': {}
        }
        
        for profile_id, allocation in results['allocations'].items():
            profile_stats = {
                'total_volume': 0,
                'weighted_sla': 0,
                'links_used': len(allocation['routes'])
            }
            
            for route in allocation['routes']:
                volume = route['volume']
                sla = route['sla'] or 0
                profile_stats['total_volume'] += volume
                profile_stats['weighted_sla'] += volume * (sla / 100.0)
            
            if profile_stats['total_volume'] > 0:
                profile_stats['achieved_sla'] = (
                    profile_stats['weighted_sla'] / profile_stats['total_volume']
                )
            else:
                profile_stats['achieved_sla'] = 0
                
            stats['profiles'][profile_id] = profile_stats
            stats['total_volume'] += profile_stats['total_volume']
            stats['total_links_used'] += profile_stats['links_used']
        
        return stats