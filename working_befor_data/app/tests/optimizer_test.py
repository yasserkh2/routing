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
    print("\n" + "="*50)
    print("          OPTIMIZER TEST")
    print("="*50 + "\n")
    
    # Initialize services
    data_service = DataPreparationService()
    optimizer = RoutingOptimizer()
    
    try:
        # Get all profiles
        all_profiles = await data_service.get_all_profiles()
        
        if not all_profiles:
            print("No profiles found. Test cannot continue.")
            return
        
        print(f"Retrieved {len(all_profiles)} profiles")
        
        # Test each profile
        for profile in all_profiles:
            print("\n" + "-"*50)
            print(f"PROFILE: {profile.name} (ID: {profile.profile_id})")
            print("-"*50)
            print(f"EXPECTED SLA:    {profile.expected_sla}%")
            print(f"In-Use Links:    {len(profile.in_use_links)}")
            print(f"Alternative Links: {len(profile.alternative_links)}")
            
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
            
            # Display original profile information
            print("\nPROFILE BEFORE OPTIMIZATION (ORIGINAL ALLOCATION):")
            print("-" * 50)
            original_cost = 0
            original_sla = 0
            print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
            print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
            for link_id, link_data in original_links_data.items():
                traffic_pct = link_data['traffic']
                sla_value = link_data['sla']
                sla_display = f"{sla_value:.1f}%" if sla_value is not None else "N/A"
                link_cost = (traffic_pct / 100.0) * link_data['price']
                original_cost += link_cost
                if sla_value is not None:
                    original_sla += (traffic_pct / 100.0) * (sla_value / 100.0)
                
                print(f"| {link_id:<13} | {link_data['provider']:<29} | {traffic_pct:9.1f}% | {sla_display:8} | ${link_data['price']:8.3f} | ${link_cost:8.4f} |")
            
            print("-" * 90)
            print(f"Total Original Cost: ${original_cost:.4f}")
            print(f"Original SLA:        {original_sla*100:.2f}%")
            
            # Get link data for this profile using data preparation service
            links_data = await data_service.prepare_links_data_for_optimizer(profile)
            print(f"\nPrepared data for {len(links_data)} links")
            
            # Display sample of link data
            print("\nSAMPLE LINK DATA:")
            print("-" * 30)
            sample_count = min(3, len(links_data))
            for i, (link_id, link_data) in enumerate(list(links_data.items())[:sample_count]):
                print(f"Link {link_id} ({link_data['provider']}):")
                print(f"  SLA:           {link_data['sla']*100:.1f}%")
                print(f"  Tier:          {link_data['tier']}")
                print(f"  Price:         ${link_data['price']:.3f}")
                print()
            
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
                
                print("\nPROFILE AFTER OPTIMIZATION:")
                print("-" * 50)
                print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                optimized_cost = 0
                for route in routing_plan['routes']:
                    if route['percentage'] > 0:  # Only show routes with traffic
                        link_cost = (route['percentage'] / 100.0) * route['price']
                        optimized_cost += link_cost
                        print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
                
                print("-" * 90)
                print(f"Total Optimized Cost: ${optimized_cost:.4f}")
                print(f"Cost Difference:      ${optimized_cost - original_cost:+.4f} ({((optimized_cost - original_cost)/original_cost)*100:+.2f}%)")
                
                # Calculate traffic changes
                print("\nTRAFFIC CHANGES (BEFORE -> AFTER):")
                print("-" * 50)
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
                        
                        print(f"| {link_id:<13} | {provider:<29} | {original_traffic:7.1f}% | {new_traffic:7.1f}% | {traffic_change:+7.1f}% | ${cost_impact:+14.4f} |")
                
                print("\nOPTIMIZATION STATS:")
                print("-" * 30)
                print(f"ACHIEVED SLA:    {stats['achieved_sla']:.2f}%")
                print(f"EXPECTED SLA:    {stats['expected_sla']:.2f}%")
                print(f"SLA Difference:  {stats['sla_difference']:+.2f}%")
                print(f"Total Cost:      ${stats['total_cost']:.4f}")
                print(f"Links Used:      {stats['links_used']}")
                print(f"Status:          {stats['optimization_status']}")
                
                # Display tier statistics with proper sorting (if available from data service)
                try:
                    tier_stats = await data_service.calculate_tier_statistics_for_profile(profile, routing_plan)
                    if tier_stats:
                        print("\nTIER STATISTICS:")
                        print("-" * 30)
                        # Sort tiers, handling None values by putting them at the end
                        sorted_tiers = sorted(tier_stats.items(), key=lambda x: (x[0] is None, x[0]))
                        for tier, tier_data in sorted_tiers:
                            tier_display = tier if tier is not None else "None"
                            print(f"Tier {tier_display}:")
                            print(f"  Traffic:       {tier_data['traffic']:.1f}%")
                            print(f"  Required SLA:  {tier_data['required_sla']:.1f}%")
                except Exception as e:
                    logger.warning(f"Could not calculate tier statistics: {e}")
                
                # Display warning if target SLA cannot be achieved
                if not stats['sla_achievable']:
                    print(f"\nWARNING: Target SLA of {stats['expected_sla']:.1f}% cannot be achieved.")
                    print(f"Maximum achievable SLA: {stats['max_achievable_sla']:.2f}%")
                
                # Run optimization with reduced SLA (5% lower)
                reduced_sla = max(profile.expected_sla - 5, 0)  # Ensure SLA doesn't go below 0
                print("\n" + "-"*50)
                print(f"OPTIMIZATION WITH REDUCED SLA: {reduced_sla}%")
                print("-"*50)
                
                
                # Reset optimizer for the reduced SLA test
                optimizer.reset()
                
                # Run optimization with reduced SLA
                reduced_success = optimizer.solve(links_data, reduced_sla)
                
                if reduced_success:
                    # Get optimization results for reduced SLA
                    reduced_profile_info = {
                        'profile_id': profile.profile_id,
                        'name': profile.name,
                        'expected_sla': reduced_sla
                    }
                    reduced_routing_plan = optimizer.get_routing_plan(links_data, reduced_profile_info)
                    reduced_stats = optimizer.get_optimization_stats(links_data, reduced_sla)
                    
                    print("\nPROFILE WITH REDUCED SLA AFTER OPTIMIZATION:")
                    print("-" * 50)
                    print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                    print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                    reduced_optimized_cost = 0
                    for route in reduced_routing_plan['routes']:
                        if route['percentage'] > 0:  # Only show routes with traffic
                            link_cost = (route['percentage'] / 100.0) * route['price']
                            reduced_optimized_cost += link_cost
                            print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
                    
                    print("-" * 90)
                    print(f"Total Optimized Cost: ${reduced_optimized_cost:.4f}")
                    print(f"Cost Difference from Original: ${reduced_optimized_cost - original_cost:+.4f} ({((reduced_optimized_cost - original_cost)/original_cost)*100:+.2f}%)")
                    print(f"Cost Difference from Standard SLA: ${reduced_optimized_cost - optimized_cost:+.4f} ({((reduced_optimized_cost - optimized_cost)/optimized_cost)*100:+.2f}%)")
                    
                    print("\nOPTIMIZATION STATS (REDUCED SLA):")
                    print("-" * 30)
                    print(f"ACHIEVED SLA:    {reduced_stats['achieved_sla']:.2f}%")
                    print(f"EXPECTED SLA:    {reduced_stats['expected_sla']:.2f}%")
                    print(f"SLA Difference:  {reduced_stats['sla_difference']:+.2f}%")
                    print(f"Total Cost:      ${reduced_stats['total_cost']:.4f}")
                    print(f"Links Used:      {reduced_stats['links_used']}")
                    print(f"Status:          {reduced_stats['optimization_status']}")
                    
                    # Compare with original SLA optimization
                    print("\nCOMPARISON BETWEEN STANDARD AND REDUCED SLA:")
                    print("-" * 50)
                    print(f"Standard SLA Target: {profile.expected_sla:.2f}% | Reduced SLA Target: {reduced_sla:.2f}%")
                    print(f"Standard SLA Cost:   ${optimized_cost:.4f} | Reduced SLA Cost:   ${reduced_optimized_cost:.4f}")
                    print(f"Cost Savings with Reduced SLA: ${optimized_cost - reduced_optimized_cost:+.4f} ({((optimized_cost - reduced_optimized_cost)/optimized_cost)*100:+.2f}%)")
                    
                    # Display traffic differences between standard and reduced SLA
                    print("\nTRAFFIC DIFFERENCES (STANDARD SLA -> REDUCED SLA):")
                    print("-" * 50)
                    print("| Link ID       | Provider                      | Standard | Reduced  | Change   |")
                    print("|---------------|-------------------------------|----------|----------|----------|")
                    
                    # Collect all links used in either optimization
                    all_links = set()
                    for route in routing_plan['routes']:
                        if route['percentage'] > 0:
                            all_links.add(route['link'])
                    for route in reduced_routing_plan['routes']:
                        if route['percentage'] > 0:
                            all_links.add(route['link'])
                    
                    # Display traffic differences
                    for link_id in all_links:
                        standard_traffic = next((route['percentage'] for route in routing_plan['routes'] if route['link'] == link_id), 0)
                        reduced_traffic = next((route['percentage'] for route in reduced_routing_plan['routes'] if route['link'] == link_id), 0)
                        traffic_change = reduced_traffic - standard_traffic
                        
                        if standard_traffic > 0 or reduced_traffic > 0:
                            provider = next((route['provider'] for route in routing_plan['routes'] if route['link'] == link_id), 
                                          next((route['provider'] for route in reduced_routing_plan['routes'] if route['link'] == link_id), "Unknown"))
                            
                            print(f"| {link_id:<13} | {provider:<29} | {standard_traffic:7.1f}% | {reduced_traffic:7.1f}% | {traffic_change:+7.1f}% |")
                else:
                    print("\nFailed to find optimal solution with reduced SLA")
                
                # Reset optimizer for next profile
                optimizer.reset()
            else:
                print("\nFailed to find optimal solution")
        
        print("\n" + "="*50)
        print("          PRICE CHANGE IMPACT TEST")
        print("="*50 + "\n")
        
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
                
                print(f"Testing price change for link {link_name}")
                print(f"Old price: ${old_rate:.3f}")
                print(f"New price: ${new_rate:.3f}")
                
                # Find profiles affected by this price change
                affected_profiles = data_service.get_profiles_affected_by_price_change(all_profiles, link_name)
                print(f"Found {len(affected_profiles)} affected profiles")
                
                if affected_profiles:
                    # Test with the first affected profile
                    test_profile = affected_profiles[0]
                    print(f"\nTesting with profile: {test_profile.name}")
                    
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
                        
                        print("\nBEFORE PRICE CHANGE:")
                        print("-" * 30)
                        print(f"ACHIEVED SLA:    {stats_before['achieved_sla']:.2f}%")
                        print(f"EXPECTED SLA:    {stats_before['expected_sla']:.2f}%")
                        print(f"SLA Difference:  {stats_before['sla_difference']:+.2f}%")
                        print(f"Total Cost:      ${stats_before['total_cost']:.4f}")
                        print(f"Links Used:      {stats_before['links_used']}")
                        
                        # Apply price change
                        print("\nApplying price change...")
                        data_service.update_link_price([test_profile], link_name, new_rate, old_rate)
                        
                        # Get links data after price change
                        links_data_after = await data_service.prepare_links_data_for_optimizer(test_profile)
                        
                        # Run optimization with new price
                        optimizer_after = RoutingOptimizer()
                        if optimizer_after.solve(links_data_after, test_profile.expected_sla):
                            plan_after = optimizer_after.get_routing_plan(links_data_after, profile_info)
                            stats_after = optimizer_after.get_optimization_stats(links_data_after, test_profile.expected_sla)
                            
                            print("\nAFTER PRICE CHANGE:")
                            print("-" * 30)
                            print(f"ACHIEVED SLA:    {stats_after['achieved_sla']:.2f}%")
                            print(f"EXPECTED SLA:    {stats_after['expected_sla']:.2f}%")
                            print(f"SLA Difference:  {stats_after['sla_difference']:+.2f}%")
                            print(f"Total Cost:      ${stats_after['total_cost']:.4f}")
                            print(f"Links Used:      {stats_after['links_used']}")
                            
                            # Calculate impact using optimizer's built-in method
                            impact = optimizer_after.calculate_cost_impact(plan_before, plan_after)
                            sla_change = stats_after['achieved_sla'] - stats_before['achieved_sla']
                            
                            print("\nIMPACT ANALYSIS:")
                            print("-" * 50)
                            print(f"Cost Change:     ${impact['cost_change']:+.4f} ({impact['cost_change_percentage']:+.2f}%)")
                            print(f"SLA Change:      {sla_change:+.2f}%")
                            print(f"Before SLA:      {stats_before['achieved_sla']:.2f}% (Expected: {stats_before['expected_sla']:.2f}%)")
                            print(f"After SLA:       {stats_after['achieved_sla']:.2f}% (Expected: {stats_after['expected_sla']:.2f}%)")
                            print(f"Before Cost:     ${stats_before['total_cost']:.4f}")
                            print(f"After Cost:      ${stats_after['total_cost']:.4f}")
                            
                            if impact['savings'] > 0:
                                print(f"Savings:         ${impact['savings']:.4f} ({impact['savings_percentage']:.2f}%)")
                            
                            print("\nPrice change impact test completed successfully!")
                        else:
                            print("Failed to optimize after price change")
                    else:
                        print("Failed to optimize before price change")
                else:
                    print("No profiles affected by this price change")
            else:
                print("No price changes found in the data file")
                
        except Exception as e:
            print(f"Error in price change test: {str(e)}")
        
        print("\nAll tests completed!")
        
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