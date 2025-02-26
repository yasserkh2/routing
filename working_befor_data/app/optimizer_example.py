from optimizer import RoutingOptimizer
from profile import Profile
from link import Link
from sla_data import SLAData
from datetime import datetime

def create_sample_data():
    """Create sample profile and links for demonstration"""
    # Create SLA data with average values
    sla_data1 = SLAData(
        average_sla=99.0,  # High SLA
        last_updated=datetime.now()
    )
    sla_data2 = SLAData(
        average_sla=90.0,  # Medium SLA
        last_updated=datetime.now()
    )
    sla_data3 = SLAData(
        average_sla=85.0,  # Basic SLA
        last_updated=datetime.now()
    )

    # Create links with different SLAs and prices
    links = [
        Link(
            link_id="450271",
            operator="Operator1",
            mnc="01",
            routing_priority=1,
            is_active=True,
            last_used=datetime.now(),
            sla_data=sla_data1,
            price=100.0  # Higher price for better SLA
        ),
        Link(
            link_id="450272",
            operator="Operator1",
            mnc="01",
            routing_priority=2,
            is_active=True,
            last_used=datetime.now(),
            sla_data=sla_data2,
            price=80.0   # Medium price for medium SLA
        ),
        Link(
            link_id="450273",
            operator="Operator2",
            mnc="02",
            routing_priority=3,
            is_active=True,
            last_used=datetime.now(),
            sla_data=sla_data3,
            price=60.0   # Lower price for lower SLA
        )
    ]

    # Create profile with SLA requirement
    profile = Profile(
        profile_id="PROF_1",
        name="Standard_Profile",
        expected_sla=88.0,  # Target SLA requirement
        priority="MEDIUM",
        links=links
    )

    return profile

def demonstrate_optimization():
    """Demonstrate the routing optimization"""
    print("\n=== Routing Optimization Example ===")
    
    # Create and set up optimizer
    profile = create_sample_data()
    optimizer = RoutingOptimizer(profile)
    
    # Run optimization
    if optimizer.solve():
        # Get and display results
        routing_plan = optimizer.get_routing_plan()
        stats = optimizer.get_optimization_stats()
        
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

if __name__ == "__main__":
    print("Routing Optimization Example")
    print("===========================")
    demonstrate_optimization()