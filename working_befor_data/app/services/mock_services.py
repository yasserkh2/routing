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
        self.sla_updates = {}    # Store SLA updates
    
    def _read_json_file(self, filename: str) -> Dict:
        """Helper method to read JSON files from mock_data directory"""
        file_path = os.path.join(self.mock_data_dir, filename)
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def handle_price_change(self, link_name: str, new_price: float, old_price: Optional[float] = None) -> Event:
        """Handle price change event for a link"""
        # Create price change event
        event_data = {
            'link': link_name,
            'old_price': old_price,
            'new_price': new_price,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Get current link data for metadata only
            links_data = self._read_json_file('links_data.json')
            for link in links_data:
                if link['link'] == link_name:
                    # Keep track of the old price
                    if old_price is None:
                        old_price = link['price']
                    event_data['old_price'] = old_price
                    event_data['operator'] = link['operator']
                    event_data['mnc'] = link['mnc']
                    event_data['mcc'] = link.get('mcc', '426')  # Default to 426 if not found
                    break
            
            # Store price changes in memory only for simulation
            self.price_updates[link_name] = {
                'old_price': old_price,
                'new_price': new_price
            }
            
            # Prepare event data with required fields
            event_data['Type'] = EventType.PRICE_UPDATE.value
            event_data['Payload'] = {
                'old_price': event_data.pop('old_price'),
                'new_price': event_data.pop('new_price')
            }
            
            # Create and return event
            return self.event_handler.create_event(event_data)
            
        except Exception as e:
            print(f"Error handling price change: {e}")
            return None
    
    def handle_sla_change(self, link_name: str, changed_sla: Dict[str, Dict[str, float]]) -> Event:
        """Handle SLA change event for a link"""
        try:
            print(f"Reading links data for SLA change on {link_name}")
            # Get current link data
            links_data = self._read_json_file('links_data.json')
            print(f"Found {len(links_data)} links")
            event_data = {
                'link': link_name,
                'timestamp': datetime.now().isoformat()
            }
            print(f"Event data initialized: {event_data}")
            
            link_found = False
            for link in links_data:
                if link['link'] == link_name:
                    print(f"Found matching link: {link}")
                    link_found = True
                    # Just store metadata for event, don't modify link data
                    event_data['operator'] = link['operator']
                    event_data['mnc'] = link['mnc']
                    event_data['mcc'] = link.get('mcc', '426')  # Default to 426 if not found
                    break
            
            if not link_found:
                print(f"Link {link_name} not found in links_data")
                raise ValueError(f"Link {link_name} not found")
            
            # Store SLA changes in memory for simulation only
            self.sla_updates[link_name] = changed_sla
            
            # Prepare event data
            event_data['Type'] = EventType.SLA_UPDATE.value
            event_data['Payload'] = {
                'changed_sla': changed_sla,
                'status': 'Increased' if all(v['new'] > v['old'] for v in changed_sla.values()) else 'Mixed'
            }
            
            # Create and return event
            return self.event_handler.create_event(event_data)
            
        except Exception as e:
            print(f"Error handling SLA change: {e}")
            return None

    async def get_links_sla_data(self, mnc: Optional[str] = None) -> List[Dict]:
        """Get SLA data for links"""
        try:
            # Get base data
            data = self._read_json_file('links_data.json')
            
            # Create a deep copy of data for simulation
            import copy
            simulation_data = copy.deepcopy(data)
            
            # Apply any price and SLA updates to the copy
            for link in simulation_data:
                # Apply price updates
                if link['link'] in self.price_updates:
                    update = self.price_updates[link['link']]
                    link['price'] = update['new_price']
                    print(f"Applied price update for {link['link']}: ${link['price']} (was ${update['old_price']})")
                
                # Apply SLA updates
                if link['link'] in self.sla_updates:
                    update = self.sla_updates[link['link']]
                    for sla_type, values in update.items():
                        if sla_type == 'DD':
                            link['sla_dd'] = values['new']
                        elif sla_type == 'Tested':
                            link['sla_tested'] = values['new']
                        elif sla_type == 'Assumed':
                            link['sla_assumed'] = values['new']
                    print(f"Applied SLA updates for {link['link']}")
            
            # Filter by MNC if provided
            if mnc:
                simulation_data = [link for link in simulation_data if link['mnc'] == mnc]
                
            return simulation_data
            
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