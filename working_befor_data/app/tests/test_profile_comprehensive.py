import os
import json
import sys

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.models.profile import Profile
from app.models.link import Link

def test_profile_comprehensive():
    """Comprehensive test for Profile class including extraction, labels, and status"""
    print("\n" + "="*50)
    print("          COMPREHENSIVE PROFILE CLASS TEST")
    print("="*50 + "\n")
    
    try:
        # Load Postman collection data
        postman_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'Routing_SLA_API.postman_collection.json'
        )
        
        print(f"Reading data from: {postman_path}", flush=True)
        with open(postman_path, 'r') as f:
            collection_data = json.load(f)
        
        # PART 1: DATA EXTRACTION TEST
        print("\n" + "="*40)
        print("PART 1: PROFILE DATA EXTRACTION TEST")
        print("="*40 + "\n", flush=True)
        
        if collection_data.get('profiles'):
            # Process first profile
            profile_data = collection_data['profiles'][0]
            
            # Add alternative links to the profile data
            profile_data['alternative_links'] = []
            for alt_link in collection_data.get('alternative_links', [])[:5]:  # Take first 5 alternative links
                # Convert to the format expected by Profile.from_api_data
                link_data = {
                    'link': alt_link.get('link', ''),
                    'provider': alt_link.get('provider', ''),
                    'buy_price': alt_link.get('base_buy_price', 0.0),
                    'tier': 1 if 'Prime' in alt_link.get('tier', '') else 6,
                    'last_updated': '2025-03-15T10:00:00.000000'
                }
                profile_data['alternative_links'].append(link_data)
            
            print("\nRaw Profile Data:", flush=True)
            print(f"ID: {profile_data.get('profile_id')}", flush=True)
            print(f"Name: {profile_data.get('name')}", flush=True)
            print(f"Expected SLA: {profile_data.get('expected_sla')}%", flush=True)
            print(f"MCC/MNC: {profile_data.get('mcc')}/{profile_data.get('mnc')}", flush=True)
            
            print("\nIn-Use Links in Raw Data:", flush=True)
            for link_data in profile_data.get('in_use_links', []):
                print(f"  - {link_data.get('link')}", flush=True)
            
            print("\nAlternative Links in Raw Data:", flush=True)
            for link_data in profile_data.get('alternative_links', []):
                print(f"  - {link_data.get('link')}", flush=True)
            
            # Create profile from data
            print("\nCreating Profile object from data...", flush=True)
            profile = Profile.from_api_data(profile_data)
            
            print("\nExtracted Profile Data:", flush=True)
            print(f"ID: {profile.profile_id}", flush=True)
            print(f"Name: {profile.name}", flush=True)
            print(f"Expected SLA: {profile.expected_sla}%", flush=True)
            print(f"MCC/MNC: {profile.mcc}/{profile.mnc}", flush=True)
            
            print("\nExtracted In-Use Links:", flush=True)
            for link_name in profile.in_use_links:
                label = profile.get_link_label(link_name)
                status = profile.get_link_status(link_name)
                print(f"  - {link_name} (Label: {label}, Status: {status})", flush=True)
            
            print("\nExtracted Alternative Links:", flush=True)
            for link_name in profile.alternative_links:
                label = profile.get_link_label(link_name)
                status = profile.get_link_status(link_name)
                print(f"  - {link_name} (Label: {label}, Status: {status})", flush=True)
            
            print("\nData Extraction Successful!", flush=True)
            
            # PART 2: LINK OPERATIONS TEST
            print("\n" + "="*40)
            print("PART 2: LINK OPERATIONS TEST")
            print("="*40 + "\n", flush=True)
            
            # Get all links
            all_links = profile.get_all_links()
            print(f"All Links Count: {len(all_links)}", flush=True)
            
            # Check if profile has specific links
            if profile.in_use_links:
                test_link = profile.in_use_links[0]
                print(f"\nTesting with link: {test_link}", flush=True)
                print(f"Has Link: {profile.has_link(test_link)}", flush=True)
                print(f"Is Active: {profile.is_link_active(test_link)}", flush=True)
                print(f"Label: {profile.get_link_label(test_link)}", flush=True)
                print(f"Status: {profile.get_link_status(test_link)}", flush=True)
            
            # Test adding a new link with label
            new_link = "NEW_TEST_LINK"
            custom_label = "My Custom Test Link"
            profile.add_link(new_link, is_active=True, label=custom_label)
            print(f"\nAfter adding new active link with custom label:", flush=True)
            print(f"Has Link: {profile.has_link(new_link)}", flush=True)
            print(f"Is Active: {profile.is_link_active(new_link)}", flush=True)
            print(f"Label: {profile.get_link_label(new_link)}", flush=True)
            print(f"Status: {profile.get_link_status(new_link)}", flush=True)
            
            # Test changing label
            new_label = "Updated Label"
            profile.set_link_label(new_link, new_label)
            print(f"\nAfter changing label:", flush=True)
            print(f"Label: {profile.get_link_label(new_link)}", flush=True)
            
            # Test changing status
            profile.set_link_status(new_link, "alternative")
            print(f"\nAfter changing status to alternative:", flush=True)
            print(f"Is Active: {profile.is_link_active(new_link)}", flush=True)
            print(f"Status: {profile.get_link_status(new_link)}", flush=True)
            print(f"In alternative_links list: {new_link in profile.alternative_links}", flush=True)
            print(f"In in_use_links list: {new_link in profile.in_use_links}", flush=True)
            
            # Test removing a link
            profile.remove_link(new_link)
            print(f"\nAfter removing link:", flush=True)
            print(f"Has Link: {profile.has_link(new_link)}", flush=True)
            
            # PART 3: CLONE AND ADVANCED OPERATIONS TEST
            print("\n" + "="*40)
            print("PART 3: CLONE AND ADVANCED OPERATIONS TEST")
            print("="*40 + "\n", flush=True)
            
            # Test cloning
            cloned = profile.clone()
            print(f"\nClone Test:", flush=True)
            print(f"Original ID: {profile.profile_id}", flush=True)
            print(f"Cloned ID: {cloned.profile_id}", flush=True)
            print(f"Links Match: {profile.get_all_links() == cloned.get_all_links()}", flush=True)
            print(f"Labels Match: {profile.link_labels == cloned.link_labels}", flush=True)
            print(f"Status Match: {profile.link_status == cloned.link_status}", flush=True)
            
            # Test get_links_with_info
            print(f"\nLinks with Info:", flush=True)
            print("-" * 40, flush=True)
            links_info = profile.get_links_with_info()
            for link_info in links_info:
                print(f"  - {link_info['link']} (Label: {link_info['label']}, Status: {link_info['status']}, Active: {link_info['is_active']})", flush=True)
            
            # PART 4: VALIDATION TESTS
            print("\n" + "="*40)
            print("PART 4: VALIDATION TESTS")
            print("="*40 + "\n", flush=True)
            
            # Test missing required fields
            invalid_profile = {
                'profile_id': 'TEST_001',
                'name': 'Test Profile'
                # Missing other required fields
            }
            try:
                Profile.from_api_data(invalid_profile)
                print("❌ Should have failed: Missing required fields", flush=True)
            except ValueError as e:
                print(f"✓ Correctly caught missing fields: {str(e)}", flush=True)
            
            # Test invalid SLA value
            invalid_profile = {
                'profile_id': 'TEST_001',
                'name': 'Test Profile',
                'expected_sla': 150.0,  # Invalid: > 100%
                'description': 'Test description',
                'sell_price_min': 10.0,
                'sell_price_max': 15.0,
                'profile_avg_cost': 7.5,
                'mcc': '123',
                'mnc': '45',
                'in_use_links': [],
                'alternative_links': []
            }
            try:
                Profile.from_api_data(invalid_profile)
                print("❌ Should have failed: Invalid SLA value", flush=True)
            except ValueError as e:
                print(f"✓ Correctly caught invalid SLA value: {str(e)}", flush=True)
            
            # Test negative sell price
            invalid_profile = {
                'profile_id': 'TEST_001',
                'name': 'Test Profile',
                'expected_sla': 95.0,
                'description': 'Test description',
                'sell_price_min': -10.0,  # Invalid: negative price
                'sell_price_max': 15.0,
                'profile_avg_cost': 7.5,
                'mcc': '123',
                'mnc': '45',
                'in_use_links': [],
                'alternative_links': []
            }
            try:
                Profile.from_api_data(invalid_profile)
                print("❌ Should have failed: Negative sell price", flush=True)
            except ValueError as e:
                print(f"✓ Correctly caught negative sell price: {str(e)}", flush=True)
            
            # Test invalid price range
            invalid_profile = {
                'profile_id': 'TEST_001',
                'name': 'Test Profile',
                'expected_sla': 95.0,
                'description': 'Test description',
                'sell_price_min': 20.0,
                'sell_price_max': 15.0,  # Invalid: less than min
                'profile_avg_cost': 7.5,
                'mcc': '123',
                'mnc': '45',
                'in_use_links': [],
                'alternative_links': []
            }
            try:
                Profile.from_api_data(invalid_profile)
                print("❌ Should have failed: Invalid price range", flush=True)
            except ValueError as e:
                print(f"✓ Correctly caught invalid price range: {str(e)}", flush=True)
            
            # Test negative average cost
            invalid_profile = {
                'profile_id': 'TEST_001',
                'name': 'Test Profile',
                'expected_sla': 95.0,
                'description': 'Test description',
                'sell_price_min': 10.0,
                'sell_price_max': 15.0,
                'profile_avg_cost': -7.5,  # Invalid: negative cost
                'mcc': '123',
                'mnc': '45',
                'in_use_links': [],
                'alternative_links': []
            }
            try:
                Profile.from_api_data(invalid_profile)
                print("❌ Should have failed: Negative average cost", flush=True)
            except ValueError as e:
                print(f"✓ Correctly caught negative average cost: {str(e)}", flush=True)
            
            # Test adding multiple links with different statuses
            print(f"\nTesting Multiple Link Operations:", flush=True)
            print("-" * 40, flush=True)
            
            # Add several test links
            test_links = [
                {"name": "TEST_LINK_1", "active": True, "label": "Test Link 1"},
                {"name": "TEST_LINK_2", "active": False, "label": "Test Link 2"},
                {"name": "TEST_LINK_3", "active": True, "label": "Test Link 3"}
            ]
            
            for link in test_links:
                profile.add_link(link["name"], is_active=link["active"], label=link["label"])
            
            print(f"After adding multiple test links:", flush=True)
            print(f"In-Use Links: {profile.in_use_links}", flush=True)
            print(f"Alternative Links: {profile.alternative_links}", flush=True)
            
            # Test changing status of multiple links
            profile.set_link_status("TEST_LINK_1", "alternative")
            profile.set_link_status("TEST_LINK_2", "in_use")
            
            print(f"\nAfter changing status of multiple links:", flush=True)
            print(f"In-Use Links: {profile.in_use_links}", flush=True)
            print(f"Alternative Links: {profile.alternative_links}", flush=True)
            
            # Test removing multiple links
            for link in test_links:
                profile.remove_link(link["name"])
            
            print(f"\nAfter removing all test links:", flush=True)
            print(f"In-Use Links Count: {len(profile.in_use_links)}", flush=True)
            print(f"Alternative Links Count: {len(profile.alternative_links)}", flush=True)
            
            print("\nAll Profile Tests Completed Successfully!", flush=True)
        else:
            print("No profile data found in the Postman collection", flush=True)
    except Exception as e:
        print(f"Error during profile test: {str(e)}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)

if __name__ == "__main__":
    test_profile_comprehensive()