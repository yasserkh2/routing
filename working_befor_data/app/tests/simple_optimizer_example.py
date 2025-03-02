from datetime import datetime
from sla_data import SLAData
from link import Link
from profile import Profile
from simple_optimizer import SimpleRoutingOptimizer

def create_test_data():
    """Create test profiles and links"""
    
    # Create SLA data for links
    sla_data_1 = SLAData(
        sla_dd=99.9,
        sla_tested=98.5,
        sla_assumed=97.0,
        last_updated=datetime.fromisoformat("2025-02-06T12:00:00Z")
    )
    
    sla_data_2 = SLAData(
        sla_dd=None,
        sla_tested=97.8,
        sla_assumed=96.5,
        last_updated=datetime.fromisoformat("2025-02-06T11:00:00Z")
    )
    
    sla_data_3 = SLAData(
        sla_dd=None,
        sla_tested=None,
        sla_assumed=95.0,
        last_updated=datetime.fromisoformat("2025-02-06T10:00:00Z")
    )
    
    # Create links
    links = [
        Link(
            link_id="450271",
            operator="Togo Cell",
            mnc="01",
            routing_priority=1,
            is_active=True,
            last_used=datetime.fromisoformat("2025-02-06T12:00:00Z"),
            sla_data=sla_data_1
        ),
        Link(
            link_id="450272",
            operator="Togo Cell",
            mnc="01",
            routing_priority=2,
            is_active=True,
            last_used=datetime.fromisoformat("2025-02-06T11:00:00Z"),
            sla_data=sla_data_2
        ),
        Link(
            link_id="450273",
            operator="Togo Cell",
            mnc="01",
            routing_priority=3,
            is_active=True,
            last_used=datetime.fromisoformat("2025-02-06T10:00:00Z"),
            sla_data=sla_data_3
        )
    ]
    
    # Create profiles with different SLA requirements
    profiles = [
        Profile(
            profile_id="PROF_1",
            name="Premium_Gold_Profile",
            expected_sla=99.5,
            priority="CRITICAL",
            links=links[:2]  # First two links for premium
        ),
        Profile(
            profile_id="PROF_2",
            name="Standard_Profile",
            expected_sla=97.0,
            priority="MEDIUM",
            links=links  # All links for standard
        )
    ]
    
    return profiles

def main():
    """Demonstrate the optimizer with Profile and Link objects"""
    
    # Create test data
    profiles = create_test_data()
    
    print("Profiles to Optimize:")
    for profile in profiles:
        print(f"\nProfile: {profile.name}")
        print(f"Expected SLA: {profile.expected_sla}%")
        print("Active Links:")
        for link in profile.get_active_links():
            print(f"- Link {link.link_id}:")
            print(f"  SLA: {link.get_effective_sla()}%")
            print(f"  Priority: {link.routing_priority}")
    
    # Create and run optimizer
    print("\nRunning optimization...")
    optimizer = SimpleRoutingOptimizer()
    results = optimizer.optimize(profiles, default_volume=1000.0)
    
    # Get optimization statistics
    stats = optimizer.get_optimization_stats(results)
    
    print("\nOptimization Results:")
    print(f"Status: {results['status']}")
    print(f"Objective Value: {results['objective_value']:.2f}")
    
    print("\nRouting Plan:")
    for profile_id, allocation in results['allocations'].items():
        print(f"\nProfile: {allocation['name']}")
        print(f"Expected SLA: {allocation['expected_sla']}%")
        print("Routes:")
        for route in allocation['routes']:
            print(f"- Link {route['link_id']}:")
            print(f"  Volume: {route['volume']:.1f}")
            print(f"  SLA: {route['sla']}%")
            print(f"  Priority: {route['routing_priority']}")
    
    print("\nOptimization Statistics:")
    print(f"Total Volume: {stats['total_volume']:.1f}")
    print(f"Total Profiles: {stats['total_profiles']}")
    print(f"Total Links Used: {stats['total_links_used']}")
    
    print("\nPer-Profile Statistics:")
    for profile_id, profile_stats in stats['profiles'].items():
        print(f"\nProfile {profile_id}:")
        print(f"  Volume: {profile_stats['total_volume']:.1f}")
        print(f"  Achieved SLA: {profile_stats['achieved_sla']*100:.1f}%")
        print(f"  Links Used: {profile_stats['links_used']}")

if __name__ == "__main__":
    main()