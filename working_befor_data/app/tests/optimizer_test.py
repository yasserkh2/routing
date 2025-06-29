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
            
            # First, optimize using only the in-use links
            print("\n" + "-"*50)
            print("OPTIMIZATION STEP 1: USING ONLY IN-USE LINKS")
            print("-"*50)
            
            # Create a filtered version of links_data with only in-use links
            in_use_links_data = {}
            for link_id in original_links_data.keys():
                # Get the link data from the full dataset
                for link_id_full, link_data in (await data_service.prepare_links_data_for_optimizer(profile)).items():
                    if link_id_full == link_id:
                        in_use_links_data[link_id] = link_data
                        break
            
            print(f"\nOptimizing with {len(in_use_links_data)} in-use links")
            
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
                
                print("\nPROFILE AFTER IN-USE LINKS OPTIMIZATION:")
                print("-" * 50)
                print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                in_use_optimized_cost = 0
                for route in in_use_routing_plan['routes']:
                    if route['percentage'] > 0:  # Only show routes with traffic
                        link_cost = (route['percentage'] / 100.0) * route['price']
                        in_use_optimized_cost += link_cost
                        print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
                
                print("-" * 90)
                print(f"Total In-Use Optimized Cost: ${in_use_optimized_cost:.4f}")
                print(f"Cost Difference from Original: ${in_use_optimized_cost - original_cost:+.4f} ({((in_use_optimized_cost - original_cost)/original_cost)*100:+.2f}%)")
                
                print("\nIN-USE OPTIMIZATION STATS:")
                print("-" * 30)
                print(f"ACHIEVED SLA:    {in_use_stats['achieved_sla']:.2f}%")
                print(f"EXPECTED SLA:    {in_use_stats['expected_sla']:.2f}%")
                print(f"SLA Difference:  {in_use_stats['sla_difference']:+.2f}%")
                print(f"Total Cost:      ${in_use_stats['total_cost']:.4f}")
                print(f"Links Used:      {in_use_stats['links_used']}")
                print(f"Status:          {in_use_stats['optimization_status']}")
                
                # Display warning if target SLA cannot be achieved with in-use links
                if not in_use_stats['sla_achievable']:
                    print(f"\nWARNING: Target SLA of {in_use_stats['expected_sla']:.1f}% cannot be achieved with in-use links only.")
                    print(f"Maximum achievable SLA with in-use links: {in_use_stats['max_achievable_sla']:.2f}%")
            else:
                print("\nFailed to find optimal solution with in-use links only")
            
            # Reset optimizer for the full optimization
            in_use_optimizer.reset()
            
            # Now proceed with full optimization including alternative links
            print("\n" + "-"*50)
            print("OPTIMIZATION STEP 2: USING ALL AVAILABLE LINKS")
            print("-"*50)
            
            # Clear any previous ignored links
            data_service.clear_ignored_links()
            
            # Get all alternative links with their details before price cleaning
            print("\nALTERNATIVE LINKS BEFORE PRICE CLEANING:")
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
            
            # Print alternative links table
            print(f"\nALTERNATIVE LINKS ({len(profile.alternative_links)} total):")
            print(f"{'-'*100}")
            print(f"{'LINK ID':<30} {'TIER':<10} {'COST':<15} {'PROVIDER':<30}")
            print(f"{'-'*100}")
            
            for link in alt_links_details:
                link_id = link['link_id']
                tier = link['tier']
                cost = link['cost']
                provider = link['provider']
                cost_str = f"${cost:.4f}" if cost is not None else "$0.0000"
                print(f"{link_id:<30} {str(tier):<10} {cost_str:<15} {provider:<30}")
            
            # Show price thresholds
            print(f"\nPRICE CLEANING THRESHOLDS:")
            print(f"Tier 1 threshold: ${profile.profile_avg_cost * 0.6:.4f} (60% of profile avg cost)")
            print(f"Tier 2 threshold: ${profile.profile_avg_cost * 0.4:.4f} (40% of profile avg cost)")
            
            # Get link data for this profile using data preparation service (this will apply price cleaning)
            links_data = await data_service.prepare_links_data_for_optimizer(profile)
            
            # Get ignored links for this profile
            profile_ignored_links = data_service.get_ignored_links(profile.profile_id)
            ignored_link_ids = [link['link_id'] for link in profile_ignored_links]
            
            # Print results of price cleaning
            print(f"\nRESULTS AFTER PRICE CLEANING:")
            print(f"Links prepared for optimizer: {len(links_data)}")
            print(f"Links ignored due to price cleaning: {len(profile_ignored_links)}")
            
            if profile_ignored_links:
                print(f"\nIGNORED LINKS DUE TO PRICE CLEANING:")
                print(f"{'-'*100}")
                print(f"{'LINK ID':<30} {'TIER':<10} {'COST':<15} {'REASON'}")
                print(f"{'-'*100}")
                
                for link_data in profile_ignored_links:
                    link_id = link_data['link_id']
                    tier = link_data['link_tier']
                    cost = link_data['link_cost']
                    reason = link_data['reason']
                    cost_str = f"${cost:.4f}" if cost is not None else "$0.0000"
                    print(f"{link_id:<30} {str(tier):<10} {cost_str:<15} {reason}")
            
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
                
                # Run optimization with minimum links constraint - 4 links
                min_links_count = 4  # Set minimum number of links to 4
                min_traffic = 0.05  # Set minimum traffic per link to 5%
                print("\n" + "-"*50)
                print(f"OPTIMIZATION WITH MINIMUM LINKS CONSTRAINT: {min_links_count} links, min {min_traffic*100}% traffic per link")
                print("-"*50)
                
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
                    
                    print("\nPROFILE WITH 4 LINKS CONSTRAINT AFTER OPTIMIZATION:")
                    print("-" * 50)
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
                    
                    print("-" * 90)
                    print(f"Total Optimized Cost: ${min_links_optimized_cost:.4f}")
                    print(f"Number of Links Used: {active_links} (Minimum required: {min_links_count})")
                    print(f"Cost Difference from Standard Optimization: ${min_links_optimized_cost - optimized_cost:+.4f} ({((min_links_optimized_cost - optimized_cost)/optimized_cost)*100:+.2f}%)")
                    
                    print("\nOPTIMIZATION STATS (MINIMUM LINKS):")
                    print("-" * 30)
                    print(f"ACHIEVED SLA:    {min_links_stats['achieved_sla']:.2f}%")
                    print(f"EXPECTED SLA:    {min_links_stats['expected_sla']:.2f}%")
                    print(f"SLA Difference:  {min_links_stats['sla_difference']:+.2f}%")
                    print(f"Total Cost:      ${min_links_stats['total_cost']:.4f}")
                    print(f"Links Used:      {min_links_stats['links_used']}")
                    print(f"Status:          {min_links_stats['optimization_status']}")
                    
                    # Compare with standard optimization
                    print("\nCOMPARISON BETWEEN STANDARD AND MINIMUM LINKS OPTIMIZATION:")
                    print("-" * 50)
                    print(f"Standard Links Used: {stats['links_used']} | Minimum Links Required: {min_links_count}")
                    print(f"Standard Cost:       ${optimized_cost:.4f} | Minimum Links Cost:     ${min_links_optimized_cost:.4f}")
                    print(f"Cost Impact of Minimum Links Constraint: ${min_links_optimized_cost - optimized_cost:+.4f} ({((min_links_optimized_cost - optimized_cost)/optimized_cost)*100:+.2f}%)")
                    
                    # Display traffic differences between standard and minimum links optimization
                    print("\nTRAFFIC DIFFERENCES (STANDARD -> MINIMUM LINKS):")
                    print("-" * 50)
                    print("| Link ID       | Provider                      | Standard | Min Links| Change   |")
                    print("|---------------|-------------------------------|----------|----------|----------|")
                    
                    # Collect all links used in either optimization
                    all_links = set()
                    for route in routing_plan['routes']:
                        if route['percentage'] > 0:
                            all_links.add(route['link'])
                    for route in min_links_routing_plan['routes']:
                        if route['percentage'] > 0:
                            all_links.add(route['link'])
                    
                    # Display traffic differences
                    for link_id in all_links:
                        standard_traffic = next((route['percentage'] for route in routing_plan['routes'] if route['link'] == link_id), 0)
                        min_links_traffic = next((route['percentage'] for route in min_links_routing_plan['routes'] if route['link'] == link_id), 0)
                        traffic_change = min_links_traffic - standard_traffic
                        
                        if standard_traffic > 0 or min_links_traffic > 0:
                            provider = next((route['provider'] for route in routing_plan['routes'] if route['link'] == link_id), 
                                          next((route['provider'] for route in min_links_routing_plan['routes'] if route['link'] == link_id), "Unknown"))
                            
                            print(f"| {link_id:<13} | {provider:<29} | {standard_traffic:7.1f}% | {min_links_traffic:7.1f}% | {traffic_change:+7.1f}% |")
                else:
                    print("\nFailed to find optimal solution with minimum links constraint")
                
                # Run optimization with minimum links constraint - 5 links
                min_links_count_5 = 5  # Set minimum number of links to 5
                print("\n" + "-"*50)
                print(f"OPTIMIZATION WITH MINIMUM LINKS CONSTRAINT: {min_links_count_5} links, min {min_traffic*100}% traffic per link")
                print("-"*50)
                
                # Reset optimizer for the 5 links test
                optimizer.reset()
                
                # Run optimization with 5 links constraint
                min_links_success_5 = optimizer.solve(links_data, profile.expected_sla, min_links=min_links_count_5, min_traffic_per_link=min_traffic)
                
                if min_links_success_5:
                    # Get optimization results for 5 links
                    min_links_profile_info_5 = {
                        'profile_id': profile.profile_id,
                        'name': profile.name,
                        'expected_sla': profile.expected_sla
                    }
                    min_links_routing_plan_5 = optimizer.get_routing_plan(links_data, min_links_profile_info_5)
                    min_links_stats_5 = optimizer.get_optimization_stats(links_data, profile.expected_sla)
                    
                    print("\nPROFILE WITH 5 LINKS CONSTRAINT AFTER OPTIMIZATION:")
                    print("-" * 50)
                    print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                    print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                    min_links_optimized_cost_5 = 0
                    active_links_5 = 0
                    for route in min_links_routing_plan_5['routes']:
                        if route['percentage'] > 0:  # Only show routes with traffic
                            active_links_5 += 1
                            link_cost = (route['percentage'] / 100.0) * route['price']
                            min_links_optimized_cost_5 += link_cost
                            print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
                    
                    print("-" * 90)
                    print(f"Total Optimized Cost: ${min_links_optimized_cost_5:.4f}")
                    print(f"Number of Links Used: {active_links_5} (Minimum required: {min_links_count_5})")
                    print(f"Cost Difference from Standard Optimization: ${min_links_optimized_cost_5 - optimized_cost:+.4f} ({((min_links_optimized_cost_5 - optimized_cost)/optimized_cost)*100:+.2f}%)")
                    
                    print("\nOPTIMIZATION STATS (5 LINKS):")
                    print("-" * 30)
                    print(f"ACHIEVED SLA:    {min_links_stats_5['achieved_sla']:.2f}%")
                    print(f"EXPECTED SLA:    {min_links_stats_5['expected_sla']:.2f}%")
                    print(f"SLA Difference:  {min_links_stats_5['sla_difference']:+.2f}%")
                    print(f"Total Cost:      ${min_links_stats_5['total_cost']:.4f}")
                    print(f"Links Used:      {min_links_stats_5['links_used']}")
                    print(f"Status:          {min_links_stats_5['optimization_status']}")
                else:
                    print("\nFailed to find optimal solution with 5 links constraint")
                
                # Run optimization with minimum links constraint - 6 links
                min_links_count_6 = 6  # Set minimum number of links to 6
                print("\n" + "-"*50)
                print(f"OPTIMIZATION WITH MINIMUM LINKS CONSTRAINT: {min_links_count_6} links, min {min_traffic*100}% traffic per link")
                print("-"*50)
                
                # Reset optimizer for the 6 links test
                optimizer.reset()
                
                # Run optimization with 6 links constraint
                min_links_success_6 = optimizer.solve(links_data, profile.expected_sla, min_links=min_links_count_6, min_traffic_per_link=min_traffic)
                
                if min_links_success_6:
                    # Get optimization results for 6 links
                    min_links_profile_info_6 = {
                        'profile_id': profile.profile_id,
                        'name': profile.name,
                        'expected_sla': profile.expected_sla
                    }
                    min_links_routing_plan_6 = optimizer.get_routing_plan(links_data, min_links_profile_info_6)
                    min_links_stats_6 = optimizer.get_optimization_stats(links_data, profile.expected_sla)
                    
                    print("\nPROFILE WITH 6 LINKS CONSTRAINT AFTER OPTIMIZATION:")
                    print("-" * 50)
                    print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                    print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                    min_links_optimized_cost_6 = 0
                    active_links_6 = 0
                    for route in min_links_routing_plan_6['routes']:
                        if route['percentage'] > 0:  # Only show routes with traffic
                            active_links_6 += 1
                            link_cost = (route['percentage'] / 100.0) * route['price']
                            min_links_optimized_cost_6 += link_cost
                            print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
                    
                    print("-" * 90)
                    print(f"Total Optimized Cost: ${min_links_optimized_cost_6:.4f}")
                    print(f"Number of Links Used: {active_links_6} (Minimum required: {min_links_count_6})")
                    print(f"Cost Difference from Standard Optimization: ${min_links_optimized_cost_6 - optimized_cost:+.4f} ({((min_links_optimized_cost_6 - optimized_cost)/optimized_cost)*100:+.2f}%)")
                    
                    print("\nOPTIMIZATION STATS (6 LINKS):")
                    print("-" * 30)
                    print(f"ACHIEVED SLA:    {min_links_stats_6['achieved_sla']:.2f}%")
                    print(f"EXPECTED SLA:    {min_links_stats_6['expected_sla']:.2f}%")
                    print(f"SLA Difference:  {min_links_stats_6['sla_difference']:+.2f}%")
                    print(f"Total Cost:      ${min_links_stats_6['total_cost']:.4f}")
                    print(f"Links Used:      {min_links_stats_6['links_used']}")
                    print(f"Status:          {min_links_stats_6['optimization_status']}")
                    
                    # Compare all minimum links optimizations
                    print("\nCOMPARISON BETWEEN DIFFERENT LINK COUNT OPTIMIZATIONS:")
                    print("-" * 50)
                    print(f"Standard Links Used: {stats['links_used']} | Cost: ${optimized_cost:.4f}")
                    print(f"4 Links Required:    {min_links_stats['links_used']} | Cost: ${min_links_optimized_cost:.4f} | Diff: ${min_links_optimized_cost - optimized_cost:+.4f} ({((min_links_optimized_cost - optimized_cost)/optimized_cost)*100:+.2f}%)")
                    print(f"5 Links Required:    {min_links_stats_5['links_used']} | Cost: ${min_links_optimized_cost_5:.4f} | Diff: ${min_links_optimized_cost_5 - optimized_cost:+.4f} ({((min_links_optimized_cost_5 - optimized_cost)/optimized_cost)*100:+.2f}%)")
                    print(f"6 Links Required:    {min_links_stats_6['links_used']} | Cost: ${min_links_optimized_cost_6:.4f} | Diff: ${min_links_optimized_cost_6 - optimized_cost:+.4f} ({((min_links_optimized_cost_6 - optimized_cost)/optimized_cost)*100:+.2f}%)")
                else:
                    print("\nFailed to find optimal solution with 6 links constraint")
                
                # Run optimization with all links except Undel
                print("\n" + "-"*50)
                print("OPTIMIZATION STEP 3: USING ALL LINKS EXCEPT UNDEL")
                print("-"*50)
                
                # Reset optimizer for the new test
                optimizer.reset()
                
                # Create a filtered version of links_data without Undel
                no_undel_links_data = {}
                for link_id, link_data in links_data.items():
                    if link_id != "Undel":
                        no_undel_links_data[link_id] = link_data
                
                print(f"\nOptimizing with {len(no_undel_links_data)} links (excluding Undel)")
                
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
                    
                    print("\nPROFILE AFTER OPTIMIZATION (WITHOUT UNDEL):")
                    print("-" * 50)
                    print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                    print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                    no_undel_optimized_cost = 0
                    for route in no_undel_routing_plan['routes']:
                        if route['percentage'] > 0:  # Only show routes with traffic
                            link_cost = (route['percentage'] / 100.0) * route['price']
                            no_undel_optimized_cost += link_cost
                            print(f"| {route['link']:<13} | {route['provider']:<29} | {route['percentage']:9.1f}% | {route['sla']:7.1f}% | ${route['price']:8.3f} | ${link_cost:8.4f} |")
                    
                    print("-" * 90)
                    print(f"Total Optimized Cost: ${no_undel_optimized_cost:.4f}")
                    print(f"Cost Difference from Original: ${no_undel_optimized_cost - original_cost:+.4f} ({((no_undel_optimized_cost - original_cost)/original_cost)*100:+.2f}%)")
                    print(f"Cost Difference from Standard Optimization: ${no_undel_optimized_cost - optimized_cost:+.4f} ({((no_undel_optimized_cost - optimized_cost)/optimized_cost)*100:+.2f}%)")
                    
                    print("\nOPTIMIZATION STATS (WITHOUT UNDEL):")
                    print("-" * 30)
                    print(f"ACHIEVED SLA:    {no_undel_stats['achieved_sla']:.2f}%")
                    print(f"EXPECTED SLA:    {no_undel_stats['expected_sla']:.2f}%")
                    print(f"SLA Difference:  {no_undel_stats['sla_difference']:+.2f}%")
                    print(f"Total Cost:      ${no_undel_stats['total_cost']:.4f}")
                    print(f"Links Used:      {no_undel_stats['links_used']}")
                    print(f"Status:          {no_undel_stats['optimization_status']}")
                    
                    # Compare with standard optimization
                    print("\nCOMPARISON BETWEEN STANDARD AND NO-UNDEL OPTIMIZATION:")
                    print("-" * 50)
                    print(f"Standard Links Used: {stats['links_used']} | No-Undel Links Used: {no_undel_stats['links_used']}")
                    print(f"Standard Cost:       ${optimized_cost:.4f} | No-Undel Cost:       ${no_undel_optimized_cost:.4f}")
                    print(f"Cost Impact of Removing Undel: ${no_undel_optimized_cost - optimized_cost:+.4f} ({((no_undel_optimized_cost - optimized_cost)/optimized_cost)*100:+.2f}%)")
                    
                    # Display traffic differences between standard and no-undel optimization
                    print("\nTRAFFIC DIFFERENCES (STANDARD -> NO-UNDEL):")
                    print("-" * 50)
                    print("| Link ID       | Provider                      | Standard | No-Undel | Change   |")
                    print("|---------------|-------------------------------|----------|----------|----------|")
                    
                    # Collect all links used in either optimization
                    all_links = set()
                    for route in routing_plan['routes']:
                        if route['percentage'] > 0:
                            all_links.add(route['link'])
                    for route in no_undel_routing_plan['routes']:
                        if route['percentage'] > 0:
                            all_links.add(route['link'])
                    
                    # Display traffic differences
                    for link_id in all_links:
                        standard_traffic = next((route['percentage'] for route in routing_plan['routes'] if route['link'] == link_id), 0)
                        no_undel_traffic = next((route['percentage'] for route in no_undel_routing_plan['routes'] if route['link'] == link_id), 0)
                        traffic_change = no_undel_traffic - standard_traffic
                        
                        if standard_traffic > 0 or no_undel_traffic > 0:
                            provider = next((route['provider'] for route in routing_plan['routes'] if route['link'] == link_id), 
                                          next((route['provider'] for route in no_undel_routing_plan['routes'] if route['link'] == link_id), "Unknown"))
                            
                            print(f"| {link_id:<13} | {provider:<29} | {standard_traffic:7.1f}% | {no_undel_traffic:7.1f}% | {traffic_change:+7.1f}% |")
                else:
                    print("\nFailed to find optimal solution without Undel")
                    
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