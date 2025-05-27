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
                            'sla': link_data.get('sla_dd', 90)
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
            
            # Get link data for this profile
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
            
            # Run optimization
            optimizer = RoutingOptimizer(profile)
            success = await optimizer.solve()
            
            if success:
                # Get optimization results
                routing_plan = await optimizer.get_routing_plan()
                stats = await optimizer.get_optimization_stats()
                
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
                        provider = original_links_data.get(link_id, {}).get('provider') or next((route['provider'] for route in routing_plan['routes'] if route['link'] == link_id), "Unknown")
                        
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
                print(f"SLA Difference:  {stats['achieved_sla'] - stats['expected_sla']:+.2f}%")
                print(f"Total Cost:      ${stats['total_cost']:.4f}")
                print(f"Links Used:      {stats['links_used']}")
                
                # Display tier statistics
                print("\nTIER STATISTICS:")
                print("-" * 30)
                for tier, tier_data in sorted(stats['tier_stats'].items()):
                    print(f"Tier {tier}:")
                    print(f"  Traffic:       {tier_data['traffic']:.1f}%")
                    print(f"  Required SLA:  {tier_data['required_sla']:.1f}%")
                
                # Display detailed link information if available
                if 'link_details' in stats:
                    print("\nDETAILED LINK INFORMATION:")
                    print("-" * 50)
                    for link_detail in stats['link_details']:
                        print(f"Link: {link_detail['link']} ({link_detail['provider']})")
                        print(f"  Price:         ${link_detail['old_price']:.4f} -> ${link_detail['new_price']:.4f} ({link_detail['price_change_pct']:+.2f}%)")
                        print(f"  Traffic:       {link_detail['old_traffic']:.1f}% -> {link_detail['new_traffic']:.1f}% ({link_detail['traffic_change']:+.1f}%)")
                        print(f"  SLA:           {link_detail['old_sla']:.2f}% -> {link_detail['new_sla']:.2f}% ({link_detail['sla_change']:+.2f}%)")
                        print()
                
                # Display warning if target SLA cannot be achieved
                if not stats['sla_achievable']:
                    print(f"\nWARNING: {stats['warning']}")
                    print(f"Max Achievable SLA: {stats['max_achievable_sla']:.2f}%")
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
                    
                    # Run optimization with original price
                    optimizer_before = RoutingOptimizer(test_profile)
                    if await optimizer_before.solve():
                        stats_before = await optimizer_before.get_optimization_stats()
                        plan_before = await optimizer_before.get_routing_plan()
                        
                        # Get original traffic allocation from mock data
                        original_links_data = {}
                        combined_data = await data_service.mock_api.get_combined_data()
                        for profile_data in combined_data:
                            if profile_data['profile_id'] == test_profile.profile_id:
                                for link_data in profile_data['in_use_links']:
                                    original_links_data[link_data['link']] = {
                                        'provider': link_data['provider'],
                                        'traffic': link_data.get('traffic', 0),
                                        'price': link_data['buy_price'],
                                        'sla': link_data.get('sla_dd', 90)
                                    }
                                break
                        
                        print("\nBEFORE OPTIMIZATION (ORIGINAL ALLOCATION FROM DATABASE):")
                        print("-" * 90)
                        print("| Link ID       | Provider                      | Traffic % | SLA      | Price ($) | Cost ($)  |")
                        print("|---------------|-------------------------------|-----------|----------|-----------|-----------|")
                        original_cost = 0
                        original_sla = 0
                        for link_id, link_data in original_links_data.items():
                            traffic_pct = link_data['traffic']
                            sla_value = link_data['sla']
                            sla_display = f"{sla_value:.1f}%" if sla_value is not None else "N/A"
                            link_cost = (traffic_pct / 100.0) * link_data['price']
                            original_cost += link_cost
                            if sla_value is not None:
                                original_sla += (traffic_pct / 100.0) * (sla_value / 100.0)
                            
                            provider = link_data.get('provider', "Unknown")
                            print(f"| {link_id:<13} | {provider:<29} | {traffic_pct:9.1f}% | {sla_display:8} | ${link_data['price']:8.3f} | ${link_cost:8.4f} |")
                        
                        print("-" * 90)
                        print(f"Total Original Cost: ${original_cost:.4f}")
                        print(f"Original SLA:        {original_sla*100:.2f}%")
                        
                        print("\nAFTER OPTIMIZATION (BEFORE PRICE CHANGE):")
                        print("-" * 30)
                        print(f"ACHIEVED SLA:    {stats_before['achieved_sla']:.2f}%")
                        print(f"EXPECTED SLA:    {stats_before['expected_sla']:.2f}%")
                        print(f"SLA Difference:  {stats_before['achieved_sla'] - stats_before['expected_sla']:+.2f}%")
                        print(f"Total Cost:      ${stats_before['total_cost']:.4f}")
                        print(f"Cost Savings:    ${original_cost - stats_before['total_cost']:+.4f} ({((original_cost - stats_before['total_cost'])/original_cost)*100:+.2f}%)")
                        print(f"Links Used:      {stats_before['links_used']}")
                        
                        # Apply price change
                        print("\nApplying price change...")
                        data_service.update_link_price([test_profile], link_name, new_rate, old_rate)
                        
                        # Run optimization with new price
                        optimizer_after = RoutingOptimizer(test_profile)
                        if await optimizer_after.solve():
                            stats_after = await optimizer_after.get_optimization_stats()
                            plan_after = await optimizer_after.get_routing_plan()
                            
                            print("\nAFTER OPTIMIZATION WITH PRICE CHANGE:")
                            print("-" * 30)
                            print(f"ACHIEVED SLA:    {stats_after['achieved_sla']:.2f}%")
                            print(f"EXPECTED SLA:    {stats_after['expected_sla']:.2f}%")
                            print(f"SLA Difference:  {stats_after['achieved_sla'] - stats_after['expected_sla']:+.2f}%")
                            print(f"Total Cost:      ${stats_after['total_cost']:.4f}")
                            print(f"Links Used:      {stats_after['links_used']}")
                            
                            # Calculate impact
                            cost_change = stats_after['total_cost'] - stats_before['total_cost']
                            cost_change_pct = (cost_change / stats_before['total_cost']) * 100 if stats_before['total_cost'] > 0 else 0
                            sla_change = stats_after['achieved_sla'] - stats_before['achieved_sla']
                            
                            print("\nIMPACT ANALYSIS:")
                            print("-" * 50)
                            print(f"Cost Change:     ${cost_change:+.4f} ({cost_change_pct:+.2f}%)")
                            print(f"SLA Change:      {sla_change:+.2f}%")
                            print(f"Before SLA:      {stats_before['achieved_sla']:.2f}% (Expected: {stats_before['expected_sla']:.2f}%)")
                            print(f"After SLA:       {stats_after['achieved_sla']:.2f}% (Expected: {stats_after['expected_sla']:.2f}%)")
                            print(f"Before Cost:     ${stats_before['total_cost']:.4f}")
                            print(f"After Cost:      ${stats_after['total_cost']:.4f}")
                            
                            # Compare routing plans
                            # Create a comprehensive comparison table of all three allocations
                            print("\nCOMPREHENSIVE COMPARISON OF ALL ALLOCATIONS:")
                            print("-" * 120)
                            print("| Link ID       | Provider                      | Original % | Original $ | Optimized % | Optimized $ | After Price % | After Price $ |")
                            print("|---------------|-------------------------------|------------|------------|-------------|-------------|---------------|---------------|")
                            
                            # Collect all links from all three allocations
                            all_links = set()
                            for link_id in original_links_data:
                                all_links.add(link_id)
                            for route in plan_before['routes']:
                                if route['percentage'] > 0:
                                    all_links.add(route['link'])
                            for route in plan_after['routes']:
                                if route['percentage'] > 0:
                                    all_links.add(route['link'])
                            
                            # Create lookup dictionaries for each allocation
                            before_routes = {route['link']: route for route in plan_before['routes'] if route['percentage'] > 0}
                            after_routes = {route['link']: route for route in plan_after['routes'] if route['percentage'] > 0}
                            
                            # Sort links by their presence in the allocations (original first, then optimized, then after price change)
                            sorted_links = sorted(all_links, key=lambda link: (
                                link not in original_links_data,
                                link not in before_routes,
                                link not in after_routes
                            ))
                            
                            # Display each link's data across all three allocations
                            for link_id in sorted_links:
                                # Original allocation data
                                orig_traffic = original_links_data.get(link_id, {}).get('traffic', 0)
                                orig_price = original_links_data.get(link_id, {}).get('price', 0)
                                orig_cost = (orig_traffic / 100.0) * orig_price if orig_traffic > 0 else 0
                                
                                # Optimized allocation data (before price change)
                                opt_route = before_routes.get(link_id, {})
                                opt_traffic = opt_route.get('percentage', 0)
                                opt_price = opt_route.get('price', 0)
                                opt_cost = (opt_traffic / 100.0) * opt_price if opt_traffic > 0 else 0
                                
                                # After price change allocation data
                                after_route = after_routes.get(link_id, {})
                                after_traffic = after_route.get('percentage', 0)
                                after_price = after_route.get('price', 0)
                                after_cost = (after_traffic / 100.0) * after_price if after_traffic > 0 else 0
                                
                                # Get provider name (use the first available)
                                provider = (
                                    original_links_data.get(link_id, {}).get('provider') or
                                    opt_route.get('provider') or
                                    after_route.get('provider') or
                                    "Unknown"
                                )
                                
                                # Format the row with all data
                                print(
                                    f"| {link_id:<13} | {provider:<29} | "
                                    f"{orig_traffic:10.1f}% | ${orig_cost:10.4f} | "
                                    f"{opt_traffic:11.1f}% | ${opt_cost:11.4f} | "
                                    f"{after_traffic:13.1f}% | ${after_cost:13.4f} |"
                                )
                            
                            print("-" * 120)
                            
                            # Calculate totals
                            original_total = sum((original_links_data.get(link_id, {}).get('traffic', 0) / 100.0) * 
                                               original_links_data.get(link_id, {}).get('price', 0) 
                                               for link_id in original_links_data)
                            
                            before_total = sum((before_routes.get(link_id, {}).get('percentage', 0) / 100.0) * 
                                             before_routes.get(link_id, {}).get('price', 0) 
                                             for link_id in before_routes)
                            
                            after_total = sum((after_routes.get(link_id, {}).get('percentage', 0) / 100.0) * 
                                            after_routes.get(link_id, {}).get('price', 0) 
                                            for link_id in after_routes)
                            
                            # Display totals and differences
                            print(f"| {'TOTALS':<13} | {'':<29} | "
                                  f"{100.0:10.1f}% | ${original_total:10.4f} | "
                                  f"{100.0:11.1f}% | ${before_total:11.4f} | "
                                  f"{100.0:13.1f}% | ${after_total:13.4f} |")
                            
                            print("\nCOST IMPACT SUMMARY:")
                            print("-" * 60)
                            opt_savings = original_total - before_total
                            opt_savings_pct = (opt_savings / original_total) * 100 if original_total > 0 else 0
                            print(f"Original to Optimized:       ${opt_savings:+.4f} ({opt_savings_pct:+.2f}%)")
                            
                            price_impact = after_total - before_total
                            price_impact_pct = (price_impact / before_total) * 100 if before_total > 0 else 0
                            print(f"Impact of Price Change:      ${price_impact:+.4f} ({price_impact_pct:+.2f}%)")
                            
                            total_impact = after_total - original_total
                            total_impact_pct = (total_impact / original_total) * 100 if original_total > 0 else 0
                            print(f"Total Impact (Net Savings):  ${total_impact:+.4f} ({total_impact_pct:+.2f}%)")
                                    
                            # Add a more detailed summary of changes
                            print("\nDETAILED SUMMARY OF CHANGES:")
                            print("-" * 60)
                            
                            # Count links used in each allocation
                            orig_links_used = sum(1 for link_id in original_links_data if original_links_data[link_id].get('traffic', 0) > 0)
                            opt_links_used = len(before_routes)
                            after_links_used = len(after_routes)
                            
                            print(f"1. Original Database Allocation:")
                            print(f"   - {orig_links_used} links used")
                            print(f"   - Total cost: ${original_total:.4f}")
                            print(f"   - SLA: {original_sla*100:.2f}%")
                            
                            print(f"\n2. Optimized Allocation (Before Price Change):")
                            print(f"   - {opt_links_used} links used")
                            print(f"   - Total cost: ${before_total:.4f}")
                            print(f"   - Cost savings: ${opt_savings:+.4f} ({opt_savings_pct:+.2f}%)")
                            print(f"   - SLA: {stats_before['achieved_sla']:.2f}%")
                            
                            print(f"\n3. Optimized Allocation (After Price Change):")
                            print(f"   - {after_links_used} links used")
                            print(f"   - Total cost: ${after_total:.4f}")
                            print(f"   - Price change impact: ${price_impact:+.4f} ({price_impact_pct:+.2f}%)")
                            print(f"   - SLA: {stats_after['achieved_sla']:.2f}%")
                            
                            # Identify links with significant traffic changes
                            print("\nSIGNIFICANT TRAFFIC SHIFTS DUE TO PRICE CHANGE:")
                            print("-" * 60)
                            significant_shifts = []
                            
                            for link_id in all_links:
                                before_traffic = before_routes.get(link_id, {}).get('percentage', 0)
                                after_traffic = after_routes.get(link_id, {}).get('percentage', 0)
                                traffic_change = after_traffic - before_traffic
                                
                                # Consider shifts of more than 5% as significant
                                if abs(traffic_change) >= 5.0:
                                    provider = (
                                        original_links_data.get(link_id, {}).get('provider') or
                                        before_routes.get(link_id, {}).get('provider') or
                                        after_routes.get(link_id, {}).get('provider') or
                                        "Unknown"
                                    )
                                    
                                    before_price = before_routes.get(link_id, {}).get('price', 0)
                                    after_price = after_routes.get(link_id, {}).get('price', 0)
                                    price_change = after_price - before_price
                                    price_change_pct = (price_change / before_price) * 100 if before_price > 0 else 0
                                    
                                    significant_shifts.append({
                                        'link_id': link_id,
                                        'provider': provider,
                                        'before_traffic': before_traffic,
                                        'after_traffic': after_traffic,
                                        'traffic_change': traffic_change,
                                        'price_change': price_change,
                                        'price_change_pct': price_change_pct
                                    })
                            
                            if significant_shifts:
                                # Sort by absolute traffic change (largest first)
                                significant_shifts.sort(key=lambda x: abs(x['traffic_change']), reverse=True)
                                
                                for shift in significant_shifts:
                                    print(f"Link {shift['link_id']} ({shift['provider']}):")
                                    print(f"  - Traffic: {shift['before_traffic']:.1f}% -> {shift['after_traffic']:.1f}% ({shift['traffic_change']:+.1f}%)")
                                    if shift['price_change'] != 0:
                                        print(f"  - Price: ${shift['before_traffic']:.3f} -> ${shift['after_traffic']:.3f} ({shift['price_change_pct']:+.2f}%)")
                                    print()
                            else:
                                print("No significant traffic shifts detected (>= 5% change)")
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
    output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'optimizer_results.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        sys.stdout = f
        asyncio.run(test_optimizer())
        sys.stdout = original_stdout
    
    print(f"Test completed. Results written to {output_file}")