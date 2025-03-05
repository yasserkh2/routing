# Models Directory

This directory contains all data models and schemas used throughout the application.

## Components

- `link.py`: Defines the Link model for representing network connections
- `models.py`: Contains shared base models and common data structures
- `profile.py`: Implements the Profile model for routing configurations
- `sla_data.py`: Defines SLA (Service Level Agreement) data structures

## Purpose

The models directory provides the data structure definitions that form the foundation of the application. These models ensure:

- Consistent data representation across the system
- Type safety and validation
- Clear interfaces for data manipulation
- Standardized format for SLA metrics and routing profiles

Each model includes validation rules and business logic specific to its domain, helping maintain data integrity throughout the application.