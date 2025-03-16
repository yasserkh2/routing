import asyncio
from ..services.mock_services import MockAPIService
from ..services.data_preparation_service import DataPreparationService
from ..core.optimizer import RoutingOptimizer
from ..models.profile import Profile
from ..models.link import Link
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
        # Load price change
        price_changes_path = os.path.join(os.path.dirname(__file__), '../../mock_data/price_changes.json')
        with open(price_changes_path, 'r') as f:
            change = json.load(f)
        
        # Get all profiles using DataPreparationService
        all_profiles = await data_service.get_all_profiles()
        
        # Process the price change
        link_name = change['link']
        old_rate = change['Payload']['old_rate']
        new_rate = change['Payload']['new_rate']
        status = change['Payload']['status']
            
        # Find affected profiles
        affected_profiles = data_service.get_profiles_affected_by_price_change(all_profiles, link_name)
        
        print("\n" + "-"*50)
        print(f"PRICE CHANGE DETAILS FOR {link_name}")
        print("-"*50)
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
                    for route in initial_plan['routes']:
                        current_link = data_service.find_link_by_id(profile.links, route['link'])
                        if current_link:
                            # Use old_rate for the changed link
                            override_price = old_rate if route['link'] == link_name else None
                            route_info = current_link.format_display_info(route['percentage'], override_price)
                            # Display link price in larger format (x10)
                            display_price = route_info['price'] * 10
                            print(f"Link {route_info['link']}:")
                            print(f"  Traffic:    {route_info['traffic']:.1f}%")
                            print(f"  SLA:        {route_info['sla']:.1f}%")
                            print(f"  Price:      ${display_price:.3f}")
                    
                    # Calculate initial stats using Link's methods
                    total_cost = 0.0
                    active_links = 0
                    for route in initial_plan['routes']:
                        if route['percentage'] > 0:
                            active_links += 1
                            current_link = data_service.find_link_by_id(profile.links, route['link'])
                            if current_link:
                                # Use old_rate for the changed link
                                override_price = old_rate if route['link'] == link_name else None
                                total_cost += current_link.calculate_cost_for_traffic(route['percentage'], override_price)
                    
                    # Load profile's sell price from profiles.json
                    profiles_path = os.path.join(os.path.dirname(__file__), '../../mock_data/profiles.json')
                    with open(profiles_path, 'r') as f:
                        profiles_data = json.load(f)
                        profile_data = next(p for p in profiles_data if p["profile_id"] == profile.profile_id)
                        sell_price = profile_data["sell_price"]
                    
                    # Calculate initial profit
                    initial_profit = sell_price - total_cost
                    
                    # Display costs in larger format (x10)
                    display_total_cost = total_cost * 10
                    display_sell_price = sell_price * 10
                    display_initial_profit = initial_profit * 10
                    
                    # Get optimization stats
                    stats = optimizer.get_optimization_stats()
                    
                    print(f"\nTotal Cost:    ${display_total_cost:.3f}")
                    print(f"Sell Price:    ${display_sell_price:.3f}")
                    print(f"Profit:        ${display_initial_profit:.3f}")
                    print(f"Active Links:  {active_links}")
                    # Show achieved SLA
                    stats = optimizer.get_optimization_stats()
                    print(f"Achieved SLA:  {stats['achieved_sla']:.2f}%")
                    
                    # Display warning if target SLA cannot be achieved and show max achievable
                    if not stats['sla_achievable']:
                        print(f"\nWARNING: {stats['warning']}")
                        print(f"Max Achievable SLA: {stats['max_achievable_sla']:.2f}%")
                    
                    # Apply the price change using DataPreparationService
                    DataPreparationService.update_link_price(
                        [profile],
                        link_name,
                        new_rate,
                        old_rate
                    )

                    # Then handle the price change in mock API with both old and new rates
                    mock_api.handle_price_change(link_name, new_rate, old_rate)
                    
                    # Get fresh profile data with updated prices using DataPreparationService
                    updated_profile = await data_service.get_profile_for_optimization(profile.profile_id)
                    optimizer = RoutingOptimizer(updated_profile)
                    success = optimizer.solve()
                    
                    if success:
                        # Get and display new results
                        after_plan = optimizer.get_routing_plan()
                        
                        print("\nAFTER PRICE CHANGE:")
                        print("-" * 30)
                        for route in after_plan['routes']:
                            current_link = data_service.find_link_by_id(updated_profile.links, route['link'])
                            if current_link:
                                # Use new_rate for the changed link
                                override_price = new_rate if route['link'] == link_name else None
                                route_info = current_link.format_display_info(route['percentage'], override_price)
                                print(f"Link {route_info['link']}:")
                                print(f"  Traffic:    {route_info['traffic']:.1f}%")
                                print(f"  SLA:        {route_info['sla']:.1f}%")
                                print(f"  Price:      ${route_info['price']:.3f}")
                        
                        # Calculate after stats using Link's methods
                        total_cost = 0.0
                        active_links = 0
                        for route in after_plan['routes']:
                            if route['percentage'] > 0:
                                active_links += 1
                                current_link = data_service.find_link_by_id(updated_profile.links, route['link'])
                                if current_link:
                                    # Use new_rate for the changed link
                                    override_price = new_rate if route['link'] == link_name else None
                                    total_cost += current_link.calculate_cost_for_traffic(route['percentage'], override_price)
                        
                        # Calculate profit after price change
                        profiles_path = os.path.join(os.path.dirname(__file__), '../../mock_data/profiles.json')
                        with open(profiles_path, 'r') as f:
                            profiles_data = json.load(f)
                            profile_data = next(p for p in profiles_data if p["profile_id"] == profile.profile_id)
                            sell_price = profile_data["sell_price"]
                        
                        # Calculate new profit and compare
                        new_profit = sell_price - total_cost
                        profit_change = new_profit - initial_profit
                        profit_status = "Increased" if profit_change > 0 else "Decreased" if profit_change < 0 else "Unchanged"
                        
                        # Get optimization stats
                        stats = optimizer.get_optimization_stats()
                        
                        print(f"\nTotal Cost:    ${total_cost:.3f}")
                        print(f"Sell Price:    ${sell_price:.3f}")
                        print(f"Profit:        ${new_profit:.3f}")
                        print(f"Profit Change: ${profit_change:.3f} ({profit_status})")
                        print(f"Active Links:  {active_links}")
                        print(f"Achieved SLA:  {stats['achieved_sla']:.2f}%")
                        
                        # Display warning if target SLA cannot be achieved and show max achievable
                        if not stats['sla_achievable']:
                            print(f"\nWARNING: {stats['warning']}")
                            print(f"Max Achievable SLA: {stats['max_achievable_sla']:.2f}%")
                    else:
                        print("\nFailed to find optimal solution after price change")
                else:
                    print("\nFailed to find initial optimal solution")
            
    except Exception as e:
        print(f"Error running optimizer: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_optimizer_test())