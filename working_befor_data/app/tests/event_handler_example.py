import asyncio
from ..services.event_handler import EventHandler, EventType, Event
from ..api.api_caller import APICaller
from ..api.api_interfaces import APIClient, APIResponse
from typing import Dict, Any

import os
import json

# Read test data from mock directory
mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
with open(os.path.join(mock_data_dir, 'price_changes.json'), 'r') as f:
    MOCK_EVENT_DATA = json.load(f)

async def handle_price_change(event: Event) -> None:
    """
    Handler for price update events that demonstrates:
    1. Query1: GetProfilesRelatedToLink(link, mnc)
    2. Query2: GetLinksSLAByMNC(mnc)
    3. Query3: GetProfilesWithLinks()
    """
    print(f"\nProcessing price update event:")
    print(f"Link: {event.link}")
    print(f"MCC: {event.mcc}")
    print(f"MNC: {event.mnc}")
    print(f"Price Change: ${event.payload['old_rate']:.4f} -> ${event.payload['new_rate']:.4f}")
    print(f"Status: {event.payload['status']}")
    print(f"Timestamp: {event.timestamp}")
    
    # Create API caller
    api_caller = APICaller()
    
    print("\nExecuting all API calls...")
    results = await api_caller.call_all_apis(event)
    
    # Process results
    print("\nEvent Details:")
    print(f"Type: {event.type}")
    print(f"Link: {event.link}")
    print(f"MCC/MNC: {event.mcc}/{event.mnc}")
    print(f"Price Change: ${event.payload['old_rate']:.2f} -> ${event.payload['new_rate']:.2f}")
    print(f"Status: {event.payload['status']}")
    print(f"Timestamp: {event.timestamp}")

    print("\nLinks Data:")
    if 'links_data' in results:
        links_response = results['links_data']
        print(f"Timestamp: {links_response.timestamp}")
        if links_response.success:
            print(f"Total Links: {len(links_response.data)}")
            for link in links_response.data:
                print(f"\nLink: {link['link']}")
                print(f"Operator: {link['operator']}")
                print(f"MNC: {link['mnc']}")
                print(f"Provider: {link['provider']}")
                print(f"Price: ${link['price']}")
                print("SLA Data:")
                print(f"  SLA DD: {link['sla_dd'] if link['sla_dd'] is not None else 'Not Available'}")
                print(f"  SLA Tested: {link['sla_tested'] if link['sla_tested'] is not None else 'Not Available'}")
                print(f"  SLA Assumed: {link['sla_assumed'] if link['sla_assumed'] is not None else 'Not Available'}")
                print(f"Last Updated: {link['last_updated']}")
        else:
            print(f"Error getting links data: {links_response.error}")

    print("\nProfile Configurations:")
    if 'profile_config' in results:
        profile_response = results['profile_config']
        print(f"Timestamp: {profile_response.timestamp}")
        if profile_response.success:
            print(f"Total Profiles: {len(profile_response.data)}")
            for profile in profile_response.data:
                print(f"\nProfile: {profile['name']}")
                print(f"ID: {profile['profile_id']}")
                print(f"Description: {profile['description']}")
                print(f"Expected SLA: {profile['expected_sla']}%")
                print(f"Sell Price: ${profile['sell_price']}")
                print("Links:")
                for link in profile['links']:
                    print(f"  - {link}")
        else:
            print(f"Error getting profile data: {profile_response.error}")

async def main():
    try:
        print("\nStarting event handler example...")
        
        # Create event handler
        handler = EventHandler()
        print("Event handler created successfully")

        # Register price update handler
        print("Registering price update handler...")
        handler.register_handler("PriceUpdate", handle_price_change, is_async=True)
        print("Handler registered successfully")

        # Create price update event
        print("\nCreating price update event...")
        try:
            price_update_event = handler.create_event(MOCK_EVENT_DATA)
            print("Event created successfully")
        except Exception as e:
            print(f"Error creating event: {str(e)}")
            raise

        # Process the event
        print("\nProcessing event...")
        try:
            await handler.handle_event(price_update_event)
            print("Event processed successfully")
        except Exception as e:
            print(f"Error processing event: {str(e)}")
            raise

    except Exception as e:
        print(f"\nError in main: {str(e)}")
        raise

    # Print event metadata
    print("\nEvent Processing Metadata:")
    print(f"Event Type: {price_update_event.type}")
    print(f"Link: {price_update_event.link}")
    print(f"MCC/MNC: {price_update_event.mcc}/{price_update_event.mnc}")
    print(f"Timestamp: {price_update_event.timestamp}")

    print("\nImplemented API Queries:")
    print("1. Query1 - GetProfilesRelatedToLink(link, mnc)")
    print("   - Gets profiles associated with a specific link and MNC")
    print("   - Shows expected SLA per profile")
    print("   - Includes link-specific information")
    print("\n2. Query2 - GetLinksSLAByMNC(mnc)")
    print("   - Gets all links for an MNC with their SLA data")
    print("   - Shows SLA from different sources:")
    print("     * DataDog (current performance)")
    print("     * Auto Router V1 (testing results)")
    print("     * Tiering (assumed values)")
    print("\n3. Query3 - GetProfilesWithLinks()")
    print("   - Gets all profiles with their associated links")
    print("   - Shows which links are used by each profile")
    print("   - Includes routing priorities and status")

if __name__ == "__main__":
    asyncio.run(main())
