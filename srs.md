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
|transactions|	The financial ledger.|	id (UUID), plaid_transaction_id (Unique), card_id (FK), amount, date, is_analyzable|

### 4. Functional Requirements (FR)
#### 4.1 Incremental Data Sync
- FR 1.1 (Manual Refresh): The system shall implement a manual "Refresh" button in the UI rather than automated webhooks.
- FR 1.2 (Cursor Tracking): Every sync request must use and update the last_cursor stored in the plaid_items table to ensure only new transactions are fetched.
- FR 1.3 (Idempotency): The system must use an UPSERT strategy based on the plaid_transaction_id to prevent duplicate records during overlapping sync windows.

#### 4.2 Category Normalization (Placeholder)
- FR 2.1: The system shall implement a mapping layer to translate Plaid PFCv2 categories into a simplified list of "Internal Reward Buckets."
- FR 2.2: Logic to be defined by User.

#### 4.3 Optimization Engine
- FR 3.1: For every analyzable transaction, the engine shall calculate the cashback earned on the actual card used.
- FR 3.2: The engine shall iterate through the user's other registered cards to find the "Best Possible" reward rate for that transaction's category.
- FR 3.3: The difference (Best - Actual) shall be stored as lost_savings.

### 5. Non-Functional Requirements (NFR)
- NFR 1 (Security): All Plaid access_tokens must be handled as sensitive secrets, stored in encrypted environment variables or encrypted database columns.
- NFR 2 (Auditability): Every analyzed transaction must maintain a reference to the best_card_id used for the "What-If" calculation for transparency.
- NFR 3 (DevOps): The entire stack must be deployable via a single docker-compose up command.

### 6. Success Metrics for MVP
- Successful connection to Plaid Sandbox and retrieval of 30 days of transactions.
- Zero duplicate transactions in the database after multiple "Refresh" clicks.
- Identification of at least one "Sub-optimal" transaction where a different card would have yielded higher returns.
