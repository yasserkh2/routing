from datetime import datetime
from sla_data import SLAData
from link import Link
from profile import Profile
from optimizer import RoutingOptimizer

def demonstrate_optimizer():
    # Create some example links with different SLAs and prices
    links = [
        Link.from_dict({
            'link_id': '450271',
            'operator': 'Togo Cell',
            'mnc': '01',
            'routing_priority': 1,
            'is_active': True,
            'last_used': '2025-02-06T12:00:00Z',
            'sla_data': {
                'sla_dd': 99.9,
                'sla_tested': 98.5,
                'sla_assumed': 97.0,
                'last_updated': '2025-02-06T12:00:00Z'
            },
            'price_difference': 0.02  # $0.02 profit per unit
        }),
        Link.from_dict({
            'link_id': '450272',
            'operator': 'Togo Cell',
            'mnc': '01',
            'routing_priority': 2,
            'is_active': True,
            'last_used': '2025-02-06T11:00:00Z',
            'sla_data': {
                'sla_dd': None,
                'sla_tested': 97.8,
                'sla_assumed': 96.5,
                'last_updated': '2025-02-06T11:00:00Z'
            },
            'price_difference': 0.03  # $0.03 profit per unit
        }),
        Link.from_dict({
            'link_id': '450273',
            'operator': 'Togo Cell',
            'mnc': '01',
            'routing_priority': 3,
            'is_active': True,
            'last_used': '2025-02-06T10:00:00Z',
            'sla_data': {
                'sla_dd': None,
                'sla_tested': None,
                'sla_assumed': 95.0,
                'last_updated': '2025-02-06T10:00:00Z'
            },
            'price_difference': 0.04  # $0.04 profit per unit
        })
    ]

    # Create profiles with different SLA requirements
    profiles = [
        Profile.from_dict({
            'profile_id': 'PROF_1',
            'name': 'Premium_Gold_Profile',
            'expected_sla': 99.5,
            'priority': 'CRITICAL',
            'links': [link.to_dict() for link in links[:2]]  # Only high SLA links
        }),
        Profile.from_dict({
            'profile_id': 'PROF_2',
            'name': 'Standard_Profile',
            'expected_sla': 97.0,
            'priority': 'MEDIUM',
            'links': [link.to_dict() for link in links]  # All links
        })
    ]

    # Create and setup optimizer
    optimizer = RoutingOptimizer(profiles)
    
    # Set different volumes for each profile
    profile_volumes = {
        'PROF_1': 2000.0,  # Premium profile: 2000 units
        'PROF_2': 5000.0   # Standard profile: 5000 units
    }
    
    print("Setting up optimization model...")
    optimizer.setup_model(profile_volumes)
    
    print("\nSolving optimization model...")
    if optimizer.solve():
        print("\nOptimization successful!")
        
        # Get the routing plan
        routing_plan = optimizer.get_routing_plan()
        print("\nRouting Plan:")
        for profile_id, plan in routing_plan.items():
            print(f"\nProfile: {plan['name']}")
            print(f"Expected SLA: {plan['expected_sla']}%")
            print("Routes:")
            for route in plan['routes']:
                print(f"- Link {route['link_id']}:")
                print(f"  Volume: {route['volume']:.1f}")
                print(f"  Effective SLA: {route['effective_sla']}%")
                print(f"  Priority: {route['routing_priority']}")
        
        # Get optimization statistics
        stats = optimizer.get_optimization_stats()
        print("\nOptimization Statistics:")
        print(f"Total Profit: ${stats['total_profit']:.2f}")
        print(f"Total Volume: {stats['total_volume']:.1f}")
        print(f"Profiles Optimized: {stats['profiles_optimized']}")
        print(f"Links Used: {stats['links_used']}")
    else:
        print("\nOptimization failed - could not find a feasible solution")

if __name__ == "__main__":
    demonstrate_optimizer()