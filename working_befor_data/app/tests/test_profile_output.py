import json
import os
from ..models.profile import Profile

def test_profile_output():
    """Test and display Profile data extraction"""
    import sys
    def print_flush(*args, **kwargs):
        print(*args, **kwargs)
        sys.stdout.flush()
        
    print_flush("\n=== Testing Profile Data Extraction ===\n")
    print_flush("Starting test...")
    
    # Load test data
    mock_data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'mock_data',
        'api_round_2_reorganized_links_no_sla.json'
    )
    
    try:
        print_flush(f"Reading data from: {mock_data_path}")
        with open(mock_data_path, 'r') as f:
            raw_data = json.load(f)
        print_flush(f"Successfully loaded {len(raw_data)} profiles from JSON")
            
        for i, profile_data in enumerate(raw_data, 1):
            print_flush(f"\nProcessing Profile {i} of {len(raw_data)}")
            print_flush(f"Raw data: {profile_data['profile_id']}, {profile_data['name']}")
            
            # Create Profile instance
            profile = Profile.from_api_data(profile_data)
            print_flush("Successfully created Profile instance")
            
            # Display Profile data
            print_flush(f"\nProfile Details:")
            print_flush(f"---------------")
            print_flush(f"ID: {profile.profile_id}")
            print_flush(f"Name: {profile.name}")
            print_flush(f"Expected SLA: {profile.expected_sla}%")
            print_flush(f"Description: {profile.description}")
            print_flush(f"Sell Price Range: ${profile.sell_price_min} - ${profile.sell_price_max}")
            print_flush(f"Average Cost: ${profile.profile_avg_cost}")
            print_flush(f"MCC/MNC: {profile.mcc}/{profile.mnc}")
            
            print_flush(f"\nIn-Use Links ({len(profile.in_use_links)} links):")
            for link_name in profile.in_use_links:
                print_flush(f"  - {link_name}")
                
            print_flush(f"\nAlternative Links ({len(profile.alternative_links)} links):")
            for link_name in profile.alternative_links:
                print_flush(f"  - {link_name}")
            
            print_flush("\nUtility Methods Test:")
            print_flush("--------------------")
            all_links = profile.get_all_links()
            print_flush(f"All Links Count: {len(all_links)}")
            print_flush(f"Unique Links Count: {len(set(all_links))}")
            
            test_link = profile.in_use_links[0] if profile.in_use_links else ""
            if test_link:
                print_flush(f"Testing link operations with '{test_link}':")
                print_flush(f"  Has Link: {profile.has_link(test_link)}")
                print_flush(f"  Is Active: {profile.is_link_active(test_link)}")
            
            # Test clone functionality
            cloned = profile.clone()
            print_flush("\nClone Test:")
            print_flush(f"  Original ID: {profile.profile_id}")
            print_flush(f"  Cloned ID: {cloned.profile_id}")
            print_flush(f"  Links Match: {profile.get_all_links() == cloned.get_all_links()}")
            
            print_flush("\n" + "="*50 + "\n")
            
    except Exception as e:
        print_flush(f"Error during profile test: {str(e)}")
        import traceback
        print_flush(traceback.format_exc())
        raise

if __name__ == "__main__":
    test_profile_output()