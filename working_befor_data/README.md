# Routing Optimizer System

## Overview
This system optimizes routing decisions based on SLA requirements, costs, and traffic distribution. It provides a web interface for analyzing and optimizing routing configurations.

## Components

### Web Interface
- Located in `/web_interface`
- FastAPI server running on localhost
- HTML interface for submitting and viewing routing analysis

### Core Components
- Profile Management
- Link Management
- SLA Optimization
- Traffic Distribution

## SLA Calculation Logic

The system calculates SLA values using the following rules:

1. For In-Use Links:
   - If both DD SLA and Tier SLA are available:
     * Final SLA = (DD SLA + Tier SLA) / 2
   - If only DD SLA is available:
     * Final SLA = DD SLA
   - If only Tier SLA is available:
     * Final SLA = Tier SLA based on tier mapping

2. For Alternative Links:
   - SLA is calculated based on tier mapping:
     * Tier 1: 99% SLA
     * Tier 2: 95% SLA
     * Tier 3: 90% SLA

3. Tier-Based SLA Mapping:
   - Tier 1 (Premium): 99% SLA
   - Tier 2 (Standard): 95% SLA
   - Tier 3 (Basic): 90% SLA

## Traffic Distribution

The optimizer calculates traffic distribution based on:
- Link costs
- SLA requirements
- Link capacity
- Tier preferences

Traffic percentages are assigned to optimize for:
1. Meeting required SLA
2. Minimizing costs
3. Maintaining tier-appropriate distribution

## API Endpoints

### POST /api/profiles/links
- Input: Link ID, MCC, MNC
- Output: Profile analysis including:
  * SLA calculations
  * Traffic distribution
  * Cost analysis
  * Alternative routing options

## Running the System

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the web server:
```bash
cd web_interface
python server.py
```

3. Access the interface at:
```
http://localhost:8004
```

## Mock Data
Mock data for testing is available in the `/mock_data` directory:
- `api_round_2_reorganized_links_no_sla.json`: Link and profile configurations
- `price_changes.json`: Price update simulations
- `sla_update.json`: SLA change simulations
