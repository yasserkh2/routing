import json
import os
from ..models.profile import Profile
from ..models.link import Link

def test_data_models():
    """Test Profile and Link data extraction"""
    print("\n" + "="*50)
    print("          DATA MODEL EXTRACTION TEST")
    print("="*50 + "\n")
    
    try:
        # Load test data
        mock_data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'mock_data',
            'api_round_2_reorganized_links_no_sla.json'
        )
        with open(mock_data_path, 'r') as f:
            raw_data = json.load(f)
        
        # Test Profile Data Extraction
        print("TESTING PROFILE DATA EXTRACTION:")
        print("-" * 30)
        
        for profile_data in raw_data:
            profile = Profile.from_api_data(profile_data)
            print(f"\nProfile ID: {profile.profile_id}")
            print(f"Name: {profile.name}")
            print(f"Expected SLA: {profile.expected_sla}%")
            print(f"Description: {profile.description}")
            print(f"Sell Price Range: ${profile.sell_price_min} - ${profile.sell_price_max}")
            print(f"Average Cost: ${profile.profile_avg_cost}")
            print(f"MCC/MNC: {profile.mcc}/{profile.mnc}")
            print("\nIn-Use Links:")
            for link_name in profile.in_use_links:
                print(f"  - {link_name}")
            print("\nAlternative Links:")
            for link_name in profile.alternative_links:
                print(f"  - {link_name}")
            
            # Test Link Data Extraction
            print("\nTESTING LINK DATA EXTRACTION:")
            print("-" * 30)
            
            print("\nIn-Use Links Details:")
            for link_data in profile_data['in_use_links']:
                link = Link.from_api_data(link_data)
                print(f"\nLink ID: {link.link}")
                print(f"Provider: {link.provider}")
                print(f"Buy Price: ${link.buy_price}")
                print(f"SLA DD: {link.sla_dd}%")
                print(f"Tier: {link.tier}")
                print(f"Traffic: {link.traffic}%")
                print(f"Last Updated: {link.last_updated}")
            
            print("\nAlternative Links Details:")
            for link_data in profile_data['alternative_links']:
                link = Link.from_api_data(link_data)
                print(f"\nLink ID: {link.link}")
                print(f"Provider: {link.provider}")
                print(f"Buy Price: ${link.buy_price}")
                print(f"SLA DD: {link.sla_dd}%")
                print(f"Tier: {link.tier}")
                print(f"Traffic: {link.traffic}%")
                print(f"Last Updated: {link.last_updated}")
            
            print("\n" + "="*50)
            
    except Exception as e:
        print(f"Error during data model test: {str(e)}")

if __name__ == "__main__":
    test_data_models()