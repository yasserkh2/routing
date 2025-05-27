import os
import json
import sys

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.models.link import Link
from datetime import datetime

def test_link_comprehensive():
    """Comprehensive test for Link class including labels, status, and data extraction"""
    print("\n" + "="*50)
    print("          COMPREHENSIVE LINK CLASS TEST")
    print("="*50 + "\n", flush=True)
    
    try:
        # PART 1: BASIC LINK CREATION AND PROPERTIES
        print("\n" + "="*40)
        print("PART 1: BASIC LINK CREATION AND PROPERTIES")
        print("="*40 + "\n", flush=True)
        
        # Create a basic link
        basic_link = Link(
            link="TestLink",
            provider="Test Provider",
            buy_price=0.15,
            sla_dd=95.0,
            tier=1,
            traffic=50.0,
            label="Test Link",
            status="in_use",
            last_updated=datetime.now()
        )
        
        print("Basic Link Properties:", flush=True)
        print(f"ID: {basic_link.link}", flush=True)
        print(f"Provider: {basic_link.provider}", flush=True)
        print(f"Buy Price: ${basic_link.buy_price}", flush=True)
        print(f"SLA DD: {basic_link.sla_dd}%", flush=True)
        print(f"Tier: {basic_link.tier}", flush=True)
        print(f"Traffic: {basic_link.traffic}%", flush=True)
        print(f"Label: {basic_link.label}", flush=True)
        print(f"Status: {basic_link.status}", flush=True)
        print(f"Last Updated: {basic_link.last_updated}", flush=True)
        
        # Test to_dict method
        link_dict = basic_link.to_dict()
        print("\nLink as Dictionary:", flush=True)
        for key, value in link_dict.items():
            print(f"{key}: {value}", flush=True)
        
        # Test to_optimizer_format method
        optimizer_format = basic_link.to_optimizer_format()
        print("\nLink in Optimizer Format:", flush=True)
        for key, value in optimizer_format.items():
            print(f"{key}: {value}", flush=True)
        
        # Test utility methods
        print("\nUtility Methods:", flush=True)
        print(f"Meets SLA Requirement (90%): {basic_link.meets_sla_requirement(90.0)}", flush=True)
        print(f"Meets SLA Requirement (98%): {basic_link.meets_sla_requirement(98.0)}", flush=True)
        print(f"Cost for 50% Traffic: ${basic_link.calculate_cost_for_traffic(50.0)}", flush=True)
        print(f"Cost for 100% Traffic: ${basic_link.calculate_cost_for_traffic(100.0)}", flush=True)
        
        # PART 2: LINK CREATION FROM API DATA
        print("\n" + "="*40)
        print("PART 2: LINK CREATION FROM API DATA")
        print("="*40 + "\n", flush=True)
        
        # Test in-use link
        in_use_data = {
            'link': 'ADA_Direct',
            'provider': 'ADA SINGAPORE PTE. LTD',
            'buy_price': 0.172,
            'sla_dd': 95.0,
            'tier': 1,
            'traffic': 100,
            'last_updated': '2025-03-10T13:20:15.505294'
        }
        
        in_use_link = Link.from_api_data(in_use_data)
        print("In-Use Link:", flush=True)
        print(f"ID: {in_use_link.link}", flush=True)
        print(f"Provider: {in_use_link.provider}", flush=True)
        print(f"Status: {in_use_link.status}", flush=True)
        print(f"Label: {in_use_link.label}", flush=True)
        print(f"Traffic: {in_use_link.traffic}%", flush=True)
        print(flush=True)
        
        # Test alternative link
        alt_data = {
            'link': 'STC_WL_Offnet70723',
            'provider': 'Saudi Telecom Company',
            'buy_price': 0.0213,
            'tier': 6,
            'last_updated': '2025-03-05T14:15:20.112934'
        }
        
        alt_link = Link.from_api_data(alt_data)
        print("Alternative Link:", flush=True)
        print(f"ID: {alt_link.link}", flush=True)
        print(f"Provider: {alt_link.provider}", flush=True)
        print(f"Status: {alt_link.status}", flush=True)
        print(f"Label: {alt_link.label}", flush=True)
        print(f"Traffic: {alt_link.traffic}%", flush=True)
        print(flush=True)
        
        # Test link with explicit status
        explicit_data = {
            'link': 'Ameex',
            'provider': 'Ameex',
            'buy_price': 0.1402,
            'status': 'in_use',
            'traffic': 0.0,  # Even though traffic is 0, status is explicitly set
            'last_updated': '2025-03-10T13:30:00.505294'
        }
        
        explicit_link = Link.from_api_data(explicit_data)
        print("Link with Explicit Status:", flush=True)
        print(f"ID: {explicit_link.link}", flush=True)
        print(f"Provider: {explicit_link.provider}", flush=True)
        print(f"Status: {explicit_link.status}", flush=True)
        print(f"Label: {explicit_link.label}", flush=True)
        print(f"Traffic: {explicit_link.traffic}%", flush=True)
        print(flush=True)
        
        # Test link with custom label
        custom_label_data = {
            'link': 'MTN_UK_USD',
            'provider': 'MTN HUB USD',
            'buy_price': 0.1782,
            'label': 'My Custom Link Label',
            'last_updated': '2025-03-15T10:00:00.000000'
        }
        
        custom_label_link = Link.from_api_data(custom_label_data)
        print("Link with Custom Label:", flush=True)
        print(f"ID: {custom_label_link.link}", flush=True)
        print(f"Provider: {custom_label_link.provider}", flush=True)
        print(f"Status: {custom_label_link.status}", flush=True)
        print(f"Label: {custom_label_link.label}", flush=True)
        print(f"Traffic: {custom_label_link.traffic}%", flush=True)
        
        # PART 3: ADVANCED LINK OPERATIONS
        print("\n" + "="*40)
        print("PART 3: ADVANCED LINK OPERATIONS")
        print("="*40 + "\n", flush=True)
        
        # Test with_updated_price method
        original_link = Link(
            link="PriceTestLink",
            provider="Price Test Provider",
            buy_price=0.10,
            sla_dd=90.0,
            tier=2,
            traffic=75.0,
            label="Price Test Link",
            status="in_use",
            last_updated=datetime.now()
        )
        
        # Update price
        new_price = 0.15
        updated_link = original_link.with_updated_price(new_price)
        
        print("Price Update Test:", flush=True)
        print(f"Original Price: ${original_link.buy_price}", flush=True)
        print(f"Updated Price: ${updated_link.buy_price}", flush=True)
        print(f"Last Updated Changed: {original_link.last_updated != updated_link.last_updated}", flush=True)
        
        # Test format_display_info method
        display_info = original_link.format_display_info(80.0, 0.12)
        print("\nDisplay Info Test:", flush=True)
        for key, value in display_info.items():
            print(f"{key}: {value}", flush=True)
        
        # Test error handling in from_api_data
        print("\nError Handling and Validation Tests:", flush=True)
        
        # Missing required fields
        try:
            Link.from_api_data({})
            print("Test Failed: Should have raised an error for missing required fields", flush=True)
        except ValueError as e:
            print(f"Test Passed: Correctly raised error for missing fields: {str(e)}", flush=True)
        
        # Invalid values
        try:
            Link.from_api_data({
                'link': 'TestLink',
                'provider': 'Test Provider',
                'buy_price': 'not a number'
            })
            print("Test Failed: Should have raised an error for invalid buy_price", flush=True)
        except ValueError as e:
            print(f"Test Passed: Correctly raised error for invalid value: {str(e)}", flush=True)
            
        # Test invalid SLA value
        try:
            Link.from_api_data({
                'link': 'TEST_LINK_001',
                'provider': 'Test Provider',
                'buy_price': 10.0,
                'sla_dd': 150.0,  # Invalid: > 100%
                'tier': 1,
                'traffic': 25.0,
                'last_updated': '2025-05-22T15:00:00'
            })
            print("Test Failed: Should have raised an error for invalid SLA value", flush=True)
        except ValueError as e:
            print(f"Test Passed: Correctly caught invalid SLA value: {str(e)}", flush=True)
        
        # Test invalid traffic value
        try:
            Link.from_api_data({
                'link': 'TEST_LINK_001',
                'provider': 'Test Provider',
                'buy_price': 10.0,
                'sla_dd': 95.0,
                'tier': 1,
                'traffic': -10.0,  # Invalid: negative traffic
                'last_updated': '2025-05-22T15:00:00'
            })
            print("Test Failed: Should have raised an error for invalid traffic value", flush=True)
        except ValueError as e:
            print(f"Test Passed: Correctly caught invalid traffic value: {str(e)}", flush=True)
        
        # Test invalid tier value
        try:
            Link.from_api_data({
                'link': 'TEST_LINK_001',
                'provider': 'Test Provider',
                'buy_price': 10.0,
                'sla_dd': 95.0,
                'tier': 0,  # Invalid: tier must be positive
                'traffic': 25.0,
                'last_updated': '2025-05-22T15:00:00'
            })
            print("Test Failed: Should have raised an error for invalid tier value", flush=True)
        except ValueError as e:
            print(f"Test Passed: Correctly caught invalid tier value: {str(e)}", flush=True)
        
        # Test negative buy price
        try:
            Link.from_api_data({
                'link': 'TEST_LINK_001',
                'provider': 'Test Provider',
                'buy_price': -5.0,  # Invalid: negative price
                'sla_dd': 95.0,
                'tier': 1,
                'traffic': 25.0,
                'last_updated': '2025-05-22T15:00:00'
            })
            print("Test Failed: Should have raised an error for invalid buy price", flush=True)
        except ValueError as e:
            print(f"Test Passed: Correctly caught negative buy price: {str(e)}", flush=True)
        
        print("\nAll Link Tests Completed Successfully!", flush=True)
        
    except Exception as e:
        print(f"Error during link test: {str(e)}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)

if __name__ == "__main__":
    test_link_comprehensive()