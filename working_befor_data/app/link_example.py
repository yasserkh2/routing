from datetime import datetime
from link import Link
from profile import Profile
from sla_data import SLAData

def create_sample_data():
    """Create sample profiles and links for demonstration"""
    # Create SLA data for multiple links
    sla_data = {
        "450271": SLAData(average_sla=99.13, last_updated=datetime.now()),  # MNC 01
        "450272": SLAData(average_sla=97.83, last_updated=datetime.now()),  # MNC 01
        "450273": SLAData(average_sla=96.75, last_updated=datetime.now()),  # MNC 02
        "450274": SLAData(average_sla=98.50, last_updated=datetime.now()),  # MNC 03
        "450275": SLAData(average_sla=95.20, last_updated=datetime.now()),  # MNC 03
        "450276": SLAData(average_sla=99.45, last_updated=datetime.now()),  # MNC 04
        "450277": SLAData(average_sla=97.90, last_updated=datetime.now()),  # MNC 04
        "450278": SLAData(average_sla=96.30, last_updated=datetime.now()),  # MNC 05
    }

    # Create links for different MNCs
    links_mnc_01 = [
        Link(link_id="450271", operator="Operator1", mnc="01", sla_data=sla_data["450271"]),
        Link(link_id="450272", operator="Operator1", mnc="01", sla_data=sla_data["450272"])
    ]

    links_mnc_02 = [
        Link(link_id="450273", operator="Operator2", mnc="02", sla_data=sla_data["450273"])
    ]

    links_mnc_03 = [
        Link(link_id="450274", operator="Operator3", mnc="03", sla_data=sla_data["450274"]),
        Link(link_id="450275", operator="Operator3", mnc="03", sla_data=sla_data["450275"])
    ]

    links_mnc_04 = [
        Link(link_id="450276", operator="Operator4", mnc="04", sla_data=sla_data["450276"]),
        Link(link_id="450277", operator="Operator4", mnc="04", sla_data=sla_data["450277"])
    ]

    links_mnc_05 = [
        Link(link_id="450278", operator="Operator5", mnc="05", sla_data=sla_data["450278"])
    ]

    # Create profiles with different link combinations
    profiles = [
        Profile(
            profile_id="PROF_1",
            name="Premium_Gold_Profile",
            expected_sla=99.5,
            priority="HIGH",
            links=links_mnc_01 + links_mnc_04  # High SLA links from MNC 01 and 04
        ),
        Profile(
            profile_id="PROF_2",
            name="Standard_Profile",
            expected_sla=97.0,
            priority="MEDIUM",
            links=links_mnc_02 + links_mnc_03  # Medium SLA links from MNC 02 and 03
        ),
        Profile(
            profile_id="PROF_3",
            name="Basic_Profile",
            expected_sla=95.0,
            priority="LOW",
            links=links_mnc_05  # Basic SLA links from MNC 05
        ),
        Profile(
            profile_id="PROF_4",
            name="Multi_Operator_Profile",
            expected_sla=98.0,
            priority="HIGH",
            links=links_mnc_01 + links_mnc_03 + links_mnc_04  # Mix of high and medium SLA links
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

    print("\n=== Links with Detailed SLA Information ===")
    links_info = Link.get_links_with_mnc_sla(profiles)
    for info in links_info:
        print(f"Link {info['link_id']} (MNC: {info['mnc']})")
        print(f"  Operator: {info['operator']}")
        print(f"  Average SLA: {info['sla']:.2f}%")

    print("\n=== Links with Average SLA ===")
    avg_sla_links = Link.get_links_with_average_sla(profiles)
    for link in avg_sla_links:
        print(f"Link {link['link_id']} ({link['operator']}, MNC: {link['mnc']})")
        print(f"  Average SLA: {link['average_sla']:.2f}%")

    # Demonstrate filtering for multiple MNCs
    for mnc in ["01", "03", "04", "05"]:
        print(f"\n=== Links Filtered by MNC '{mnc}' ===")
        filtered_links = Link.get_links_by_mnc(profiles, mnc)
        for link_info in filtered_links:
            print(f"Link {link_info['link_id']} (MNC: {link_info['mnc']})")
            print(f"  Operator: {link_info['operator']}")
            print(f"  Average SLA: {link_info['sla']:.2f}%")

if __name__ == "__main__":
    print("Link Operations Example")
    print("======================")
    demonstrate_link_operations()