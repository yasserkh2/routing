from datetime import datetime
from sla_data import SLAData
from link import Link
from profile import Profile

def demonstrate_models():
    # Example SLA Data
    sla_data = SLAData.from_dict({
        'sla_dd': 99.1,
        'sla_tested': 98.5,
        'sla_assumed': 97.0,
        'last_updated': '2025-02-06T12:00:00Z'
    })
    print("\nSLA Data Example:")
    print(f"Best SLA: {sla_data.get_best_sla()}%")  # Will use DataDog SLA
    print(f"Last Updated: {sla_data.last_updated}")

    # Example Link
    link = Link.from_dict({
        'link_id': '450271',
        'operator': 'Togo Cell',
        'mnc': '01',
        'routing_priority': 1,
        'is_active': True,
        'last_used': '2025-02-06T12:00:00Z',
        'sla_data': {
            'sla_dd': 99.1,
            'sla_tested': 98.5,
            'sla_assumed': 97.0,
            'last_updated': '2025-02-06T12:00:00Z'
        }
    })
    print("\nLink Example:")
    print(f"Link ID: {link.link_id}")
    print(f"Operator: {link.operator}")
    print(f"Effective SLA: {link.get_effective_sla()}%")
    print(f"Is Usable: {link.is_usable()}")

    # Example Profile with multiple links
    profile = Profile.from_dict({
        'profile_id': 'PROF_1',
        'name': 'Premium_Gold_Profile',
        'expected_sla': 99.5,
        'priority': 'CRITICAL',
        'links': [
            {
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
                }
            },
            {
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
                }
            }
        ]
    })

    print("\nProfile Example:")
    print(f"Profile: {profile.name}")
    print(f"Expected SLA: {profile.expected_sla}%")
    print(f"Number of Links: {len(profile.links)}")
    print(f"Active Links: {len(profile.get_active_links())}")
    
    best_link = profile.get_best_link()
    if best_link:
        print("\nBest Available Link:")
        print(f"Link ID: {best_link.link_id}")
        print(f"Routing Priority: {best_link.routing_priority}")
        print(f"Effective SLA: {best_link.get_effective_sla()}%")

    print("\nAverage SLA across usable links:", end=" ")
    avg_sla = profile.get_average_sla()
    print(f"{avg_sla:.1f}%" if avg_sla is not None else "No usable links")

    # Demonstrate link filtering
    togo_links = profile.get_links_by_operator("Togo Cell")
    print(f"\nLinks for Togo Cell: {len(togo_links)}")
    for link in togo_links:
        print(f"- Link {link.link_id}: Priority {link.routing_priority}, "
              f"SLA {link.get_effective_sla()}%")

if __name__ == "__main__":
    demonstrate_models()