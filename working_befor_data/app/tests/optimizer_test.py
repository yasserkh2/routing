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
                
                print("\nOPTIMIZED ROUTING:")
                print("-" * 30)
                for route in routing_plan['routes']:
                    if route['percentage'] > 0:  # Only show routes with traffic
                        print(f"Link {route['link']} ({route['provider']}):")
                        print(f"  Traffic:       {route['percentage']:.1f}%")
                        print(f"  SLA:           {route['sla']:.1f}%")
                        print(f"  Tier:          {route['tier']}")
                        print(f"  Price:         ${route['price']:.3f}")
                        print()
                
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
                        print("-" * 30)
                        original_cost = 0
                        original_sla = 0
                        for link_id, link_data in original_links_data.items():
                            traffic_pct = link_data['traffic']
                            print(f"- Link {link_id}: {traffic_pct:.1f}% (SLA: {link_data['sla']:.1f}%, Price: ${link_data['price']:.3f})")
                            original_cost += (traffic_pct / 100.0) * link_data['price']
                            original_sla += (traffic_pct / 100.0) * (link_data['sla'] / 100.0)
                        
                        print(f"\nOriginal Cost:   ${original_cost:.4f}")
                        print(f"Original SLA:    {original_sla*100:.2f}%")
                        
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
                            
                            print("\nIMPACT ANALYSIS:")
                            print("-" * 30)
                            print(f"Cost Change:     ${cost_change:+.4f} ({cost_change_pct:+.2f}%)")
                            
                            # Compare routing plans
                            print("\nCOMPARISON OF OPTIMIZED ALLOCATIONS:")
                            print("- Before Price Change (Optimized):")
                            for route in plan_before['routes']:
                                if route['percentage'] > 0:
                                    print(f"  Link {route['link']}: {route['percentage']:.1f}% (SLA: {route['sla']:.1f}%, Price: ${route['price']:.3f})")
                            
                            print("\n- After Price Change (Optimized):")
                            for route in plan_after['routes']:
                                if route['percentage'] > 0:
                                    print(f"  Link {route['link']}: {route['percentage']:.1f}% (SLA: {route['sla']:.1f}%, Price: ${route['price']:.3f})")
                                    
                            print("\nSUMMARY OF CHANGES:")
                            print("1. Original Database Allocation: 25% traffic to each of 4 in-use links")
                            print("2. Optimized Allocation: Redistributed to minimize cost while meeting SLA")
                            print("3. Optimized After Price Change: Adjusted based on new pricing")
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
    asyncio.run(test_optimizer())