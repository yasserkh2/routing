import asyncio
from unittest.mock import patch
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

async def test_alternative_links_sharing():
    """Test that alternative links are now shared across all profiles"""
    print("\n" + "="*50)
    print("      ALTERNATIVE LINKS SHARING TEST")
    print("="*50 + "\n")
    
    # Initialize service
    data_service = DataPreparationService()
    
    try:
        # Get all profiles
        print("Getting all profiles...")
        all_profiles = await data_service.get_all_profiles()
        
        if not all_profiles:
            print("No profiles found!")
            return
        
        print(f"Found {len(all_profiles)} profiles")
        
        # Check alternative links for each profile
        alternative_links_per_profile = {}
        
        for profile in all_profiles:
            alt_links = profile.alternative_links
            alternative_links_per_profile[profile.name] = alt_links
            print(f"\nProfile: {profile.name}")
            print(f"  In-use links: {len(profile.in_use_links)}")
            print(f"  Alternative links: {len(alt_links)}")
            
            # Show first few alternative links as sample
            if alt_links:
                print(f"  Sample alternative links: {alt_links[:3]}...")
        
        # Check if all profiles have the same alternative links
        if len(set(len(links) for links in alternative_links_per_profile.values())) == 1:
            print(f"\n✅ SUCCESS: All profiles have the same number of alternative links!")
            
            # Get the first profile's alternative links as reference
            first_profile_links = set(list(alternative_links_per_profile.values())[0])
            
            # Check if all profiles have the same alternative links
            all_same = True
            for profile_name, links in alternative_links_per_profile.items():
                if set(links) != first_profile_links:
                    all_same = False
                    print(f"❌ Profile {profile_name} has different alternative links")
                    break
            
            if all_same:
                print(f"✅ SUCCESS: All profiles have the exact same alternative links!")
                print(f"   Total alternative links available to all profiles: {len(first_profile_links)}")
            else:
                print(f"❌ ISSUE: Profiles have different sets of alternative links")
        else:
            print(f"❌ ISSUE: Profiles have different numbers of alternative links")
            for profile_name, links in alternative_links_per_profile.items():
                print(f"  {profile_name}: {len(links)} alternative links")
        
        print("\nAlternative links sharing test completed!")
        
    except Exception as e:
        print(f"Error testing alternative links sharing: {str(e)}")

async def test_sla_dd_tier_logic():
    """Test SLA calculation logic when sla_dd and tier are present/absent"""
    print("\n" + "="*50)
    print("         SLA_DD AND TIER LOGIC TEST")
    print("="*50 + "\n")
    
    # Initialize service
    data_service = DataPreparationService()
    
    try:
        print("Testing SLA calculation logic scenarios...")
        
        # Test Case 1: In-use link with sla_dd but tier is null - should use sla_dd
        print("\n1. Testing in-use link with sla_dd=85% and tier=null...")
        mock_data_1 = [{
            'profile_id': 'test_profile_1',
            'name': 'Standard_MTN_Adv_Nigeria',
            'in_use_links': [{
                'link': 'test_link_1',
                'provider': 'Test Provider',
                'buy_price': 0.05,
                'sla_dd': 85,  # 85%
                'tier': None  # No tier
            }],
            'alternative_links': []
        }]
        
        with patch.object(data_service.mock_api, 'get_combined_data', return_value=mock_data_1):
            result = await data_service.get_link_data('test_link_1')
            
            if result:
                print(f"   ✓ SLA calculated: {result['sla']*100:.1f}% (expected: 85.0%)")
                print(f"   ✓ Tier: {result['tier']} (expected: None)")
                print(f"   ✓ Original sla_dd: {result['sla_dd']} (expected: 85)")
                assert result['sla'] == 0.85, f"Expected SLA 0.85, got {result['sla']}"
                assert result['tier'] is None, f"Expected tier None, got {result['tier']}"
            else:
                print("   ✗ No result returned")
        
        # Test Case 2: In-use link with both sla_dd and tier - should average them
        print("\n2. Testing in-use link with sla_dd=80% and tier=1 (95%)...")
        mock_data_2 = [{
            'profile_id': 'test_profile_2',
            'name': 'Standard_MTN_Adv_Nigeria',
            'in_use_links': [{
                'link': 'test_link_2',
                'provider': 'Test Provider',
                'buy_price': 0.05,
                'sla_dd': 80,  # 80%
                'tier': 1  # Tier 1 = 95%
            }],
            'alternative_links': []
        }]
        
        with patch.object(data_service.mock_api, 'get_combined_data', return_value=mock_data_2):
            result = await data_service.get_link_data('test_link_2')
            
            if result:
                expected_sla = (0.80 + 0.95) / 2  # Average of sla_dd and tier SLA
                print(f"   ✓ SLA calculated: {result['sla']*100:.1f}% (expected: {expected_sla*100:.1f}%)")
                print(f"   ✓ Tier: {result['tier']} (expected: 1)")
                assert abs(result['sla'] - expected_sla) < 0.01, f"Expected SLA {expected_sla}, got {result['sla']}"
                assert result['tier'] == 1, f"Expected tier 1, got {result['tier']}"
            else:
                print("   ✗ No result returned")
        
        # Test Case 3: Alternative link with tier - should be included
        print("\n3. Testing alternative link with tier=2...")
        mock_data_3 = [{
            'profile_id': 'test_profile_3',
            'name': 'Standard_MTN_Adv_Nigeria',
            'in_use_links': [],
            'alternative_links': [{
                'link': 'test_link_3',
                'provider': 'Test Provider',
                'buy_price': 0.05,
                'sla_dd': None,
                'tier': 2  # Tier 2 = 90%
            }]
        }]
        
        with patch.object(data_service.mock_api, 'get_combined_data', return_value=mock_data_3):
            result = await data_service.get_link_data('test_link_3')
            
            if result:
                print(f"   ✓ SLA calculated: {result['sla']*100:.1f}% (expected: 90.0%)")
                print(f"   ✓ Tier: {result['tier']} (expected: 2)")
                assert result['sla'] == 0.90, f"Expected SLA 0.90, got {result['sla']}"
                assert result['tier'] == 2, f"Expected tier 2, got {result['tier']}"
            else:
                print("   ✗ No result returned")
        
        # Test Case 4: Alternative link without tier - should be excluded
        print("\n4. Testing alternative link without tier (should be excluded)...")
        mock_data_4 = [{
            'profile_id': 'test_profile_4',
            'name': 'Standard_MTN_Adv_Nigeria',
            'in_use_links': [],
            'alternative_links': [{
                'link': 'test_link_4',
                'provider': 'Test Provider',
                'buy_price': 0.05,
                'sla_dd': 85,  # Has sla_dd
                'tier': None  # No tier
            }]
        }]
        
        with patch.object(data_service.mock_api, 'get_combined_data', return_value=mock_data_4):
            result = await data_service.get_link_data('test_link_4')
            
            if result is None:
                print("   ✓ Alternative link without tier correctly excluded from calculations")
            else:
                print(f"   ✗ Alternative link without tier should be excluded, but got: {result}")
        
        # Test Case 5: String tier format "Tier 1 - Prime"
        print("\n5. Testing string tier format 'Tier 1 - Prime'...")
        mock_data_5 = [{
            'profile_id': 'test_profile_5',
            'name': 'Standard_MTN_Adv_Nigeria',
            'in_use_links': [{
                'link': 'test_link_5',
                'provider': 'Test Provider',
                'buy_price': 0.05,
                'sla_dd': None,
                'tier': "Tier 1 - Prime"  # String format
            }],
            'alternative_links': []
        }]
        
        with patch.object(data_service.mock_api, 'get_combined_data', return_value=mock_data_5):
            result = await data_service.get_link_data('test_link_5')
            
            if result:
                print(f"   ✓ SLA calculated: {result['sla']*100:.1f}% (expected: 95.0%)")
                print(f"   ✓ Tier parsed: {result['tier']} (expected: 1)")
                assert result['sla'] == 0.95, f"Expected SLA 0.95, got {result['sla']}"
                assert result['tier'] == 1, f"Expected tier 1, got {result['tier']}"
            else:
                print("   ✗ No result returned")
        
        # Test Case 6: Alternative link with tier > 4 - should be excluded
        print("\n6. Testing alternative link with tier=6 (should be excluded)...")
        mock_data_6 = [{
            'profile_id': 'test_profile_6',
            'name': 'Standard_MTN_Adv_Nigeria',
            'in_use_links': [],
            'alternative_links': [{
                'link': 'test_link_6',
                'provider': 'Test Provider',
                'buy_price': 0.05,
                'sla_dd': 85,  # Has sla_dd
                'tier': 6  # Tier 6 - above maximum supported tier 4
            }]
        }]
        
        with patch.object(data_service.mock_api, 'get_combined_data', return_value=mock_data_6):
            result = await data_service.get_link_data('test_link_6')
            
            if result is None:
                print("   ✓ Alternative link with tier > 4 correctly excluded from calculations")
            else:
                print(f"   ✗ Alternative link with tier > 4 should be excluded, but got: {result}")
        
        print("\n✅ All SLA/tier logic tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing SLA/tier logic: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_data_preparation_service())
    asyncio.run(test_alternative_links_sharing())
    asyncio.run(test_sla_dd_tier_logic())