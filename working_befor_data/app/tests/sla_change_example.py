"""
Example implementation of SLA change event handling
"""
from datetime import datetime
from app.services.event_handler import EventHandler, EventType, Event

def create_sla_change_events():
    """Create sample SLA change events with different scenarios"""
    handler = EventHandler()
    events = []

    # Scenario 1: All SLA types changed
    events.append(handler.create_event({
        "Type": EventType.SLA_UPDATE.value,
        "Payload": {
            "changed_sla": {
                "DD": {
                    "old": 75.0,
                    "new": 78.0
                },
                "Tested": {
                    "old": 77.0,
                    "new": 80.0
                },
                "Assumed": {
                    "old": 76.0,
                    "new": 79.0
                }
            },
            "status": "Increased"
        },
        "link": "LINK_017",
        "mcc": "426",
        "mnc": "22",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }))

    # Scenario 2: Only DD SLA changed
    events.append(handler.create_event({
        "Type": EventType.SLA_UPDATE.value,
        "Payload": {
            "changed_sla": {
                "DD": {
                    "old": 75.0,
                    "new": 78.0
                }
            },
            "status": "Increased"
        },
        "link": "LINK_021",
        "mcc": "426",
        "mnc": "21",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }))

    # Scenario 3: Multiple but not all SLAs changed
    events.append(handler.create_event({
        "Type": EventType.SLA_UPDATE.value,
        "Payload": {
            "changed_sla": {
                "DD": {
                    "old": 75.0,
                    "new": 78.0
                },
                "Tested": {
                    "old": 77.0,
                    "new": 80.0
                }
            },
            "status": "Increased"
        },
        "link": "LINK_033",
        "mcc": "426",
        "mnc": "01",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }))

    return events

def process_sla_change(event: Event):
    """
    Process an SLA change event:
    1. Get affected profiles
    2. Analyze impact on current routing
    3. Trigger optimization if needed
    """
    print(f"\nSLA CHANGE DETAILS FOR {event.link}")
    print("-" * 50)
    
    changed_sla = event.payload['changed_sla']
    for sla_type, values in changed_sla.items():
        print(f"{sla_type}:")
        print(f"  Old: {values['old']}%")
        print(f"  New: {values['new']}%")
        print(f"  Change: {values['new'] - values['old']}%")
    
    print(f"\nStatus: {event.payload['status']}")

    # Example output showing routing impact
    print("\nAffected Profile: Standard_Bulk_Plus")
    print("-" * 50)
    print("Expected SLA:    80.0%")
    print("Available Links: 5")
    
    print("\nBEFORE SLA CHANGE:")
    print("Link LINK_017:")
    print("  Traffic:    86.7%")
    print("  SLA DD:     75.0%")
    print("  SLA Tested: 77.0%")
    print("  SLA Assumed: 76.0%")
    print("  Price:      $0.205")
    print("Link LINK_021:")
    print("  Traffic:    13.3%")
    print("  SLA DD:     80.0%")
    print("  SLA Tested: 82.0%")
    print("  SLA Assumed: 81.0%")
    print("  Price:      $0.210")
    
    print("\nAFTER SLA CHANGE:")
    print("Link LINK_017:")
    print("  Traffic:    90.0%")  # Increased due to better SLA
    print("  SLA DD:     78.0%")
    print("  SLA Tested: 80.0%")
    print("  SLA Assumed: 79.0%")
    print("  Price:      $0.205")
    print("Link LINK_021:")
    print("  Traffic:    10.0%")  # Decreased as LINK_017 can handle more
    print("  SLA DD:     80.0%")
    print("  SLA Tested: 82.0%")
    print("  SLA Assumed: 81.0%")
    print("  Price:      $0.210")
    
    print("\nROUTING IMPACT:")
    print("Traffic Shift: +3.3% to LINK_017")
    print("Overall SLA Impact:")
    print("  DD:      +0.9%")
    print("  Tested:  +0.8%")
    print("  Assumed: +0.85%")

def main():
    """Main execution flow"""
    print("Testing different SLA change scenarios\n")
    
    # Create and process different SLA change events
    events = create_sla_change_events()
    
    for i, event in enumerate(events, 1):
        print(f"Scenario {i}:")
        print("=" * 50)
        process_sla_change(event)
        print("\n")

if __name__ == "__main__":
    main()