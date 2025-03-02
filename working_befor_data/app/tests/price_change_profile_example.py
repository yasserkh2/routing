import json
import os
import asyncio
from datetime import datetime
from ..services.event_handler import EventHandler, EventType
from ..services.mock_services import MockAPIService
from ..models.profile import Profile
from ..models.link import Link
from ..core.optimizer import RoutingOptimizer

async def test_price_change_with_profiles():
    # Initialize services
    mock_api = MockAPIService()
    event_handler = EventHandler()

    # Read mock data
    mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
    
    # Read price changes
    with open(os.path.join(mock_data_dir, 'price_changes.json'), 'r') as f:
        price_changes = json.load(f)
    
    # Read links data
    with open(os.path.join(mock_data_dir, 'mock_links_data.json'), 'r') as f:
        links_data = json.load(f)
    
    # Read profiles data
    with open(os.path.join(mock_data_dir, 'mock_profiles.json'), 'r') as f:
        profiles_data = json.load(f)

    # Create Link objects
    available_links = [Link.from_api_data(link_data) for link_data in links_data]
    
    # Create Profile objects
    profiles = [Profile.from_api_data(profile_data, available_links) for profile_data in profiles_data]
    
    # Process the price change event
    price_change = price_changes[0]  # Get our single example
    affected_link_id = price_change['reference_id']
    
    # Find profiles affected by this price change
    affected_profiles = Profile.get_profiles_affected_by_price_change(profiles, affected_link_id)
    
    print(f"\nProcessing price change for link {affected_link_id}")
    print(f"Old price: ${price_change['old_rate']}")
    print(f"New price: ${price_change['new_rate']}")
    
    print(f"\nAffected Profiles:")
    for profile in affected_profiles:
        print(f"\n{'='*80}")
        print(f"Profile: {profile.name} (ID: {profile.profile_id})")
        print(f"Expected SLA: {profile.expected_sla}%")
        print(f"Priority: {profile.priority}")
        
        # Create optimizer and get original routing plan
        optimizer = RoutingOptimizer(profile)
        print("\nOriginal Routing Plan:")
        if optimizer.solve():
            original_plan = optimizer.get_routing_plan()
            original_stats = optimizer.get_optimization_stats()
            
            print("\nRoute Allocations:")
            for route in original_plan['routes']:
                if route['percentage'] > 0:
                    print(f"- Link {route['link_id']}: {route['percentage']:.1f}% "
                          f"(SLA: {route['sla']}%, Price: ${route['price']})")
            
            print("\nOptimization Stats:")
            print(f"Total Cost: ${original_stats['total_cost']:.4f}")
            print(f"Links Used: {original_stats['links_used']}")
            print(f"Achieved SLA: {original_stats['achieved_sla']:.1f}%")
        
        # Update the link price
        profile.update_link_price(affected_link_id, price_change['new_rate'])
        
        # Get new optimized routing plan
        optimizer = RoutingOptimizer(profile)
        print("\nNew Routing Plan (After Price Change):")
        if optimizer.solve():
            new_plan = optimizer.get_routing_plan()
            new_stats = optimizer.get_optimization_stats()
            
            print("\nNew Route Allocations:")
            for route in new_plan['routes']:
                if route['percentage'] > 0:
                    print(f"- Link {route['link_id']}: {route['percentage']:.1f}% "
                          f"(SLA: {route['sla']}%, Price: ${route['price']})")
            
            print("\nNew Optimization Stats:")
            print(f"Total Cost: ${new_stats['total_cost']:.4f}")
            print(f"Links Used: {new_stats['links_used']}")
            print(f"Achieved SLA: {new_stats['achieved_sla']:.1f}%")
            
            # Calculate changes
            cost_change = ((new_stats['total_cost'] - original_stats['total_cost']) 
                         / original_stats['total_cost'] * 100)
            sla_change = new_stats['achieved_sla'] - original_stats['achieved_sla']
            
            print("\nChanges:")
            print(f"Cost Change: {cost_change:+.2f}%")
            print(f"SLA Change: {sla_change:+.2f}%")
            print(f"Links Used Change: {new_stats['links_used'] - original_stats['links_used']:+d}")

if __name__ == "__main__":
    asyncio.run(test_price_change_with_profiles())