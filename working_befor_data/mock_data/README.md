# Mock Data Directory

## Data Files

### Primary Data Files
- `api_round_2_reorganized_links_no_sla.json`: Combined profile and link data
  * Contains profile configurations
  * In-use links with traffic distribution
  * Alternative links
  * SLA and pricing information

### Legacy/Reference Files
- `links_data.json`: Original links data format (for reference)
- `profiles.json`: Original profiles data format (for reference)

### Event Testing Files
- `price_changes.json`: Sample price update events
- `sla_update.json`: Sample SLA update events

## Required Files
```
mock_data/
├── README.md                                  # This documentation
├── api_round_2_reorganized_links_no_sla.json # Current data format
├── links_data.json                           # Legacy links data
├── profiles.json                             # Legacy profiles data
├── price_changes.json                        # Price update events
└── sla_update.json                          # SLA update events
```

## Data Format Examples

### Current Format (api_round_2_reorganized_links_no_sla.json)
```json
{
  "profile_id": "PROF_001",
  "name": "Ultra_Premium_OTP",
  "expected_sla": 96.0,
  "description": "Ultra premium OTP service",
  "sell_price_min": 12.0,
  "sell_price_max": 18.0,
  "profile_avg_cost": 7.2,
  "mcc": "426",
  "mnc": "01",
  "in_use_links": [
    {
      "link": "LINK_001",
      "provider": "Provider A",
      "buy_price": 9.0,
      "sla_dd": 99.0,
      "tier": 1,
      "traffic": 25.0,
      "last_updated": "2025-05-22T15:00:00"
    }
  ],
  "alternative_links": [
    {
      "link": "LINK_005",
      "provider": "Provider B",
      "buy_price": 7.5,
      "tier": 2,
      "last_updated": "2025-05-22T15:00:00"
    }
  ]
}
```

### Event Data Format (price_changes.json, sla_update.json)
```json
{
  "link": "LINK_001",
  "type": "price_update",
  "new_value": 8.5,
  "timestamp": "2025-05-22T15:00:00"
}