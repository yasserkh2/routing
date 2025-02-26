import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from .event_handler import EventHandler, EventType, validate_route_data, validate_sla_data, log_event

class MockAPIService:
    """Main service to coordinate all mock APIs"""
    
    def __init__(self):
        self.mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mock_data')
        self.event_handler = EventHandler()
        
        # Register default handlers
        self.event_handler.register_handler(EventType.ROUTE_UPDATE, validate_route_data)
        self.event_handler.register_handler(EventType.SLA_UPDATE, validate_sla_data)
        self.event_handler.register_handler(EventType.CUSTOM, log_event)
        
    def _read_json_file(self, filename: str) -> Dict:
        """Helper method to read JSON files from mock_data directory"""
        file_path = os.path.join(self.mock_data_dir, filename)
        with open(file_path, 'r') as f:
            return json.load(f)
            
    def _write_json_file(self, filename: str, data: Dict):
        """Helper method to write JSON files to mock_data directory"""
        file_path = os.path.join(self.mock_data_dir, filename)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_routes_with_sla(self,
                           product_name: Optional[str] = None,
                           mcc: Optional[str] = None,
                           mnc: Optional[str] = None) -> List[Dict]:
        """Get routes with their SLA information from all sources"""
        # Create and handle event before processing
        event_data = {
            'product_name': product_name,
            'mcc': mcc,
            'mnc': mnc,
            'operation': 'get_routes_with_sla'
        }
        event = self.event_handler.create_event(EventType.ROUTE_UPDATE, event_data)
        self.event_handler.handle_event(event)
        
        routes = self._read_json_file('routes.json')
        filtered_routes = routes
        
        if product_name:
            filtered_routes = [r for r in filtered_routes if r['product_name'] == product_name]
        if mcc:
            filtered_routes = [r for r in filtered_routes if r['mcc'] == mcc]
        if mnc:
            filtered_routes = [r for r in filtered_routes if r['mnc'] == mnc]
            
        return filtered_routes
    
    def get_profiles(self) -> List[Dict]:
        """Get unique profiles with their route information"""
        data = self._read_json_file('profiles.json')
        return data['profiles']

    def get_available_profiles(self, network: Optional[Dict] = None) -> Dict:
        """Get available profiles with their network coverage"""
        profiles = self._read_json_file('available_profiles.json')
        if network:
            filtered_profiles = []
            for profile in profiles:
                for net in profile['networks']:
                    if (not network.get('mcc') or net['mcc'] == network['mcc']) and \
                       (not network.get('mnc') or net['mnc'] == network['mnc']):
                        filtered_profiles.append(profile)
                        break
            return {
                'count': len(filtered_profiles),
                'profiles': filtered_profiles
            }
        return {
            'count': len(profiles),
            'profiles': profiles
        }
    
    def get_profile_sla(self, product_name: Optional[str] = None) -> Dict:
        """Get SLA expectations and thresholds for products"""
        data = self._read_json_file('profile_sla.json')
        if product_name:
            filtered_profiles = [p for p in data['profiles'] if p['product_name'] == product_name]
            return {
                'count': len(filtered_profiles),
                'profiles': filtered_profiles
            }
        return data

    def get_links_sla(self,
                        product_name: Optional[str] = None,
                        status: Optional[str] = None,
                        network: Optional[Dict] = None,
                        provider: Optional[str] = None) -> Dict:
        """Get SLA measurements for links grouped by profile"""
        # Create and handle event before processing
        event_data = {
            'product_name': product_name,
            'status': status,
            'network': network,
            'provider': provider,
            'operation': 'get_links_sla'
        }
        event = self.event_handler.create_event(EventType.SLA_UPDATE, event_data)
        self.event_handler.handle_event(event)
        
        links = self._read_json_file('links_sla.json')
        filtered_links = links

        if product_name:
            filtered_links = [l for l in filtered_links if l['product_name'] == product_name]
        
        if status:
            filtered_links = [l for l in filtered_links if l['status'] == status]
        
        if network:
            filtered_links = [l for l in filtered_links
                            if (not network.get('mcc') or l['mcc'] == network['mcc']) and
                               (not network.get('mnc') or l['mnc'] == network['mnc'])]
        
        if provider:
            filtered_links = [l for l in filtered_links if l['provider'] == provider]

        # Group links by product
        products = {}
        for link in filtered_links:
            product = link['product_name']
            if product not in products:
                products[product] = []
            products[product].append(link)

        filtered_profiles = []
        for product_name, product_links in products.items():
            dd_values = [l['sla_dd'] for l in product_links if l['sla_dd'] is not None]
            tested_values = [l['sla_tested'] for l in product_links if l['sla_tested'] is not None]
            
            filtered_profile = {
                'product_name': product_name,
                'links': product_links,
                'sla_summary': {
                    'total_links': len(product_links),
                    'dd_coverage': round(len(dd_values) / len(product_links) * 100, 2),
                    'test_coverage': round(len(tested_values) / len(product_links) * 100, 2),
                    'average_dd': round(sum(dd_values) / len(dd_values), 2) if dd_values else 0,
                    'average_tested': round(sum(tested_values) / len(tested_values), 2) if tested_values else 0,
                    'average_assumed': round(sum(l['sla_assumed'] for l in product_links) / len(product_links), 2)
                }
            }
            filtered_profiles.append(filtered_profile)

        # Calculate overall summary
        if filtered_links:
            status_dist = {
                'Healthy': sum(1 for l in filtered_links if l['status'] == 'Healthy'),
                'Warning': sum(1 for l in filtered_links if l['status'] == 'Warning'),
                'Critical': sum(1 for l in filtered_links if l['status'] == 'Critical')
            }

            dd_values = [l['sla_dd'] for l in filtered_links if l['sla_dd'] is not None]
            tested_values = [l['sla_tested'] for l in filtered_links if l['sla_tested'] is not None]

            network_dist = {}
            for link in filtered_links:
                key = link['network_name']
                if key not in network_dist:
                    network_dist[key] = {
                        'mcc': link['mcc'],
                        'mnc': link['mnc'],
                        'links': 0
                    }
                network_dist[key]['links'] += 1

            provider_dist = {}
            for link in filtered_links:
                provider = link['provider']
                provider_dist[provider] = provider_dist.get(provider, 0) + 1

            summary = {
                'total_profiles': len(filtered_profiles),
                'total_links': len(filtered_links),
                'status_distribution': status_dist,
                'sla_coverage': {
                    'dd_coverage': round(len(dd_values) / len(filtered_links) * 100, 2),
                    'test_coverage': round(len(tested_values) / len(filtered_links) * 100, 2),
                    'average_dd': round(sum(dd_values) / len(dd_values), 2) if dd_values else 0,
                    'average_tested': round(sum(tested_values) / len(tested_values), 2) if tested_values else 0,
                    'average_assumed': round(sum(l['sla_assumed'] for l in filtered_links) / len(filtered_links), 2)
                },
                'network_distribution': network_dist,
                'provider_distribution': provider_dist
            }
        else:
            summary = {
                'total_profiles': 0,
                'total_links': 0,
                'status_distribution': {'Healthy': 0, 'Warning': 0, 'Critical': 0},
                'sla_coverage': {
                    'dd_coverage': 0,
                    'test_coverage': 0,
                    'average_dd': 0,
                    'average_tested': 0,
                    'average_assumed': 0
                },
                'network_distribution': {},
                'provider_distribution': {}
            }

        return {
            'count': len(filtered_profiles),
            'profiles': filtered_profiles,
            'summary': summary
        }
    
    def get_route_sla(self, mcc: str, mnc: str, product_name: Optional[str] = None) -> Dict:
        """Get SLA data for specific route"""
        data = self._read_json_file('route_sla.json')
        
        if product_name:
            if product_name in data['products']:
                return {
                    'mcc': data['mcc'],
                    'mnc': data['mnc'],
                    'products': {product_name: data['products'][product_name]}
                }
            return None
        return data
    
    def get_summary(self) -> Dict:
        """Get routes summary statistics"""
        return self._read_json_file('summary.json')
    
    def get_price_changes(self,
                         status: Optional[str] = None,
                         min_margin: Optional[float] = None,
                         max_margin: Optional[float] = None) -> Dict:
        """Get routes with price changes"""
        routes = self._read_json_file('price_changes.json')
        filtered_routes = routes
        
        if status:
            filtered_routes = [r for r in filtered_routes if r['price_change_status'] == status]
        if min_margin is not None:
            filtered_routes = [r for r in filtered_routes if r['margin_percentage'] >= min_margin]
        if max_margin is not None:
            filtered_routes = [r for r in filtered_routes if r['margin_percentage'] <= max_margin]
        
        # Recalculate summary for filtered routes
        if len(filtered_routes) > 0:
            summary = {
                'increased_count': sum(1 for r in filtered_routes if r['price_change_status'] == "Increased"),
                'decreased_count': sum(1 for r in filtered_routes if r['price_change_status'] == "Decreased"),
                'average_margin': round(sum(r['margin_percentage'] for r in filtered_routes) / len(filtered_routes), 2)
            }
        else:
            summary = {
                'increased_count': 0,
                'decreased_count': 0,
                'average_margin': 0
            }
            
        return {
            'count': len(filtered_routes),
            'routes': filtered_routes,
            'summary': summary
        }
    
    def refresh_mock_data(self):
        """Reset mock data to original state"""
        # Create and handle refresh event
        event_data = {
            'operation': 'refresh_mock_data',
            'timestamp': datetime.now().isoformat()
        }
        event = self.event_handler.create_event(EventType.DATA_REFRESH, event_data)
        self.event_handler.handle_event(event)
        
        # Clear event history when refreshing data
        self.event_handler.clear_history()
        
        # Implementation for resetting mock data would go here
        # For now we'll just log the refresh event
        return {"message": "Mock data refresh triggered", "status": "success"}