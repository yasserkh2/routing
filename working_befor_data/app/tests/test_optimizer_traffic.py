import asyncio
import os
import sys
import json
from typing import Dict, List, Any

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.profile import Profile
from app.services.data_preparation_service import DataPreparationService
from app.core.optimizer import RoutingOptimizer

async def test_optimizer_traffic():
    """Test the optimizer traffic allocation"""
    print("\n" + "="*50)
    print("          OPTIMIZER TRAFFIC TEST")
    print("="*50 + "\n")
    
    # Initialize services
    data_service = DataPreparationService()
    
    try:
        # Get all profiles
        all_profiles = await data_service.get_all_profiles()
        
        if not all_profiles:
            print("No profiles found. Test cannot continue.")
            return
        
        # Test with the first profile
        profile = all_profiles[0]
        print(f"\nUsing profile: {profile.name} (ID: {profile.profile_id})")
        print(f"Expected SLA: {profile.expected_sla}%")
        print(f"In-Use Links: {len(profile.in_use_links)}")
        print(f"Alternative Links: {len(profile.alternative_links)}")
        
        # Prepare SLA data for optimizer
        links_data = await data_service.prepare_sla_data_for_optimizer(profile)
        print(f"\nPrepared SLA data for {len(links_data)} links")
        
        # Print links_data for debugging
        print("\nLINKS DATA:")
        print("-" * 30)
        for link_id, link_data in links_data.items():
            print(f"Link {link_id} ({link_data['provider']}):")
            print(f"  SLA:           {link_data['sla']*100:.1f}%")
            print(f"  Price:         ${link_data['price']:.3f}")
            print()
        
        # Run optimization
        optimizer = RoutingOptimizer(profile, links_data)
        success = optimizer.solve()
        
        if success:
            # Get optimization results
            results = optimizer.get_results()
            
            print("\nOPTIMIZATION RESULTS:")
            print("-" * 30)
            for link_id, percentage in results.items():
                if percentage > 0:  # Only include routes with traffic
                    link_data = links_data[link_id]
                    print(f"Link {link_id} ({link_data['provider']}):")
                    print(f"  Traffic:       {percentage*100:.1f}%")
                    print(f"  SLA:           {link_data['sla']*100:.1f}%")
                    print(f"  Price:         ${link_data['price']:.3f}")
                    print()
            
            # Calculate optimization statistics
            total_cost = sum(results[link_id] * links_data[link_id]['price'] for link_id in results)
            achieved_sla = sum(results[link_id] * links_data[link_id]['sla'] for link_id in results)
            active_links = sum(1 for percentage in results.values() if percentage > 0)
            
            print("\nOPTIMIZATION STATS:")
            print("-" * 30)
            print(f"Achieved SLA:    {achieved_sla*100:.2f}%")
            print(f"Total Cost:      ${total_cost:.2f}")
            print(f"Links Used:      {active_links}")
        else:
            print("\nFailed to find optimal solution")
        
    except Exception as e:
        print(f"Error testing optimizer traffic: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_optimizer_traffic())