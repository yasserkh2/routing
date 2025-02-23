import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class MockDatadogAPI:
    """Mock service to simulate Datadog API for actual SLA data"""
    
    def __init__(self):
        # Simulate some routes having existing SLA data in Datadog
        self._sla_data = {}
        
    def get_sla_for_route(self, mcc: str, mnc: str, product_name: str) -> Optional[float]:
        """
        Get actual SLA from Datadog for currently used routes
        Returns None if route is not currently being used
        """
        key = f"{mcc}_{mnc}_{product_name}"
        if key not in self._sla_data:
            # 30% chance of having Datadog data
            if random.random() < 0.3:
                self._sla_data[key] = round(random.uniform(95.0, 99.9), 2)
            else:
                self._sla_data[key] = None
        return self._sla_data[key]

class MockAutoRouterAPI:
    """Mock service to simulate Auto Router V1 testing results"""
    
    def __init__(self):
        # Simulate some routes having been tested
        self._test_results = {}
        
    def get_tested_sla(self, mcc: str, mnc: str, product_name: str) -> Optional[float]:
        """
        Get SLA from previous Auto Router V1 testing
        Returns None if route was not tested
        """
        key = f"{mcc}_{mnc}_{product_name}"
        if key not in self._test_results:
            # 40% chance of having test data
            if random.random() < 0.4:
                self._test_results[key] = round(random.uniform(90.0, 99.0), 2)
            else:
                self._test_results[key] = None
        return self._test_results[key]

class MockTieringAPI:
    """Mock service to simulate routing team's Tiering data"""
    
    def __init__(self):
        # Tiering data is always available as fallback
        self.tier_mapping = {
            # Map MCC ranges to tiers
            (100, 299): 'Tier1',  # Europe
            (300, 499): 'Tier2',  # North America
            (500, 799): 'Tier3',  # Asia & Africa
        }
        self.tier_sla = {
            'Tier1': 98.5,
            'Tier2': 96.0,
            'Tier3': 94.0
        }
        
    def get_assumed_sla(self, mcc: str, mnc: str) -> float:
        """Get SLA based on Tiering data - always returns a value"""
        mcc_num = int(mcc)
        for (start, end), tier in self.tier_mapping.items():
            if start <= mcc_num <= end:
                return self.tier_sla[tier]
        return self.tier_sla['Tier3']  # Default to Tier3

class MockOutputAPI:
    """Mock service to simulate the output table API"""
    
    def __init__(self):
        self.providers = [
            "AMD Telecom",
            "Infobip",
            "Twilio",
            "MessageBird"
        ]
        
        self.products = [
            "Talabat_Jordan",
            "Cequens_Premium_EUR",
            "Cequens_Standard_USD",
            "Cequens_Operators_Premium",
            "Regional_Enterprise_INTL"
        ]
        
        self.networks = [
            {"name": "Togo Cell", "mcc": "615", "mnc": "1"},
            {"name": "Kuwait Virgin Mobile", "mcc": "419", "mnc": "9"},
            {"name": "Vodafone Egypt", "mcc": "602", "mnc": "2"},
            {"name": "Orange Jordan", "mcc": "416", "mnc": "77"},
            {"name": "STC Kuwait", "mcc": "419", "mnc": "2"}
        ]
        
        self._generate_mock_data()
        
    def _generate_mock_data(self, count: int = 20):
        """Generate initial mock data"""
        self.routes = []
        ref_id = 450000
        
        for _ in range(count):
            provider = random.choice(self.providers)
            network = random.choice(self.networks)
            product = random.choice(self.products)
            
            old_rate = round(random.uniform(0.05, 0.15), 4)
            new_rate = round(old_rate * random.uniform(0.8, 1.5), 4)
            margin = round((new_rate - old_rate) / old_rate * 100, 2)
            
            route = {
                "reference_id": str(ref_id),
                "product_name": product,
                "provider_name": provider,
                "name": f"{product.split('_')[0]}_{network['name']}_{provider}",
                "network_name": network['name'],
                "mcc": network["mcc"],
                "mnc": network["mnc"],
                "old_rate": old_rate,
                "new_rate": new_rate,
                "margin_percentage": margin,
                "price_change_status": "Increased" if new_rate > old_rate else "Decreased",
                "created_on": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat()
            }
            
            self.routes.append(route)
            ref_id += 1
    
    def get_routes(self, 
                  product_name: Optional[str] = None,
                  mcc: Optional[str] = None,
                  mnc: Optional[str] = None) -> List[Dict]:
        """Get routes with optional filtering"""
        filtered_routes = self.routes.copy()
        
        if product_name:
            filtered_routes = [r for r in filtered_routes if r['product_name'] == product_name]
        if mcc:
            filtered_routes = [r for r in filtered_routes if r['mcc'] == mcc]
        if mnc:
            filtered_routes = [r for r in filtered_routes if r['mnc'] == mnc]
            
        return filtered_routes

class MockAPIService:
    """Main service to coordinate all mock APIs"""
    
    def __init__(self):
        self.output_api = MockOutputAPI()
        self.datadog_api = MockDatadogAPI()
        self.auto_router_api = MockAutoRouterAPI()
        self.tiering_api = MockTieringAPI()
    
    def get_routes_with_sla(self,
                           product_name: Optional[str] = None,
                           mcc: Optional[str] = None,
                           mnc: Optional[str] = None) -> List[Dict]:
        """Get routes with their SLA information from all sources"""
        routes = self.output_api.get_routes(product_name, mcc, mnc)
        
        for route in routes:
            # Get SLA from each source
            sla_dd = self.datadog_api.get_sla_for_route(
                route['mcc'],
                route['mnc'],
                route['product_name']
            )
            
            sla_tested = self.auto_router_api.get_tested_sla(
                route['mcc'],
                route['mnc'],
                route['product_name']
            )
            
            sla_assumed = self.tiering_api.get_assumed_sla(
                route['mcc'],
                route['mnc']
            )
            
            # Add SLA data to route
            route.update({
                'sla_dd': sla_dd,
                'sla_tested': sla_tested,
                'sla_assumed': sla_assumed
            })
            
        return routes
    
    def get_profiles(self) -> List[Dict]:
        """Get unique profiles with their route information"""
        routes = self.get_routes_with_sla()
        profiles = {}
        
        for route in routes:
            product = route['product_name']
            if product not in profiles:
                profiles[product] = {
                    'product_name': product,
                    'route_count': 0,
                    'routes_with_dd': 0,
                    'routes_with_tested': 0,
                    'total_margin': 0,
                }
            
            profile = profiles[product]
            profile['route_count'] += 1
            profile['total_margin'] += route['margin_percentage']
            
            if route['sla_dd'] is not None:
                profile['routes_with_dd'] += 1
            if route['sla_tested'] is not None:
                profile['routes_with_tested'] += 1
        
        # Calculate averages and format profiles
        result = []
        for profile in profiles.values():
            result.append({
                'product_name': profile['product_name'],
                'route_count': profile['route_count'],
                'average_margin': round(profile['total_margin'] / profile['route_count'], 2),
                'dd_coverage': round(profile['routes_with_dd'] / profile['route_count'] * 100, 2),
                'test_coverage': round(profile['routes_with_tested'] / profile['route_count'] * 100, 2)
            })
            
        return result
    
    def refresh_mock_data(self):
        """Refresh all mock data"""
        self.output_api._generate_mock_data()