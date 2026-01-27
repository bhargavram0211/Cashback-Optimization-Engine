# Cashback Optimization Engine

A financial analysis tool designed to ingest credit card transactions via Plaid and identify "Opportunity Costs" where a different card in your portfolio would have yielded higher rewards.

## ✨ Features

- **Transaction Analysis**: Automatically sync credit card transactions via Plaid API
- **Opportunity Cost Detection**: Identify where using a different card would yield higher rewards
- **Card Portfolio Management**: Manage multiple credit cards and their reward structures
- **Savings Insights**: Dashboard showing total savings, lost opportunities, and category breakdowns
- **Card Discovery**: Browse and filter available credit card products
- **Bank Integration**: Connect multiple bank accounts via Plaid
- **Mobile Responsive**: Works seamlessly on desktop, tablet, and mobile devices

## 🚀 Quick Start

This setup provides a minimal, stable environment where a FastAPI container can communicate with a PostgreSQL 16 container.

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Docker Compose installed
- 4GB+ RAM available
- Ports 3000, 8000, and 5432 available

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
   - Build and start the React frontend on port 3000
   - Wait for the database to be healthy before starting the backend

3. **Access the application**
   
   - **📊 Dashboard (Frontend)**: http://localhost:3000
     - Modern React application with savings insights and card management
   
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
| `/test-map` | POST | Test category normalization mapper |
| `/users` | POST | Create a user (for testing) |
| `/users` | GET | List all users |
| `/users/{user_id}` | GET | Get specific user |
| `/items` | POST | Create a PlaidItem (for testing) |
| `/items` | GET | List all PlaidItems |
| `/items/{item_id}` | GET | Get specific PlaidItem |
| `/sync/{item_id}` | POST | Sync transactions from Plaid |
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

- **frontend-js**: React application (Vite dev server)
  - Port: 3000
  - Platform: linux/arm64
  - Connects to backend via Docker network (reverse proxy)

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
- Ensure Docker is running and up to date

## 📁 Project Structure

```
.
├── backend/                 # Backend service
│   ├── app/                 # FastAPI application
│   │   ├── main.py          # Application entry point
│   │   ├── api/             # API endpoint routers
│   │   │   ├── sync.py      # Transaction sync endpoints
│   │   │   ├── users.py     # User management endpoints
│   │   │   ├── items.py     # PlaidItem endpoints
│   │   │   └── analytics.py # Analytics endpoints
│   │   ├── routers/         # Complex consolidated routers
│   │   │   └── reports.py   # Consolidated reports endpoint
│   │   ├── core/            # Core configurations
│   │   │   ├── database.py  # Database connection & session
│   │   │   └── plaid.py     # Plaid API client singleton
│   │   ├── logic/           # Business logic
│   │   │   └── mapper.py    # Category normalization mapper
│   │   ├── models/          # Database models
│   │   │   └── models.py    # SQLModel definitions
│   │   ├── services/        # Business services
│   │   │   ├── optimizer.py # Cashback optimization engine
│   │   │   └── analytics.py # Analytics calculations
│   │   └── schemas/         # Pydantic schemas
│   │       └── schemas.py   # API response models
│   ├── scripts/             # Backend utility scripts
│   │   ├── seed_poc_cards.py    # Seed test cards & rules
│   │   ├── audit_mappings.py    # Category mapper audit
│   │   └── update_buckets.py    # Re-map transaction categories
│   ├── Dockerfile           # Backend container definition
│   └── requirements.txt     # Backend Python dependencies
├── frontend-js/              # Frontend service (React)
│   ├── src/                  # React source code
│   │   ├── pages/            # Page components
│   │   ├── components/        # Reusable UI components
│   │   ├── api/              # API client
│   │   └── ...
│   ├── Dockerfile            # Development container
│   ├── Dockerfile.prod       # Production container (Nginx)
│   ├── nginx.conf            # Nginx reverse proxy config
│   ├── package.json          # Node.js dependencies
│   └── README.md             # Frontend documentation
├── docker-compose.yml        # Development multi-container orchestration
├── docker-compose.prod.yml   # Production deployment (registry images)
├── env.example               # Environment variables template
├── DEPLOYMENT.md             # Production deployment guide
├── DOCKER_GUIDE.md           # Docker development guide
└── README.md                 # This file
```

## 🛠️ Tech Stack

- **Backend**: Python 3.12+ with FastAPI
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Database**: PostgreSQL 16
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **External APIs**: Plaid API (transaction sync)
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx (production frontend)
- **Platform**: Multi-platform support (ARM64/AMD64)

## 📝 Development Status

**Phase 1: Core Infrastructure** ✅
- Docker, PostgreSQL, FastAPI setup
- Data models and database schema
- Category normalization mapper
- Plaid transaction sync engine

**Phase 2: Optimization Engine** ✅
- Card and reward rules registry
- Cashback optimization calculations
- Analytics and reporting services

**Phase 3: Frontend** ✅
- React application with TypeScript
- Authentication and session management
- Dashboard, Card Discovery, Bank Management
- Mobile-responsive design
- Production deployment ready

**Next Steps:**
- Enhanced analytics and time-series data
- Advanced filtering and export features
- Merchant insights and recommendations

## 🚀 Production Deployment

The application is Docker registry ready and can be deployed using pre-built images.

**Quick Start:**
1. Pull images from Docker Hub
2. Configure environment variables (see `env.example`)
3. Run `docker-compose -f docker-compose.prod.yml up -d`

For detailed deployment instructions, see **[DEPLOYMENT.md](./DEPLOYMENT.md)**.

**Key Features:**
- Reverse proxy pattern (no build-time configuration needed)
- Configurable image registry and tags
- Multi-platform support (ARM64/AMD64)
- Production-ready Nginx frontend

## 📖 Documentation

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment guide with Docker registry instructions
- **[DOCKER_GUIDE.md](./DOCKER_GUIDE.md)** - Docker development and troubleshooting guide
- **[ACID_TEST_GUIDE.md](./ACID_TEST_GUIDE.md)** - Complete guide to testing the sync engine with Plaid Sandbox
- **[srs.md](./srs.md)** - Software Requirements Specification
- **[backend/scripts/README.md](./backend/scripts/README.md)** - Backend utility scripts documentation
- **[frontend-js/README.md](./frontend-js/README.md)** - Frontend development guide

## 🧪 Testing

The application includes comprehensive testing for the sync engine and transaction processing.

**For complete testing guide**: See [ACID_TEST_GUIDE.md](./ACID_TEST_GUIDE.md)

The guide includes:
- Step-by-step instructions for end-to-end testing
- How to get a real Plaid Sandbox access token
- Database verification queries
- Troubleshooting tips

**Acid Test Results:**
- ✅ 6/6 test categories passed
- ✅ 146 transactions synced successfully
- ✅ Idempotency verified (no duplicates on second sync)
- ✅ 3-stage filter working correctly
- ✅ Category normalization applied to all transactions
- ✅ Automatic card creation validated

## 🛠️ Utility Scripts

### Category Mapping Audit
```bash
docker exec cashback-backend python scripts/audit_mappings.py
```
Analyzes coverage of the category mapper against all 123 Plaid PFCv2 categories. Shows:
- Distribution across 10 reward buckets
- Categories falling back to GENERAL
- Categories using primary fallbacks
- Coverage statistics and recommendations

## 📄 License

This is a private development project.
