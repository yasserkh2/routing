import json
import os
import asyncio
from datetime import datetime
from ..services.event_handler import EventHandler, EventType
from ..services.mock_services import MockAPIService
from ..models.profile import Profile
from ..models.link import Link
from ..core.optimizer import RoutingOptimizer

async def test_system_integration():
    print("\n=== System Integration Test ===\n")
    
    # Step 1: Initialize Services
    print("Step 1: Initializing Services")
    mock_api = MockAPIService()
    event_handler = EventHandler()
    
    # Read mock data
    mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
    
    # Read initial data
    with open(os.path.join(mock_data_dir, 'price_changes.json'), 'r') as f:
        price_changes = json.load(f)
    with open(os.path.join(mock_data_dir, 'mock_links_data.json'), 'r') as f:
        links_data = json.load(f)
    with open(os.path.join(mock_data_dir, 'mock_profiles.json'), 'r') as f:
        profiles_data = json.load(f)
    
    print("\nStep 2: Creating Price Change Event")
    price_change = price_changes[0]
    event_data = {
        'link': price_change['reference_id'],
        'old_price': price_change['old_rate'],
        'new_price': price_change['new_rate'],
        'provider': price_change['provider_name'],
        'network': price_change['network_name'],
        'mcc': price_change['mcc'],
        'mnc': price_change['mnc'],
        'timestamp': datetime.now().isoformat()
    }
    
    # Create event through event handler
    event = event_handler.create_event(EventType.PRICE_CHANGE, event_data)
    print(f"Created event: {event}")
    
    print("\nStep 3: Processing Event Through API Service")
    # Handle price change through mock API service
    api_event = mock_api.handle_price_change(
        event_data['link'],
        event_data['new_price']
    )
    print(f"API processed event: {api_event}")
    
    print("\nStep 4: Verifying Link Updates")
    # Get updated link data
    updated_links = await mock_api.get_links_sla_data(mnc=event_data['mnc'])
    affected_link = next((link for link in updated_links if link['link'] == event_data['link']), None)
    if affected_link:
        print(f"Link {affected_link['link']} updated price: ${affected_link['price']}")
    
    print("\nStep 5: Creating Link Objects")
    # Create Link objects with updated data
    available_links = [Link.from_api_data(link_data) for link_data in links_data]
    for link in available_links:
        if link.link == event_data['link']:
            print(f"Link object created: {link}")
            print(f"Price history: {link.price_history}")
    
    print("\nStep 6: Creating and Updating Profiles")
    # Create Profile objects
    profiles = [Profile.from_api_data(profile_data, available_links) for profile_data in profiles_data]
    affected_profiles = Profile.get_profiles_affected_by_price_change(profiles, event_data['link'])
    print(f"Found {len(affected_profiles)} affected profiles")
    
    print("\nStep 7: Running Optimization for Affected Profiles")
    print("\n=== Revenue Impact Dashboard ===")
    total_old_revenue = 0
    total_new_revenue = 0
    
    for profile in affected_profiles:
        print(f"\nProfile: {profile.name}")
        print(f"SLA Requirement: {profile.expected_sla}%")
        
        # Calculate revenue before price change
        optimizer_before = RoutingOptimizer(profile)
        if optimizer_before.solve():
            stats_before = optimizer_before.get_optimization_stats()
            old_revenue = stats_before['total_cost']
            total_old_revenue += old_revenue
            
            # Update link price for the affected link
            affected_link = profile.get_link_by_id(event_data['link'])
            if affected_link:
                profile.update_link_price(event_data['link'], event_data['new_price'])
            
            # Calculate revenue after price change and optimization
            optimizer_after = RoutingOptimizer(profile)
            if optimizer_after.solve():
                stats_after = optimizer_after.get_optimization_stats()
                new_revenue = stats_after['total_cost']
                total_new_revenue += new_revenue
                
                # Calculate changes
                revenue_change = new_revenue - old_revenue
                revenue_change_pct = (revenue_change / old_revenue) * 100 if old_revenue > 0 else 0
                
                print("\nRevenue Analysis:")
                print(f"Before Optimization: ${old_revenue:.4f}")
                print(f"After Optimization:  ${new_revenue:.4f}")
                print(f"Revenue Change:     ${revenue_change:+.4f} ({revenue_change_pct:+.2f}%)")
                
                # Show routing changes
                plan_before = optimizer_before.get_routing_plan()
                plan_after = optimizer_after.get_routing_plan()
                
                print("\nRouting Changes:")
                print("Before:")
                for route in plan_before['routes']:
                    if route['percentage'] > 0:
                        print(f"- Link {route['link']}: {route['percentage']:.1f}% "
                              f"(SLA: {route['sla']}%, Price: ${route['price']})")
                
                print("After:")
                for route in plan_after['routes']:
                    if route['percentage'] > 0:
                        print(f"- Link {route['link']}: {route['percentage']:.1f}% "
                              f"(SLA: {route['sla']}%, Price: ${route['price']})")
    
    # Calculate total impact
    total_revenue_change = total_new_revenue - total_old_revenue
    total_revenue_change_pct = (total_revenue_change / total_old_revenue) * 100 if total_old_revenue > 0 else 0
    
    print("\n=== Total Revenue Impact ===")
    print(f"Total Revenue Before: ${total_old_revenue:.4f}")
    print(f"Total Revenue After:  ${total_new_revenue:.4f}")
    print(f"Total Revenue Change: ${total_revenue_change:+.4f} ({total_revenue_change_pct:+.2f}%)")
    
    print("\n=== Integration Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_system_integration())