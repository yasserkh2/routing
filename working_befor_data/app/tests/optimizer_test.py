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
                        
                        # Calculate original cost and SLA
                        original_cost = 0
                        original_sla = 0
                        for link_id, link_data in original_links_data.items():
                            traffic_pct = link_data['traffic']
                            sla_value = link_data['sla']
                            link_cost = (traffic_pct / 100.0) * link_data['price']
                            original_cost += link_cost
                            if sla_value is not None:
                                original_sla += (traffic_pct / 100.0) * (sla_value / 100.0)
                        
                        # Apply price change
                        print("\nApplying price change...")
                        data_service.update_link_price([test_profile], link_name, new_rate, old_rate)
                        
                        # Run optimization with new price
                        optimizer_after = RoutingOptimizer(test_profile)
                        if await optimizer_after.solve():
                            stats_after = await optimizer_after.get_optimization_stats()
                            plan_after = await optimizer_after.get_routing_plan()
                            
                            # Compare routing plans
                            # Calculate totals
                            original_total = sum((original_links_data.get(link_id, {}).get('traffic', 0) / 100.0) * 
                                               original_links_data.get(link_id, {}).get('price', 0) 
                                               for link_id in original_links_data)
                            
                            before_routes = {route['link']: route for route in plan_before['routes'] if route['percentage'] > 0}
                            after_routes = {route['link']: route for route in plan_after['routes'] if route['percentage'] > 0}
                            
                            before_total = sum((before_routes.get(link_id, {}).get('percentage', 0) / 100.0) * 
                                             before_routes.get(link_id, {}).get('price', 0) 
                                             for link_id in before_routes)
                            
                            after_total = sum((after_routes.get(link_id, {}).get('percentage', 0) / 100.0) * 
                                            after_routes.get(link_id, {}).get('price', 0) 
                                            for link_id in after_routes)
                            
                            # Calculate savings and impacts
                            opt_savings = original_total - before_total
                            opt_savings_pct = (opt_savings / original_total) * 100 if original_total > 0 else 0
                            price_impact = after_total - before_total
                            price_impact_pct = (price_impact / before_total) * 100 if before_total > 0 else 0
                            total_impact = after_total - original_total
                            total_impact_pct = (total_impact / original_total) * 100 if original_total > 0 else 0
                            
                            # Count links used in each allocation
                            orig_links_used = sum(1 for link_id in original_links_data if original_links_data[link_id].get('traffic', 0) > 0)
                            opt_links_used = len(before_routes)
                            after_links_used = len(after_routes)
                            
                            # Print simplified summary
                            print("\n=== SIMPLIFIED PRICE CHANGE IMPACT SUMMARY ===")
                            print("\n1. ORIGINAL ALLOCATION:")
                            print(f"   Links used:  {orig_links_used}")
                            print(f"   Total cost:  ${original_total:.4f}")
                            print(f"   SLA:         {original_sla*100:.2f}%")
                            
                            print("\n2. OPTIMIZED ALLOCATION:")
                            print(f"   Links used:  {opt_links_used}")
                            print(f"   Total cost:  ${before_total:.4f}")
                            print(f"   Cost savings: ${opt_savings:+.4f} ({opt_savings_pct:+.2f}%)")
                            print(f"   SLA:         {stats_before['achieved_sla']:.2f}%")
                            
                            print("\n3. AFTER PRICE CHANGE:")
                            print(f"   Links used:  {after_links_used}")
                            print(f"   Total cost:  ${after_total:.4f}")
                            print(f"   Price impact: ${price_impact:+.4f} ({price_impact_pct:+.2f}%)")
                            print(f"   SLA:         {stats_after['achieved_sla']:.2f}%")
                            
                            print("\n=== KEY LINKS ===")
                            # Show only the most important links (those with traffic in any allocation)
                            important_links = []
                            
                            # Collect all links from all three allocations that have traffic
                            all_links = set()
                            for link_id, link_data in original_links_data.items():
                                if link_data.get('traffic', 0) > 0:
                                    all_links.add(link_id)
                            
                            for route in plan_before['routes']:
                                if route['percentage'] > 0:
                                    all_links.add(route['link'])
                                    
                            for route in plan_after['routes']:
                                if route['percentage'] > 0:
                                    all_links.add(route['link'])
                            
                            # Show only links with significant traffic in any allocation
                            for link_id in all_links:
                                orig_traffic = original_links_data.get(link_id, {}).get('traffic', 0)
                                opt_traffic = next((route['percentage'] for route in plan_before['routes'] if route['link'] == link_id), 0)
                                after_traffic = next((route['percentage'] for route in plan_after['routes'] if route['link'] == link_id), 0)
                                
                                # Only show links with significant traffic (>= 10%)
                                if orig_traffic >= 10 or opt_traffic >= 10 or after_traffic >= 10:
                                    provider = (
                                        original_links_data.get(link_id, {}).get('provider') or
                                        next((route['provider'] for route in plan_before['routes'] if route['link'] == link_id), None) or
                                        next((route['provider'] for route in plan_after['routes'] if route['link'] == link_id), "Unknown")
                                    )
                                    
                                    print(f"\n{link_id} ({provider}):")
                                    print(f"   Original:   {orig_traffic:.1f}%")
                                    print(f"   Optimized:  {opt_traffic:.1f}%")
                                    print(f"   After price change: {after_traffic:.1f}%")
                            
                            # Show bottom line
                            print("\n=== BOTTOM LINE ===")
                            print(f"Original cost:      ${original_total:.4f}")
                            print(f"Optimized cost:     ${before_total:.4f}")
                            print(f"After price change: ${after_total:.4f}")
                            print(f"Total savings:      ${total_impact:+.4f} ({total_impact_pct:+.2f}%)")
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