import json
import os
from ..models.profile import Profile
from ..models.link import Link

def test_data_validation():
    """Test data validation in Profile and Link models"""
    import sys
    def print_flush(*args, **kwargs):
        print(*args, **kwargs)
        sys.stdout.flush()
        
    print_flush("\n=== Testing Data Validation ===\n")
    
    # Test Profile Validation
    print_flush("Testing Profile Validation:")
    print_flush("-" * 25)
    
    # Test missing required fields
    invalid_profile = {
        'profile_id': 'TEST_001',
        'name': 'Test Profile'
        # Missing other required fields
    }
    try:
        Profile.from_api_data(invalid_profile)
        print_flush("❌ Should have failed: Missing required fields")
    except ValueError as e:
        print_flush(f"✓ Correctly caught missing fields: {str(e)}")
    
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
        print_flush("❌ Should have failed: Invalid SLA value")
    except ValueError as e:
        print_flush(f"✓ Correctly caught invalid SLA value: {str(e)}")
    
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
        print_flush("❌ Should have failed: Negative sell price")
    except ValueError as e:
        print_flush(f"✓ Correctly caught negative sell price: {str(e)}")
    
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
        print_flush("❌ Should have failed: Invalid price range")
    except ValueError as e:
        print_flush(f"✓ Correctly caught invalid price range: {str(e)}")
    
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
        print_flush("❌ Should have failed: Negative average cost")
    except ValueError as e:
        print_flush(f"✓ Correctly caught negative average cost: {str(e)}")
    
    # Test Link Validation
    print_flush("\nTesting Link Validation:")
    print_flush("-" * 25)
    
    # Test missing required fields
    invalid_link = {
        'link': 'TEST_LINK_001',
        # Missing provider and buy_price
    }
    try:
        Link.from_api_data(invalid_link)
        print_flush("❌ Should have failed: Missing required fields")
    except ValueError as e:
        print_flush(f"✓ Correctly caught missing fields: {str(e)}")
    
    # Test invalid SLA value
    invalid_link = {
        'link': 'TEST_LINK_001',
        'provider': 'Test Provider',
        'buy_price': 10.0,
        'sla_dd': 150.0,  # Invalid: > 100%
        'tier': 1,
        'traffic': 25.0,
        'last_updated': '2025-05-22T15:00:00'
    }
    try:
        Link.from_api_data(invalid_link)
        print_flush("❌ Should have failed: Invalid SLA value")
    except ValueError as e:
        print_flush(f"✓ Correctly caught invalid SLA value: {str(e)}")
    
    # Test invalid traffic value
    invalid_link = {
        'link': 'TEST_LINK_001',
        'provider': 'Test Provider',
        'buy_price': 10.0,
        'sla_dd': 95.0,
        'tier': 1,
        'traffic': -10.0,  # Invalid: negative traffic
        'last_updated': '2025-05-22T15:00:00'
    }
    try:
        Link.from_api_data(invalid_link)
        print_flush("❌ Should have failed: Invalid traffic value")
    except ValueError as e:
        print_flush(f"✓ Correctly caught invalid traffic value: {str(e)}")
    
    # Test invalid tier value
    invalid_link = {
        'link': 'TEST_LINK_001',
        'provider': 'Test Provider',
        'buy_price': 10.0,
        'sla_dd': 95.0,
        'tier': 0,  # Invalid: tier must be positive
        'traffic': 25.0,
        'last_updated': '2025-05-22T15:00:00'
    }
    try:
        Link.from_api_data(invalid_link)
        print_flush("❌ Should have failed: Invalid tier value")
    except ValueError as e:
        print_flush(f"✓ Correctly caught invalid tier value: {str(e)}")
    
    # Test negative buy price
    invalid_link = {
        'link': 'TEST_LINK_001',
        'provider': 'Test Provider',
        'buy_price': -5.0,  # Invalid: negative price
        'sla_dd': 95.0,
        'tier': 1,
        'traffic': 25.0,
        'last_updated': '2025-05-22T15:00:00'
    }
    try:
        Link.from_api_data(invalid_link)
        print_flush("❌ Should have failed: Invalid buy price")
    except ValueError as e:
        print_flush(f"✓ Correctly caught negative buy price: {str(e)}")
    
    print_flush("\n✓ All validation tests completed")

if __name__ == "__main__":
    test_data_validation()