# Data Model

## Database Schema

### Core Tables

1. providers
   - id (PK)
   - name
   - description
   - created_at

2. products
   - id (PK)
   - provider_id (FK)
   - name
   - description
   - created_at

3. sla_links
   - id (PK)
   - product_id (FK)
   - network_name
   - mcc
   - mnc
   - created_at

4. prices
   - id (PK)
   - sla_link_id (FK)
   - old_rate
   - new_rate
   - margin_percentage
   - price_change_status
   - created_at

5. ml_predictions
   - id (PK)
   - sla_link_id (FK)
   - predicted_price
   - predicted_demand
   - confidence_score
   - created_at

6. optimization_results
   - id (PK)
   - sla_link_id (FK)
   - ml_prediction_id (FK)
   - optimized_price
   - optimized_decision
   - created_at

7. decisions
   - id (PK)
   - optimization_result_id (FK)
   - decision_status
   - approved_by
   - created_at

## Data Flow

### Price Update Flow
1. Receive price updates via API/events
2. Store in prices table
3. Trigger ML predictions
4. Run optimization
5. Generate decisions

### Decision Making Flow
1. ML model generates predictions
2. Optimization engine processes constraints
3. Decision engine applies business rules
4. Final decision stored and tracked

## Data Relationships
(Document relationships between tables, foreign key constraints)

## Data Retention
- Active data retention period
- Archival strategy
- Cleanup policies