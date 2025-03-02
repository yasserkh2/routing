import json
import os
import asyncio
from datetime import datetime
from ..services.event_handler import EventHandler, EventType
from ..services.mock_services import MockAPIService

async def test_price_change_event():
    # Initialize services
    mock_api = MockAPIService()
    event_handler = EventHandler()

    # Read mock price change data
    mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
    with open(os.path.join(mock_data_dir, 'price_changes.json'), 'r') as f:
        price_changes = json.load(f)
    
    # Process the price change event
    price_change = price_changes[0]  # Get our single example
    
    # Create price change event
    event_data = {
        'link_id': price_change['reference_id'],  # Using LINK_001
        'old_price': price_change['old_rate'],
        'new_price': price_change['new_rate'],
        'provider': price_change['provider_name'],
        'network': price_change['network_name'],
        'mcc': price_change['mcc'],
        'mnc': price_change['mnc'],
        'sla_data': {
            'dd': price_change['sla_dd'],
            'tested': price_change['sla_tested'],
            'assumed': price_change['sla_assumed']
        },
        'timestamp': datetime.now().isoformat()
    }

    # Create event through event handler
    event = event_handler.create_event(
        EventType.PRICE_CHANGE,
        event_data
    )
    print(f"\nCreated price change event: {event}")

    # Handle price change through mock API service
    api_event = mock_api.handle_price_change(
        event_data['link_id'],
        event_data['new_price']
    )
    print(f"\nAPI handled price change: {api_event}")

    # Get updated link data to verify price change
    updated_links = await mock_api.get_links_sla_data(mnc=event_data['mnc'])
    print(f"\nUpdated link data: {json.dumps(updated_links, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_price_change_event())