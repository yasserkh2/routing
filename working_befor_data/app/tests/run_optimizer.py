import asyncio
from ..services.data_preparation_service import DataPreparationService
from ..services.mock_services import MockAPIService
from ..core.optimizer import RoutingOptimizer
from ..models.profile import Profile
import json
import os

async def run_optimizer_test():
    """Test the optimizer with mock data"""
    print("\n" + "="*50)
    print("          PRICE CHANGE IMPACT ANALYSIS")
    print("="*50 + "\n")
    
    # Initialize services
    mock_api = MockAPIService()
    data_service = DataPreparationService()
    
    try:
        # Load price changes
        price_changes_path = os.path.join(os.path.dirname(__file__), '../../mock_data/price_changes.json')
        with open(price_changes_path, 'r') as f:
            price_changes = json.load(f)
        
        # Get all profiles
        all_profiles = await data_service.get_all_profiles()
        
        # For each price change, find affected profiles and optimize
        for change in price_changes:
            link_id = change['reference_id']
            old_rate = change['old_rate']
            new_rate = change['new_rate']
            status = change['status']
            provider = change['provider_name']
            network = change['network_name']
            
            # Find affected profiles
            affected_profiles = Profile.get_profiles_affected_by_price_change(all_profiles, link_id)
            
            print("\n" + "-"*50)
            print(f"PRICE CHANGE DETAILS FOR {link_id}")
            print("-"*50)
            print(f"Provider:     {provider}")
            print(f"Network:      {network}")
            print(f"Old Price:    ${old_rate:.3f}")
            print(f"New Price:    ${new_rate:.3f}")
            print(f"Change:       {status}")
            print(f"SLA:         {change['sla_dd']}%")
            print(f"\nNumber of Affected Profiles: {len(affected_profiles)}")
            
            # Apply the price change
            mock_api.handle_price_change(link_id, new_rate)
            
            # Process each affected profile
            for profile in affected_profiles:
                print("\n" + "-"*50)
                print(f"PROFILE: {profile.name}")
                print("-"*50)
                print(f"Expected SLA:    {profile.expected_sla}%")
                print(f"Available Links: {len(profile.links)}")
                
                # Run initial optimization
                optimizer = RoutingOptimizer(profile)
                success = optimizer.solve()
                
                if success:
                    # Get and display initial results
                    routing_plan = optimizer.get_routing_plan()
                    stats = optimizer.get_optimization_stats()
                    
                    print("\nBEFORE PRICE CHANGE:")
                    print("-" * 30)
                    for route in routing_plan['routes']:
                        if route['percentage'] > 0:
                            print(f"Link {route['link_id']}:")
                            print(f"  Traffic:    {route['percentage']:.1f}%")
                            print(f"  SLA:        {route['sla']:.1f}%")
                            print(f"  Price:      ${route['price']:.3f}")
                    
                    print(f"\nTotal Cost:    ${stats['total_cost']:.3f}")
                    print(f"Active Links:  {stats['links_used']}")
                    print(f"Achieved SLA:  {stats['achieved_sla']:.2f}%")
                    
                    # Get fresh profile data with updated prices
                    updated_profile = await data_service.get_profile_for_optimization(profile.profile_id)
                    optimizer = RoutingOptimizer(updated_profile)
                    success = optimizer.solve()
                    
                    if success:
                        # Get and display new results
                        routing_plan = optimizer.get_routing_plan()
                        stats = optimizer.get_optimization_stats()
                        
                        print("\nAFTER PRICE CHANGE:")
                        print("-" * 30)
                        for route in routing_plan['routes']:
                            if route['percentage'] > 0:
                                print(f"Link {route['link_id']}:")
                                print(f"  Traffic:    {route['percentage']:.1f}%")
                                print(f"  SLA:        {route['sla']:.1f}%")
                                print(f"  Price:      ${route['price']:.3f}")
                        
                        print(f"\nTotal Cost:    ${stats['total_cost']:.3f}")
                        print(f"Active Links:  {stats['links_used']}")
                        print(f"Achieved SLA:  {stats['achieved_sla']:.2f}%")
                        
                        # Calculate and show cost impact
                        cost_change = stats['total_cost'] - routing_plan['routes'][0]['price']
                        cost_change_pct = (cost_change / routing_plan['routes'][0]['price']) * 100
                        print(f"\nCOST IMPACT:")
                        print("-" * 30)
                        print(f"Savings:      ${abs(cost_change):.3f}")
                        print(f"Percentage:   {abs(cost_change_pct):.1f}%")
                    else:
                        print("\nFailed to find optimal solution after price change")
                else:
                    print("\nFailed to find initial optimal solution")
            
    except Exception as e:
        print(f"Error running optimizer: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_optimizer_test())