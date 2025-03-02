from datetime import datetime
from ..services.mock_services import MockAPIService
from ..models.profile import Profile
from ..models.link import Link
from ..models.sla_data import SLAData
from ..core.optimizer import RoutingOptimizer

def get_best_sla(link_data: dict) -> float:
    """Get the best available SLA value from the metrics"""
    if link_data.get('sla_dd') is not None:
        return link_data['sla_dd']  # DD is most reliable
    elif link_data.get('sla_tested') is not None:
        return link_data['sla_tested']  # Tested is second best
    return link_data.get('sla_assumed', 0.0)  # Assumed is fallback

def create_profile_from_api(mock_api: MockAPIService, product_name: str) -> Profile:
    """Create Profile object from API data"""
    # Get links for the product
    print(f"\nFetching links for product: {product_name}")
    links_data = mock_api.get_links_sla(product_name=product_name)
    print(f"Raw links data: {links_data}")
    
    if not links_data.get('profiles'):
        raise ValueError(f"No data found for product: {product_name}")
    
    # Find the profile with matching product name
    matching_profiles = [p for p in links_data['profiles'] if p['product_name'] == product_name]
    print(f"Found {len(matching_profiles)} matching profiles")
    
    if not matching_profiles:
        raise ValueError(f"No links found for product: {product_name}")
    
    # Get profile SLA requirement
    print("\nFetching SLA requirements")
    sla_profiles = mock_api.get_profile_sla(product_name)
    print(f"Found {len(sla_profiles)} matching SLA profiles")
    
    if not sla_profiles:
        raise ValueError(f"No SLA data found for product: {product_name}")
    
    sla_profile = sla_profiles[0]
    
    # Get profile SLA thresholds
    critical_threshold = sla_profile['sla_thresholds']['critical']
    warning_threshold = sla_profile['sla_thresholds']['warning']
    target_sla = sla_profile['sla_thresholds']['target']
    
    # Create Link objects that meet minimum SLA requirements
    links = []
    for link in matching_profiles[0].get('links', []):
        # Get best available SLA
        sla = get_best_sla(link)
        
        # Skip links that don't meet minimum SLA requirement
        if sla < critical_threshold:
            print(f"Skipping link {link['link_id']} - SLA {sla}% below critical threshold {critical_threshold}%")
            continue
            
        # Calculate price with premium based on SLA and status
        base_price = 50.0
        sla_premium = sla * 0.5
        status_premium = {
            'Healthy': 0.0,
            'Warning': 5.0,
            'Critical': 10.0
        }.get(link['status'], 0.0)
        price = base_price + sla_premium + status_premium
        
        # Create Link object
        link_obj = Link(
            link_id=link['link_id'],
            operator=link['provider'],
            mnc=str(link['mnc']),
            price=price,
            sla_data=SLAData(
                average_sla=sla,
                last_updated=datetime.fromisoformat(link['last_updated'].replace('Z', '+00:00'))
            )
        )
        links.append(link_obj)
        print(f"Added link {link['link_id']} - SLA: {sla}%, Status: {link['status']}, Price: ${price}")
    
    # Create Profile directly
    profile = Profile(
        profile_id=f"PROF_{product_name}",
        name=product_name,
        expected_sla=sla_profile['expected_sla'],
        priority=sla_profile['priority'],
        links=links
    )
    
    print(f"\nProfile data:")
    print(f"- Product: {profile.name}")
    print(f"- Links: {len(profile.links)}")
    print(f"\nCreated Link objects:")
    for link in profile.links:
        print(f"- {link.link_id}: SLA={link.sla_data.average_sla}%, Price=${link.price}")
    
    return profile

def demonstrate_optimization_with_api_data():
    """Demonstrate routing optimization using API data"""
    print("\n=== Routing Optimization with API Data ===")
    
    # Initialize mock API service
    mock_api = MockAPIService()
    
    # Get available products from profile SLA data
    profile_sla_data = mock_api.get_profile_sla()
    if not profile_sla_data:
        print("No products found")
        return
    
    # Use the first product for demonstration
    product_name = profile_sla_data[0]['product_name']
    print(f"\nOptimizing routes for product: {product_name}")
    
    try:
        # Create profile from API data
        profile = create_profile_from_api(mock_api, product_name)
        
        # Initialize and run optimizer
        print("\nPreparing optimization:")
        print(f"- Profile: {profile.name}")
        print(f"- Expected SLA: {profile.expected_sla}%")
        print(f"- Available Links: {len(profile.links)}")
        
        optimizer = RoutingOptimizer(profile)
        print("\nRunning optimization...")
        success = optimizer.solve()
        
        if success:
            # Get and display results
            routing_plan = optimizer.get_routing_plan()
            stats = optimizer.get_optimization_stats()
            
            print("\nOptimization successful!")
            
            print(f"\nProfile: {routing_plan['name']} (Expected SLA: {routing_plan['expected_sla']}%)")
            print("\nOptimal Route Allocation:")
            for route in routing_plan['routes']:
                print(f"- Link {route['link_id']}: {route['percentage']:.1f}% (SLA: {route['sla']:.2f}%, Price: ${route['price']:.2f})")
            
            print("\nOptimization Statistics:")
            print(f"Total Cost: ${stats['total_cost']:.2f}")
            print(f"Links Used: {stats['links_used']}")
            print(f"Achieved SLA: {stats['achieved_sla']:.2f}%")
            print(f"Expected SLA: {stats['expected_sla']:.2f}%")
        else:
            print("Failed to find optimal solution")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("Routing Optimization with API Data Example")
    print("=========================================")
    demonstrate_optimization_with_api_data()