import asyncio
from ..services.data_preparation_service import DataPreparationService
from ..services.mock_services import MockAPIService
from ..core.optimizer import RoutingOptimizer

async def run_optimizer_test():
    """Test the optimizer with mock data"""
    print("\n=== Running Optimizer Test ===\n")
    
    # Initialize services
    mock_api = MockAPIService()
    data_service = DataPreparationService()
    
    try:
        # First run optimization with original prices
        print("Initial Optimization:")
        print("--------------------")
        
        # Get Premium_2FA profile which has 95% SLA requirement
        profile = await data_service.get_profile_for_optimization("PROF_002")
        if not profile:
            print("Error: No profile found!")
            return
            
        print(f"Testing optimization for profile: {profile.name}")
        print(f"Expected SLA: {profile.expected_sla}%")
        print(f"Available Links: {len(profile.links)}")
        
        # Run optimizer
        optimizer = RoutingOptimizer(profile)
        success = optimizer.solve()
        
        if success:
            # Get and display initial results
            routing_plan = optimizer.get_routing_plan()
            stats = optimizer.get_optimization_stats()
            
            print("\nInitial Route Allocation:")
            for route in routing_plan['routes']:
                print(f"- Link {route['link_id']}: {route['percentage']:.1f}% (SLA: {route['sla']:.1f}%, Price: ${route['price']:.3f})")
            
            print("\nInitial Statistics:")
            print(f"Total Cost: ${stats['total_cost']:.3f}")
            print(f"Links Used: {stats['links_used']}")
            print(f"Achieved SLA: {stats['achieved_sla']:.2f}%")
            
            # Simulate price changes
            print("\nSimulating Price Changes:")
            print("------------------------")
            # Increase price for most used link
            most_used_link = routing_plan['routes'][0]['link_id']
            old_price = routing_plan['routes'][0]['price']
            new_price = old_price * 1.5  # 50% increase
            
            print(f"Increasing price for {most_used_link} from ${old_price:.3f} to ${new_price:.3f}")
            mock_api.handle_price_change(most_used_link, new_price)
            
            # Run optimization again with new prices
            print("\nRe-running Optimization:")
            print("----------------------")
            profile = await data_service.get_profile_for_optimization("PROF_002")
            optimizer = RoutingOptimizer(profile)
            success = optimizer.solve()
            
            if success:
                # Get and display new results
                routing_plan = optimizer.get_routing_plan()
                stats = optimizer.get_optimization_stats()
                
                print("\nNew Route Allocation:")
                for route in routing_plan['routes']:
                    print(f"- Link {route['link_id']}: {route['percentage']:.1f}% (SLA: {route['sla']:.1f}%, Price: ${route['price']:.3f})")
                
                print("\nNew Statistics:")
                print(f"Total Cost: ${stats['total_cost']:.3f}")
                print(f"Links Used: {stats['links_used']}")
                print(f"Achieved SLA: {stats['achieved_sla']:.2f}%")
        else:
            print("Failed to find optimal solution")
            
    except Exception as e:
        print(f"Error running optimizer: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_optimizer_test())