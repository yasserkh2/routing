import json
import os
import asyncio
from datetime import datetime
from ..services.event_handler import EventHandler, EventType
from ..services.mock_services import MockAPIService
from ..services.data_preparation_service import DataPreparationService
from ..models.profile import Profile
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
    
    print("\nStep 2: Creating Price Change Event")
    price_change = price_changes[0]
    event_data = {
        'Type': 'PriceUpdate',
        'Payload': {
            'old_rate': price_change['Payload']['old_rate'],
            'new_rate': price_change['Payload']['new_rate'],
            'status': price_change['Payload']['status']
        },
        'link': price_change['link'],
        'mcc': price_change['mcc'],
        'mnc': price_change['mnc'],
        'timestamp': datetime.now().isoformat()
    }
    
    # Create event through event handler
    event = event_handler.create_event(event_data)
    print(f"Created event: {event}")
    
    print("\nStep 3: Processing Event Through API Service")
    # Handle price change through mock API service
    api_event = mock_api.handle_price_change(
        event_data['link'],
        event_data['Payload']['new_rate']
    )
    print(f"API processed event: {api_event}")
    
    print("\nStep 4: Verifying Link Updates")
    # Get updated link data
    updated_links = await mock_api.get_links_data(mnc=event_data['mnc'])
    affected_link = next((link for link in updated_links if link['link'] == event_data['link']), None)
    if affected_link:
        print(f"Link {affected_link['link']} updated price: ${affected_link['price']:.3f}")
    
    print("\nStep 5: Creating and Updating Profiles")
    # Create Profile objects using DataPreparationService
    data_service = DataPreparationService()
    profiles = await data_service.get_all_profiles()
    affected_profiles = data_service.get_profiles_affected_by_price_change(profiles, event_data['link'])
    print(f"Found {len(affected_profiles)} affected profiles")
    
    print("\nStep 6: Running Optimization for Affected Profiles")
    print("\n=== Revenue Impact Dashboard ===")
    total_old_revenue = 0
    total_new_revenue = 0
    
    for profile in affected_profiles:
        print(f"\nProfile: {profile.name}")
        print(f"SLA Requirement: {profile.expected_sla}%")
        
        # Calculate revenue before price change
        optimizer_before = RoutingOptimizer(profile)
        if await optimizer_before.solve():
            stats_before = await optimizer_before.get_optimization_stats()
            old_revenue = stats_before['total_cost']
            total_old_revenue += old_revenue
            
            # Update link price for the affected link using DataPreparationService
            DataPreparationService.update_link_price(
                [profile], 
                event_data['link'], 
                event_data['Payload']['new_rate']
            )

            # Calculate revenue after price change and optimization
            optimizer_after = RoutingOptimizer(profile)
            if await optimizer_after.solve():
                stats_after = await optimizer_after.get_optimization_stats()
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
                plan_before = await optimizer_before.get_routing_plan()
                plan_after = await optimizer_after.get_routing_plan()
                
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