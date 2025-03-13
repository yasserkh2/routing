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
    print("          SLA CHANGE IMPACT ANALYSIS")
    print("="*50 + "\n")
    
    # Initialize services
    mock_api = MockAPIService()
    data_service = DataPreparationService()
    
    try:
        # Load SLA change
        sla_update_path = os.path.join(os.path.dirname(__file__), '../../mock_data/sla_update.json')
        with open(sla_update_path, 'r') as f:
            change = json.load(f)
        
        # Get all profiles using DataPreparationService
        all_profiles = await data_service.get_all_profiles()
        
        # Process the SLA change
        link_name = change['link']
        changed_sla = change['Payload']['changed_sla']
        status = change['Payload']['status']

        # Find affected profiles
        affected_profiles = data_service.get_profiles_affected_by_price_change(all_profiles, link_name)
        
        print("\n" + "-"*50)
        print(f"SLA CHANGE DETAILS FOR {link_name}")
        print("-"*50)
        for sla_type, values in changed_sla.items():
            print(f"{sla_type}:")
            print(f"  Old:     {values['old']:.1f}%")
            print(f"  New:     {values['new']:.1f}%")
            print(f"  Change:  {values['new'] - values['old']:.1f}%")
        print(f"Status:    {status}")
        print(f"\nNumber of Affected Profiles: {len(affected_profiles)}")
        
        # Process each affected profile
        for profile in affected_profiles:
            print("\n" + "-"*50)
            print(f"PROFILE: {profile.name}")
            print("-"*50)
            print(f"Expected SLA:    {profile.expected_sla}%")
            print(f"Available Links: {len(profile.links)}")
            
            # Run initial optimization with old SLA values
            optimizer = RoutingOptimizer(profile)
            success = optimizer.solve()
            
            if success:
                # Get and store initial results
                initial_plan = optimizer.get_routing_plan()
                
                print("\nBEFORE SLA CHANGE:")
                print("-" * 30)
                for route in initial_plan['routes']:
                    current_link = data_service.find_link_by_id(profile.links, route['link'])
                    if current_link:
                        route_info = current_link.format_display_info(route['percentage'])
                        print(f"Link {route_info['link']}:")
                        print(f"  Traffic:    {route_info['traffic']:.1f}%")
                        print(f"  SLA:        {route_info['sla']:.1f}%")
                        print(f"  Price:      ${route_info['price']:.3f}")
                
                # Get optimization stats
                stats = optimizer.get_optimization_stats()
                print(f"\nAchieved SLA:  {stats['achieved_sla']:.2f}%")
                
                # Simulate SLA change without modifying database
                target_link = data_service.find_link_by_id(profile.links, link_name)
                if target_link:
                    # Update the link with new SLA values
                    updated_link = target_link.update_sla(changed_sla)
                    # Replace the old link with the updated one in this profile only
                    profile.links = [updated_link if link.link == link_name else link for link in profile.links]
                optimizer = RoutingOptimizer(profile)
                success = optimizer.solve()
                
                if success:
                    # Get and display new results
                    after_plan = optimizer.get_routing_plan()
                    
                    print("\nAFTER SLA CHANGE:")
                    print("-" * 30)
                    for route in after_plan['routes']:
                        current_link = data_service.find_link_by_id(profile.links, route['link'])
                        if current_link:
                            route_info = current_link.format_display_info(route['percentage'])
                            print(f"Link {route_info['link']}:")
                            print(f"  Traffic:    {route_info['traffic']:.1f}%")
                            print(f"  SLA:        {route_info['sla']:.1f}%")
                            print(f"  Price:      ${route_info['price']:.3f}")
                    
                    # Get optimization stats
                    stats = optimizer.get_optimization_stats()
                    print(f"\nAchieved SLA:  {stats['achieved_sla']:.2f}%")
                    
                    # Display warning if target SLA cannot be achieved and show max achievable
                    if not stats['sla_achievable']:
                        print(f"\nWARNING: {stats['warning']}")
                        print(f"Max Achievable SLA: {stats['max_achievable_sla']:.2f}%")
                else:
                    print("\nFailed to find optimal solution after SLA change")
            else:
                print("\nFailed to find initial optimal solution")
            
    except Exception as e:
        print(f"Error running optimizer: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_optimizer_test())