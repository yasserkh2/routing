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
            print(f"\nNumber of Affected Profiles: {len(affected_profiles)}")
            
            # Process each affected profile
            for profile in affected_profiles:
                print("\n" + "-"*50)
                print(f"PROFILE: {profile.name}")
                print("-"*50)
                print(f"Expected SLA:    {profile.expected_sla}%")
                print(f"Available Links: {len(profile.links)}")
                
                # Run initial optimization with old price
                optimizer = RoutingOptimizer(profile)
                success = optimizer.solve()
                
                if success:
                    # Get and store initial results with old price
                    initial_plan = optimizer.get_routing_plan()
                    
                    print("\nBEFORE PRICE CHANGE:")
                    print("-" * 30)
                    for route_info in profile.format_routing_display(initial_plan):
                        print(f"Link {route_info['link_id']}:")
                        print(f"  Traffic:    {route_info['traffic']:.1f}%")
                        print(f"  SLA:        {route_info['sla']:.1f}%")
                        print(f"  Price:      ${old_rate if route_info['link_id'] == link_id else route_info['price']:.3f}")
                    
                    # For initial stats, use old_rate for the changed link
                    total_cost = 0.0
                    active_links = 0
                    for route in initial_plan['routes']:
                        if route['percentage'] > 0:
                            active_links += 1
                            traffic_ratio = route['percentage'] / 100.0
                            if route['link_id'] == link_id:
                                total_cost += traffic_ratio * old_rate
                            else:
                                total_cost += traffic_ratio * route['price']
                    
                    print(f"\nTotal Cost:    ${total_cost:.3f}")
                    print(f"Active Links:  {active_links}")
                    print(f"Achieved SLA:  {profile.calculate_achieved_sla(initial_plan):.2f}%")
                    
                    # Apply the price change
                    # First update the link with both old and new prices
                    for link in profile.links:
                        if link.link_id == link_id:
                            profile.update_link_price(link_id, new_rate, old_rate)
                            break
                    
                    # Then handle the price change in mock API with both old and new rates
                    mock_api.handle_price_change(link_id, new_rate, old_rate)
                    
                    # Get fresh profile data with updated prices
                    updated_profile = await data_service.get_profile_for_optimization(profile.profile_id)
                    optimizer = RoutingOptimizer(updated_profile)
                    success = optimizer.solve()
                    
                    if success:
                        # Get and display new results
                        after_plan = optimizer.get_routing_plan()
                        
                        print("\nAFTER PRICE CHANGE:")
                        print("-" * 30)
                        for route_info in updated_profile.format_routing_display(after_plan):
                            print(f"Link {route_info['link_id']}:")
                            print(f"  Traffic:    {route_info['traffic']:.1f}%")
                            print(f"  SLA:        {route_info['sla']:.1f}%")
                            print(f"  Price:      ${new_rate if route_info['link_id'] == link_id else route_info['price']:.3f}")
                        
                        # For after stats, use new_rate for the changed link
                        total_cost = 0.0
                        active_links = 0
                        for route in after_plan['routes']:
                            if route['percentage'] > 0:
                                active_links += 1
                                traffic_ratio = route['percentage'] / 100.0
                                if route['link_id'] == link_id:
                                    total_cost += traffic_ratio * new_rate
                                else:
                                    total_cost += traffic_ratio * route['price']
                        
                        print(f"\nTotal Cost:    ${total_cost:.3f}")
                        print(f"Active Links:  {active_links}")
                        print(f"Achieved SLA:  {updated_profile.calculate_achieved_sla(after_plan):.2f}%")
                    else:
                        print("\nFailed to find optimal solution after price change")
                else:
                    print("\nFailed to find initial optimal solution")
            
    except Exception as e:
        print(f"Error running optimizer: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_optimizer_test())