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
   - Build and start the Streamlit frontend on port 8501
   - Wait for the database to be healthy before starting the backend

3. **Access the application**
   
   - **📊 Dashboard (Frontend)**: http://localhost:8501
     - Interactive Streamlit dashboard with savings insights
   
   - **🔌 API Backend**: http://localhost:8000/
     - Expected response: `{"status": "Backend is Online"}`
   
   - **📚 API Documentation**: http://localhost:8000/docs
     - Auto-generated Swagger UI
   
   - **🗄️ Database Connection Test**: http://localhost:8000/db-test
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

- **frontend**: Streamlit dashboard
  - Port: 8501
  - Platform: linux/arm64
  - Connects to backend via Docker network

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
├── app/                     # Backend application
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API endpoint routers
│   │   ├── sync.py          # Transaction sync endpoints
│   │   ├── users.py         # User management endpoints
│   │   ├── items.py         # PlaidItem endpoints
│   │   └── analytics.py     # Analytics endpoints
│   ├── routers/             # Complex consolidated routers
│   │   └── reports.py       # Consolidated reports endpoint
│   ├── core/                # Core configurations
│   │   ├── database.py      # Database connection & session
│   │   └── plaid.py         # Plaid API client singleton
│   ├── logic/               # Business logic
│   │   └── mapper.py        # Category normalization mapper
│   ├── models/              # Database models
│   │   └── models.py        # SQLModel definitions
│   ├── services/            # Business services
│   │   ├── optimizer.py     # Cashback optimization engine
│   │   └── analytics.py     # Analytics calculations
│   └── schemas/             # Pydantic schemas
│       └── schemas.py       # API response models
├── frontend/                # Streamlit dashboard
│   ├── app.py               # Main dashboard application
│   ├── Dockerfile           # Frontend container definition
│   ├── requirements.txt     # Frontend Python dependencies
│   └── README.md            # Frontend documentation
├── scripts/                 # Utility scripts
│   ├── seed_poc_cards.py    # Seed test cards & rules
│   ├── audit_mappings.py    # Category mapper audit
│   └── update_buckets.py    # Re-map transaction categories
├── docker-compose.yml       # Multi-container orchestration
├── Dockerfile               # Backend container definition
├── requirements.txt         # Backend Python dependencies
├── .env.example             # Environment variables template
├── LEARNINGS.md             # Troubleshooting guide
└── README.md                # This file
```

## 🛠️ Tech Stack

- **Backend**: Python 3.12+ with FastAPI
- **Frontend**: Streamlit with Plotly visualizations
- **Database**: PostgreSQL 16
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **External APIs**: Plaid API (transaction sync)
- **Containerization**: Docker & Docker Compose
- **Platform**: Optimized for MacBook M2 (arm64)

## 📝 Development Status

**Phase 1: Core Infrastructure** ✅
- ✅ Sub-Phase 1.1: Infrastructure Shell (Docker, PostgreSQL, FastAPI)
- ✅ Sub-Phase 1.2: Data Models (User, PlaidItem, Card, Transaction, RewardRule)
- ✅ Sub-Phase 1.3: Category Mapper (Plaid PFCv2 → 10 internal reward buckets)
  - ✅ Sub-Phase 1.3.1: Mapping Optimization (improved coverage after review)
- ✅ Sub-Phase 1.4: Sync Engine (Plaid transaction sync with 3-stage filter)
  - ✅ 145 transactions synced from Plaid Sandbox
  - ✅ 4 credit cards created
  - ✅ UPSERT logic validated (no duplicates)
  - ✅ 3-stage filter working (83.4% analyzable)

**Phase 2: Optimization Engine** ✅
- ✅ Phase 2.1: Card & Rules Registry (RewardRule model, card metadata)
- ✅ Phase 2.2: Optimization Engine
  - ✅ Seeding script with 4 POC cards
  - ✅ Optimizer service calculating opportunity cost
  - ✅ $611.86 in lost savings identified across 121 transactions
- ✅ Phase 2.3: Analytics Service
  - ✅ Savings summary endpoint
  - ✅ Category breakdown endpoint
  - ✅ Card recommendation endpoint
  - ✅ Transaction opportunities endpoint
  - ✅ Consolidated reports endpoint

**Phase 3: Frontend** ✅
- ✅ Streamlit dashboard with Docker deployment
- ✅ Top-level metrics (Spent, Earned, Lost)
- ✅ Interactive category breakdown charts
- ✅ Card recommendation display
- ✅ Transaction explorer (top 50 opportunities)
- ✅ User selection sidebar

**Next Steps:**
- Phase 4: Additional features (time-series, merchant insights)
- Production deployment considerations
- Frontend enhancements (filters, export)

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
