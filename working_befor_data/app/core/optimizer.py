from typing import Dict, Any, List
from pulp import *
from ..models.profile import Profile
from ..utils.logger import setup_logger
from ..services.data_preparation_service import DataPreparationService

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
        self.data_service = DataPreparationService()
        logger.info(f"Initialized RoutingOptimizer for profile {profile.profile_id}")

    async def optimize(self, links_data: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        Run the PuLP optimization algorithm to minimize cost while meeting SLA requirements.
        
        Args:
            links_data: Dictionary mapping link IDs to their data
            
        Returns:
            Dictionary mapping link IDs to traffic allocation (as fractions)
        """
        if not links_data:
            logger.error("No valid links provided for optimization")
            return {}

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
        
        # Return results if optimization was successful
        if status == 1:  # LpStatusOptimal
            results = {
                link_id: var.varValue
                for link_id, var in self.variables.items()
            }
            logger.info("Optimization completed successfully")
            return results
        
        # Return empty dictionary if optimization failed
        logger.error("Optimization failed")
        return {}
    
    async def solve(self) -> bool:
        """
        Solve the optimization problem, including data preparation and fallback logic.
        
        Returns:
            bool: True if optimization was successful, False otherwise
        """
        # Get links data from data preparation service
        links_data = await self.data_service.prepare_links_data_for_optimizer(self.profile)
        logger.info(f"Found {len(links_data)} links")
        
        if not links_data:
            logger.error("No valid links found for optimization")
            return False
            
        # Run the optimization algorithm
        optimization_results = await self.optimize(links_data)
        
        if optimization_results:
            # Store the results
            self.results = optimization_results
            return True
            
        # If optimization fails, use the highest SLA link as fallback
        best_link_id = await self.data_service.get_highest_sla_link_for_profile(self.profile)
        if best_link_id:
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
            
        # Use data preparation service to prepare the routing plan
        return await self.data_service.prepare_routing_plan_for_profile(self.profile, self.results)
        
    async def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        if not self.results:
            raise ValueError("No results available. Solve the model first.")
            
        # Get routing plan
        routing_plan = await self.get_routing_plan()
        
        # Use data preparation service to calculate statistics
        return await self.data_service.calculate_optimization_stats_for_profile(self.profile, routing_plan)