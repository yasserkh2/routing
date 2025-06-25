from typing import Dict, Any, List
import pulp
from ..utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class RoutingOptimizer:
    """Pure linear optimization algorithm for minimizing cost while meeting SLA requirements"""
    
    def __init__(self):
        logger.info("Initialized RoutingOptimizer")
    
    def minimize_cost_with_target_sla(self, links: Dict[str, Dict[str, Any]], target_sla: float) -> Dict[str, Any]:
        """
        Solve a linear optimization problem to distribute traffic among multiple links
        so that the overall SLA meets the target_sla exactly, while minimizing total cost.
        
        :param links: dict {
             link_id: { "sla": float, "price": float, "provider": str }
        }
        :param target_sla: float, e.g., 0.90 (as decimal) or 90.0 (as percentage)
        :return: dict containing { 'status', 'allocation', 'min_cost', 'achieved_sla' }
        """
        logger.info(f"Starting optimization with {len(links)} links, target SLA: {target_sla}")
        
        if not links:
            logger.error("No valid links provided for optimization")
            return {
                'status': 'No_Links',
                'allocation': {},
                'min_cost': 0,
                'achieved_sla': 0
            }
        
        # Convert target_sla to decimal if it's given as percentage
        if target_sla > 1.0:
            target_sla = target_sla / 100.0
        
        # Normalize link data format
        normalized_links = {}
        for link_id, link_data in links.items():
            # Handle different possible key names
            sla = link_data.get('sla', link_data.get('SLA', 0))
            price = link_data.get('price', link_data.get('Price', 0))
            
            # Convert SLA to decimal if it's given as percentage
            if sla > 1.0:
                sla = sla / 100.0
                
            normalized_links[link_id] = {
                'SLA': sla,
                'Price': price,
                'provider': link_data.get('provider', 'Unknown')
            }
        
        # 1) Create a minimization LP problem
        model = pulp.LpProblem("Minimize_Cost_While_Achieving_SLA", pulp.LpMinimize)
        
        # Decision variables: fraction of traffic on each link i
        x = {}
        for link_id in normalized_links:
            x[link_id] = pulp.LpVariable(f"x_{link_id.replace('-', '_')}", lowBound=0, upBound=1, cat='Continuous')
        
        # 2) Objective: minimize sum(x_i * price_i)
        model += pulp.lpSum([
            x[link_id] * normalized_links[link_id]['Price']
            for link_id in normalized_links
        ]), "Total_Cost"
        
        # 3) Constraints:
        
        # (A) Fractions sum to 1 (all traffic allocated)
        model += pulp.lpSum([x[link_id] for link_id in normalized_links]) == 1, "TotalTraffic"
        
        # (B) Achieve target SLA (with minimum requirement but allow exceeding if necessary)
        tolerance = 0.001  # 0.1% tolerance
        sla_expression = pulp.lpSum([
            x[link_id] * normalized_links[link_id]['SLA']
            for link_id in normalized_links
        ])
        
        # Set SLA constraint to achieve at least the target SLA
        model += sla_expression >= target_sla - tolerance, "SLA_Minimum"
        
        # (C) Limit "Undel" link to maximum 5% traffic if present
        if "Undel" in normalized_links:
            logger.info("Adding constraint: Undel link limited to maximum 5% traffic")
            model += x["Undel"] <= 0.05, "Undel_Max_Traffic"
        
        # Define the objective function (minimize cost)
        model += pulp.lpSum([
            x[link_id] * normalized_links[link_id]['Price']
            for link_id in normalized_links
        ]), "Total_Cost"
        
        logger.info(f"SLA constraints: {(target_sla-tolerance)*100:.1f}% <= SLA <= {(target_sla+tolerance)*100:.1f}%")
        
        # 4) Solve the problem
        solver = pulp.PULP_CBC_CMD(msg=0)
        model.solve(solver)
        
        # 5) Collect results
        status = pulp.LpStatus[model.status]
        allocation = {
            link_id: x[link_id].varValue if x[link_id].varValue is not None else 0.0
            for link_id in normalized_links
        }
        min_cost = pulp.value(model.objective) if model.objective else 0
        
        # Calculate achieved SLA
        achieved_sla = sum(
            allocation[link_id] * normalized_links[link_id]['SLA']
            for link_id in normalized_links
        )
        
        logger.info(f"Optimization result: Status={status}, Cost={min_cost:.4f}, Achieved SLA={achieved_sla*100:.2f}%")
        
        # If optimization failed, try fallback to highest SLA link
        if status != 'Optimal' and normalized_links:
            logger.warning("Optimization failed, using fallback strategy")
            # Find the link with highest SLA
            best_link = max(normalized_links.items(), key=lambda x: x[1]['SLA'])
            best_link_id = best_link[0]
            
            # Reset allocation to use only the best link
            allocation = {link_id: 0.0 for link_id in normalized_links}
            allocation[best_link_id] = 1.0
            
            min_cost = normalized_links[best_link_id]['Price']
            achieved_sla = normalized_links[best_link_id]['SLA']
            status = 'Fallback'
            
            logger.info(f"Fallback result: Using {best_link_id}, Cost={min_cost:.4f}, SLA={achieved_sla*100:.2f}%")
        
        return {
            'status': status,
            'allocation': allocation,
            'min_cost': min_cost,
            'achieved_sla': achieved_sla
        }
    
    def solve(self, links_data: Dict[str, Dict[str, Any]], target_sla: float) -> bool:
        """
        Solve the optimization problem (wrapper for backward compatibility)
        
        Args:
            links_data: Dictionary mapping link IDs to their data
            target_sla: Target SLA as percentage (e.g., 85.0 for 85%)
        
        Returns:
            bool: True if optimization was successful, False otherwise
        """
        result = self.minimize_cost_with_target_sla(links_data, target_sla)
        
        # Store results for backward compatibility
        self.results = result['allocation']
        self.optimization_result = result
        
        return result['status'] in ['Optimal', 'Fallback']
    
    def get_results(self) -> Dict[str, float]:
        """Get the optimization results as traffic allocation fractions"""
        if not hasattr(self, 'results') or not self.results:
            raise ValueError("No results available. Solve the model first.")
        return self.results.copy()
    
    def get_routing_plan(self, links_data: Dict[str, Dict[str, Any]], profile_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get the optimized routing plan with detailed information
        
        Args:
            links_data: Dictionary mapping link IDs to their data
            profile_info: Optional profile information (profile_id, name, expected_sla)
        
        Returns:
            Dictionary containing the routing plan with routes and metadata
        """
        if not hasattr(self, 'results') or not self.results:
            raise ValueError("No results available. Solve the model first.")

        # Get allocation for all links with traffic > 0
        routes = []
        for link_id, allocation in self.results.items():
            percentage = allocation * 100  # Convert fraction to percentage
            if percentage > 0.001:  # Only include routes with significant traffic (>0.1%)
                link_data = links_data[link_id]
                
                # Handle different possible key names and formats
                sla = link_data.get('sla', link_data.get('SLA', 0))
                price = link_data.get('price', link_data.get('Price', 0))
                provider = link_data.get('provider', 'Unknown')
                
                # Convert SLA to percentage if it's in decimal
                if sla <= 1.0:
                    sla = sla * 100
                
                routes.append({
                    'link': link_id,
                    'percentage': percentage,
                    'sla': sla,
                    'price': price,
                    'provider': provider
                })

        # Sort routes by percentage (highest first), then by SLA
        routes.sort(key=lambda x: (-x['percentage'], -x['sla']))

        routing_plan = {
            'routes': routes
        }
        
        # Add profile information if provided
        if profile_info:
            routing_plan.update({
                'profile_id': profile_info.get('profile_id', ''),
                'name': profile_info.get('name', ''),
                'expected_sla': profile_info.get('expected_sla', 0.0)
            })

        return routing_plan

    def get_optimization_stats(self, links_data: Dict[str, Dict[str, Any]], target_sla: float) -> Dict[str, Any]:
        """Get optimization statistics"""
        if not hasattr(self, 'optimization_result'):
            raise ValueError("No results available. Solve the model first.")
        
        result = self.optimization_result
        active_links = sum(1 for allocation in result['allocation'].values() if allocation > 0.001)
        
        stats = {
            'total_cost': result['min_cost'],
            'links_used': active_links,
            'achieved_sla': result['achieved_sla'] * 100,  # Convert to percentage
            'expected_sla': target_sla if target_sla <= 1.0 else target_sla,  # Handle both formats
            'sla_difference': (result['achieved_sla'] * 100) - (target_sla if target_sla > 1.0 else target_sla * 100),
            'sla_achievable': result['status'] in ['Optimal', 'Fallback'],
            'max_achievable_sla': result['achieved_sla'] * 100,
            'optimization_status': result['status']
        }
        
        logger.info(f"Stats: Cost={stats['total_cost']:.4f}, Links={stats['links_used']}, SLA={stats['achieved_sla']:.2f}%")
        
        return stats

    def calculate_cost(self, routing_plan: Dict[str, Any]) -> float:
        """Calculate total cost based on a routing plan"""
        total_cost = 0.0
        for route in routing_plan.get('routes', []):
            if route['percentage'] > 0:
                total_cost += (route['percentage'] / 100.0) * route['price']
        return total_cost

    def calculate_achieved_sla(self, routing_plan: Dict[str, Any]) -> float:
        """Calculate achieved SLA based on routing plan"""
        achieved_sla = 0.0
        for route in routing_plan.get('routes', []):
            if route['percentage'] > 0:
                sla = route['sla']
                # Convert to decimal if it's in percentage
                if sla > 1.0:
                    sla = sla / 100.0
                achieved_sla += (route['percentage'] / 100.0) * sla
        return achieved_sla * 100  # Convert to percentage

    def calculate_cost_impact(self, before_plan: Dict[str, Any], after_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost impact between two routing plans"""
        before_cost = self.calculate_cost(before_plan)
        after_cost = self.calculate_cost(after_plan)
        cost_change = after_cost - before_cost
        cost_change_pct = (cost_change / before_cost) * 100 if before_cost > 0 else 0
        
        return {
            'before_cost': before_cost,
            'after_cost': after_cost,
            'cost_change': cost_change,
            'cost_change_percentage': cost_change_pct,
            'savings': abs(cost_change) if cost_change < 0 else 0,
            'savings_percentage': abs(cost_change_pct) if cost_change < 0 else 0
        }

    def reset(self):
        """Reset the optimizer state for a new optimization"""
        if hasattr(self, 'results'):
            delattr(self, 'results')
        if hasattr(self, 'optimization_result'):
            delattr(self, 'optimization_result')
        logger.info("Optimizer state reset")


# Example usage and testing function
def test_optimizer():
    """Test the optimizer with sample data"""
    optimizer = RoutingOptimizer()
    
    # Example links data
    links_data = {
        "link1": {"sla": 0.92, "price": 100, "provider": "Provider A"},
        "link2": {"sla": 0.90, "price": 120, "provider": "Provider B"},
        "link3": {"sla": 0.85, "price": 80, "provider": "Provider C"},
        "link4": {"sla": 0.95, "price": 150, "provider": "Provider D"},
    }
    target_sla = 90.0  # 90%
    
    result = optimizer.minimize_cost_with_target_sla(links_data, target_sla)
    
    print("Solver Status:", result['status'])
    print("Optimal Allocation (fractions of total traffic):")
    for link_id, fraction in result['allocation'].items():
        if fraction > 0.001:  # Only show links with significant traffic
            print(f"  {link_id}: {fraction:.3f} ({fraction*100:.1f}%)")
    print(f"Minimum Total Cost: {result['min_cost']:.2f}")
    print(f"Achieved SLA: {result['achieved_sla']*100:.2f}%")
    
    return result


if __name__ == "__main__":
    test_optimizer()