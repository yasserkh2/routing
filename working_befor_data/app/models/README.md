# Models Directory

## Core Models

### profile.py
- Profile class for handling profile data
- Validates profile configuration
- Manages link references
- Tracks link labels and status information
- Provides methods for link status management
- Supports cloning and comprehensive link information retrieval

### link.py
- Link class for handling link data
- Validates link properties
- Manages SLA and traffic data
- Supports custom labels and status tracking
- Provides utility methods for cost calculation and SLA verification

## Required Files
```
models/
├── __init__.py          # Makes models a package
├── README.md           # This documentation
├── profile.py          # Profile model
└── link.py            # Link model