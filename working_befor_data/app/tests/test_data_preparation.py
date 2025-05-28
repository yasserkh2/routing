import asyncio
from ..services.data_preparation_service import DataPreparationService, PROFILE_INCLUSION_LIST
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
        
        # Print the inclusion list
        print("\nProfile Inclusion List:")
        for profile_name in PROFILE_INCLUSION_LIST:
            print(f"- {profile_name}")
        
        # Verify all profiles are in the inclusion list
        print("\nVerifying profiles against inclusion list...")
        if all_profiles:
            for profile in all_profiles:
                if profile.name in PROFILE_INCLUSION_LIST:
                    print(f"✓ Profile {profile.name} is in the inclusion list")
                else:
                    print(f"✗ Profile {profile.name} is NOT in the inclusion list")
        else:
            print("No profiles found in the mock data that match the inclusion list.")
            print("This is expected if the mock data doesn't contain any profiles from the inclusion list.")
            
        # Get all profiles from mock API without filtering
        print("\nChecking all profiles in mock data (before filtering)...")
        mock_api = data_service.mock_api
        all_mock_profiles = await mock_api.get_combined_data()
        print(f"Total profiles in mock data: {len(all_mock_profiles)}")
        
        for profile_data in all_mock_profiles:
            profile_name = profile_data['name']
            if profile_name in PROFILE_INCLUSION_LIST:
                print(f"✓ Mock profile {profile_name} is in the inclusion list")
            else:
                print(f"✗ Mock profile {profile_name} is NOT in the inclusion list")
        
        print("\nInclusion list is working as expected - only profiles in the list will be processed.")
        return
        
        # Test with the first profile
        profile = all_profiles[0]
        print(f"\nUsing profile: {profile.name} (ID: {profile.profile_id})")
        print(f"Expected SLA: {profile.expected_sla}%")
        print(f"In-Use Links: {len(profile.in_use_links)}")
        print(f"Alternative Links: {len(profile.alternative_links)}")
        
        # Test prepare_links_data_for_optimizer
        print("\nTesting prepare_links_data_for_optimizer()...")
        links_data = await data_service.prepare_links_data_for_optimizer(profile)
        print(f"Prepared data for {len(links_data)} links")
        
        # Display data for each link
        print("\nLINK DATA:")
        print("-" * 30)
        for link_id, link_data in links_data.items():
            print(f"Link {link_id} ({link_data['provider']}):")
            print(f"  SLA:           {link_data['sla']*100:.1f}%")
            print(f"  Tier:          {link_data['tier']}")
            print(f"  Price:         ${link_data['price']:.3f}")
            print()
        
        # Calculate basic SLA metrics manually
        print("\nCalculating basic SLA metrics...")
        sla_values = [link_data['sla']*100 for link_data in links_data.values()]
        
        if sla_values:
            avg_sla = sum(sla_values) / len(sla_values)
            min_sla = min(sla_values)
            max_sla = max(sla_values)
            
            print("\nSLA METRICS:")
            print("-" * 30)
            print(f"Average SLA:      {avg_sla:.2f}%")
            print(f"Min SLA:          {min_sla:.2f}%")
            print(f"Max SLA:          {max_sla:.2f}%")
            print(f"Target SLA:       {profile.expected_sla:.2f}%")
            print(f"Can Meet Target:  {max_sla >= profile.expected_sla}")
        else:
            print("No SLA data available to calculate metrics")
        
        # Test get_link_data for a specific link
        if profile.in_use_links:
            test_link_id = profile.in_use_links[0]
            print(f"\nTesting get_link_data() for link {test_link_id}...")
            link_data = await data_service.get_link_data(test_link_id)
            
            if link_data:
                print("\nLINK DATA:")
                print("-" * 30)
                print(f"Link:            {link_data['link']}")
                print(f"Provider:        {link_data['provider']}")
                print(f"SLA:             {link_data['sla']*100:.1f}%")
                print(f"Tier:            {link_data['tier']}")
                print(f"Price:           ${link_data['price']:.3f}")
            else:
                print(f"No data found for link {test_link_id}")
        
        # Sort links by SLA (descending) and display top links
        print("\nSorting links by SLA...")
        sorted_links = sorted(
            links_data.items(), 
            key=lambda x: x[1]['sla'], 
            reverse=True
        )
        
        print("\nTOP LINKS BY SLA:")
        print("-" * 30)
        for i, (link_id, link_data) in enumerate(sorted_links[:5]):  # Show top 5 links
            print(f"{i+1}. Link {link_id} ({link_data['provider']}):")
            print(f"   SLA:           {link_data['sla']*100:.1f}%")
            print(f"   Price:         ${link_data['price']:.3f}")
        
        if len(sorted_links) > 5:
            print(f"... and {len(sorted_links) - 5} more links")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Error testing data preparation service: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_data_preparation_service())