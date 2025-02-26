from datetime import datetime
from link import Link
from profile import Profile
from sla_data import SLAData

def create_sample_data():
    """Create sample profiles and links for demonstration"""
    # Create SLA data with average values
    sla_data1 = SLAData(
        average_sla=99.13,  # Average SLA for link 450271
        last_updated=datetime.now()
    )
    sla_data2 = SLAData(
        average_sla=97.83,  # Average SLA for link 450272
        last_updated=datetime.now()
    )
    sla_data3 = SLAData(
        average_sla=96.75,  # Average SLA for link 450273
        last_updated=datetime.now()
    )

    # Create links for MNC "01"
    links_mnc_01 = [
        Link(
            link_id="450271",
            operator="Operator1",
            mnc="01",
            routing_priority=1,
            is_active=True,
            last_used=datetime.now(),
            sla_data=sla_data1
        ),
        Link(
            link_id="450272",
            operator="Operator1",
            mnc="01",
            routing_priority=2,
            is_active=True,
            last_used=datetime.now(),
            sla_data=sla_data2
        )
    ]

    # Create links for MNC "02"
    links_mnc_02 = [
        Link(
            link_id="450273",
            operator="Operator2",
            mnc="02",
            routing_priority=1,
            is_active=True,
            last_used=datetime.now(),
            sla_data=sla_data3
        )
    ]

    # Create profiles with overlapping links
    profiles = [
        Profile(
            profile_id="PROF_1",
            name="Premium_Gold_Profile",
            expected_sla=99.5,
            priority="HIGH",
            links=links_mnc_01  # Only MNC 01 links
        ),
        Profile(
            profile_id="PROF_2",
            name="Standard_Profile",
            expected_sla=97.0,
            priority="MEDIUM",
            links=links_mnc_01 + links_mnc_02  # Both MNC 01 and 02 links
        )
    ]

    return profiles

def demonstrate_link_operations():
    """Demonstrate the Link class operations"""
    profiles = create_sample_data()

    print("\n=== All Available Links ===")
    all_links = Link.extract_all_links(profiles)
    for link in all_links:
        print(f"Link {link.link_id} ({link.operator}, MNC: {link.mnc})")
        print(f"  Average SLA: {link.average_sla:.2f}%")
        print(f"  Priority: {link.routing_priority}")

    print("\n=== Links with Detailed SLA Information ===")
    links_info = Link.get_links_with_mnc_sla(profiles)
    for info in links_info:
        print(f"Link {info['link_id']} (MNC: {info['mnc']})")
        print(f"  Operator: {info['operator']}")
        print(f"  Average SLA: {info['sla']:.2f}%")
        print(f"  Priority: {info['routing_priority']}")

    print("\n=== Links with Average SLA ===")
    avg_sla_links = Link.get_links_with_average_sla(profiles)
    for link in avg_sla_links:
        print(f"Link {link['link_id']} ({link['operator']}, MNC: {link['mnc']})")
        print(f"  Average SLA: {link['average_sla']:.2f}%")
        print(f"  Priority: {link['routing_priority']}")

    print("\n=== Links Filtered by MNC '01' ===")
    mnc_01_links = Link.get_links_by_mnc(profiles, "01")
    for link_info in mnc_01_links:
        print(f"Link {link_info['link_id']}")
        print(f"  Operator: {link_info['operator']}")
        print(f"  Average SLA: {link_info['sla']:.2f}%")
        print(f"  Priority: {link_info['routing_priority']}")
        print(f"  Last Used: {link_info['last_used']}")

if __name__ == "__main__":
    print("Link Operations Example")
    print("======================")
    demonstrate_link_operations()