# Software Requirements Specification (SRS)
## Project: Cashback Optimization Engine (MVP)

### 1. Project Overview
A financial analysis tool designed to ingest credit card transactions via Plaid and identify "Opportunity Costs" where a different card in the user’s portfolio would have yielded higher rewards. The goal is educational: training the user to make better card-choice decisions in the future.

### 2. Data Strategy & Constraints
#### 2.1 Strict Filtering
Account Types: The system shall only process accounts where type == "credit" and subtype == "credit card". All other account types (Checking, Savings, Loans) must be ignored.

Transaction Status: The system shall only process transactions where pending == False. Pending transactions are to be discarded to ensure finality of amounts (e.g., tips, adjusted totals).

#### 2.2 Transaction Discard/Ignore Policy
Payments/Transfers: Transactions categorized as "Payment" or "Transfer" (e.g., paying off the credit card bill) must be discarded.

Refunds/Returns: Transactions with a negative amount (refunds) shall be stored for ledger completeness but excluded from the Optimization/What-If analysis engine.

Positive Charges: Only transactions where the amount > 0 are candidates for the "What-If" engine.

### 3. Technical Architecture
#### 3.1 Tech Stack
- Backend: Python 3.12+ (FastAPI).
- Frontend: Streamlit (v1.30+) for the analytics dashboard.
- Database: PostgreSQL 16.
- ORM: SQLModel (integrates SQLAlchemy and Pydantic).
- Infrastructure: Docker & Docker Compose.

#### 3.2 Database Schema (The 4-Table Model)
The system uses a normalized relational structure to ensure data integrity and idempotency.

| Table |	Description |	Key Fields
| -------- | ------- | ------- |
|users|	Primary identity.|	id (UUID), email|
|plaid_items|	Represents a bank login.|	id (UUID), access_token, last_cursor, institution_id|
|cards|	Individual credit accounts.|	id (UUID), plaid_account_id, official_name, mask, reward_slug|
|transactions|	The financial ledger.|	id (UUID), plaid_transaction_id (Unique), card_id (FK), amount, date,plaid_primary_category,plaid_detailed_category, is_analyzable|

### 4. Category Normalization Mapper
This layer translates Plaid's PFCv2 Detailed Categories into internal Reward Buckets.

#### 4.1 Internal Reward Buckets
The engine shall normalize all spending into the following buckets: DINING, GROCERY, GAS, TRAVEL, ONLINE_SHOPPING, STREAMING, WHOLESALE, DRUGSTORE, UTILITIES, GENERAL.

#### 4.2 Mapping Logic (Reference Table)
| Plaid Category (Detailed or Primary) | Internal Bucket |
| -------- | ------- |
|"FOOD_AND_DRINK_RESTAURANTS, FOOD_AND_DRINK_COFFEE_SHOPS, FOOD_AND_DRINK_FAST_FOOD"|DINING|
|"FOOD_AND_DRINK_GROCERIES, GENERAL_MERCHANDISE_SUPERMARKETS"|GROCERY|
|"TRANSPORTATION_GAS, TRANSPORTATION_FUEL"|GAS|
|"TRAVEL_FLIGHTS, TRAVEL_HOTELS_AND_MOTELS, TRAVEL_TAXI_AND_RIDE_SHARES"|TRAVEL|
|GENERAL_MERCHANDISE_ONLINE_MARKETPLACES|ONLINE_SHOPPING|
|"ENTERTAINMENT_TV_AND_MOVIES, ENTERTAINMENT_MUSIC_AND_AUDIO"|STREAMING|
|GENERAL_MERCHANDISE_WHOLESALE_CLUBS|WHOLESALE|
|MEDICAL_PHARMACIES_AND_SUPPLEMENTS|DRUGSTORE|
|* (Any unmapped category)|GENERAL|

### 5. Functional Requirements (FR)
#### 5.1 Incremental Data Sync
- FR 1.1 (Manual Refresh): The system shall provide a "Refresh" button in the Streamlit UI to trigger a manual sync. Automated webhooks are out of scope for the MVP to prioritize local development simplicity.
- FR 1.2 (Cursor-Based Sync): Every sync request must retrieve the last_cursor from the plaid_items table. Upon a successful /transactions/sync call, the system must update that record with the new cursor provided by Plaid.
- FR 1.3 (Idempotent Upsert): The system shall use the plaid_transaction_id as a unique natural key. New records must be inserted, and existing records must be updated (UPSERT) to handle data corrections without creating duplicates.
- FR 1.4 (Three-Stage Filter): During ingestion, the system must apply the following logic:
  Discard if pending == True.
  Discard if subtype != "credit card".
  Mark is_analyzable = False if the amount is negative (refunds) or the category is LOAN_PAYMENTS or TRANSFER_IN/OUT.

#### 5.2 Category Normalization (Placeholder)
- FR 2.1 (PFCv2 Mapping): The system shall implement a logic layer that translates Plaid’s PFCv2 Detailed Categories into a standardized list of Internal Reward Buckets (e.g., DINING, GROCERY, TRAVEL).
- FR 2.2 (Tiered Fallback): The mapper must first attempt to match the detailed category. If no match exists, it must fall back to the primary category, and finally to GENERAL.
- FR 2.3 (Rule Mapping): The system must link these Internal Buckets to the multipliers defined in rules.json (e.g., DINING -> 3x for Chase Sapphire).

#### 5.3 Optimization Engine
- FR 3.1 (Actual Rewards): For every analyzable transaction, the engine must calculate the cashback earned on the card used by looking up its reward rate for that specific category.
- FR 3.2 (Cross-Portfolio Comparison): The engine shall iterate through all other cards in the cards table for that user to identify which card offers the highest multiplier for that transaction's category.
- FR 3.3 (Opportunity Cost): The system shall calculate and store the lost_savings ($Best Possible - Actual$) for every positive transaction to populate the "Total Missed Wins" dashboard.

### 6. Non-Functional Requirements (NFR)
- NFR 1 (Security): All Plaid access_tokens must be handled as sensitive secrets, stored in encrypted environment variables or encrypted database columns.
- NFR 2 (Auditability): Every analyzed transaction must maintain a reference to the best_card_id used for the "What-If" calculation for transparency.
- NFR 3 (DevOps): The entire stack must be deployable via a single docker-compose up command.

### 7. Success Metrics for MVP
- Successful connection to Plaid Sandbox and retrieval of 30 days of transactions.
- Zero duplicate transactions in the database after multiple "Refresh" clicks.
- Identification of at least one "Sub-optimal" transaction where a different card would have yielded higher returns.
