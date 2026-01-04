# Cashback Optimization Engine

A financial analysis tool designed to ingest credit card transactions via Plaid and identify "Opportunity Costs" where a different card in your portfolio would have yielded higher rewards.

## 🧪 Testing the Sync Engine

**For a complete guide to testing Sub-Phase 1.4, see [ACID_TEST_GUIDE.md](./ACID_TEST_GUIDE.md)**

The guide includes:
- Step-by-step instructions for end-to-end testing
- How to get a real Plaid Sandbox access token
- Database verification queries
- Troubleshooting tips

## 🚀 Quick Start (Sub-Phase 1.1: Infrastructure Shell)

This setup provides a minimal, stable environment where a FastAPI container can communicate with a PostgreSQL 16 container on your MacBook M2 (arm64).

### Prerequisites

- Docker Desktop for Mac (with Apple Silicon support)
- MacBook M2 (arm64 architecture)

### Setup Instructions

1. **Create the environment file**
   ```bash
   cp env.example .env
   ```
   
   The `.env` file contains default credentials for local development. You can modify them if needed.

2. **Build and start the containers**
   ```bash
   docker-compose up --build
   ```
   
   This will:
   - Start a PostgreSQL 16 database on port 5432
   - Build and start the FastAPI backend on port 8000
   - Wait for the database to be healthy before starting the backend

3. **Verify the setup**
   
   Open your browser and test these endpoints:
   
   - **Backend Health Check**: http://localhost:8000/
     - Expected response: `{"status": "Backend is Online"}`
   
   - **Database Connection Test**: http://localhost:8000/db-test
     - Expected response: `{"status": "Database Connected"}`

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check - verifies backend is running |
| `/db-test` | GET | Database connectivity test |
| `/test-map` | POST | Test category normalization mapper (Sub-Phase 1.3) |
| `/users` | POST | Create a user (for testing) |
| `/users` | GET | List all users |
| `/users/{user_id}` | GET | Get specific user |
| `/items` | POST | Create a PlaidItem (for testing) |
| `/items` | GET | List all PlaidItems |
| `/items/{item_id}` | GET | Get specific PlaidItem |
| `/sync/{item_id}` | POST | Sync transactions from Plaid (Sub-Phase 1.4) |
| `/docs` | GET | Auto-generated API documentation (Swagger UI) |
| `/redoc` | GET | Alternative API documentation (ReDoc) |

**Example: Test Category Mapper**
```bash
curl -X POST http://localhost:8000/test-map \
  -H "Content-Type: application/json" \
  -d '{
    "primary_category": "FOOD_AND_DRINK",
    "detailed_category": "FOOD_AND_DRINK_RESTAURANT"
  }'

# Response:
# {
#   "primary_category": "FOOD_AND_DRINK",
#   "detailed_category": "FOOD_AND_DRINK_RESTAURANT",
#   "internal_bucket": "DINING",
#   "tier_used": "detailed"
# }
```

**Example: Sync Transactions**
```bash
# Sync transactions for a specific Plaid item
curl -X POST http://localhost:8000/sync/{item_id}

# Response:
# {
#   "item_id": "550e8400-e29b-41d4-a716-446655440000",
#   "transactions_added": 15,
#   "transactions_updated": 2,
#   "transactions_removed": 0,
#   "accounts_synced": 3,
#   "cursor_updated": true
# }
```

### Docker Services

- **db**: PostgreSQL 16 database
  - Port: 5432
  - Platform: linux/arm64
  - Healthcheck enabled
  
- **backend**: FastAPI application
  - Port: 8000
  - Platform: linux/arm64
  - Hot-reload enabled (code changes reflect automatically)

### Stopping the Services

```bash
# Stop containers (keeps data)
docker-compose down

# Stop containers and remove volumes (clears database)
docker-compose down -v
```

### Troubleshooting

**Database connection fails:**
- Ensure Docker Desktop is running
- Check if port 5432 is available: `lsof -i :5432`
- Verify the database is healthy: `docker-compose ps`

**Backend not accessible:**
- Ensure port 8000 is available: `lsof -i :8000`
- Check backend logs: `docker-compose logs backend`

**Build fails:**
- Clear Docker cache: `docker-compose build --no-cache`
- Ensure you're using the latest Docker Desktop for Apple Silicon

## 📁 Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API endpoints (future)
│   ├── core/                # Core configurations (future)
│   ├── logic/               # Business logic (future)
│   └── models/              # Database models (future)
├── docker-compose.yml       # Multi-container orchestration
├── Dockerfile               # Backend container definition
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🛠️ Tech Stack

- **Backend**: Python 3.12+ with FastAPI
- **Database**: PostgreSQL 16
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Containerization**: Docker & Docker Compose
- **Platform**: Optimized for MacBook M2 (arm64)

## 📝 Development Status

**Completed:**
- ✅ Sub-Phase 1.1: Infrastructure Shell (Docker, PostgreSQL, FastAPI)
- ✅ Sub-Phase 1.2: Data Models (User, PlaidItem, Card, Transaction)
- ✅ Sub-Phase 1.3: Category Mapper (Plaid PFCv2 → 10 internal reward buckets)
  - ✅ Sub-Phase 1.3.1: Mapping Optimization (74.2% spending coverage)
- ✅ Sub-Phase 1.4: Sync Engine (Plaid transaction sync with 3-stage filter)
  - ✅ Acid Test Complete: 6/6 test categories passed
  - ✅ 146 transactions synced from Plaid Sandbox
  - ✅ 2 credit cards automatically created
  - ✅ UPSERT logic validated (no duplicates)
  - ✅ 3-stage filter working (83.6% analyzable, 16.4% non-analyzable)

**Known Issue:**
- ⚠️ `internal_bucket` field missing from Transaction model (fix in progress)

**Next Steps:**
- Fix: Add `internal_bucket` field to Transaction model
- Sub-Phase 1.5: Optimization Engine (calculate best_card_id, lost_savings)
- Reward rules management
- Streamlit dashboard

## 📖 Documentation

- **[LEARNINGS.md](LEARNINGS.md)** - Comprehensive troubleshooting guide with all issues encountered and solutions across Sub-Phases 1.1-1.4
- **[ACID_TEST_GUIDE.md](ACID_TEST_GUIDE.md)** - Complete guide to testing the sync engine with Plaid Sandbox
- **[srs.md](srs.md)** - Software Requirements Specification
- **[scripts/README.md](scripts/README.md)** - Utility scripts documentation

## 🧪 Testing

**Acid Test Results (Sub-Phase 1.4):**
- ✅ 6/6 test categories passed
- ✅ 146 transactions synced successfully
- ✅ Idempotency verified (no duplicates on second sync)
- ✅ 3-stage filter working correctly
- ✅ Category normalization applied to all transactions
- ✅ Automatic card creation validated

See [ACID_TEST_GUIDE.md](./ACID_TEST_GUIDE.md) for detailed testing instructions.

## 🛠️ Utility Scripts

### Category Mapping Audit
```bash
python scripts/audit_mappings.py
```
Analyzes coverage of the category mapper against all 123 Plaid PFCv2 categories. Shows:
- Distribution across 10 reward buckets
- Categories falling back to GENERAL
- Categories using primary fallbacks
- Coverage statistics and recommendations

## 📄 License

This is a private development project.
