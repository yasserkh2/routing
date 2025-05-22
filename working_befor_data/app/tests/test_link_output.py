import json
import os
from ..models.link import Link

def test_link_output():
    """Test and display Link data extraction"""
    import sys
    def print_flush(*args, **kwargs):
        print(*args, **kwargs)
        sys.stdout.flush()
        
    print_flush("\n=== Testing Link Data Extraction ===\n")
    
    # Load test data
    mock_data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'mock_data',
        'api_round_2_reorganized_links_no_sla.json'
    )
    
    try:
        print_flush(f"Opening file: {mock_data_path}")
        with open(mock_data_path, 'r') as f:
            raw_data = json.load(f)
        print_flush(f"Successfully loaded JSON data")
            
        # Test in-use links
        print_flush("\nTesting In-Use Links:")
        print_flush(f"Found {len(raw_data)} profiles")
        print_flush("-" * 20)
        for profile in raw_data:
            print_flush(f"\nProcessing profile: {profile['profile_id']}")
            print_flush(f"In-use links count: {len(profile['in_use_links'])}")
            for link_data in profile['in_use_links']:
                print_flush(f"\nProcessing link data: {link_data}")
                link = Link.from_api_data(link_data)
                print_flush(f"\nLink Details:")
                print_flush(f"ID: {link.link}")
                print_flush(f"Provider: {link.provider}")
                print_flush(f"Buy Price: ${link.buy_price}")
                print_flush(f"SLA DD: {link.sla_dd}%")
                print_flush(f"Tier: {link.tier}")
                print_flush(f"Traffic: {link.traffic}%")
                print_flush(f"Last Updated: {link.last_updated}")
                
                # Test dictionary conversion
                dict_data = link.to_dict()
                print_flush("\nDictionary Format:")
                for key, value in dict_data.items():
                    print_flush(f"  {key}: {value}")
                print_flush("-" * 40)
                
        # Test alternative links
        print_flush("\nTesting Alternative Links:")
        print_flush(f"Found {len(raw_data)} profiles")
        print_flush("-" * 25)
        for profile in raw_data:
            print_flush(f"\nProcessing profile: {profile['profile_id']}")
            print_flush(f"Alternative links count: {len(profile['alternative_links'])}")
            for link_data in profile['alternative_links']:
                print_flush(f"\nProcessing link data: {link_data}")
                link = Link.from_api_data(link_data)
                print_flush(f"\nLink Details:")
                print_flush(f"ID: {link.link}")
                print_flush(f"Provider: {link.provider}")
                print_flush(f"Buy Price: ${link.buy_price}")
                print_flush(f"SLA DD: {link.sla_dd}%")  # Should be 0.0 if not provided
                print_flush(f"Tier: {link.tier}")
                print_flush(f"Traffic: {link.traffic}%")  # Should be 0.0 if not provided
                print_flush(f"Last Updated: {link.last_updated}")
                
                # Test dictionary conversion
                dict_data = link.to_dict()
                print_flush("\nDictionary Format:")
                for key, value in dict_data.items():
                    print_flush(f"  {key}: {value}")
                print_flush("-" * 40)
            
    except Exception as e:
        print_flush(f"Error during link test: {str(e)}")
        raise

if __name__ == "__main__":
    test_link_output()