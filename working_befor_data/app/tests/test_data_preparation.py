import asyncio
from ..services.data_preparation_service import DataPreparationService
from ..models.profile import Profile
import json
import os

async def test_data_preparation_service():
    """Test the data preparation service, focusing on SLA preparation functionality"""
    print("\n" + "="*50)
    print("          DATA PREPARATION SERVICE TEST")
    print("="*50 + "\n")
    
    # Initialize service
    data_service = DataPreparationService()
    
    try:
        # Get all profiles
        print("Testing get_all_profiles()...")
        all_profiles = await data_service.get_all_profiles()
        print(f"Retrieved {len(all_profiles)} profiles")
        
        if not all_profiles:
            print("No profiles found. Test cannot continue.")
            return
        
        # Test with the first profile
        profile = all_profiles[0]
        print(f"\nUsing profile: {profile.name} (ID: {profile.profile_id})")
        print(f"Expected SLA: {profile.expected_sla}%")
        print(f"In-Use Links: {len(profile.in_use_links)}")
        print(f"Alternative Links: {len(profile.alternative_links)}")
        
        # Test prepare_sla_data_for_optimizer
        print("\nTesting prepare_sla_data_for_optimizer()...")
        links_data = await data_service.prepare_sla_data_for_optimizer(profile)
        print(f"Prepared SLA data for {len(links_data)} links")
        
        # Display SLA data for each link
        print("\nSLA DATA FOR LINKS:")
        print("-" * 30)
        for link_id, link_data in links_data.items():
            print(f"Link {link_id} ({link_data['provider']}):")
            print(f"  SLA:           {link_data['sla']*100:.1f}%")
            if 'sla_dd' in link_data and link_data['sla_dd'] is not None:
                print(f"  DD SLA:        {link_data['sla_dd']*100:.1f}%")
            print(f"  Tier SLA:      {link_data.get('tier_sla', 0)*100:.1f}%")
            print(f"  Tier:          {link_data['tier']}")
            print(f"  Price:         ${link_data['price']:.3f}")
            print()
        
        # Test calculate_profile_sla_metrics
        print("\nTesting calculate_profile_sla_metrics()...")
        sla_metrics = await data_service.calculate_profile_sla_metrics(profile)
        print("\nSLA METRICS:")
        print("-" * 30)
        print(f"Average SLA:      {sla_metrics['average_sla']:.2f}%")
        print(f"Min SLA:          {sla_metrics['min_sla']:.2f}%")
        print(f"Max SLA:          {sla_metrics['max_sla']:.2f}%")
        print(f"Achievable SLA:   {sla_metrics['achievable_sla']:.2f}%")
        print(f"Target SLA:       {sla_metrics['target_sla']:.2f}%")
        print(f"Can Meet Target:  {sla_metrics['can_meet_target']}")
        
        # Test get_link_sla_data for a specific link
        if profile.in_use_links:
            test_link_id = profile.in_use_links[0]
            print(f"\nTesting get_link_sla_data() for link {test_link_id}...")
            link_sla_data = await data_service.get_link_sla_data(test_link_id)
            
            if link_sla_data:
                print("\nLINK SLA DATA:")
                print("-" * 30)
                print(f"Link:            {link_sla_data['link']}")
                print(f"Provider:        {link_sla_data['provider']}")
                print(f"SLA:             {link_sla_data['sla']*100:.1f}%")
                if 'sla_dd' in link_sla_data and link_sla_data['sla_dd'] is not None:
                    print(f"DD SLA:          {link_sla_data['sla_dd']*100:.1f}%")
                print(f"Tier SLA:        {link_sla_data.get('tier_sla', 0)*100:.1f}%")
                print(f"Tier:            {link_sla_data['tier']}")
                print(f"Price:           ${link_sla_data['price']:.3f}")
            else:
                print(f"No SLA data found for link {test_link_id}")
        
        # Test get_optimized_sla_links
        print("\nTesting get_optimized_sla_links()...")
        optimized_links = await data_service.get_optimized_sla_links(profile)
        print(f"Retrieved {len(optimized_links)} optimized links")
        
        print("\nOPTIMIZED LINKS (sorted by SLA and price):")
        print("-" * 30)
        for i, link_data in enumerate(optimized_links[:5]):  # Show top 5 links
            print(f"{i+1}. Link {link_data['link']} ({link_data['provider']}):")
            print(f"   SLA:           {link_data['sla']*100:.1f}%")
            print(f"   Price:         ${link_data['price']:.3f}")
        
        if len(optimized_links) > 5:
            print(f"... and {len(optimized_links) - 5} more links")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Error testing data preparation service: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_data_preparation_service())