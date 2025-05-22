import asyncio
from ..services.mock_services import MockAPIService
from ..services.data_preparation_service import DataPreparationService
from ..core.optimizer import RoutingOptimizer
from ..models.profile import Profile
from ..models.link import Link
import json
import os

async def run_optimizer_test():
    """Test the optimizer with mock data focusing on SLA and tier requirements"""
    print("\n" + "="*50)
    print("          SLA OPTIMIZATION TEST")
    print("="*50 + "\n")
    
    # Initialize services
    mock_api = MockAPIService()
    data_service = DataPreparationService()
    
    try:
        # Get all profiles using DataPreparationService
        all_profiles = await data_service.get_all_profiles()
        
        # Process each profile
        for profile in all_profiles:
            print("\n" + "-"*50)
            print(f"PROFILE: {profile.name}")
            print("-"*50)
            print(f"Expected SLA:    {profile.expected_sla}%")
            print(f"In-Use Links:    {len(profile.in_use_links)}")
            print(f"Alternative Links: {len(profile.alternative_links)}")
            
            print("\nAVAILABLE LINKS:")
            print("-" * 30)
            for link in profile.get_all_links():
                print(f"Link {link.link} ({link.provider}):")
                print(f"  Tier:          {link.tier}")
                print(f"  Actual SLA:    {link.sla_dd:.1f}%")
                print(f"  Required SLA:   {link.TIER_SLA_MAP.get(link.tier, 90.0):.1f}%")
                print(f"  Price:         ${link.price:.3f}")
                print()
            
            # Run optimization
            optimizer = RoutingOptimizer(profile)
            success = optimizer.solve()
            
            if success:
                # Get and display results
                routing_plan = optimizer.get_routing_plan()
                stats = optimizer.get_optimization_stats()
                
                print("\nOPTIMIZED ROUTING:")
                print("-" * 30)
                for route in routing_plan['routes']:
                    print(f"Link {route['link']} ({route['provider']}):")
                    print(f"  Traffic:       {route['percentage']:.1f}%")
                    print(f"  Tier:          {route['tier']}")
                    print(f"  Actual SLA:    {route['sla_dd']:.1f}%")
                    print(f"  Required SLA:   {route['tier_sla']:.1f}%")
                    print(f"  Price:         ${route['price']:.3f}")
                    print()
                
                print("\nOPTIMIZATION STATS:")
                print("-" * 30)
                print(f"Achieved SLA:    {stats['achieved_sla']:.2f}%")
                print(f"Total Cost:      ${stats['total_cost']:.2f}")
                print(f"Links Used:      {stats['links_used']}")
                
                print("\nTIER STATISTICS:")
                print("-" * 30)
                for tier, tier_data in sorted(stats['tier_stats'].items()):
                    print(f"Tier {tier}:")
                    print(f"  Traffic:       {tier_data['traffic']:.1f}%")
                    print(f"  Required SLA:   {tier_data['required_sla']:.1f}%")
                
                if not stats['sla_achievable']:
                    print(f"\nWARNING: {stats['warning']}")
            else:
                print("\nFailed to find optimal solution")
            
    except Exception as e:
        print(f"Error running optimizer: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_optimizer_test())