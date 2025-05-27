import asyncio
import os
import sys
from typing import Dict, List, Any
from ..services.data_preparation_service import DataPreparationService
from ..core.optimizer import RoutingOptimizer

async def show_optimization_results():
    """
    Show the optimization results for all profiles.
    This script focuses on displaying the traffic distribution and SLA achievements.
    """
    print("\n=====================================")
    print("    OPTIMIZATION RESULTS REPORT")
    print("=====================================\n")
    
    # Initialize services
    data_service = DataPreparationService()
    
    # Get all profiles
    all_profiles = await data_service.get_all_profiles()
    
    if not all_profiles:
        print("No profiles found.")
        return
    
    print(f"Found {len(all_profiles)} profiles\n")
    
    # Process each profile
    for profile in all_profiles:
        print(f"\n=== PROFILE: {profile.name} (ID: {profile.profile_id}) ===")
        print(f"Expected SLA: {profile.expected_sla}%")
        
        # Get original traffic distribution (equal distribution)
        links_data = await data_service.prepare_links_data_for_optimizer(profile)
        traffic_per_link = 100.0 / len(profile.in_use_links) if profile.in_use_links else 0
        
        print("\nORIGINAL TRAFFIC DISTRIBUTION:")
        print("-------------------------------")
        
        original_cost = 0
        original_sla = 0
        
        for link_id in profile.in_use_links:
            link_data = links_data.get(link_id)
            if link_data:
                print(f"Link {link_id}: {traffic_per_link:.1f}% traffic, {link_data['sla']*100:.1f}% SLA, ${link_data['price']:.3f}")
                original_cost += (traffic_per_link / 100.0) * link_data['price']
                original_sla += (traffic_per_link / 100.0) * link_data['sla']
        
        original_sla = original_sla * 100  # Convert to percentage
        print(f"Original Cost: ${original_cost:.4f}")
        print(f"Original SLA: {original_sla:.2f}%")
        
        # Run optimization
        optimizer = RoutingOptimizer(profile)
        success = await optimizer.solve()
        
        if success:
            # Get optimization results
            routing_plan = await optimizer.get_routing_plan()
            stats = await optimizer.get_optimization_stats()
            
            print("\nOPTIMIZED TRAFFIC DISTRIBUTION:")
            print("-------------------------------")
            
            for route in routing_plan['routes']:
                if route['percentage'] > 0:  # Only show routes with traffic
                    print(f"Link {route['link']}: {route['percentage']:.1f}% traffic, {route['sla']:.1f}% SLA, ${route['price']:.3f}")
            
            print(f"\nAchieved SLA: {stats['achieved_sla']:.2f}%")
            print(f"Total Cost: ${stats['total_cost']:.4f}")
            print(f"Cost Savings: ${original_cost - stats['total_cost']:+.4f} ({((original_cost - stats['total_cost'])/original_cost)*100:+.2f}%)")
            
            # Show tier statistics
            print("\nTraffic by Tier:")
            for tier, tier_data in sorted(stats['tier_stats'].items()):
                print(f"- Tier {tier}: {tier_data['traffic']:.1f}% traffic")
        else:
            print("\nFailed to find optimal solution")
    
    print("\nReport completed!")

if __name__ == "__main__":
    asyncio.run(show_optimization_results())