import asyncio
import os
import json
from typing import Dict, List, Any
from ..services.data_preparation_service import DataPreparationService
from ..core.optimizer import RoutingOptimizer
from ..utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

async def test_optimizer():
    """
    Comprehensive test for the optimizer using data from the data preparation service.
    Tests both SLA optimization and price change impact analysis.
    """
    # Initialize services
    data_service = DataPreparationService()
    optimizer = RoutingOptimizer()
    
    try:
        # Get all profiles
        all_profiles = await data_service.get_all_profiles()
        
        if not all_profiles:
            return
        
        # Test each profile
        for profile in all_profiles:
            
            # Get original traffic allocation from mock data
            original_links_data = {}
            combined_data = await data_service.mock_api.get_combined_data()
            for profile_data in combined_data:
                if profile_data['profile_id'] == profile.profile_id:
                    for link_data in profile_data['in_use_links']:
                        original_links_data[link_data['link']] = {
                            'provider': link_data['provider'],
                            'traffic': link_data.get('traffic', 0),
                            'price': link_data['buy_price'],
                            'sla': link_data.get('sla_dd', 0.85)
                        }
                    break
            
            # First, optimize using only the in-use links (Round 1)
            
            # Create a filtered version of links_data with only in-use links
            in_use_links_data = {}
            for link_id in original_links_data.keys():
                # Get the link data from the full dataset
                for link_id_full, link_data in (await data_service.prepare_links_data_for_optimizer(profile)).items():
                    if link_id_full == link_id:
                        in_use_links_data[link_id] = link_data
                        break
            
            # Run optimization using only in-use links
            in_use_optimizer = RoutingOptimizer()
            in_use_success = in_use_optimizer.solve(in_use_links_data, profile.expected_sla)
            
            if in_use_success:
                # Get optimization results for in-use links
                profile_info = {
                    'profile_id': profile.profile_id,
                    'name': profile.name,
                    'expected_sla': profile.expected_sla
                }
                in_use_routing_plan = in_use_optimizer.get_routing_plan(in_use_links_data, profile_info)
                in_use_stats = in_use_optimizer.get_optimization_stats(in_use_links_data, profile.expected_sla)
                
                print(f"\n--- 1. Profile: {profile.name} - Round 1: reusuing current routes ---")
                print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                in_use_optimized_cost = 0
                for route in in_use_routing_plan['routes']:
                    if route['percentage'] > 0:  # Only show routes with traffic
                        link_cost = (route['percentage'] / 100.0) * route['price']
                        in_use_optimized_cost += link_cost
                        print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
            
            # Reset optimizer for the full optimization
            in_use_optimizer.reset()
            
            # Now proceed with full optimization including alternative links (Round 2)
            
            # Clear any previous ignored links
            data_service.clear_ignored_links()
            
            # Get all alternative links with their details before price cleaning
            alt_links_details = []
            for link_id in profile.alternative_links:
                link_data = await data_service.get_link_data(link_id)
                if link_data:
                    alt_links_details.append({
                        'link_id': link_id,
                        'tier': link_data.get('tier'),
                        'cost': link_data.get('price'),
                        'provider': link_data.get('provider')
                    })
            
            # Sort alternative links by tier and then by cost
            alt_links_details.sort(key=lambda x: (x['tier'] if x['tier'] is not None else 999, x['cost'] if x['cost'] is not None else 0))
            
            # Get link data for this profile using data preparation service (this will apply price cleaning)
            links_data = await data_service.prepare_links_data_for_optimizer(profile)
            
            # Get ignored links for this profile
            profile_ignored_links = data_service.get_ignored_links(profile.profile_id)
            ignored_link_ids = [link['link_id'] for link in profile_ignored_links]
            
            # Run optimization using the new pure optimizer with original expected SLA
            success = optimizer.solve(links_data, profile.expected_sla)
            
            if success:
                # Get optimization results
                profile_info = {
                    'profile_id': profile.profile_id,
                    'name': profile.name,
                    'expected_sla': profile.expected_sla
                }
                routing_plan = optimizer.get_routing_plan(links_data, profile_info)
                stats = optimizer.get_optimization_stats(links_data, profile.expected_sla)
                
                print(f"\n--- 2. Profile: {profile.name} - All other links including undel ---")
                print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                optimized_cost = 0
                for route in routing_plan['routes']:
                    if route['percentage'] > 0:  # Only show routes with traffic
                        link_cost = (route['percentage'] / 100.0) * route['price']
                        optimized_cost += link_cost
                        print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
                
                """# Calculate traffic changes
                print(f"\n--- Profile: {profile.name} - Traffic Changes (Original vs. Full Optimization) ---")
                print("| Link ID       | Provider                      | Before % | After %  | Change   | Cost Impact ($) |")
                print("|---------------|-------------------------------|----------|----------|----------|----------------|")
                for link_id in set(original_links_data.keys()) | set(route['link'] for route in routing_plan['routes'] if route['percentage'] > 0):
                    original_traffic = original_links_data.get(link_id, {}).get('traffic', 0)
                    new_traffic = next((route['percentage'] for route in routing_plan['routes'] if route['link'] == link_id), 0)
                    traffic_change = new_traffic - original_traffic
                    
                    if original_traffic > 0 or new_traffic > 0:
                        provider = original_links_data.get(link_id, {}).get('provider')
                        if not provider:
                            provider = next((route['provider'] for route in routing_plan['routes'] if route['link'] == link_id), "Unknown")
                        
                        # Calculate cost impact
                        original_price = original_links_data.get(link_id, {}).get('price', 0)
                        new_price = next((route['price'] for route in routing_plan['routes'] if route['link'] == link_id), original_price)
                        
                        original_link_cost = (original_traffic / 100.0) * original_price
                        new_link_cost = (new_traffic / 100.0) * new_price
                        cost_impact = new_link_cost - original_link_cost
                        
                        print(f"| {link_id:<13} | {provider:<29} | {original_traffic:7.1f}% | {new_traffic:7.1f}% | {traffic_change:+7.1f}% | ${cost_impact:+14.4f} |")"""
                
                # Run optimization with minimum links constraint - 4 links
                min_links_count = 4  # Set minimum number of links to 4
                min_traffic = 0.05  # Set minimum traffic per link to 5%
                
                # Reset optimizer for the minimum links test
                optimizer.reset()
                
                # Run optimization with minimum links constraint
                min_links_success = optimizer.solve(links_data, profile.expected_sla, min_links=min_links_count, min_traffic_per_link=min_traffic)
                
                if min_links_success:
                    # Get optimization results for minimum links
                    min_links_profile_info = {
                        'profile_id': profile.profile_id,
                        'name': profile.name,
                        'expected_sla': profile.expected_sla
                    }
                    min_links_routing_plan = optimizer.get_routing_plan(links_data, min_links_profile_info)
                    min_links_stats = optimizer.get_optimization_stats(links_data, profile.expected_sla)
                    
                    print(f"\n--- 3. Profile: {profile.name} - All other links including undel (minimum 4 links) ---")
                    print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                    print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                    min_links_optimized_cost = 0
                    active_links = 0
                    for route in min_links_routing_plan['routes']:
                        if route['percentage'] > 0:  # Only show routes with traffic
                            active_links += 1
                            link_cost = (route['percentage'] / 100.0) * route['price']
                            min_links_optimized_cost += link_cost
                            print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
                    
                # Reset optimizer for the new test
                optimizer.reset()
                
                # Create a filtered version of links_data without Undel
                no_undel_links_data = {}
                for link_id, link_data in links_data.items():
                    if link_id != "Undel":
                        no_undel_links_data[link_id] = link_data
                
                # Run optimization without Undel
                no_undel_success = optimizer.solve(no_undel_links_data, profile.expected_sla)
                
                if no_undel_success:
                    # Get optimization results without Undel
                    no_undel_profile_info = {
                        'profile_id': profile.profile_id,
                        'name': profile.name,
                        'expected_sla': profile.expected_sla
                    }
                    no_undel_routing_plan = optimizer.get_routing_plan(no_undel_links_data, no_undel_profile_info)
                    no_undel_stats = optimizer.get_optimization_stats(no_undel_links_data, profile.expected_sla)
                    
                    print(f"\n--- 4. Profile: {profile.name} - All other links excluding undel ---")
                    print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                    print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                    no_undel_optimized_cost = 0
                    for route in no_undel_routing_plan['routes']:
                        if route['percentage'] > 0:  # Only show routes with traffic
                            link_cost = (route['percentage'] / 100.0) * route['price']
                            no_undel_optimized_cost += link_cost
                            print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
                    
                # Reset optimizer for the new test
                optimizer.reset()
                
                # Run optimization without Undel with minimum 4 links
                no_undel_min_links_success = optimizer.solve(no_undel_links_data, profile.expected_sla, min_links=min_links_count, min_traffic_per_link=min_traffic)
                
                if no_undel_min_links_success:
                    # Get optimization results without Undel with minimum 4 links
                    no_undel_min_links_profile_info = {
                        'profile_id': profile.profile_id,
                        'name': profile.name,
                        'expected_sla': profile.expected_sla
                    }
                    no_undel_min_links_routing_plan = optimizer.get_routing_plan(no_undel_links_data, no_undel_min_links_profile_info)
                    no_undel_min_links_stats = optimizer.get_optimization_stats(no_undel_links_data, profile.expected_sla)
                    
                    print(f"\n--- 5. Profile: {profile.name} - All other links excluding undel (minimum 4 links) ---")
                    print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                    print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                    no_undel_min_links_optimized_cost = 0
                    active_links_no_undel = 0
                    for route in no_undel_min_links_routing_plan['routes']:
                        if route['percentage'] > 0:  # Only show routes with traffic
                            active_links_no_undel += 1
                            link_cost = (route['percentage'] / 100.0) * route['price']
                            no_undel_min_links_optimized_cost += link_cost
                            print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
                    
                    """# Display traffic differences
                    print(f"\n--- Profile: {profile.name} - Traffic Differences (No-Undel vs. No-Undel+Min Links) ---")
                    print("| Link ID       | Provider                      | No-Undel | No-Undel+4| Change   |")
                    print("|---------------|-------------------------------|----------|-----------|----------|")
                    
                    # Collect all links used in either optimization
                    all_links = set()
                    for route in no_undel_routing_plan['routes']:
                        if route['percentage'] > 0:
                            all_links.add(route['link'])
                    for route in no_undel_min_links_routing_plan['routes']:
                        if route['percentage'] > 0:
                            all_links.add(route['link'])
                    
                    # Display traffic differences
                    for link_id in all_links:
                        no_undel_traffic = next((route['percentage'] for route in no_undel_routing_plan['routes'] if route['link'] == link_id), 0)
                        no_undel_min_links_traffic = next((route['percentage'] for route in no_undel_min_links_routing_plan['routes'] if route['link'] == link_id), 0)
                        traffic_change = no_undel_min_links_traffic - no_undel_traffic
                        
                        if no_undel_traffic > 0 or no_undel_min_links_traffic > 0:
                            provider = next((route['provider'] for route in no_undel_routing_plan['routes'] if route['link'] == link_id), 
                                          next((route['provider'] for route in no_undel_min_links_routing_plan['routes'] if route['link'] == link_id), "Unknown"))
                            
                            print(f"| {link_id:<13} | {provider:<29} | {no_undel_traffic:7.1f}% | {no_undel_min_links_traffic:8.1f}% | {traffic_change:+7.1f}% |")"""
                
                # Reset optimizer for next profile
                optimizer.reset()
        
        # Load price change data
        mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
        price_changes_path = os.path.join(mock_data_dir, 'price_changes.json')
        
        try:
            with open(price_changes_path, 'r') as f:
                price_changes = json.load(f)
                
            if price_changes:
                # Use the first price change for testing
                price_change = price_changes[0]
                link_name = price_change['link']
                old_rate = price_change['Payload']['old_rate']
                new_rate = price_change['Payload']['new_rate']
                
                # Find profiles affected by this price change
                affected_profiles = data_service.get_profiles_affected_by_price_change(all_profiles, link_name)
                
                if affected_profiles:
                    # Test with the first affected profile
                    test_profile = affected_profiles[0]
                    
                    # Get links data before price change
                    links_data_before = await data_service.prepare_links_data_for_optimizer(test_profile)
                    
                    # Run optimization with original price
                    optimizer_before = RoutingOptimizer()
                    if optimizer_before.solve(links_data_before, test_profile.expected_sla):
                        profile_info = {
                            'profile_id': test_profile.profile_id,
                            'name': test_profile.name,
                            'expected_sla': test_profile.expected_sla
                        }
                        plan_before = optimizer_before.get_routing_plan(links_data_before, profile_info)
                        stats_before = optimizer_before.get_optimization_stats(links_data_before, test_profile.expected_sla)
                        
                        # Apply price change
                        data_service.update_link_price([test_profile], link_name, new_rate, old_rate)
                        
                        # Get links data after price change
                        links_data_after = await data_service.prepare_links_data_for_optimizer(test_profile)
                        
                        # Run optimization with new price
                        optimizer_after = RoutingOptimizer()
                        if optimizer_after.solve(links_data_after, test_profile.expected_sla):
                            plan_after = optimizer_after.get_routing_plan(links_data_after, profile_info)
                            stats_after = optimizer_after.get_optimization_stats(links_data_after, test_profile.expected_sla)
        except Exception as e:
            pass
    except Exception as e:
        print(f"Error running optimizer test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Redirect stdout to a file
    import sys
    import os
    original_stdout = sys.stdout
    
    # Use an absolute path to ensure the file is created in the correct location
    output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'optimizer_test_results.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        sys.stdout = f
        asyncio.run(test_optimizer())
        sys.stdout = original_stdout
    
    print(f"Test completed. Results written to {output_file}")
