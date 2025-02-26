from datetime import datetime
from profile_manager import ProfileManager
from profile import Profile
from link import Link
from sla_data import SLAData

def create_sample_data():
    """Create sample profiles and links for demonstration"""
    # Create SLA data with average values
    sla_data1 = SLAData(
        average_sla=99.13,  # High SLA
        last_updated=datetime.now()
    )
    sla_data2 = SLAData(
        average_sla=97.83,  # Medium SLA
        last_updated=datetime.now()
    )
    sla_data3 = SLAData(
        average_sla=96.75,  # Basic SLA
        last_updated=datetime.now()
    )

    # Create links with different SLAs
    links_premium = [
        Link(
            link_id="450271",
            operator="Operator1",
            mnc="01",
            routing_priority=1,
            is_active=True,
            last_used=datetime.now(),
            sla_data=sla_data1,
            price=100.0
        ),
        Link(
            link_id="450272",
            operator="Operator1",
            mnc="01",
            routing_priority=2,
            is_active=True,
            last_used=datetime.now(),
            sla_data=sla_data2,
            price=80.0
        )
    ]

    links_standard = [
        Link(
            link_id="450273",
            operator="Operator2",
            mnc="02",
            routing_priority=1,
            is_active=True,
            last_used=datetime.now(),
            sla_data=sla_data3,
            price=60.0
        )
    ]

    # Create profiles with different SLA requirements
    profiles = [
        Profile(
            profile_id="PROF_1",
            name="Premium_Gold_Profile",
            expected_sla=98.0,
            priority="HIGH",
            links=links_premium
        ),
        Profile(
            profile_id="PROF_2",
            name="Premium_Silver_Profile",
            expected_sla=97.5,
            priority="HIGH",
            links=links_premium + links_standard
        ),
        Profile(
            profile_id="PROF_3",
            name="Standard_Profile",
            expected_sla=97.0,
            priority="MEDIUM",
            links=links_premium + links_standard
        ),
        Profile(
            profile_id="PROF_4",
            name="Basic_Profile",
            expected_sla=96.0,
            priority="LOW",
            links=links_standard
        )
    ]

    return profiles

def demonstrate_profile_management():
    """Demonstrate ProfileManager functionality"""
    # Create ProfileManager with sample data
    profiles = create_sample_data()
    manager = ProfileManager(profiles=profiles)

    print("\n=== Profile SLA Summary ===")
    summary = manager.get_sla_summary()
    print(f"Total Profiles: {summary['profiles_count']}")
    print(f"Minimum SLA: {summary['min_sla']:.2f}%")
    print(f"Maximum SLA: {summary['max_sla']:.2f}%")
    print(f"Average SLA: {summary['avg_sla']:.2f}%")

    print("\n=== Average SLA by Priority ===")
    priority_slas = manager.get_average_sla_by_priority()
    for priority, avg_sla in priority_slas.items():
        print(f"{priority}: {avg_sla:.2f}%")

    print("\n=== High SLA Profiles (>=98%) ===")
    high_sla_profiles = manager.get_profiles_by_sla(98.0)
    for profile in high_sla_profiles:
        print(f"Profile: {profile.name} (SLA: {profile.expected_sla}%)")

    print("\n=== Profiles Using MNC '01' ===")
    mnc_profiles = manager.get_profiles_by_mnc("01")
    for profile in mnc_profiles:
        print(f"Profile: {profile.name}")
        mnc_links = profile.get_links_by_mnc("01")
        for link in mnc_links:
            print(f"  - Link {link.link_id}: {link.average_sla:.2f}% SLA")

    print("\n=== Profiles Meeting Their SLA Requirements ===")
    meeting_sla = manager.get_profiles_meeting_sla()
    for profile in meeting_sla:
        print(f"Profile: {profile.name} (Required: {profile.expected_sla}%)")
        usable_links = [l for l in profile.links if l.average_sla >= profile.expected_sla]
        for link in usable_links:
            print(f"  - Link {link.link_id}: {link.average_sla:.2f}% SLA")

if __name__ == "__main__":
    print("Profile Management Example")
    print("=========================")
    demonstrate_profile_management()