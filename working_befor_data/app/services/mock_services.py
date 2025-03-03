import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from .event_handler import EventHandler, EventType, Event

class MockAPIService:
    """Main service to coordinate all mock APIs"""
    
    def __init__(self):
        self.mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
        self.event_handler = EventHandler()
        self.price_updates = {}  # Store price updates
    
    def _read_json_file(self, filename: str) -> Dict:
        """Helper method to read JSON files from mock_data directory"""
        file_path = os.path.join(self.mock_data_dir, filename)
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def handle_price_change(self, link_id: str, new_price: float, old_price: Optional[float] = None) -> Event:
        """Handle price change event for a link"""
        # Create price change event
        event_data = {
            'link_id': link_id,
            'old_price': old_price,
            'new_price': new_price,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Get current link data
            links_data = self._read_json_file('links_data.json')
            for link in links_data:
                if link['link_id'] == link_id:
                    # Keep track of the old price
                    if old_price is None:
                        old_price = link['price']
                    event_data['old_price'] = old_price
                    event_data['operator'] = link['operator']
                    event_data['mnc'] = link['mnc']
                    # Update price in links_data
                    link['price'] = new_price
                    link['last_updated'] = datetime.now().isoformat()
                    break
            
            # Write updated data back to file
            file_path = os.path.join(self.mock_data_dir, 'links_data.json')
            with open(file_path, 'w') as f:
                json.dump(links_data, f, indent=4)
            
            # Store both old and new prices in memory
            self.price_updates[link_id] = {
                'old_price': old_price,
                'new_price': new_price
            }
            
            # Create and return event
            return self.event_handler.create_event(
                EventType.PRICE_CHANGE,
                event_data
            )
            
        except Exception as e:
            print(f"Error handling price change: {e}")
            return None
    
    async def get_links_sla_data(self, mnc: Optional[str] = None) -> List[Dict]:
        """Get SLA data for links"""
        try:
            # Get base data
            data = self._read_json_file('links_data.json')
            
            # Apply any price updates
            for link in data:
                if link['link_id'] in self.price_updates:
                    update = self.price_updates[link['link_id']]
                    link['price'] = update['new_price']
                    print(f"Applied price update for {link['link_id']}: ${link['price']} (was ${update['old_price']})")
            
            # Filter by MNC if provided
            if mnc:
                data = [link for link in data if link['mnc'] == mnc]
                
            return data
            
        except Exception as e:
            print(f"Error reading links data: {e}")
            return []
    
    async def get_profile_config(self, profile_id: Optional[str] = None) -> List[Dict]:
        """Get profile configurations"""
        try:
            data = self._read_json_file('profiles.json')
            if profile_id:
                data = [p for p in data if p['profile_id'] == profile_id]
            return data
        except Exception as e:
            print(f"Error reading profile data: {e}")
            return []