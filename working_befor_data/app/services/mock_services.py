import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from .event_handler import EventHandler, EventType, Event
from ..utils.logger import setup_logger
from ..api.api import API

# Setup logger
logger = setup_logger(__name__)

class MockAPIService(API):
    """Main service to coordinate all mock APIs"""
    
    def __init__(self):
        self.mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
        self.event_handler = EventHandler()
        self.price_updates = {}  # Store price updates
        self.sla_updates = {}    # Store SLA updates
        logger.info(f"MockAPIService initialized with mock data directory: {self.mock_data_dir}")
    
    def _read_json_file(self, filename: str) -> Dict:
        """Helper method to read JSON files from mock_data directory"""
        file_path = os.path.join(self.mock_data_dir, filename)
        logger.debug(f"Reading JSON file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            logger.debug(f"Successfully read JSON file: {filename}")
            return data
        except Exception as e:
            logger.error(f"Failed to read JSON file {filename}: {str(e)}", exc_info=True)
            raise
    
    async def get_combined_data(self) -> List[Dict]:
        """Get combined profile and link data"""
        try:
            # Get base data
            data = self._read_json_file('api_round_2_reorganized_links_no_sla.json')
            
            # Transform data to the expected format
            simulation_data = []
            
            # Process each profile
            for profile in data.get('profiles', []):
                # Create a profile entry with in_use_links from the profile
                profile_entry = {
                    'profile_id': profile['profile_id'],
                    'name': profile['name'],
                    'mcc': profile['mcc'],
                    'mnc': profile['mnc'],
                    'expected_sla': profile['expected_sla'],
                    'description': profile['description'],
                    'sell_price_min': profile['sell_price_min'],
                    'sell_price_max': profile['sell_price_max'],
                    'profile_avg_cost': profile.get('ProfileAvgCostUSD', 0.0),
                    'in_use_links': profile.get('in_use_links', []),
                    'alternative_links': []
                }
                
                # Add alternative links to the profile
                # We'll add all alternative links to each profile for testing purposes
                for alt_link in data.get('alternative_links', []):
                    # Convert base_buy_price to buy_price for consistency
                    alt_link_copy = alt_link.copy()
                    if 'base_buy_price' in alt_link_copy:
                        alt_link_copy['buy_price'] = alt_link_copy.pop('base_buy_price')
                    profile_entry['alternative_links'].append(alt_link_copy)
                
                simulation_data.append(profile_entry)
            
            # Create a deep copy for simulation
            import copy
            simulation_data = copy.deepcopy(simulation_data)
            
            # Apply any price and SLA updates
            for profile in simulation_data:
                # Update in_use_links
                for link in profile['in_use_links']:
                    if link['link'] in self.price_updates:
                        update = self.price_updates[link['link']]
                        link['buy_price'] = update['new_price']
                        logger.info(f"Applied price update for {link['link']}: ${link['buy_price']} (was ${update['old_price']})")
                    
                    if link['link'] in self.sla_updates:
                        update = self.sla_updates[link['link']]
                        if 'DD' in update:
                            link['sla_dd'] = update['DD']['new']
                        logger.info(f"Applied SLA update for {link['link']}: {update}")
                
                # Update alternative_links
                for link in profile['alternative_links']:
                    if link['link'] in self.price_updates:
                        update = self.price_updates[link['link']]
                        link['buy_price'] = update['new_price']
                        logger.info(f"Applied price update for {link['link']}: ${link['buy_price']} (was ${update['old_price']})")
            
            return simulation_data
            
        except Exception as e:
            logger.error(f"Error reading combined data: {str(e)}", exc_info=True)
            return []
    
    async def get_links_data(self, mnc: Optional[str] = None) -> List[Dict]:
        """Get comprehensive data for links (legacy method)"""
        try:
            # Get data from new format
            combined_data = await self.get_combined_data()
            
            # Extract and flatten all links
            links = []
            for profile in combined_data:
                profile_mnc = profile['mnc']
                if mnc is None or profile_mnc == mnc:
                    # Add in_use_links
                    for link in profile['in_use_links']:
                        links.append({
                            'link': link['link'],
                            'operator': link['provider'],
                            'mnc': profile_mnc,
                            'price': link['buy_price'],
                            'sla_dd': link['sla_dd'],
                            'tier': link['tier']
                        })
                    
                    # Add alternative_links
                    for link in profile['alternative_links']:
                        links.append({
                            'link': link['link'],
                            'operator': link['provider'],
                            'mnc': profile_mnc,
                            'price': link['buy_price'],
                            'tier': link['tier']
                        })
            
            # Remove duplicates (same link might appear in multiple profiles)
            unique_links = []
            seen_links = set()
            for link in links:
                if link['link'] not in seen_links:
                    seen_links.add(link['link'])
                    unique_links.append(link)
            
            return unique_links
            
        except Exception as e:
            logger.error(f"Error getting links data: {str(e)}", exc_info=True)
            return []
    
    async def get_profile_config(self, profile_id: Optional[str] = None) -> List[Dict]:
        """Get profile configurations (legacy method)"""
        try:
            # Get data from new format
            combined_data = await self.get_combined_data()
            
            # Filter and convert to old format
            profiles = []
            for profile_data in combined_data:
                if profile_id is None or profile_data['profile_id'] == profile_id:
                    # Get all links for this profile
                    links = []
                    for link in profile_data['in_use_links']:
                        links.append(link['link'])
                    for link in profile_data['alternative_links']:
                        links.append(link['link'])
                    
                    profiles.append({
                        'profile_id': profile_data['profile_id'],
                        'name': profile_data['name'],
                        'expected_sla': profile_data['expected_sla'],
                        'links': links
                    })
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error getting profile config: {str(e)}", exc_info=True)
            return []
    
    def handle_price_change(self, link_name: str, new_price: float, old_price: Optional[float] = None) -> Event:
        """Handle price change event for a link"""
        try:
            logger.info(f"Processing price change for link: {link_name}")
            # Get current data
            data = self._read_json_file('api_round_2_reorganized_links_no_sla.json')
            
            event_data = {
                'link': link_name,
                'timestamp': datetime.now().isoformat()
            }
            
            # Find the link in any profile's in_use_links or alternative_links
            link_found = False
            for profile in data:
                # Check in_use_links
                for link in profile['in_use_links']:
                    if link['link'] == link_name:
                        link_found = True
                        if old_price is None:
                            old_price = link['buy_price']
                        event_data.update({
                            'provider': link['provider'],
                            'mcc': profile['mcc'],
                            'mnc': profile['mnc']
                        })
                        break
                
                # Check alternative_links if not found
                if not link_found:
                    for link in profile['alternative_links']:
                        if link['link'] == link_name:
                            link_found = True
                            if old_price is None:
                                old_price = link['buy_price']
                            event_data.update({
                                'provider': link['provider'],
                                'mcc': profile['mcc'],
                                'mnc': profile['mnc']
                            })
                            break
                
                if link_found:
                    break
            
            if not link_found:
                error_msg = f"Link {link_name} not found in any profile"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Store price changes in memory for simulation
            self.price_updates[link_name] = {
                'old_price': old_price,
                'new_price': new_price
            }
            
            # Prepare event data
            event_data['Type'] = EventType.PRICE_UPDATE.value
            event_data['Payload'] = {
                'old_price': old_price,
                'new_price': new_price
            }
            
            # Create and return event
            return self.event_handler.create_event(event_data)
            
        except Exception as e:
            logger.error(f"Error handling price change for link {link_name}: {str(e)}", exc_info=True)
            return None
    
    def handle_sla_change(self, link_name: str, changed_sla: Dict[str, Dict[str, float]]) -> Event:
        """Handle SLA change event for a link"""
        try:
            logger.info(f"Processing SLA change for link: {link_name}")
            # Get current data
            data = self._read_json_file('api_round_2_reorganized_links_no_sla.json')
            
            event_data = {
                'link': link_name,
                'timestamp': datetime.now().isoformat()
            }
            
            # Find the link in any profile's in_use_links
            link_found = False
            for profile in data:
                for link in profile['in_use_links']:
                    if link['link'] == link_name:
                        link_found = True
                        event_data.update({
                            'provider': link['provider'],
                            'mcc': profile['mcc'],
                            'mnc': profile['mnc']
                        })
                        break
                if link_found:
                    break
            
            if not link_found:
                error_msg = f"Link {link_name} not found in any profile's in_use_links"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Store SLA changes in memory for simulation
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
            logger.error(f"Error handling SLA change for link {link_name}: {str(e)}", exc_info=True)
            return None