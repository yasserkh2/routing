import asyncio
from event_handler import EventHandler, EventType, Event, EventPriority
from api_selector import APISelector
from api_strategy import MockAPIClient

# Mock price update event data
MOCK_EVENT_DATA = {
    "Type": "PriceUpdate",
    "Payload": {
        "old_rate": 0.2050,
        "new_rate": 0.15,
        "status": "Decreased"
    },
    "link": "LINK_001",
    "mcc": "426",
    "mnc": "21",
    "timestamp": "2025-03-03T12:40:00.000Z"
}

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
    
    # Create API selector with mock client
    api_client = MockAPIClient()
    api_selector = APISelector(api_client=api_client)
    
    # Analyze which APIs will be called
    analysis = api_selector.analyze_strategies(event)
    print("\nAPI Strategy Analysis:")
    print(f"Event Type: {analysis['event_type']}")
    print(f"APIs to call: {', '.join(analysis['strategies'])}")
    
    # Execute API calls
    print("\nExecuting API calls...")
    results = await api_selector.execute_strategies(event)
    
    # Process results
    print("\nRoute Details:")
    if 'RouteDetailsAPIStrategy' in results:
        route_data = results['RouteDetailsAPIStrategy']
        print(f"Operator: {route_data['network']} ({route_data['operator_id']})")
        print(f"Country: {route_data['country']}")
        print(f"Quality Score: {route_data['quality_score']}")
        print(f"Active: {route_data['active']}")
        print(f"MNC: {route_data['mnc']}")

    print("\nQuery1 - GetProfilesRelatedToLink Results:")
    if 'GetProfilesRelatedToLinkStrategy' in results:
        profiles_data = results['GetProfilesRelatedToLinkStrategy']
        print(f"Link: {profiles_data['link']}")
        print(f"MNC: {profiles_data['mnc']}")
        print("\nProfiles for this Link:")
        for profile in profiles_data['profiles']:
            print(f"\nProfile: {profile['name']}")
            print(f"ID: {profile['profile_id']}")
            print(f"Expected SLA: {profile['expected_sla']}%")
            print(f"Priority: {profile['priority']}")
            print("Link Information:")
            link_info = profile['link_info']
            print(f"  Active: {link_info['is_active']}")
            print(f"  Last Used: {link_info['last_used']}")
            print(f"  Routing Priority: {link_info['routing_priority']}")

    print("\nQuery2 - GetLinksSLAByMNC Results:")
    if 'GetLinksSLAByMNCStrategy' in results:
        links_data = results['GetLinksSLAByMNCStrategy']
        print(f"MNC: {links_data['mnc']}")
        print("\nLinks SLA Data:")
        for link in links_data['links']:
            print(f"\nLink: {link['link']}")
            print(f"Operator: {link['operator']}")
            print(f"MNC: {link['mnc']}")
            print("SLA Data:")
            sla = link['sla_data']
            print(f"  SLA DD: {sla['sla_dd'] if sla['sla_dd'] is not None else 'Not Available'}")
            print(f"  SLA Tested: {sla['sla_tested'] if sla['sla_tested'] is not None else 'Not Available'}")
            print(f"  SLA Assumed: {sla['sla_assumed'] if sla['sla_assumed'] is not None else 'Not Available'}")
            print(f"  Last Updated: {sla['last_updated']}")

    print("\nQuery3 - GetProfilesWithLinks Results:")
    if 'GetProfilesWithLinksStrategy' in results:
        profiles_links_data = results['GetProfilesWithLinksStrategy']
        print("\nProfiles and their Associated Links:")
        for profile in profiles_links_data['profiles']:
            print(f"\nProfile: {profile['name']}")
            print(f"ID: {profile['profile_id']}")
            print(f"Expected SLA: {profile['expected_sla']}%")
            print(f"Priority: {profile['priority']}")
            print("\nAssociated Links:")
            for link in profile['links']:
                print(f"\n  Link: {link['link']}")
                print(f"  Operator: {link['operator']}")
                print(f"  MNC: {link['mnc']}")
                print(f"  Routing Priority: {link['routing_priority']}")
                print(f"  Active: {link['is_active']}")
                print(f"  Last Used: {link['last_used']}")

async def main():
    # Create event handler
    handler = EventHandler()

    # Register price update handler
    handler.register_handler("PriceUpdate", handle_price_change, is_async=True)

    # Create price update event
    price_update_event = handler.create_event(MOCK_EVENT_DATA)

    # Process the event
    await handler.handle_event(price_update_event)

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